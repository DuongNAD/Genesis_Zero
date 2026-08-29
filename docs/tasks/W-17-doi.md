# W-17 · Đời — chết là truyền lại, không phải ngủ dậy

| | |
|---|---|
| **Track** | World · **Phụ thuộc** [W-12](W-12-thich-nghi.md), [B-08](B-08-codex.md) · **Chặn** N-13 §5 (đo lại trần Meshy) |
| **File** | `genesis/lineage.py` · ~120 dòng |
| **Giao cho model rẻ?** | ❌ tự viết |

## 1. Cái đang hỏng

Đo trên seed 55, 200 tick: **64 lượt chết, 83 lần dịch trait**. `adapt.reset_body`
kéo mọi con về vector khai sinh mỗi lần chết, nên cả 83 lần dịch ấy đều bị xoá.
Con `L5:4` dịch trait 12 lần rồi mất sạch. [W-12](W-12-thich-nghi.md) chạy đúng
và **không tích luỹ được gì**: thích nghi, chết, về nguyên trạng, thích nghi lại.

Và chết chỉ là một giấc ngủ: nằm chờ `dead_until` rồi dậy y hệt.

## 2. Cái thay vào

Con chết thì **không quay lại**; **một đời sau ra đời**. Cùng `creature_id` —
định danh ấy là DÒNG DÕI, không phải cá thể — nên khe prefix cache, khoá Sổ
Luật, sổ ghi công và đường replay đều giữ nguyên, thay vì phải dựng lại 64 lần
một ván.

| | qua đời sau | vì sao |
|---|---|---|
| Sổ Luật | ✅ (giảm `conf` mỗi đời) | thứ ngươi đã **viết ra** |
| Sổ tay hiện trường | ❌ | trải nghiệm thô không truyền được |
| Vector trait **đã dịch** | ✅ kèm một điểm đột biến | thích nghi cuối cùng có nghĩa |
| `adapt_points` | ❌ | đời sau phải tự kiếm |
| `eat_count` / `win_count` | ✅ | xem §5 — xoá chúng làm gãy W-12 |

Hai dòng đầu **đi ngược nhau**, và đó là toàn bộ ý tưởng: **chỉ thứ đã ghi vào
Sổ Luật mới sống qua cái chết.** Hiện Sổ Luật chỉ là tiện nghi — ghi hay không
thì trí nhớ vẫn nguyên. Từ đây, không ghi là mất thật. Đó đúng là cái nút mà
Qwen-7B bỏ quên suốt ván: **0% mục sổ nói về uống nước, trong khi uống chiếm
26% hành động** và `DRINK → DAMAGE` nổ 155 lần.

## 3. Thân xác trôi về phía thứ giết nó

Đột biến lệch **một điểm** theo NHÓM nguyên nhân chết:

| chết vì | lệch về | tỉ lệ đo được |
|---|---|---|
| đói | `stomach` | 61% |
| đánh nhau | `armor` / `attack` | 20% |
| độc | `sense` | 19% |

Chọn lọc thật cần hàng nghìn đời; ở đây có 64 cái chết mỗi ván nên ta nén lại
một bước Lamarck. Nhìn hình dáng một dòng dõi là đọc được thứ đang giết nó —
bụng to dần qua các đời nghĩa là thế giới này đang đói.

**Rào rò rỉ:** lệch theo NHÓM (ba loại), tuyệt đối không theo trigger của luật
ẩn. Ba nhóm thì quá thô để làm đáp án, đủ rõ để làm manh mối.

## 4. Hai ràng buộc học được lúc viết

**`brain` không bao giờ là nguồn.** Bản đầu lấy điểm từ trait cao nhất, mà
`brain` là trait cao nhất ở ba trong năm loài — nên **mỗi cái chết thành một
khoản thuế đánh vào đầu óc**: L1 (brain 4) tụt về brain 0 sau bốn lần chết,
trong một ván có 64 lượt chết. Nó phá đúng thứ dự án sinh ra để đo, và nó chính
là con lỗi vừa vá ở `founder_traits` cho người chơi qua mạng — chỉ chậm hơn và
lần này là "cố ý". Ranh giới đúng: **thân xác trôi theo thứ giết nó; đầu óc thì
không.**

