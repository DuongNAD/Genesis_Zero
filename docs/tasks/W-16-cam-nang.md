# W-16 · Cẩm nang phương pháp — trí nhớ qua nhiều ván

| | |
|---|---|
| **Track** | World · **Phụ thuộc** B-02, B-08 · **Chặn** X-08 |
| **File** | `genesis/handbook.py` · ~140 dòng · 2 giờ |
| **Giao cho model rẻ?** | ❌ ranh giới "cái gì được nhớ" là cả thiết kế |
| **Tài liệu gốc** | [03 §11.6](../03-LUAT-AN-V5.md) |

## 1. Câu hỏi sinh ra nó

> *"Sao không cho nó một bản luật để tự đọc và tra và nhớ, không cần train model?"*

Câu hỏi đúng, và câu trả lời có hai nửa.

**Nửa thứ nhất: luật ẩn CHƯA BAO GIỜ được train vào model.** Model đọc mọi thứ
lúc chạy. Luật nền thì được đưa thẳng — đó là khối A của prompt, nó đọc lại mỗi
lượt. Luật **ẩn** thì cố tình không đưa, vì *tìm ra nó* chính là bài thi. Đưa
đáp án cho thí sinh thì kỳ thi không đo được gì, và cả bản v5 tồn tại là vì
sinh tồn **không chấm được** còn luật ẩn thì **chấm được**.

**Nửa thứ hai — và đây là chỗ câu hỏi chỉ đúng vào một khoảng trống thật.** Agent
có trí nhớ trong ván (sổ tay, Sổ Luật) nhưng **không có gì sống qua ván**. Mà
thứ đáng mang sang ván sau không phải *đáp án* — luật đổi mỗi ván, chép đáp án
sang là sai — mà là **cách tìm**.

## 2. Ba tầng trí nhớ, và đừng trộn chúng

| Tầng | Nội dung | Sống bao lâu |
|---|---|---|
| Sổ tay ([B-07](B-07-so-tay.md)) | *"t382 TÔI ăn quả đỏ → mất máu"* | trong ván |
| Sổ Luật ([B-08](B-08-codex.md)) | *"KHI ăn quả đỏ THÌ nhiễm độc"* | trong ván |
| **Cẩm nang** | *"thử một thứ một lúc"* | **qua nhiều ván** |

## 3. Bất biến

**Bất biến 1 — cẩm nang KHÔNG được chứa một luật cụ thể nào.** Luật đổi mỗi ván
và bề mặt bị hoán vị lại mỗi ván ([W-13](W-13-sandbox-v5.md)). *"Quả đỏ thì
độc"* chép sang ván sau là **sai**; và nếu tình cờ đúng thì agent ăn điểm mà
không quy nạp gì — phép đo mất nghĩa.

```
✅  "Đổi một biến một lúc; đổi hai thì không quy được nhân quả."
✅  "Màu sắc bị xáo lại mỗi ván — đừng tin trực giác về màu."
❌  "Quả đỏ thì độc."          ❌  "FRUIT_A gây POISON."
```

**Bất biến 2 — `sanitize_lesson` NÉM, không lọc.** Một câu bị cắt mất nửa nghĩa
tệ hơn không có câu nào, và người viết cần biết mình vừa viết thứ không được phép.

**Bất biến 3 — sạch với MỌI hoán vị bề mặt, không riêng hoán vị ván này.** Cẩm
nang sống qua nhiều ván, nên nó bị kiểm với cả bốn màu trong `FRUIT_SURFACES`.

**Bất biến 4 — cẩm nang vào SYSTEM, không vào USER.** Nó bất biến cả ván; đặt ở
khối E là trả giá prefill cho một thứ không bao giờ đổi ([B-02](B-02-prompt.md)).

**Bất biến 5 — đầy thì bỏ dòng CŨ NHẤT.** Một cẩm nang không bao giờ quên là một
cẩm nang đóng băng ở ván đầu tiên.

## 4. Vì sao nó đáng thử TRƯỚC R-03

[03 §11.6](../03-LUAT-AN-V5.md) đề xuất dựng dữ liệu SFT hậu nghiệm sau `REVEAL`.
Cẩm nang là **bản không cần huấn luyện** của đúng ý đó: biết đáp án rồi thì viết
lại **bài học về cách tìm**, rồi đọc nó ở ván sau.

Nếu cẩm nang đủ để rút ngắn `t_discover` thì [R-03](R-03) chỉ còn là *tối ưu
hoá*, không phải điều kiện cần — cùng model, cùng trọng số, chỉ khác một đoạn
văn trong prompt. Đó là một mệnh đề **đo được**, rẻ hơn RL vài bậc độ lớn, và
đáng hỏi **trước** khi đổ giờ GPU vào.

## 5. Nghiệm thu
```bash
pytest tests/test_handbook.py -q
python scripts/x08_handbook.py --seeds 3 --ticks 200 --llm-url http://127.0.0.1:8080
# CÓ cẩm nang phải rút ngắn t_discover, hoặc trả lời thẳng rằng nó không.
```
