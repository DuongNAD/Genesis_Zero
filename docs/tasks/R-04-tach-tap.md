# R-04 · Tách train/test theo cấu trúc luật

| | |
|---|---|
| **Track** | RL · **Phụ thuộc** [R-03](R-03-grpo.md) |
| **File** | `genesis/rollout.py` — `split_by_law_structure` |
| **Giao cho model rẻ?** | ⚠️ |

## 1. Mục tiêu
Giữ lại một số **cặp (trigger, effect)** làm tập kiểm, để đo model có **tổng
quát hoá sang luật chưa từng thấy** hay chỉ nhớ luật đã gặp.

## 2. Khoá chia phải THÔ

Chia theo `(trigger.kind, effect.kind)` — **không** kèm điều kiện, tham số, hay
bề mặt.

Đo trên 400 seed: khoá mịn cho ra **400 khuôn khác nhau**, tức mỗi seed một
khuôn riêng. "Chia theo cấu trúc luật" khi ấy chỉ là **chia theo seed dưới một
cái tên khác** — mọi cặp trong tập kiểm cũng xuất hiện ở tập huấn luyện dưới
dạng biến thể, và con số tổng quát hoá đo được là con số giả.

Khoá thô cho ra vài chục khuôn, đủ để một cặp thật sự vắng mặt khỏi tập huấn
luyện.
