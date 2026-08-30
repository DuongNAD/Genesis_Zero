# W-18 · Ba tầng — nước, cạn, trời

| | |
|---|---|
| **Track** | World · **Phụ thuộc** W-13, W-15, L-05 · **Chặn** X-10 |
| **File** | `genesis/domain.py` (mới) · sửa `world`, `maps`, `tick`, `reflex`, `traits`, `config`, `lawgen` |
| **Ước lượng** | ~600 dòng · 6–8 giờ, chia ba chặng |
| **Giao cho model rẻ?** | ❌ tự viết — nó đụng `passable`, vòng tick, và cổng lọc luật |
| **Tài liệu gốc** | phiếu này |

## 1. Câu hỏi sinh ra nó

> *"Map không quá to nhưng phải đầy đủ, đủ thứ để có thật nhiều biến số và môi
> trường sinh thái — sư tử không biết trèo cây nhưng khỉ thì biết. Cá nữa, hồ,
> ao, biển, các thứ sinh vật dưới nước, trên cạn, trên trời."*

Hiện tại năm bản đồ chỉ đổi **hình dạng**, không đổi **ai đi được đâu**.
`World.passable(pos, creature=None)` đã có sẵn tham số `creature` từ đầu và
**chưa bao giờ dùng tới nó** — mọi sinh vật đi được đúng những ô như nhau. Nên
`HOANG_MAC` với `QUAN_DAO` khác nhau về mật độ, không khác nhau về **ổ sinh
thái**: không có chỗ nào mà loài này tới được còn loài kia thì không.

Không có chỗ trốn thì không có kẻ săn và con mồi, chỉ có mười lăm con vật cùng
đi lại trên cùng một mặt phẳng.

## 2. Vì sao việc này KHÔNG phải trang trí

Đây là chỗ dễ hiểu lầm nhất của phiếu, nên nói trước.

Genesis Zero đo đúng một thứ: **agent có quy nạp ra được luật ẩn không.** Thêm cá
và chim nghe như thêm nội dung cho vui. Nó không phải.

Ba tầng **chia lại ai quan sát được cái gì** — và đó chính là phiên bản sâu nhất
của [Gate D](L-05-gate-bc.md) (*luật này có phát biểu được không*). Một con cá
**không bao giờ** quan sát được luật về lửa: không phải vì nó ngu, mà vì nó chưa
bao giờ đứng gần lửa. Một con chim thấy cả bản đồ nhưng chạm được rất ít.

Nói cách khác: hôm nay Gate D hỏi *"brain 0 có nói nổi luật này không"*. Sau phiếu
này nó phải hỏi *"tầng nào nói nổi luật này"* — và đó là một câu hỏi giàu hơn hẳn.

## 3. Tầng là thuộc tính của LOÀI, không phải một trait

Quyết định khó nhất của phiếu, nên nêu lý do đầy đủ.

**Không đưa tầng vào vector trait.** Vector trait là chiều **thích nghi** — 12
điểm chia cho 6 trait, dịch được lúc chạy ([W-12](W-12-thich-nghi.md),
[B-13](B-13-dich-trait-llm.md)). Nếu tầng cũng nằm trong đó thì:

* Nó sẽ **hội tụ**. W-12 đã dính đúng lỗi này một lần: luật dịch trait cũ kéo cả
  năm loài về `(2,2,2,2,2,2)` chỉ sau ba lần dịch, xoá sạch bản sắc loài. Một
  chiều "tầng" nằm trong cùng ngân sách sẽ hội tụ về tầng nào rẻ nhất.
* **Q1 mất nhóm để so.** Câu hỏi *"brain có đáng giá không"* cần các nhóm ổn định
  suốt ván. Loài đổi tầng giữa chừng thì không còn nhóm nào để so.

**Nhưng trong một tầng thì trait VẪN mở khoá được đường đi** — và đó chính là ca
"sư tử / khỉ" của đề bài:

