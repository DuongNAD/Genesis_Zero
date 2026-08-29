# N-02 · Đường may 2 — `SpeciesRegistry` động

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** W-09 · **Chặn** N-04, N-05 |
| **File** | `genesis/registry.py` · ~50 dòng · **30 phút** |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [04 §5](../04-THE-GIOI-MO.md) đường may 2 |

## 1. Mục tiêu
Ở chế độ mở, loài do người lạ tạo ra **lúc chạy**. Hardcode 5 loài thành hằng số import-time là ngõ cụt kiến trúc.

## 2. Chữ ký và bất biến
```python
@dataclass
class SpeciesSpec:
    species_id: str; display_name: str; persona: str
    traits: Traits; pop: int; slots: list[int]
    client_id: str | None; model_name: str | None
    endpoint: str | None; is_bot: bool = False; is_feral: bool = False

class SpeciesRegistry:
    def add(self, spec: SpeciesSpec) -> list[str]: ...   # trả creature_ids
    def remove(self, species_id: str) -> None: ...
    def mark_feral(self, species_id: str, feral: bool) -> None: ...
    def __iter__(self): ...                              # thứ tự CỐ ĐỊNH theo species_id
```
**Bất biến 1:** Lab mode nạp registry **từ config**, Open mode nạp **từ `/join`**. Cùng một lớp, hai nguồn. Không có hai đường code.
**Bất biến 2:** `__iter__` trả thứ tự cố định. Registry đổi thứ tự = ván đổi kết quả.
**Bất biến 3:** `add` gọi được **giữa ván** ([W-11](W-11-vong-tick.md) bất biến 3).

## 3. Nghiệm thu
```bash
pytest tests/test_registry.py -q
# ca: nạp 5 loài từ config -> giống hệt POPULATION cũ
#     add giữa ván ở tick 100 -> vòng tick chạy tiếp không lỗi, creature mới có mặt từ tick 101
#     remove -> creature biến khỏi vòng lặp nhưng log cũ vẫn tra được theo id
python -m genesis.run --seed 90 --ticks 200 --join-at 100 --out /tmp/n02.jsonl
python -c "
import json;r=[json.loads(l) for l in open('/tmp/n02.jsonl')]
ids={x['creature_id'] for x in r if x['t']>101 and x['creature_id']}
old={x['creature_id'] for x in r if x['t']<99 and x['creature_id']}
assert len(ids)>len(old); print('THÊM GIỮA VÁN OK', len(old),'->',len(ids))"
```

## 4. Prompt giao việc
```
BỐI CẢNH: Python 3.11. Đã có genesis/traits.py, genesis/config.py (POPULATION, FOUNDERS).
Đọc trước: docs/tasks/N-02-seam-registry.md §2. Đừng đọc tài liệu khác.
VIỆC: genesis/registry.py với SpeciesSpec và SpeciesRegistry theo chữ ký §2.
from_config(config) -> SpeciesRegistry nạp 5 loài Lab. __iter__ sắp theo species_id.
add() sinh creature_id dạng f"{species_id}:{n}" và trả danh sách.
tests/test_registry.py theo ba ca ở §3.
RÀNG BUỘC: không hardcode "L1".."L5" ở đâu ngoài from_config; không tạo/sửa file khác.
NGHIỆM THU: pytest tests/test_registry.py -q
TRẢ VỀ: chỉ diff.
```
