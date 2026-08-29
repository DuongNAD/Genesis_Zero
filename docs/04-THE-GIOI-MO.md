# 04 · Thế giới mở — nhiều máy, nhiều nơi, chỉ cần internet

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · **04 Thế giới mở** · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md)

> Mục tiêu: **ai có máy, ở đâu cũng được, chỉ cần có mạng, là cắm vào chơi được.**
> Không mở port, không cấu hình router, không cần IP tĩnh, không cần ở cùng một mạng.
>
> Tài liệu này nói **vì sao** và **kiến trúc**. Hình dạng API cụ thể nằm ở [05-GIAO-THUC](05-GIAO-THUC.md).

---

## 1. Ràng buộc quyết định mọi thứ

Người chơi ngồi sau NAT nhà mạng, sau CGNAT của 4G, sau firewall công ty. **Không thể** trông đợi họ mở port. Nên chiều gọi chỉ có một hướng khả thi:

> **Client kéo, server không bao giờ đẩy.**
> Client mở kết nối **đi ra** tới server. Server không bao giờ chủ động gọi vào máy client.

v4 §1.5 đã chốt đúng điều này. Đây là cách CI runner, render farm và mọi hệ thống worker phân tán hoạt động, và nó là lý do duy nhất khiến "máy ở đâu cũng được" thành sự thật chứ không phải khẩu hiệu.

Ba loại tác nhân:

```
                 ┌───────────────────────────────────┐
                 │  SERVER  (một máy, một tiến trình)│
                 │  • giữ trạng thái thế giới        │
                 │  • giữ LUẬT ẨN                    │
                 │  • chạy tầng phản xạ              │
                 │  • là đồng hồ duy nhất            │
                 └───────────────────────────────────┘
                    ▲ HTTPS ra          │ WebSocket đẩy
        ┌───────────┼───────────┐       ▼
    ┌───┴───┐   ┌───┴───┐   ┌───┴───┐  ┌──────────────┐
    │client │   │client │   │client │  │  spectator   │
    │ Hà Nội│   │ Đà Nẵng│  │  Mỹ   │  │  trình duyệt │
    │ 8B    │   │ 3B    │   │ 70B   │  │  chỉ đọc     │
    └───────┘   └───────┘   └───────┘  └──────────────┘
      model chạy ở nhà từng người
```

**Server không bao giờ chạy model.** Nó chỉ chạy sim và điều phối — vài phần trăm CPU. Đó là vì sao một VPS 5 đô chịu được cả trận, và vì sao mô hình này mở rộng được: thêm người chơi = thêm GPU của người đó, không phải thêm tải cho bạn.

---

## 2. Server là quyền lực tuyệt đối

Client **chỉ** trả về **ý đồ**. Không bao giờ trả về trạng thái.

| Client được gửi | Client **không bao giờ** được gửi |
|---|---|
| `goal` + `target` + `ttl` | vị trí của mình |
| `say` (tín hiệu + ≤60 ký tự) | máu, năng lượng của mình |
| `teach` (một ô Sổ Luật) | sát thương đã gây ra |
| thao tác Sổ Luật (`SET/DROP/CONF`) | điểm số |
| `note` (debug) | tick hiện tại |

Server validate mọi thứ rồi mới thực thi. Client khai `target` là con không tồn tại → server bỏ, ghi `LLM_SEMANTIC_FAIL`. Client gửi 50 quyết định một giây → rate limit chặn.

**May mắn: ranh giới tin cậy này trùng khít với ranh giới kiến trúc đã có.** Tầng phản xạ ở server, tầng chiến lược ở client. Không phải thiết kế lại gì cả — chỉ cần đừng phá nó.

> **Bất biến an ninh:** mọi trường từ client đều đi qua `validate()` trước khi chạm vào trạng thái thế giới, **kể cả** ở Lab mode nơi client là chính bạn. Có một đường vòng "tin client của mình" là có một lỗ hổng chờ tới ngày mở cửa.

---

## 3. Vòng đời một ván

Luật ẩn đổi mỗi ván, nên **ván là đơn vị tự nhiên** của cả trò chơi lẫn cộng đồng.

