# R-02 · Quỹ đạo → (prompt, response, reward)

| | |
|---|---|
| **Track** | RL · **Phụ thuộc** [R-01](R-01-rollout.md) · **Chặn** R-03 |
| **File** | `genesis/rollout.py` — `samples_from`, `write_jsonl` |
| **Giao cho model rẻ?** | ✅ |

## 1. Mục tiêu
Biến log một ván thành mẫu huấn luyện. Prompt phải là **đúng prompt model đã
thấy**, không phải một bản dựng lại gần đúng.

## 2. Bất biến — đối chiếu `prompt_hash`

`samples_from` dựng lại prompt bằng chính cơ chế replay rồi **so `prompt_hash`
với log**; lệch thì **bỏ mẫu**, không đoán. Huấn luyện trên một prompt khác cái
model đã thấy là dạy sai một cách không ai nhìn thấy.

Chính ràng buộc này lộ ra **bốn lỗ hổng trong replay** — và cả bốn chỉ hiện ra
khi có model thật, vì model giả trước đó không viết `note`, không nói, không ghi
sổ. Xem [B-06](B-06-replay.md).

## 3. Lỗi đáng nhớ nhất: reward bằng 0 cho tất cả

Bản đầu tính phần thưởng bằng **`ΣR_i`** — tổng điểm các luật tìm được.

Khi chưa con nào tìm ra luật nào thì `ΣR_i = 0` **cho tất cả**, nên mọi lợi thế
chuẩn hoá theo nhóm của GRPO bằng 0, và **không có một gradient nào**. Vòng
huấn luyện chạy trơn tru, mất giờ GPU, và học đúng bằng không.

Sửa: dùng `total_reward()` đầy đủ. Cái đuôi `0.1·R_survive` chính là **dây neo
cho giai đoạn đầu** — đúng lúc cần tín hiệu nhất thì nó là tín hiệu duy nhất.


## 4. Đổi bộ mô phỏng là vô hiệu hoá mọi log cũ

`samples_from` dựng lại prompt bằng cách **chạy lại ván**. Nên bất kỳ thay đổi
nào chạm tới prompt — vector trait, sổ tay, Sổ Luật, cách chết — đều làm hash
của log cũ lệch.

Đã xảy ra thật: sau [W-17](W-17-doi.md), log thu trước đó ném
`t=29 L3:1: prompt_hash lệch` vì thừa kế đổi vector trait sau cái chết đầu
tiên, mà vector ấy nằm trong khối E.

**Đó là bộ canh chạy đúng, không phải lỗi.** Việc cần làm là **thu lại log**,
tuyệt đối không phải nới bộ canh — nới nó là huấn luyện trên prompt model chưa
bao giờ nhìn thấy, và không ai phát hiện được.
