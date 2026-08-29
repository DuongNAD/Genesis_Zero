# W-07 · Vector trait và chỉ số dẫn xuất

| | |
|---|---|
| **Track** | World (v4 M1) |
| **Phụ thuộc** | W-04 |
| **Chặn** | W-08, W-10 |
| **File** | `genesis/traits.py` |
| **Ước lượng** | ~70 dòng · 1 giờ |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 7, [02 §2](../02-SANDBOX-V4.md) |

## 1. Mục tiêu
Cơ thể. Bất biến **tổng bằng 12** là thứ khiến chống gian lận ở chế độ mở hoạt động mà không cần xác minh gì ([04 §7.1](../04-THE-GIOI-MO.md)) — nên nó phải không lách được, không phải "thường đúng".

## 2. Đầu vào đã có
`config.FOUNDERS`, `TRAIT_SUM`, và mọi hệ số dẫn xuất.

## 3. Việc phải làm
1. `Traits` frozen dataclass, 6 trường int.
2. Kiểm bất biến trong `__post_init__`.
3. Property cho mọi chỉ số dẫn xuất, công thức **lấy từ config**, không viết số.
4. `shift(from_trait, to_trait) -> Traits` trả **vector mới**, không sửa tại chỗ.

## 4. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class Traits:
    brain: int; attack: int; armor: int; speed: int; sense: int; stomach: int

    def __post_init__(self):
        assert sum(astuple(self)) == config.TRAIT_SUM
        assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in astuple(self))

    @property
    def energy_max(self)     -> float: ...
    @property
    def token_budget(self)   -> int: ...
    @property
    def think_interval(self) -> int: ...
    @property
    def damage(self)         -> float: ...
    @property
    def dmg_taken_mult(self) -> float: ...
    @property
    def moves_per_tick(self) -> int: ...
    @property
    def sight_radius(self)   -> int: ...
    @property
    def upkeep(self)         -> float: ...

    def shift(self, frm: str, to: str) -> "Traits": ...   # trả MỚI
```
**Bất biến 1:** `frozen=True`. Sửa tại chỗ là cách chắc chắn nhất để một `Traits` sai tổng lọt qua.
**Bất biến 2:** kiểm nằm trong `__post_init__`, không phải trong một hàm `validate()` mà ai đó có thể quên gọi.
**Bất biến 3 (chuẩn bị v5):** `brain` sẽ còn quyết định `codex_size` và `events_in_prompt` ([03 §4.1](../03-LUAT-AN-V5.md)). Đừng viết logic phụ thuộc `brain` rải rác — cho tất cả vào property ở đây.

## 5. Bẫy
`shift` phải kiểm cả hai đầu: `frm` phải có ≥1, `to` phải có ≤ `TRAIT_MAX - 1`. Chỉ kiểm một đầu thì `shift("brain","speed")` với `speed=5` sẽ tạo ra `speed=6` và `__post_init__` mới bắt được — muộn hơn, và thông báo lỗi khó hiểu hơn.

## 6. Nghiệm thu
```bash
python - <<'PY'
from genesis.traits import Traits
from genesis import config
for sp, v in config.FOUNDERS.items():
    t = Traits(*v); assert sum(v)==12
L1 = Traits(*config.FOUNDERS["L1"])
assert (L1.token_budget, L1.think_interval, L1.damage) == (176, 3, 13), (L1.token_budget, L1.think_interval, L1.damage)
L4 = Traits(*config.FOUNDERS["L4"]); assert abs(L4.dmg_taken_mult - 0.40) < 1e-9
L5 = Traits(*config.FOUNDERS["L5"]); assert L5.moves_per_tick == 3 and L5.token_budget == 32
for bad in [(5,5,5,5,5,5), (0,0,0,0,0,12), (4,3,1,2,1,0)]:
    try: Traits(*bad); raise SystemExit(f"PHẢI lỗi: {bad}")
    except AssertionError: pass
n = L1.shift("brain","armor"); assert n.brain==3 and n.armor==2 and L1.brain==4   # bất biến
print("OK")
PY
```
