# S-01 · Môi trường Python + khung kho

| | |
|---|---|
| **Track** | Setup |
| **Phụ thuộc** | — |
| **Chặn** | tất cả |
| **File** | `pyproject.toml`, `Makefile`, `genesis/__init__.py`, `tests/`, `.gitignore` |
| **Ước lượng** | ~40 dòng · 30 phút |
| **Giao cho model rẻ?** | ✅ cơ học thuần, test bắt được mọi lỗi |
| **Tài liệu gốc** | [02 §4](../02-SANDBOX-V4.md), v4 Bước 0.1 |

## 1. Mục tiêu
Có một kho mà `make test` và `make run` chạy được, trước khi có bất kỳ logic nào. Dựng sau thì mỗi lần thêm file lại phải sửa đường import.

## 2. Đầu vào đã có
`config.py` ở gốc kho — **chuyển vào `genesis/config.py`**, không sửa nội dung.

## 3. Việc phải làm
1. `conda create -n genesis python=3.11 -y && conda activate genesis`
2. Cấu trúc gói theo [02 §4](../02-SANDBOX-V4.md) — tạo file rỗng có docstring cho: `config.py`, `traits.py`, `creature.py`, `world.py`, `reflex.py`, `logio.py`, `render.py`, `run.py`. Đừng tạo file của track L/B/N — chưa tới lúc.
3. `pyproject.toml`: phụ thuộc **chỉ** `rich`, `httpx`. Dev: `pytest`. `pygame-ce` để dành X-07.
4. `Makefile`: `test` · `run` · `lint` · `clean`
5. `run.py` nhận `--seed --ticks --out --arm` (argparse), hiện chỉ in tham số rồi thoát.
6. `.gitignore`: `runs/`, `models/`, `__pycache__/`, `*.jsonl`, `.pytest_cache/`

## 4. Chữ ký và bất biến
```python
# genesis/run.py
def main(argv: list[str] | None = None) -> int: ...
# --seed INT (bắt buộc) --ticks INT (mặc định 400)
# --out PATH (mặc định runs/<seed>-<timestamp>.jsonl) --arm STR (mặc định "STANDARD")
```
**Bất biến:** không import chéo giữa các module ở bước này. `world.py` chưa được import `reflex.py`.

## 5. Bẫy
`config.py` phải nằm **trong** gói `genesis/`, không ở gốc. Để ở gốc thì `import config` chạy lúc dev và hỏng lúc đóng gói, và bạn sẽ mất một buổi tối.

## 6. Nghiệm thu
```bash
conda activate genesis && pip install -e ".[dev]" && make test && python -m genesis.run --seed 42 --ticks 10 && python -c "from genesis import config; assert config.GRID_W == 24; print('OK')"
```

## 7. Prompt giao việc
```
BỐI CẢNH
Sim ALife 2D, Python 3.11. Phụ thuộc runtime CHỈ rich và httpx. Dev: pytest.
Đọc trước: docs/02-SANDBOX-V4.md §4. Đừng đọc tài liệu khác.

VIỆC
Dựng khung kho: pyproject.toml (editable, extras [dev]), Makefile (test/run/lint/clean),
gói genesis/ với các file rỗng có docstring: config.py traits.py creature.py world.py
reflex.py logio.py render.py run.py. Chuyển config.py ở gốc kho vào genesis/config.py,
KHÔNG sửa nội dung. run.py có argparse: --seed (bắt buộc, int) --ticks (mặc định 400)
--out (mặc định runs/<seed>-<timestamp>.jsonl) --arm (mặc định "STANDARD"); hiện chỉ in
tham số rồi return 0. .gitignore: runs/ models/ __pycache__/ *.jsonl .pytest_cache/
Thêm tests/test_smoke.py kiểm import được genesis.config và GRID_W == 24.

RÀNG BUỘC
- Không thêm phụ thuộc ngoài danh sách trên.
- Không tạo file nào khác. Không sửa nội dung config.py.
- Không viết README.

NGHIỆM THU
pip install -e ".[dev]" && make test && python -m genesis.run --seed 42 --ticks 10

TRẢ VỀ: chỉ diff.
```