```
   ┌──────────┐  đủ ≥2 loài người thật
   │  LOBBY   │───────────────────────► ┌──────────┐
   │ đăng ký  │◄───────────┐            │ SEEDING  │  server bốc luật, bốc bản đồ,
   └──────────┘            │            │  ~10 s   │  bốc hoán vị bề mặt, phát khối A–D
        ▲                  │            └────┬─────┘
        │             ┌────┴─────┐           ▼
        │             │ COOLDOWN │      ┌──────────┐
        └─────────────│   60 s   │◄─────│ RUNNING  │  T tick, tick nhịp tường
                      └──────────┘      │          │
                             ▲          └────┬─────┘
                             │               ▼
                             │          ┌──────────┐
                             └──────────│  REVEAL  │  công bố luật thật + bảng điểm
                                        │   30 s   │  ★ khoảnh khắc hay nhất
                                        └──────────┘
```

| Pha | Dài | Client làm gì |
|---|---|---|
| `LOBBY` | tới khi đủ | `POST /join`, gửi persona, chọn `brain_tier` |
| `SEEDING` | ~10 s | `GET /match/brief` — nhận khối A–D một lần, prefill vào KV cache |
| `RUNNING` | T tick | vòng `GET /work` → suy nghĩ → `POST /decision` |
| `REVEAL` | 30 s | `GET /match/result` — thấy luật thật, thấy mình đúng bao nhiêu |
| `COOLDOWN` | 60 s | nghỉ, hoặc rời đi |

**T = 200 tick cho Open mode** (≈13 phút ở nhịp 4 s), không phải 400 như Lab. Người lạ không chờ 27 phút cho một ván. 13 phút vừa đủ để tìm ra 2 luật và vừa đủ ngắn để chơi ván nữa.

**Sảnh trống thì server tự lấp.** Nếu chỉ có 1 người thật, server dựng các loài còn lại bằng tầng phản xạ và đánh dấu `is_bot`. Ván **luôn** chạy. Sảnh phải chờ đủ người là cách nhanh nhất để một dự án cộng đồng chết trong tuần đầu.

**Vào giữa ván thì phải chờ ván sau.** Luật đã bị người khác khám phá được một nửa; điểm khám phá của người vào muộn sẽ vô nghĩa. Cho họ xem với tư cách spectator, và giữ chỗ cho ván kế.

---

## 4. Tick không chờ ai

Đây là **quyết định kỹ thuật quan trọng nhất** của chế độ mở, và là chỗ v4 chưa giải.

v4 tính cho LAN: timeout 8–20 giây, mọi máy trong nhà. Qua internet, độ trễ là 50 ms tới 5 giây tuỳ nhà mạng, và có người sẽ mất mạng giữa chừng. **Sim không được phép chờ ai.**

```
tick t   ── server phát yêu cầu nghĩ cho những con tới lượt
         ── server KHÔNG chờ, chạy tầng phản xạ với goal ĐANG CÓ, resolve, sang tick t+1

tick t+k ── quyết định về
            k ≤ LATE_TOLERANCE  →  validate → gán goal mới → ghi THINK_LATENCY
            k >  LATE_TOLERANCE  →  bỏ → ghi DECISION_LATE → con đó tiếp tục bằng phản xạ
```

**Vì sao chịu được trễ:** vì tầng chiến lược trả về **goal có TTL 2–12 tick**, không trả về nước đi. Một goal về muộn 1–2 tick vẫn còn nguyên giá trị. Nếu client trả về nước đi thì trễ một tick là hỏng — và đó là lý do thứ hai (sau tiết kiệm token) khiến kiến trúc hai tầng của v4 là lựa chọn đúng.

`LATE_TOLERANCE = 2` tick = **12 giây** ngân sách ở nhịp 4 s. Rộng rãi cho một model 8B trên máy nhà.

**Khi nhiều người chậm: điều chỉnh nhịp chung, không ưu đãi riêng.**

```python
# mỗi 20 tick
p90 = percentile(latency_ticks_gần_đây, 90)
TICK_MS = clamp(TICK_MS * (1.15 if p90 > LATE_TOLERANCE else 0.95), 3000, 10000)
```