**Nguồn cũng không được nằm trong nhóm đích.** L1 khai sinh có `attack=3,
armor=1`, nên lấy trait cao nhất sẽ lấy đúng `attack` để dồn sang `armor` —
nhóm chiến đấu xáo trong nội bộ và **không lớn lên**. Bài test bắt được: sau ba
đời chết vì đánh nhau, `attack+armor` vẫn đúng 4. Thích nghi với một mối đe doạ
nghĩa là **trả bằng thứ khác**, không phải kê lại đồ đạc.

## 5. Một chỉ số sai, và cách nó lộ ra

Lúc đề xuất, tôi hứa con số **"63/83 lần dịch bị xoá (76%)"** sẽ về gần 0. Bật
W-17 xong đo lại: **45/59 — vẫn 76%.**

Chỉ số ấy sai. Nó đếm "lần dịch xảy ra TRƯỚC một cái chết", mà thứ tự ấy không
đổi dù có thừa kế hay không. Nó chưa bao giờ đo cái nó tự nhận là đo.

Chỉ số đúng: **vector sau tái sinh lệch bao nhiêu so với vector khai sinh.**

| | đời 1 | đời 2 | đời 3 | đời 4 |
|---|---|---|---|---|
| W-17 **bật** | 3,07 | 4,92 | 4,89 | **7,00** |
| W-17 **tắt** | 0,00 | — | — | — |

Nhánh tắt ra 0,00 **theo định nghĩa** — `reset_body` kéo về founder — nên nó là
đối chứng đúng chứ không phải một phép đo. Nhánh bật cho thấy dòng dõi trôi xa
dần, đúng như thiết kế.

Và một lỗi kèm theo: bản đầu xoá luôn `eat_count`/`win_count`. Chúng là bộ đếm
tích luỹ mà `award_adapt` lấy dư (`eat_count % ADAPT_ON_EAT`) để phát điểm, nên
xoá mỗi lần chết là xoá phần dở dang — với 64 lượt chết thì **không ai đủ điểm
để dịch trait lần nào**. `test_huong_dich_do_llm_chon` chuyển sang đỏ với đúng
dòng chữ "không ai dịch trait".

## 6. Không phải chấm sinh tồn dưới tên khác

Đây là cửa sau đã giết bản v4, nên nói rõ: sống lâu **không** cho điểm, nó chỉ
cho nhiều đời hơn, mà đời chỉ đáng giá nếu có viết được gì. `t_discover` vẫn
đếm từ ĐẦU VÁN chứ không từ lúc sinh, và điểm vẫn tính theo (loài × luật) chứ
không cộng dồn theo cá thể — [B-10](B-10-score.md) không đổi một dòng.

## 7. Hệ quả cho Meshy

Khoá cache đã là `md5` của sáu trait, nên **mỗi đời đổi thân là một mesh mới,
tự động, không sửa gì**. Trần cứng tính được: 6 trait, mỗi cái 0–5, tổng 12 →
**3.431 vector hợp lệ**, sinh hết cũng chỉ 3.431 lần gọi, dùng mãi.

Nhưng [N-13 §5](N-13-mesh-3d.md) đo được "20 vector trên 180.000 trạng thái cơ
thể", và con số đẹp ấy có được **chính vì `reset_body` kéo mọi con về founder**.
W-17 cố tình phá điều đó. **Trần cũ chết cùng lúc với `reset_body` và phải đo
lại.**

## 8. Nghiệm thu
```bash
python -m pytest tests/test_lineage.py -q          # 26 mục
python -m genesis.run --seed 55 --ticks 200 --controller reflex \
  --out runs/lin-55.jsonl --truth runs/lin-55.truth.json
# rồi đo độ lệch khỏi founder theo đời — phải TĂNG
```