```
CẠN + speed >= 3  ->  trèo được CÂY
CẠN + armor >= 3  ->  băng được LỬA
```

Sư tử là `attack` cao `speed` thấp; khỉ là `speed` cao `attack` thấp. **Không
hard-code loài nào cả** — nó đọc thẳng từ vector trait, nên một dòng dõi có thể
**học cách trèo** bằng cách dịch trait sang `speed` ([B-13](B-13-dich-trait-llm.md)).
Bản sắc tầng thì cố định; đường đi trong tầng thì kiếm được.

Đó là nửa hay của tiến hoá mà không dính nửa dở (hội tụ).

## 4. Địa hình: thêm ĐÚNG HAI. Hồ, ao, biển là chuyện của BẢN ĐỒ.

Đề bài nói *"không quá to nhưng phải đầy đủ"*. Cách đạt được cả hai là **đừng
tăng số loại địa hình, hãy tăng số cách xếp chúng**.

Thêm hai:

| mới | nghĩa |
|---|---|
| `DEEP` | nước sâu — ngoài khơi, giữa hồ |
| `TREE` | cây — tầng trung gian giữa cạn và trời |

`WATER` cũ đổi nghĩa thành **nước nông** (mép nước): cạn lội vào uống được, cá
sống được.

Rồi **hồ, ao, biển sinh ra từ cách xếp**, không phải từ enum mới:

| | công thức |
|---|---|
| **ao** | một mảng `WATER` nhỏ, không có `DEEP` |
| **hồ** | mảng `WATER` vừa, lõi `DEEP` nhỏ |
| **biển** | mảng `DEEP` lớn, viền `WATER` |

Bảy loại địa hình cho ba tầng và ba kiểu nước. Đó là "đầy đủ mà không to".

## 5. Ai đi được đâu

| địa hình | NƯỚC | CẠN | TRỜI |
|---|---|---|---|
| `PLAIN` | ✗ | ✓ | ✓ bay qua |
| `BUSH` | ✗ | ✓ | ✓ |
| `WATER` nông | ✓ | ✓ | ✓ |
| `DEEP` sâu | ✓ | ✗ | ✓ bay qua |
| `TREE` | ✗ | ✓ **nếu `speed ≥ 3`** | ✓ |
| `ROCK` | ✗ | ✗ | ✓ bay qua |
| `FIRE` | ✗ | ✓ **nếu `armor ≥ 3`** | ✓ |

**Trời đi đâu cũng được — và đó mới là một nửa.** Nửa kia: **trời phải hạ xuống
mới CHẠM được.** Ăn, uống, đánh nhau đều đòi cùng ô và cùng tầng. Nên làm chim
là *đi lại tự do đổi lấy tiếp xúc kém*, không phải "mạnh hơn ở mọi mặt". Không có
ràng buộc này thì tầng trời trội tuyệt đối và hai tầng kia thành trang trí.

## 6. Ổ sinh thái cần THỨC ĂN khác nhau, không chỉ đường đi khác nhau

Đi được chỗ người khác không đi được thì mới là nửa ổ. Nửa còn lại là **ở đó có
cái để ăn**:

| nguồn | ở đâu | ai lấy được |
|---|---|---|
| quả | `PLAIN` (như hiện nay) | cạn, trời (hạ xuống) |
| **quả trên cây** | `TREE` | cạn **biết trèo**, trời |
| **cá** | `WATER`, `DEEP` | nước, trời (bổ nhào) |

Đây là chỗ ngân sách trait thành **kinh tế sinh thái** thật: một con cạn phải cân
nhắc bỏ điểm vào `speed` để với tới quả trên cây, đổi lấy `attack` hay `stomach`.
Trước phiếu này, `speed` chỉ là "đi nhanh hơn"; sau phiếu này nó là "với tới được
một nguồn thức ăn mà kẻ khác không với tới".

### Hai thứ CHẶN chặng B, đã đo (2026-08-30)

