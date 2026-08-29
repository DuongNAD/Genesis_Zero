# S-04 · JSONL và công cụ đọc log

| | |
|---|---|
| **Track** | Setup |
| **Phụ thuộc** | S-01 |
| **Chặn** | W-06, B-06, B-10, N-03 |
| **File** | `genesis/logio.py`, `scripts/logview.py` |
| **Ước lượng** | ~90 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | v4 Bước 6, [04 §5](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
Log là **giao diện duy nhất** giữa sim và bộ chấm ([03 §5](../03-LUAT-AN-V5.md): verifier không import gì từ vòng tick). Nên định dạng log là một API, và phải đúng từ đầu — thêm trường sau nghĩa là ván cũ không so được với ván mới.

## 2. Đầu vào đã có
`config.LOG_FIELDS_EXTRA` đã có sẵn `client_id` và `model_name` — v4 đã chuẩn bị cho chế độ mở.

## 3. Việc phải làm
1. `LogWriter`: một dòng JSON một sự kiện, ghi tuần tự, `flush` mỗi N dòng.
2. Mọi bản ghi có đủ **trường chung**, kể cả khi null (xem §4).
3. Đăng ký loại sự kiện: `TICK DEATH RESPAWN EAT ATTACK SPEAK MOVE LLM_CALL LLM_MISS LLM_SEMANTIC_FAIL NODE_DOWN LAW_FIRED CODEX_OP TEACH DECISION_LATE PREFIX_INVALIDATED`
4. `scripts/logview.py`: lọc theo `--kind --creature --tick-range`, in bảng `rich`.

## 4. Chữ ký và bất biến
```python
COMMON_FIELDS = ("t", "kind", "match_id", "creature_id", "species_id",
                 "client_id", "model_name")   # luôn có mặt, null cũng phải có

class LogWriter:
    def __init__(self, path: Path, match_id: str, flush_every: int = 64): ...
    def write(self, t: int, kind: str, **fields) -> None: ...
    def close(self) -> None: ...
```
**Bất biến 1:** khoá sắp xếp **ổn định** (`sort_keys=True`) — nếu không thì hai lần chạy cùng seed cho hai file khác nhau và test tái lập ở S-03 đỏ giả.
**Bất biến 2:** không có float ngẫu nhiên trong log dùng để `diff`. Làm tròn 4 chữ số.
**Bất biến 3:** `client_id` và `model_name` luôn có mặt, null ở Lab mode. Đây là đường may thứ 5 của [04 §5](../04-THE-GIOI-MO.md).

## 5. Bẫy
`json.dumps` mặc định `sort_keys=False`. Với dict Python 3.7+ thứ tự chèn là ổn định, nhưng chỉ cần một chỗ dựng dict theo thứ tự khác là hai file lệch. Ép `sort_keys=True` một lần ở đây, khỏi lo mãi.

## 6. Nghiệm thu
```bash
python - <<'PY'
from genesis.logio import LogWriter, COMMON_FIELDS
import json, tempfile, pathlib
p = pathlib.Path(tempfile.mkdtemp())/"a.jsonl"
w = LogWriter(p, "m_test"); w.write(1,"EAT",creature_id="L1:0",energy=12.3456); w.close()
r = json.loads(p.read_text().splitlines()[0])
assert all(f in r for f in COMMON_FIELDS), r
assert r["model_name"] is None and r["energy"] == 12.3456
print("OK")
PY
python scripts/logview.py --help
```

## 7. Prompt giao việc
```
BỐI CẢNH
Sim ALife 2D, Python 3.11, chỉ dùng rich + thư viện chuẩn.
Đọc trước: docs/tasks/S-04-log.md §3 §4. Đừng đọc tài liệu khác.

VIỆC
genesis/logio.py:
- COMMON_FIELDS = ("t","kind","match_id","creature_id","species_id","client_id","model_name")
- class LogWriter(path, match_id, flush_every=64) với write(t, kind, **fields) và close().
  Mỗi dòng là một JSON object chứa ĐỦ COMMON_FIELDS (null nếu không truyền) cộng **fields.
  json.dumps(..., sort_keys=True, ensure_ascii=False). Float làm tròn 4 chữ số. flush mỗi
  flush_every dòng và khi close.
- EVENT_KINDS: tập hợp các chuỗi TICK DEATH RESPAWN EAT ATTACK SPEAK MOVE LLM_CALL LLM_MISS
  LLM_SEMANTIC_FAIL NODE_DOWN LAW_FIRED CODEX_OP TEACH DECISION_LATE PREFIX_INVALIDATED.
  write() assert kind thuộc tập này.
scripts/logview.py: argparse --file --kind --creature --tick-range A:B, in bảng bằng rich.
tests/test_logio.py: kiểm mọi COMMON_FIELDS có mặt kể cả khi null; kiểm sort_keys ổn định
bằng cách ghi cùng dữ liệu hai lần theo hai thứ tự chèn khác nhau và so chuỗi.

RÀNG BUỘC
- Không thêm phụ thuộc ngoài rich.
- Không tạo file khác. Không sửa file khác trong genesis/.
- Không except: pass.

NGHIỆM THU: pytest tests/test_logio.py -q  và  python scripts/logview.py --help

TRẢ VỀ: chỉ diff.
```