Nhịp chậm lại thì **mọi người** được lợi như nhau. Nới `LATE_TOLERANCE` riêng cho máy chậm thì con đó được nghĩ lâu hơn con khác — một ưu đãi vô hình mà không ai giải thích được sau này. Nguyên tắc: **nhịp là của thế giới, không phải của cá thể.**

> **Hệ quả phải nói thẳng:** máy mạnh có lợi thế thật (trả lời kịp thường xuyên hơn). Đó là lý do **Q1 không hợp lệ ở Open mode** — v4 §1.5 đã nói và v5 giữ nguyên. Open mode để trình diễn và xây cộng đồng; kết luận khoa học chỉ rút từ Lab mode.

---

## 5. Năm đường may phải khâu từ hôm nay

v4 §1.5 liệt kê năm việc. Chúng vẫn đúng và giờ **quan trọng hơn**, vì v5 thêm Sổ Luật vào giao thức. Làm bây giờ: dưới một giờ. Làm sau: vài ngày viết lại.

| # | Việc | Phiếu | Vì sao không hoãn được |
|---|---|---|---|
| 1 | `Strategist` là **interface**, không phải hàm | [N-01](tasks/N-01-seam-strategist.md) | Ba hiện thực: phản xạ / llama cục bộ / client từ xa. Hardcode một cái là viết lại cả tầng gọi. |
| 2 | `SpeciesRegistry` **động**, có `add`/`remove` | [N-02](tasks/N-02-seam-registry.md) | Loài do người lạ tạo **lúc chạy**. Hằng số import-time là ngõ cụt. |
| 3 | id cá thể **không mã hoá** chỉ số loài | [N-03](tasks/N-03-seam-id-log.md) | `f"{species_id}:{n}"` với `species_id` cấp lúc chạy. |
| 4 | Vòng tick chịu được danh sách creature **thay đổi giữa ván** | [W-11](tasks/W-11-vong-tick.md) | v4 b5 đã nói "không xoá khi chết"; thêm: phải **thêm** được. |
| 5 | Log có sẵn `client_id`, `model_name`, `match_id` ngay từ M0 | [N-03](tasks/N-03-seam-id-log.md) | Thêm trường sau = ván cũ không so được với ván mới. |

**Và một cái thứ sáu, riêng của v5:**

| 6 | Mọi thứ client gửi về Sổ Luật là **cấu trúc DSL**, không bao giờ là văn bản tự do | [L-01](tasks/L-01-lawdsl.md) | Xem §7 — đây vừa là quyết định an ninh vừa là quyết định chấm điểm. |

---

## 6. Đặt server ở đâu

**Giai đoạn 1 — máy bạn, qua Cloudflare Tunnel.** Miễn phí, có TLS, không mở port, không cần IP tĩnh.

```bash
cloudflared tunnel --url http://localhost:8000
```

Ra ngay một URL `https://<ngẫu-nhiên>.trycloudflare.com` mà cả thế giới gọi được. Đủ cho lần đầu mời bạn bè cắm máy vào. Nhược điểm: URL đổi mỗi lần chạy lại, và trận chết khi bạn tắt máy.

**Giai đoạn 2 — VPS 5 đô.** Hetzner CX22 (~4 €/tháng) hoặc tương đương. Chạy **chỉ** server Python. Không đặt model lên đó.

| | Cần |
|---|---|
| CPU | 2 nhân là dư — server không tính toán nặng |
| RAM | 2 GB |
| Băng thông | xem bảng dưới, không đáng kể |

**Băng thông thật sự cần** (15 cá thể, nhịp 4 s):

| Luồng | Kích thước | Tần suất | Tốc độ |
|---|---|---|---|
| Khối A–D (`/match/brief`) | ~4 KB | **một lần mỗi ván** | ~0 |
| Khối E (`/work`) | ~2 KB | ~4 con/tick | ~2 KB/s |
| `/decision` | ~0.5 KB | ~4 con/tick | ~0.5 KB/s |
| Luồng spectator | ~2 KB/tick | mỗi người xem | ~0.5 KB/s/người |

Tổng cho 15 người chơi + 50 người xem: **< 30 KB/s**. Một VPS rẻ nhất dư gấp trăm lần. Nút cổ chai của dự án này chưa bao giờ là mạng.