Chặng A xong rồi mà vẫn chưa thả được cá hay chim, và lý do không phải thiếu thời
gian. Đo trên 8 seed mỗi bản đồ:

| bản đồ | ô nước | ô sâu | vùng nước to nhất |
|---|---|---|---|
| `QUAN_DAO` | 133 | 32 | 137 |
| `DONG_CO` | 54 | 8 | 36 |
| `HEM_NUI` | 49 | 5 | 38 |
| `RUNG_RAM` | 40 | 7 | 43 |
| **`HOANG_MAC`** | **18** | **1** | **25** |

**Chặn 1 — `HOANG_MAC` không nuôi nổi một quần thể nước.** 18 ô cho cả một loài
là thả cá vào chỗ chết, và M1 ("không con nào chết quá 8 lần") sẽ vỡ ngay. Nên
quần thể phải phụ thuộc BẢN ĐỒ, không phải một hằng số toàn cục — đó là một thay
đổi kiến trúc riêng, không phải một dòng config.

**Chặn 2 — và đây mới là cái thật: CÁ KHÔNG CÓ GÌ ĂN.** `spawn_plants` chỉ mọc
quả trên ô `PLAIN`. Tầng nước hiện không có một nguồn thức ăn nào, nên một con cá
thả xuống đó chết đói dù có bao nhiêu nước đi nữa.

Nghĩa là §6 ở trên **chưa được thi công**, và nó là điều kiện CẦN của chặng B chứ
không phải phần tô điểm. Thứ tự đúng: nguồn thức ăn theo tầng → quần thể theo bản
đồ → rồi mới thả loài mới. Thả loài trước là thả vào một thế giới chưa có chỗ cho
chúng sống.

## 7. Ba tầng phải GẶP NHAU — nếu không thì đây là ba trò chơi rời nhau

Bất biến bản đồ, không phải trang trí:

* **`WATER` nông là ô DUY NHẤT mà NƯỚC và CẠN đứng cạnh nhau được.** Đó là bờ
  nước — chỗ con mồi phải tới uống và kẻ săn biết điều đó. Cảnh hay nhất của cả
  trò chơi nằm ở đấy.
* **`TREE` là chỗ CẠN gặp TRỜI.**
* **Chim hạ xuống ăn** là chỗ TRỜI chạm mọi thứ.

Nên bộ sinh bản đồ **phải bảo đảm có bờ**: mọi mảng `DEEP` phải có viền `WATER`,
và phải có ít nhất một mảng `WATER` giáp `PLAIN`. Một bản đồ mà nước và cạn không
giáp nhau là một bản đồ hỏng, không phải một bản đồ khó.

## 8. Bất biến

**Bất biến 1 — mỗi tầng có mặt trong ván phải có ÍT NHẤT MỘT luật quan sát được.**
Mở rộng của Gate A/D. Thiếu nó thì cả một tầng người chơi ngồi trong một ván
không có đáp án tìm được, và `match = 0` của họ là **hiện vật của lỗi**, đúng
loại kết luận sai mà dự án này liên tục bắt được.

> **Đo trước khi xây, và phép đo nói ĐỪNG XÂY.** Trên 40 seed: cá quan sát được
> **91%** số luật, các loài khác **99–100%**, và **không loài nào** từng rơi vào
> một ván không có luật nào nó quan sát được. Ca thảm hoạ mà bất biến này lo sợ
> **không xảy ra** — bộ sinh luật chủ yếu chọn trigger vô can với tầng
> (`ADJACENT` 37 · `DRINK` 23 trên 120 luật) còn `STEP_ON` chỉ **3**.
>
> Nên chặng C **không xây cổng gác**. Một cổng gác cho một vấn đề không xảy ra
> là thêm một thứ phải bảo trì, và nó sẽ âm thầm loại bỏ những bộ luật hợp lệ.
> Thay bằng `tests/test_domain.py::test_khong_tang_nao_ngoi_trong_mot_van_KHONG_CO_DAP_AN`
> — rẻ, và nó đỏ ngay ngày ai đó làm `STEP_ON` phổ biến hơn, thêm một tầng mới,
> hay đổi `SPECIES_DOMAIN`. Tức là đúng những thay đổi khiến vấn đề bắt đầu có
> thật.

