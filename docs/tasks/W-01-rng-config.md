# W-01 · RNG tất định và config

| | |
|---|---|
| **Track** | World (v4 M0) |
| **Phụ thuộc** | S-01 |
| **Chặn** | W-02 và mọi thứ sau |
| **File** | `genesis/config.py`, `genesis/run.py` |
| **Ước lượng** | ~20 dòng · 30 phút |
| **Giao cho model rẻ?** | ❌ v4 §10 — phần tư duy, tự viết |
| **Tài liệu gốc** | v4 Bước 1 |

## 1. Mục tiêu
Khoá tính tất định từ dòng code đầu tiên. Đây là bất biến mà mọi thứ khác dựa vào: replay, so sánh giữa các nhánh thí nghiệm, gate lọc luật, và kiểm tra hồi quy. Nhồi vào sau thì phải viết lại hết.

## 2. Đầu vào đã có
`genesis/config.py` đã đủ hằng số cho M0+M1. Test bắt `random` module-level đã có ở S-03.

## 3. Việc phải làm
1. Tạo **đúng một** `random.Random(seed)` trong `run.py`.
2. Truyền nó **xuống** mọi hàm cần ngẫu nhiên qua tham số `rng`. Không có biến toàn cục.
3. In 20 số đầu ra stdout khi `--debug-rng` để kiểm bằng mắt.

## 4. Chữ ký và bất biến
```python
def main(argv=None) -> int:
    args = parse(argv)
    rng = random.Random(args.seed)      # ĐÚNG MỘT, ở đây, không nơi nào khác
    ...
```
**Bất biến 1:** không bao giờ gọi `random.xxx()` — luôn `rng.xxx()`.
**Bất biến 2:** không dùng `set` khi thứ tự ảnh hưởng kết quả. Thứ tự lặp của `set` không ổn định giữa các lần chạy. Dùng `list` hoặc `dict` (giữ thứ tự chèn).
**Bất biến 3:** không dùng `hash()` của Python cho bất cứ gì ảnh hưởng sim — nó có salt ngẫu nhiên mỗi tiến trình. Cần băm thì `hashlib.md5(...).hexdigest()`.

## 5. Bẫy
Bất biến 3 là bẫy chết người và nó **im lặng**: [02 §5](../02-SANDBOX-V4.md) dùng `hash(species_id)` để chọn màu. Với `PYTHONHASHSEED` mặc định, màu sẽ đổi mỗi lần chạy và replay sẽ ra một ván trông khác. Dùng `hashlib` ngay từ đầu.

## 6. Nghiệm thu
```bash
python -m genesis.run --seed 42 --debug-rng | head -20 > /tmp/a
python -m genesis.run --seed 42 --debug-rng | head -20 > /tmp/b
diff /tmp/a /tmp/b && echo "TẤT ĐỊNH OK"
make test   # test bắt random module-level phải xanh
```
