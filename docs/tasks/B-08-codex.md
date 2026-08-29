# B-08 · Sổ Luật và CLAIM hai pha

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-07, L-01 · **Chặn** B-09, B-10, B-12 |
| **File** | `genesis/codex.py` · ~110 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ cấu trúc giao được; **quy tắc hai pha và cấm reflex đọc thì tự** |
| **Tài liệu gốc** | [03 §4](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Nơi niềm tin của cá thể sống, và là **thứ được chấm**.

## 2. Chữ ký và bất biến
```python
@dataclass
class CodexEntry:
    law: Law; conf: int; written_at: int; source: str     # "self" | creature_id đã dạy

class Codex:
    def __init__(self, size: int): ...
    def apply(self, op: str, slot: int, law: Law | None, conf: int, tick: int) -> Verdict: ...
```
**Bất biến 1 — số ô cố định và ít.** `codex_size` từ `law_config.CODEX_SIZE_BY_BRAIN`. Sổ đầy thì muốn ghi mới phải **xoá cũ**. Đây là cơ chế chống spam quan trọng nhất: agent buộc phải *chọn tin cái gì* thay vì liệt kê mọi khả năng.
**Bất biến 2 — CLAIM hai pha.** `want_codex` trong quyết định thường (1–2 token, con nào cũng gánh được) → server phát work item `kind="codex"` riêng ở tick sau, có `claim_budget` riêng. Nhồi cả hai vào một schema thì L5 với 32 token không tham gia được.
**Bất biến 3 — không phản hồi.** Agent **không bao giờ** biết entry đúng hay sai cho tới REVEAL. Đây là thứ giết chết vét cạn ([03 §4.3](../03-LUAT-AN-V5.md)).
**Bất biến 4 — chết không xoá sổ.** [W-12](W-12-thich-nghi.md) `reset_body` không chạm codex.
**Bất biến 5 — `codex_size` giảm thì không cắt sổ.** Trait dịch làm `brain` tụt → giữ nguyên ô đang có, chỉ chặn ghi thêm.
**Bất biến 6 — tầng phản xạ KHÔNG đọc codex.** [W-09](W-09-phan-xa.md) bất biến 3. Vi phạm là phá tầng 3 của bảng chấm.

## 3. Nghiệm thu
```bash
pytest tests/test_codex.py -q
# ca bắt buộc: ghi quá số ô -> CODEX_BAD_SLOT · trong cooldown -> CODEX_COOLDOWN
# chết -> codex nguyên vẹn · brain tụt -> ô cũ còn, ô mới bị chặn
grep -rn "codex" genesis/reflex.py && echo "VI PHẠM BẤT BIẾN 6" && exit 1
python -m genesis.run --seed 66 --ticks 400 --llm all --out /tmp/b08.jsonl
python -c "
import json,collections
r=[json.loads(l) for l in open('/tmp/b08.jsonl')]
ops=[x for x in r if x['kind']=='CODEX_OP']
assert ops, 'không ai ghi sổ'
bad=collections.Counter(x['reason'] for x in ops if not x['ok'])
print('CODEX_OP', len(ops), 'lỗi:', bad)"
```