**Bất biến 2 — `passable` là đường DUY NHẤT quyết định ai đi được đâu.** Không
được có bảng thứ hai ở `reflex`, ở render, hay ở client. Đây là bài học đã trả
giá tám lần: hai bản của một khái niệm thì bản ít người nhìn sẽ mục.

**Bất biến 3 — trời phải hạ xuống mới chạm được.** Xem §5.

**Bất biến 4 — tầng KHÔNG dịch được.** Xem §3.

**Bất biến 5 — thêm địa hình vào DSL là một CÔNG TẮC riêng.** `DEEP` và `TREE`
làm miền `TERRAIN` rộng thêm 40%, mà quy nạp **đang hỏng sẵn**
([thang chẩn đoán](../06-CONG-VIEC.md)). Nên chúng vào thế giới trước, vào từ
vựng luật sau, và **X-10 đo cái giá** — chứ không giả định.

## 9. Bẫy

**Bẫy 1 — M1 sẽ vỡ.** Thêm địa hình là đổi diện tích đi được và đổi tỉ lệ chết,
mà [M1](../06-CONG-VIEC.md) tune rất chật (chết nhiều nhất 8, không con nào chưa
từng chết). Phải chạy lại `5 seed × 400 tick` và chỉnh `plant_scale` từng bản đồ.
**Đừng nới tiêu chí M1 để cho qua** — nếu thế giới mới không đạt được M1 thì đó
là tin, không phải phiền toái.

**Bẫy 2 — `speed` gánh hai việc.** Nó vừa là `moves_per_tick` vừa là khoá trèo
cây. Kiểm rằng nó không làm `speed` thành trait phải-có: đếm hướng dịch trait của
[B-13](B-13-dich-trait-llm.md) trước và sau. Cả đàn dồn vào `speed` là dấu hiệu
ngưỡng đặt sai, không phải người chơi khôn.

**Bẫy 3 — cá không được thành quả biết bơi.** Nếu cá đứng yên chờ bị ăn thì tầng
nước chỉ là `PLAIN` sơn màu xanh. Cá phải **chạy trốn** — tầng phản xạ của nó
khác tầng cạn.

**Bẫy 4 — đừng để ba tầng thành ba ván chạy song song.** Nếu mỗi tầng tự ăn tự
sống và không bao giờ gặp nhau thì ta vừa chia một ván thành ba ván nhỏ hơn và
nghèo hơn. §7 là chỗ chống lại điều đó, và nó phải có bài kiểm riêng: đếm số lần
hai sinh vật KHÁC TẦNG đứng cạnh nhau trong một ván.

## 10. Ba chặng

| chặng | nội dung | nghiệm thu |
|---|---|---|
| **A** | `Domain`, hai địa hình, `passable` theo tầng+trait, bản đồ có bờ | `pytest tests/test_domain.py` · M0 còn xanh |
| **B** | cá, quả trên cây, phản xạ theo tầng | M1 chạy lại 5 seed × 400 tick |
| **C** | ~~Gate theo tầng~~ — **đo xong: KHÔNG cần**, thay bằng bài canh chừng | `pytest tests/test_domain.py -q` |

## 11. Nghiệm thu

```bash
pytest tests/test_domain.py -q
python -m genesis.run --seed 21 --ticks 300 --no-render --out /tmp/w18.jsonl
python scripts/x10_tang.py --seeds 5 --ticks 400
# đòi: mỗi tầng đều có cá thể sống tới cuối ở >= 3/5 seed
#      số lần đứng cạnh KHÁC TẦNG > 0 ở mọi seed  (bẫy 4)
#      M1 vẫn đạt: chết nhiều nhất <= 8, không con nào chưa từng chết
```
