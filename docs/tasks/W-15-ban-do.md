# W-15 · Nhiều bản đồ

| | |
|---|---|
| **Track** | World · **Phụ thuộc** W-02, L-05 · **Chặn** N-14 |
| **File** | `genesis/maps.py` · ~110 dòng · 3 giờ |
| **Giao cho model rẻ?** | ⚠️ bộ sinh giao được; **cân bằng và quyết định "đủ khác" thì tự** |
| **Tài liệu gốc** | [02 §1](../02-SANDBOX-V4.md), [03 §6](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Một bản đồ không phải trang trí — nó quyết định **luật nào quan sát được**.

## 2. Năm bản đồ

| Bản đồ | Đổi cái gì | Hỏi câu gì |
|---|---|---|
| `DONG_CO` | mặc định, đã tune ở W-12 | ván chuẩn để so |
| `HOANG_MAC` | ít nước, nhiều đá | luật `DRINK` còn học được không? |
| `QUAN_DAO` | nhiều nước, đất vụn | quần thể tách đàn thì tri thức lan thế nào? |
| `HEM_NUI` | đá thành vách, chừa hành lang | ép chạm mặt — luật `ADJACENT` |
| `RUNG_RAM` | dày bụi rậm | **giao tiếp đáng giá bao nhiêu?** (Q2) |

`RUNG_RAM` là bản đồ đáng chú ý nhất: bụi rậm chặn tầm nhìn ([W-08](W-08-tam-nhin.md)),
mà tầm nghe lấy theo `sight_radius` của **người nghe** ([B-11](B-11-noi-danh-tieng.md))
— nên nó vừa làm quan sát gián tiếp khó hơn, vừa làm kênh nói ngắn lại.

## 3. Bất biến
**Bất biến 1 — bản mặc định không đổi một byte.** Mọi số đo cân bằng của
[W-12](W-12-thich-nghi.md) dựa trên bộ sinh cũ; `map_name=None` phải cho đúng
lưới cũ. Không thế thì mọi con số trong tài liệu thành sai mà không ai biết.

**Bất biến 2 — cổng khả giải chạy theo cặp `(bản đồ, seed)`.** Cổng B chạy một
ván THẬT, nên nó phải chạy trên **đúng bản đồ sẽ dùng**. Nhánh mang tên
`STANDARD@RUNG_RAM` để khoá đệm tự tách. Đo thẳng: một luật `DRINK` kích hoạt
**349** lần trên sa mạc và **1880** lần trên quần đảo qua 5 ván — trộn chung một
khoá là dùng lại một bộ luật đã duyệt cho một thế giới khác.

**Bất biến 3 — `FIRE` vẫn không sinh tự nhiên** ở bất kỳ bản đồ nào ([W-13](W-13-sandbox-v5.md)).

## 4. Cân bằng — đo được, và **đừng ép về một con số**

5 seed × 400 tick, không luật, chỉ phản xạ:

| bản đồ | chết nhiều nhất | chưa từng chết | tổng chết | |
|---|---|---|---|---|
| `DONG_CO` | 8 | 0/75 | 329 | ✅ đúng M1 |
| `HOANG_MAC` | 9 | 0/75 | 430 | khó hơn |
| `HEM_NUI` | 9 | 0/75 | 410 | khó hơn |
| `QUAN_DAO` | 9 | 3/75 | 309 | bất bình đẳng |
| `RUNG_RAM` | 8 | 2/75 | 192 | bất bình đẳng |

**M1 là tính chất của ĐỒNG CỎ, không phải của mọi bản đồ.** Đã quét `plant_scale`
từ 0,8 tới 3,0 trên cả năm:

* `HOANG_MAC` và `HEM_NUI`: **thêm thức ăn không cứu được** — chết ở đó đến từ
  chen chúc và đánh nhau (ít ô đi được hơn), không từ đói. Hai bản đồ này *khó
  hơn*, và đó là chủ ý.
* `QUAN_DAO` và `RUNG_RAM`: đất vụn tạo ra **túi an toàn** — vài con không bao
  giờ chết trong khi con khác chết chín lần. Bất bình đẳng ấy là **tính chất của
  bản đồ**, và nó chính là thứ làm câu hỏi Q2 có nghĩa ở `RUNG_RAM`.

Nên: ghi số ra, và khi so hai ván thì **so trong cùng một bản đồ**.

## 5. Nghiệm thu
```bash
pytest tests/test_maps.py -q
python -c "
from genesis.tick import build_match
from genesis.maps import MAPS, terrain_mix
for m in MAPS: print(f'{m:<11}', terrain_mix(build_match(1, map_name=m)[0].grid))"
```
