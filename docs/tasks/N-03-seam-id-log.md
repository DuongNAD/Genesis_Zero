# N-03 · Đường may 3 — id cá thể và trường log mở rộng

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** S-04 · **Chặn** N-04, B-10 |
| **File** | `genesis/logio.py`, `genesis/creature.py` · ~20 dòng · **15 phút** |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [04 §5](../04-THE-GIOI-MO.md) đường may 3 và 5 |

## 1. Mục tiêu
**Thêm trường vào format log sau này nghĩa là ván cũ không so được với ván mới.** Mười lăm phút hôm nay tránh việc vứt bỏ toàn bộ dữ liệu của ba tháng đầu.

## 2. Chữ ký và bất biến
```python
COMMON_FIELDS = ("t","kind","match_id","creature_id","species_id",
                 "client_id","model_name")     # luôn có mặt, null cũng phải có
```
**Bất biến 1:** `creature_id = f"{species_id}:{n}"` với `species_id` **cấp lúc chạy**. Không mã hoá chỉ số loài, không hardcode `"L1"`.
**Bất biến 2:** `client_id` và `model_name` có mặt trong **mọi** bản ghi ngay từ M0, luôn `null` ở Lab mode.
**Bất biến 3:** `match_id` có mặt từ M0. Một file log có thể chứa nhiều ván ở chế độ mở.

## 3. Nghiệm thu
```bash
python -m genesis.run --seed 1 --ticks 20 --out /tmp/n03.jsonl
python -c "
import json
for l in open('/tmp/n03.jsonl'):
    r=json.loads(l)
    for f in ('t','kind','match_id','creature_id','species_id','client_id','model_name'):
        assert f in r, (f, r)
print('MỌI DÒNG ĐỦ TRƯỜNG OK')"
! grep -rn '\"L1\"\|\"L5\"' genesis/creature.py genesis/logio.py && echo "KHÔNG HARDCODE LOÀI OK"
```
