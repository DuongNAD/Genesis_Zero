# S-03 · pytest + kiểm tra tái lập

| | |
|---|---|
| **Track** | Setup |
| **Phụ thuộc** | S-01 |
| **Chặn** | mọi việc có nghiệm thu tự động |
| **File** | `tests/conftest.py`, `tests/test_determinism.py`, `Makefile` |
| **Ước lượng** | ~50 dòng · 40 phút |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | v4 Bước 1 |

## 1. Mục tiêu
Tính tái lập là bất biến số một của dự án. Nó phải có **bài kiểm tra tự động từ ngày đầu**, không phải một lời hứa. Nhồi vào sau thì phải viết lại hết.

## 2. Đầu vào đã có
Khung kho từ S-01.

## 3. Việc phải làm
1. `conftest.py`: fixture `rng` trả `random.Random(1234)`; fixture `tmp_run` cho thư mục chạy tạm.
2. `test_determinism.py`:
   - chạy `run.py` hai lần cùng seed, so hai file JSONL **byte-by-byte**
   - quét toàn kho tìm gọi `random.` ở module-level (đọc AST, không grep)
   - quét tìm `set(` ở chỗ kết quả được lặp qua (cảnh báo, không fail)
3. `make test` → `pytest -q`. `make lint` → `ruff check` nếu có, không thì bỏ qua im lặng.

## 4. Chữ ký và bất biến
```python
def assert_runs_identical(seed: int, ticks: int, tmp_path) -> None: ...
def module_level_random_calls(pkg_dir: Path) -> list[tuple[str, int]]:
    """Trả [(file, dòng)] mọi lời gọi random.* ở module-level. Rỗng là đạt."""
```

## 5. Bẫy
Dùng **AST** để tìm `random.` ở module-level, đừng grep. Grep sẽ báo nhầm mọi dòng trong thân hàm và bạn sẽ tắt test đi sau ba lần báo động giả — mất luôn tấm lưới.

## 6. Nghiệm thu
```bash
make test
# test_determinism pass; cố tình thêm `X = random.random()` ở module-level trong genesis/world.py
# thì test PHẢI đỏ; xoá đi thì xanh lại
```

## 7. Prompt giao việc
```
BỐI CẢNH
Sim ALife 2D, Python 3.11. Kho đã có gói genesis/ và genesis/run.py với argparse
--seed --ticks --out. Đọc trước: docs/06-CONG-VIEC.md §5. Đừng đọc tài liệu khác.

VIỆC
1. tests/conftest.py: fixture `rng` -> random.Random(1234); fixture `tmp_run` -> thư mục tạm.
2. tests/test_determinism.py:
   a) assert_runs_identical(seed, ticks, tmp_path): chạy genesis.run hai lần cùng seed vào
      hai file khác nhau, so sánh nội dung byte-by-byte, assert bằng nhau.
   b) module_level_random_calls(pkg_dir) -> list[(file, lineno)]: dùng ast, duyệt mọi .py
      trong genesis/, tìm lời gọi random.<gì đó> nằm ở MODULE LEVEL (không trong hàm/lớp).
      Test assert danh sách rỗng.
3. Makefile: make test -> pytest -q

RÀNG BUỘC
- Dùng ast, KHÔNG dùng grep/regex cho việc (b).
- Không thêm phụ thuộc ngoài pytest.
- Không tạo file nào khác. Không sửa file trong genesis/.

NGHIỆM THU
make test xanh. Thêm dòng `X = random.random()` ở module-level trong genesis/world.py
thì make test PHẢI đỏ.

TRẢ VỀ: chỉ diff.
```
