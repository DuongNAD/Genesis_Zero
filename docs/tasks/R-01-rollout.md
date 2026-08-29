# R-01 · Rollout headless song song

| | |
|---|---|
| **Track** | RL · **Phụ thuộc** [B-10](B-10-score.md) · **Chặn** R-02 |
| **File** | `genesis/rollout.py`, `genesis/batch.py` |
| **Giao cho model rẻ?** | ⚠️ khung song song giao được; **ngân sách gọi model tự viết** |

## 1. Mục tiêu
Chạy hàng loạt ván không giao diện, gom `(prompt, response, reward)` để huấn
luyện. Một ván = một quỹ đạo; nhiều seed = một tập.

```bash
python -m genesis.batch --seeds 40 --ticks 400 --arm STANDARD --workers 8
```

## 2. Bất biến

**Bất biến 1 — song song ở mức VÁN, không ở mức lời gọi.** Đo trên Metal: 4 lời
gọi song song tốn **2,28×** một lời gọi, tức thông lượng bị chặn bởi **tổng số
lời gọi**, không bởi số worker. Chạy 8 ván song song, mỗi ván gọi model tuần tự,
thì GPU luôn có việc mà không ván nào bị bỏ đói.

**Bất biến 2 — hâm nóng đệm luật TRƯỚC.** Cổng khả giải ([L-05](L-05-gate-bc.md))
chạy một ván thật 200 tick cho mỗi bộ luật. Không hâm trước thì 40 seed mất hơn
2 phút chỉ để sinh luật; hâm song song đưa xuống **21 giây**.

## 3. Đã học

Bộ test phình từ **20 s lên 118 s** ngay khi `run.py` bắt đầu sinh luật — vì mỗi
lần gọi đều trả lại khoản kiểm khả giải. `generate_cached` khoá theo `(arm, seed)`
gỡ hẳn: `generate` tất định theo khoá ấy nên đệm không mất gì.
