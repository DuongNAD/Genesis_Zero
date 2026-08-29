# R-03 · GRPO + LoRA

| | |
|---|---|
| **Track** | RL · **Phụ thuộc** [R-02](R-02-mau.md) · **Trạng thái** 🟨 chạy được, chưa có kết quả |
| **File** | `scripts/r03_train.py` |
| **Giao cho model rẻ?** | ❌ tự viết |

## 1. Mục tiêu
Huấn luyện model quy nạp giỏi hơn từ chính những ván đã chơi.

```
L = −Σ A·log π(y|x) + β·KL(π ‖ π_ref)
```

`A` là lợi thế chuẩn hoá theo nhóm; `π_ref` là **chính base model với adapter
LoRA tắt đi** — không cần bản sao thứ hai trong RAM.

## 2. Vì sao ngoại tuyến, và vì sao không cần `trl`

`GRPOTrainer` của `trl` dựng cho vòng **sinh trực tuyến**: model đẻ ra câu trả
lời rồi chấm ngay. Ở đây rollout **đã có sẵn** — chúng là những ván đã chơi,
đã chấm, đã lưu. Nên viết GRPO ngoại tuyến bằng `torch` + `peft` trực tiếp
ngắn hơn và không kéo thêm phụ thuộc.

## 3. Tôi đã tuyên bố sai là việc này bị chặn

Tài liệu ghi *"chưa có `trl`/`peft` và GPU đủ lớn"* và để nguyên như thế nửa
ngày. Kiểm lại máy: **32 GB, torch 2.13 + MPS, `peft` và `transformers` đã cài
sẵn.** Chỉ thiếu `trl`, mà `trl` không cần.

Chạy được ngay trong ngày: 30 bước LoRA trên Qwen2.5-0.5B, adapter **2,1 MB**
(540k tham số, 0,11%).

> **Bài học:** "bị chặn vì thiếu tài nguyên" là một tuyên bố cần **kiểm**, không
> phải một cảm giác. Ba lần trong dự án này tôi khai báo bị chặn, và cả ba lần
> đều sai hoặc quá sớm.

## 4. Vì sao vẫn 🟨

Vòng huấn luyện chạy và lưu được adapter, nhưng **57 mẫu từ một model đang ăn
điểm ~0,05** là kiểm chứng đường ống, **không phải một kết quả**. Muốn có kết
quả cần một model tìm ra được luật — xem [W-16](W-16-cam-nang.md) và X-08.

Đừng báo cáo số từ lần chạy này như bằng chứng huấn luyện có tác dụng.
