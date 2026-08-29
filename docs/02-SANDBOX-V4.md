# 02 · Sandbox — tầng nền

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · **02 Sandbox** · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md)

> **Đây là tham chiếu chuẩn cho tầng nền.** File gốc `genesis-zero-plan (4).md` giữ nguyên làm
> hồ sơ lịch sử; chỗ nào lệch thì tin tài liệu này. Tầng luật ẩn xây lên trên: [03](03-LUAT-AN-V5.md).

## 1. Dàn nhân vật

| # | Loài | Model (Lab mode) | Số con | Vai |
|---|---|---|---|---|
| L1 | Apex | Gemma-2-9B-it | 2 | Săn mồi đầu bảng, não to nhất |
| L2 | Phục kích | Llama-3.1-8B-Instruct | 2 | Đánh mạnh, chậm, núp bụi |
| L3 | Thích nghi | Mistral-7B-Instruct-v0.3 | 3 | Ăn tạp, mắt tinh, cơ động |
| L4 | Giáp | Phi-3.5-mini-instruct | 3 | Ăn xác thối, lì đòn, não nhỏ |
| L5 | Độc | Qwen2.5-1.5B-Instruct | 5 | Nhanh, mỏng manh, có độc |

Tháp sinh thái 2/2/3/3/5 = **15 con** trên lưới 24×24 (38 ô/con). Số này là **một dòng trong `config.py`** — nhưng phân bổ phần cứng và mọi hằng số đều tính từ nó.

## 2. Vector trait — bất biến tổng bằng 12

| Loài | brain | attack | armor | speed | sense | stomach |
|---|---|---|---|---|---|---|
| L1 | 4 | 3 | 1 | 2 | 1 | 1 |
| L2 | 3 | 4 | 2 | 1 | 2 | 0 |
| L3 | 3 | 1 | 1 | 3 | 3 | 1 |
| L4 | 1 | 1 | 5 | 1 | 2 | 2 |
| L5 | 0 | 2 | 0 | 5 | 3 | 2 |

Mỗi trait 0–5, **tổng luôn đúng 12**. Bất biến này nằm trong `Traits.__post_init__` để không đường nào lách được, và nó là thứ khiến chống gian lận ở chế độ mở hoạt động ([04 §7.1](04-THE-GIOI-MO.md)).

Chỉ số dẫn xuất — công thức ở `config.py`, đừng chép số vào code:

| Loài | token_budget | think_interval | damage | giảm dmg | ô/tick | tầm nhìn | energy_max | upkeep |
|---|---|---|---|---|---|---|---|---|
| L1 | 176 | 3 | 13 | 12% | 2 | 3 | 93 | 3.50 |
| L2 | 140 | 4 | 16 | 24% | 1 | 4 | 85 | 3.35 |
| L3 | 140 | 4 | 7 | 12% | 2 | 5 | 93 | 3.35 |
| L4 | 68 | 6 | 7 | 60% | 1 | 4 | 101 | 3.40 |
| L5 | 32 | 7 | 10 | 0% | 3 | 5 | 101 | 3.80 |

> **Cập nhật W-12 (2026-08-28).** `energy_max` và `upkeep` đã đổi so với v4 §1.4 sau mốc tune:
> `ENERGY_BASE` 60→85, `ENERGY_PER_STOMACH` 20→8, `UPKEEP_STOMACH` 0.05→0.25.
> Lý do và số liệu ở [01-STATUS](01-STATUS.md).

**Khả năng cố định theo loài** (không nằm trong vector, không tiến hoá):
- L5 có **độc** — kẻ tấn công L5 chịu 3 sát thương/tick trong 5 tick.
- L4 **ăn xác thối** không mất máu; loài khác ăn xác chỉ nhận 50% năng lượng.

> Kiểm tra nhanh: L1 upkeep 3.30/tick, energy_max 80 → **~18 tick là chết đói** nếu không ăn (đã tính chi phí nghĩ). L4 sống được ~31 tick. **Não to phải kiếm ăn giỏi hơn ~70% chỉ để hoà vốn.** Đó là chủ ý.

## 3. Kiến trúc: mỗi cá thể một tâm trí

| Tầng | Ánh xạ sinh học | Hiện thực |
|---|---|---|
| Weights của model | Loài — bản năng chung | 1 tiến trình `llama-server` / loài |
| Slot + KV cache | Cá thể — trải nghiệm sống riêng | `-np N`, mỗi con **ghim cứng** 1 slot |
| Trait vector | Cơ thể | `creature.traits` |

Hai con L1 dùng chung weights nhưng khác KV cache → **hai tâm trí riêng biệt tình cờ chung một bộ não vật lý.** Chúng hiểu lầm nhau, bỏ rơi nhau, tranh nhau miếng mồi.

**Ghim slot là bắt buộc, không phải tối ưu.** Không ghim thì mỗi lần gọi phải prefill lại từ đầu.

**Lệch pha:** cá thể thứ *k* nghĩ ở tick thoả `tick % think_interval == offset_k`, offset rải đều. Cùng tổng tải, không dồn cục.

> **Bẫy `-c`:** trong `llama-server`, `-c` là **tổng** KV chia cho mọi slot. Muốn mỗi slot 3072 với 3 slot thì `-c 9216`. Sai chỗ này biểu hiện thành "model tự dưng quên hết", **không báo lỗi**. Cỡ context cho v5 ở [03 §7.4](03-LUAT-AN-V5.md).

## 4. Ba mươi sáu bước gốc → phiếu việc

