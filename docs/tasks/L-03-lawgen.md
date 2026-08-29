# L-03 · Bốc thăm luật và Gate A

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | L-01 |
| **Chặn** | L-05 |
| **File** | `genesis/lawgen.py` |
| **Ước lượng** | ~150 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ vòng bốc thăm giao được; **`observable()` tự viết** |
| **Tài liệu gốc** | [03 §3.1 §3.2 §6.3](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Sinh đề bài. Chất lượng của bộ sinh quyết định chất lượng của mọi phép đo sau đó — luật không công bằng biến điểm khám phá thành xổ số.

## 2. Đầu vào đã có
`Law`, `random_law` từ L-01. `law_config.TIER_PLAN`, `LAWS_PER_MATCH`.

## 3. Việc phải làm
1. `generate(seed, arm, world_cfg) -> list[Law]` theo `TIER_PLAN`.
2. `observable(law, min_sense) -> bool` — **Gate A**.
3. Ràng buộc [03 §6.3](../03-LUAT-AN-V5.md): ở `STANDARD` phải có **≥1 luật đơn độc** và **≥1 luật hợp tác**.
4. `HARSH` thêm luật giả (tương quan không nhân quả) — [03 §3.6](../03-LUAT-AN-V5.md).
5. Gate B và C ở [L-05](L-05-gate-bc.md), để sẵn chỗ cắm.

## 4. Chữ ký và bất biến
```python
def generate(seed: int, arm: str, world_cfg: dict) -> list[Law]: ...
def observable(law: Law, min_sense: int) -> bool: ...
def is_solo_exploitable(law: Law) -> bool: ...
def requires_cooperation(law: Law) -> bool: ...
```
**Bất biến 1:** `features(law) ⊆ observable(min_sense)`. Luật đòi hỏi thông tin mà giác quan không cấp là luật không công bằng.
**Bất biến 2:** dùng **đúng một** `random.Random(seed)` truyền xuống. Gọi `random.xxx()` ở module-level trong bộ sinh luật là cách chắc chắn nhất để mất khả năng tái lập của cả dự án.
**Bất biến 3:** hoán vị bề mặt ([W-13](W-13-sandbox-v5.md)) dùng **luồng rng riêng**, không chung với bốc luật. Chung thì luật và bề mặt tương quan.

## 5. Bẫy
Ràng buộc §6.3 dễ bị bỏ quên vì ván vẫn chạy được khi thiếu nó. Nhưng nếu cả 3 luật đều đơn độc thì **mọi agent duy lý đều im lặng**, và bạn không quan sát được gì về hợp tác — cả [B-12](B-12-teach.md) thành trang trí. Viết assert, đừng viết comment.

## 6. Nghiệm thu
```bash
python - <<'PY'
from genesis.lawgen import generate, observable, is_solo_exploitable, requires_cooperation
from genesis import law_config as lc
a = generate(42, "STANDARD", {}); b = generate(42, "STANDARD", {})
assert a == b, "bốc thăm không tất định"
for i in range(200):
    laws = generate(i, "STANDARD", {})
    assert len(laws) == 3
    assert all(observable(l, min_sense=1) for l in laws), (i, laws)
    assert any(is_solo_exploitable(l) for l in laws), i
    assert any(requires_cooperation(l) for l in laws), i
    assert sorted(l.tier() for l in laws) != ["D1","D1","D1"], i
print("OK 200 bộ luật")
PY
# đọc bằng mắt 20 bộ, phải nghe hợp lý
python scripts/lawgen_preview.py --n 20 --arm STANDARD
```