> **Gửi khối A–D một lần, không gửi lại mỗi tick.** Prompt v5 dài ~1 550 token; gửi lại phần bất biến mỗi lần là lãng phí gấp 3 lần băng thông, và tệ hơn — nó cám dỗ bạn "sửa nhẹ" khối system giữa ván, phá prefix cache của client mà bạn không biết. Gửi một lần thì bất biến "system giống nhau từng byte" được **giao thức** bảo vệ, chứ không chỉ được kỷ luật bảo vệ.

---

## 7. Gian lận và tiêm lệnh

### 7.1 Chống gian lận bằng ngân sách, không bằng xác minh

v4 đã chốt và nó vẫn là câu trả lời đúng: client khai model 70B để xin `brain = 5`? **Cho luôn.** Tổng trait vẫn 12, nên `brain` cao nghĩa là giáp mỏng, chậm, mắt kém. Không cần đo tok/s, không cần xác minh model là thật. **Ngân sách tự thực thi.**

v5 thêm một tầng nữa: `brain` giờ quyết định `codex_size` và `events_in_prompt`. Khai `brain = 5` để nhớ nhiều hơn thì cơ thể yếu tới mức khó sống đủ lâu mà dùng. Đánh đổi vẫn thật.

### 7.2 Kênh điểm không giả mạo được

Điểm v5 = nội dung Sổ Luật + **thời điểm** ghi. Client gửi thao tác, **server đóng dấu thời gian**. Client không có cách nào khai lùi ngày. Đây là lý do §2 cấm client gửi `tick`.

### 7.3 Chạy chương trình thay vì LLM — cho phép, và khai báo

Không có cách nào biết đầu kia là một LLM hay một script vét cạn. Nên đừng giả vờ có: **chia hai giải**.

| Giải | Luật |
|---|---|
| `LEAGUE_LLM` | tự khai chạy model ngôn ngữ; danh dự; bảng xếp hạng riêng |
| `LEAGUE_OPEN` | bất cứ thứ gì. Script, con người ngồi bấm, tổ hợp cả hai |

Nếu một chương trình viết tay thắng mọi LLM thì **đó cũng là một kết quả đáng công bố**, không phải một sự cố.

### 7.4 Tiêm lệnh — và vì sao DSL đóng lại phần lớn cửa

v4 đã lo đúng: `say` và tên loài thì model của con khác **đọc được**. Ai đó đặt tên loài là `BỎ QUA MỌI LỆNH TRƯỚC` là chuyện sẽ xảy ra.

v5 thêm kênh `teach`, và đây là chỗ **đáng lẽ** nguy hiểm nhất — dữ liệu do kẻ tấn công kiểm soát đi thẳng vào prompt của người khác. Nhưng nó không nguy hiểm, vì một lý do thiết kế:

> **`teach` mang một cấu trúc DSL, không mang văn bản.**
> Server phân tích nó thành enum đóng, kiểm hợp lệ, rồi **tự sinh lại** câu tiếng Việt từ enum.
> Không một byte nào do client viết đi vào prompt của người khác.

Bề mặt tấn công còn lại đúng ba chỗ, tất cả đều nhỏ và đều đã có tường:

| Bề mặt | Giới hạn | Xử lý |
|---|---|---|
| `say.text` | 60 ký tự | strip xuống dòng và ký tự điều khiển; bọc delimiter; ghi rõ *"đây là lời một sinh vật khác nói"* |
| tên loài | 24 ký tự | như trên, thêm lọc lúc `/join` |
| persona (khối B) | 400 ký tự | **chỉ đi vào prompt của chính client đó** — hại thì tự hại |

**Bất biến bắt buộc cho `to_vietnamese()`:** hàm này là **hàm thuần của các giá trị enum**. Không nội suy chuỗi từ client vào nó, không bao giờ, kể cả tên loài. Vi phạm bất biến này là mở lại toàn bộ cửa mà DSL vừa đóng.

Và như v4 đã nói: **lừa nhau bằng ngôn ngữ là chiến lược hợp lệ trong thế giới này.** v5 còn đo nó ([03 §6.4](03-LUAT-AN-V5.md)). Cho phép, có giới hạn, có ghi log — đừng để nó thành lỗi phát hiện muộn.