### M0 — Thế giới câm
- **Bước 1** RNG + config → [W-01](tasks/W-01-rng-config.md)
- **Bước 2** Lưới, địa hình → [W-02](tasks/W-02-luoi-dia-hinh.md)
- **Bước 3** Thức ăn → [W-03](tasks/W-03-thuc-an.md)
- **Bước 4** Creature + năng lượng → [W-04](tasks/W-04-creature.md)
- **Bước 5** Ăn, chết, hồi sinh → [W-05](tasks/W-05-an-chet-hoi-sinh.md)
- **Bước 6** Render + log → [W-06](tasks/W-06-render-log.md)

### M1 — Trait, chiến đấu, thích nghi  ★ mốc tune
- **Bước 7** Trait vector → [W-07](tasks/W-07-trait.md)
- **Bước 8** Tầm nhìn → [W-08](tasks/W-08-tam-nhin.md)
- **Bước 9** Tầng phản xạ → [W-09](tasks/W-09-phan-xa.md)
- **Bước 10** Chiến đấu → [W-10](tasks/W-10-chien-dau.md)
- **Bước 11** Vòng tick → [W-11](tasks/W-11-vong-tick.md)
- **Bước 12** Thích nghi → [W-12](tasks/W-12-thich-nghi.md)

### M2 — Một cá thể có tâm trí
- **Bước 13** Schema → [B-01](tasks/B-01-schema.md) · **Bước 14** Prompt → [B-02](tasks/B-02-prompt.md)
- **Bước 15** Client → [B-03](tasks/B-03-llm-client.md) · **Bước 16** Xác thực → [B-04](tasks/B-04-xac-thuc.md)
- **Bước 17** Ghép tick → [B-05](tasks/B-05-ghep-tick.md) · **Bước 18** Replay → [B-06](tasks/B-06-replay.md)

### M3 — Phân tán 5 node
Bước 19–23 (registry, dựng 5 server, async, circuit breaker, đo baseline). Ở v5, M3 **bị hấp thụ vào track N** — cùng một khái niệm ở quy mô rộng hơn. Xem [04](04-THE-GIOI-MO.md).

### M4 — Giao tiếp, danh tiếng
- **Bước 24–25** Nói + danh tiếng → [B-11](tasks/B-11-noi-danh-tieng.md)
- **Bước 26** LLM chọn hướng dịch trait → [B-13](tasks/B-13-dich-trait-llm.md)
- **Bước 27–28** Thí nghiệm Q1/Q2 → **thay bằng** [03 §9](03-LUAT-AN-V5.md) và track X

### M5 — Đồ hoạ · M6 — Chế độ mở
Bước 29–32 → X-07. Bước 31–36 → **thay bằng** track N ([04](04-THE-GIOI-MO.md), [05](05-GIAO-THUC.md)).

## 5. Tạo hình sinh vật

**Cơ thể = vector trait. Không thêm dữ liệu tạo hình nào cả.** Ở chế độ mở, loài do người lạ tạo lúc chạy — không thể vẽ sprite trước cho loài chưa tồn tại.

| Trait | Bộ phận |
|---|---|
| `stomach` | bề ngang thân |
| `speed` | số chân, độ dài chân, thân thon dài |
| `brain` | kích thước đầu |
| `sense` | kích thước và độ tách của mắt |
| `armor` | số tấm giáp dọc sống lưng, độ dày viền |
| `attack` | số và độ dài nanh/vuốt |

Màu: `hue = hash(species_id) % 360`, độ sáng theo `energy / energy_max`. Cá thể cùng loài lệch hue ±10° theo `hash(creature_id)`.

> **Cập nhật 2026-08-28 — hình 3D bằng MeshyAI ([N-13](tasks/N-13-mesh-3d.md)).** Mesh 3D sinh từ
> **chính vector trait** (dùng lại khối C của [B-02](tasks/B-02-prompt.md)), cache theo `md5(trait)` chứ
> không theo người chơi. Bất biến "cơ thể = vector trait" **giữ nguyên**; primitive procedural vẫn là
> lớp nền luôn chạy được. Trait dịch → sinh mesh mới ở nền, giữ mesh cũ tới khi xong.

**Một cấm kỵ:** kích thước trên màn hình **không được** phụ thuộc cỡ model. Client chạy 70B mà con vật to hơn thì hàm ý một lợi thế không hề tồn tại.

**Bầy đàn: đừng tạo class `Pack`.** Bầy là thuộc tính nổi lên — cùng loài + trong tầm, tính lại mỗi frame. Cách vẽ có giá trị nhất là **đồ thị "ai nghe được ai"**: nối đường mảnh giữa các con trong tầm nghe của nhau, nhấp nháy khi có `SPEAK`. Nó làm bất đối xứng thông tin hiện ra bằng mắt — cảnh quay đắt giá nhất của cả dự án, và gần như miễn phí vì dữ liệu đã có trong log.

## 6. Rủi ro còn nguyên từ v4

1. **Mọi hằng số là phỏng đoán.** M1 tồn tại để tune chúng.
2. **Ngân sách 12 điểm có thể quá chật.** Nếu M1 cho thấy mọi con đều èo uột, nới lên 15.
3. **Phương sai.** Chạy nhiều seed và **không kể chuyện dựa trên một ván** — cám dỗ sẽ rất mạnh.
4. **LLM có thể thua reflex if-else.** Nếu xảy ra thì báo cáo đúng như vậy; đó mới là điều làm dự án đáng tin.
5. **`note` không phải suy luận.** Nó là dữ liệu debug và chất liệu video, không phải bằng chứng.
