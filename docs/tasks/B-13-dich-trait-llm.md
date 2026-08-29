# B-13 · LLM tự chọn hướng dịch trait

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-05, W-12 · **Chặn** — |
| **File** | `genesis/strategist.py` · ~60 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | v4 Bước 26 |

## 1. Mục tiêu
Thay if-else "dồn vào trait thấp nhất" ở W-12: khi đủ 1 `adapt_point`, hỏi chính LLM của con đó, kèm 20 sự kiện gần nhất. Mỗi quyết định nâng cấp trở thành **dữ liệu quan sát được** — và ở v5, **hướng dịch trait ưa thích là chữ ký hành vi rõ nhất của một model**.

## 2. Chữ ký và bất biến
```json
{"from": "attack", "to": "armor", "why": "…≤80 ký tự…"}
```
**Bất biến 1:** tổng vẫn 12, mỗi trait ∈ [0,5], `from` phải có ≥1, `to` phải có ≤4. Sai → bỏ lượt, ghi log, **không** thử lại.
> "Không thử lại" phải được **thi hành**, không chỉ được viết ra. Bản đầu để `take_shift` xếp hàng lại mỗi tick khi `adapt_points` chưa tiêu, nên một câu trả lời sai khiến con vật hỏi **mãi mãi**: đo ở seed 44, L1:0 hỏi 8 lượt liên tiếp từ t=60 tới t=81 và không ra quyết định nào khác nữa. Giờ chỉ hỏi lại khi `adapt_points` đổi.
> Và câu trả lời sai **không được rơi về giàn giáo W-12**: rơi về thì cơ thể vẫn đổi (trái chính bất biến này), và số liệu B-13 trộn lẫn với luật if-else của W-12 — mà B-13 sinh ra để đo chữ ký của *model*.
**Bất biến 2:** đây là gọi LLM **riêng**, không nhét vào schema quyết định thường. Cùng lý do CLAIM hai pha ở [B-08](B-08-codex.md).
**Bất biến 3:** dịch `brain` → khối D đổi → ghi `PREFIX_INVALIDATED` ([B-02](B-02-prompt.md) bẫy).

## 3. Ghi chú thiết kế
v4 §Bước 26 nói thẳng: đây là **Lamarck, không phải Darwin** — và lý do đó đúng cho sim quần thể, **sai cho dàn nhân vật cố định**. Ở scope này nó là lựa chọn đúng. Đừng đọc lại v1 rồi đổi ý.

## 4. Nghiệm thu
```bash
python -m genesis.run --seed 80 --ticks 400 --llm all --out /tmp/b13.jsonl
# không có cờ `--trait-by-llm`: con nào có model thì CHÍNH NÓ quyết, luôn luôn.
# Một cờ bật/tắt ở đây tạo ra hai chế độ phải kiểm, và cái tắt thì không ai chạy.
python -c "
import json,collections
r=[json.loads(l) for l in open('/tmp/b13.jsonl')]
sh=[x for x in r if x['kind']=='TRAIT_SHIFT']
assert sh, 'không ai dịch trait'
bad=[x for x in sh if not x['ok']]
assert len(bad)/len(sh) < 0.2, f'{len(bad)}/{len(sh)} dịch không hợp lệ'
print('OK', collections.Counter((x['from'],x['to']) for x in sh if x['ok']).most_common(5))"
pytest tests/test_trait_shift.py -q   # tổng vẫn 12 sau MỌI lần dịch hợp lệ
```

## 5. Prompt giao việc
```
BỐI CẢNH: Python 3.11. Đọc trước: docs/tasks/B-13-dich-trait-llm.md §2 và genesis/traits.py
(Traits.shift đã có). Đừng đọc tài liệu khác.
VIỆC: thêm vào genesis/strategist.py:
- schema_for(traits,"shift") -> JSON Schema {from,to,why<=80}, enum from/to là 6 tên trait.
- async def ask_shift(strategist, creature, recent_events) -> tuple[str,str]|None:
  gọi LLM với schema đó, validate theo 4 điều kiện ở §2 bất biến 1, trả None nếu sai
  và ghi log TRAIT_SHIFT với ok=False + lý do.
- tests/test_trait_shift.py: sau MỌI lần dịch hợp lệ, sum(traits)==12 và mọi trait trong
  [0,5]; dịch từ trait đang bằng 0 -> bị từ chối; dịch tới trait đang bằng 5 -> bị từ chối.
RÀNG BUỘC: dùng lại Traits.shift, KHÔNG viết lại logic dịch; không tạo file mới;
không sửa genesis/traits.py.
NGHIỆM THU: pytest tests/test_trait_shift.py -q
TRẢ VỀ: chỉ diff.
```