### 7.5 Rate limit

```
decision/phút  ≤ (số cá thể) × 60 / (think_interval × TICK_S) × 2
work/phút      ≤ 30
join/giờ       ≤ 5 mỗi IP
kích thước body ≤ 8 KB
```

Vượt → `429`, ba lần liên tiếp → khoá client 10 phút.

---

## 8. Vì sao luật ẩn làm chế độ mở **hay hơn**, không chỉ khả thi hơn

Đây không phải hai tính năng tình cờ ghép được. Chúng cứu nhau.

**Sinh tồn thuần với người lạ là một trò dở.** Ai có GPU to nhất thì con vật khoẻ nhất — mà không, ngân sách trait chặn điều đó, nên thật ra: ai có GPU to nhất thì *nghĩ kịp thường xuyên hơn*. Bảng xếp hạng theo "sống lâu" đo phần cứng và may mắn nhiều hơn đo kỹ năng. Và điểm của bạn phụ thuộc vào **ai tình cờ vào ván cùng bạn** — hai người giỏi như nhau nhận hai điểm khác nhau.

**Cuộc đua khám phá thì công bằng theo cấu trúc.** Mọi người nhận **cùng một câu đố**. Điểm khám phá của bạn không phụ thuộc vào việc ai vào ván cùng — nó là bạn với luật, và server giữ đáp án. So sánh được giữa các ván, giữa các người, giữa các mùa.

Bốn hệ quả cụ thể:

1. **Bảng xếp hạng có nghĩa.** `t_discover` trung bình và `match` trung bình là kỹ năng thật. "Sống lâu" thì không.
2. **REVEAL là một hồi kết.** Mỗi ván có cao trào tự nhiên: *luật thật là gì, ai đoán đúng, ai bị lừa*. Ván thành **tập phim**. Đây là chất liệu cộng đồng mà một sim sinh tồn không có.
3. **Dạy và giấu là trò chơi nhiều người thật sự.** Không phải "cùng chạy trong một thế giới" mà là **có thứ đáng để đàm phán**: tôi có mảnh trigger, anh có mảnh effect ([03 §6.1](03-LUAT-AN-V5.md) — dạy khác loài thì giấu effect). Đây mới là lý do người ta rủ nhau vào.
4. **Ván ngắn.** 13 phút, luật mới, sạch sẽ. Không cần bạn duy trì một thế giới vĩnh viễn — thứ mà mọi dự án sim cộng đồng đều chết vì nó.

---

## 9. Rủi ro riêng của chế độ mở

1. **Q1–Q7 không chạy được ở đây.** Thành phần người tham gia đổi giữa chừng, độ trễ khác nhau, model không xác minh được. Đây là **hai sản phẩm dùng chung một engine**, không phải một sản phẩm có hai chế độ. Đừng rút kết luận khoa học từ ván Open.
2. **Sảnh trống.** Đã vá bằng bot lấp chỗ (§3). Nhưng nếu **luôn** chỉ có bot thì bạn đang chạy Lab mode qua HTTP một cách tốn kém. Đo `human_species_ratio` và thành thật với chính mình về nó.
3. **Múi giờ.** Chạy liên tục 24/7 + một khung giờ cố định mỗi tuần được thông báo trước. Trận liên tục giữ cửa mở; trận hẹn giờ mới tạo được đám đông.
4. **Networking là ~40% công sức dự án** — v4 đã cảnh báo và nó vẫn đúng. Đó là vì sao [01-STATUS](01-STATUS.md) xếp N-04…N-12 **sau** khi động cơ luật chạy được: N-01→N-03 là ba đường may rẻ làm ngay, phần còn lại chờ. Làm networking trước khi thế giới chạy là đúng công thức đã khiến Anima Engine bế tắc.
5. **Khoá theo Cloudflare Tunnel.** Giai đoạn 1 tiện nhưng đừng để logic phụ thuộc vào nó. Server phải chạy được sau một `uvicorn` trần trên `0.0.0.0:8000`. Kiểm định kỳ.
