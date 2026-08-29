# W-10 · Chiến đấu đồng thời và độc

| | |
|---|---|
| **Track** | World (v4 M1) |
| **Phụ thuộc** | W-07 |
| **Chặn** | W-11 |
| **File** | `genesis/world.py` |
| **Ước lượng** | ~55 dòng · 1 giờ |
| **Giao cho model rẻ?** | ❌ v4 §10 — tính đồng thời |
| **Tài liệu gốc** | v4 Bước 10 |

## 1. Mục tiêu
Xung đột. Và bài tập đầu tiên về **đồng thời** mà W-11 sẽ tổng quát hoá.

## 2. Đầu vào đã có
`Traits.damage`, `Traits.dmg_taken_mult`, `config.POISON_DAMAGE`, `POISON_DURATION`.

## 3. Việc phải làm
1. `resolve_combat(attacks, creatures) -> list[CombatResult]` — nhận **toàn bộ** đòn của tick.
2. `damage = attacker.damage * defender.dmg_taken_mult`.
3. L5 phản độc: kẻ tấn công L5 chịu `POISON_DAMAGE`/tick trong `POISON_DURATION` tick.

## 4. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class Attack:  attacker_id: str; defender_id: str
@dataclass(frozen=True)
class CombatResult: target_id: str; dmg: float; poison_from: str | None

def resolve_combat(attacks: list[Attack], creatures: dict[str, Creature]) -> list[CombatResult]: ...
```
**Bất biến — đây là cả việc này:** hai con cùng tấn công nhau trong một tick thì **cả hai** nhận sát thương, tính từ chỉ số **trước** tick. Chụp lại `hp` và trait ở đầu hàm, tính hết, rồi mới áp dụng. **Đừng resolve tuần tự** — nó cho con đi trước một lợi thế vô hình mà không ai giải thích được sau này.

## 5. Bẫy
Độc cũng phải đồng thời: A đánh L5, L5 đánh A, cùng tick → A dính độc **và** L5 nhận sát thương. Nếu bạn kiểm "L5 còn sống không" trước khi gán độc thì kết quả phụ thuộc thứ tự.

## 6. Nghiệm thu
```bash
python - <<'PY'
from genesis.world import resolve_combat, Attack
from genesis.creature import Creature
from genesis.traits import Traits
from genesis import config
def mk(i,sp): 
    c=Creature(i,sp,(0,0),50,100); c.traits=Traits(*config.FOUNDERS[sp]); return c
cs={c.id:c for c in [mk("L2:0","L2"), mk("L4:0","L4"), mk("L1:0","L1"), mk("L5:0","L5")]}
r={x.target_id:x for x in resolve_combat([Attack("L2:0","L4:0")], cs)}
assert abs(r["L4:0"].dmg - 6.4) < 1e-9, r["L4:0"].dmg      # 16 * 0.40
r={x.target_id:x for x in resolve_combat([Attack("L1:0","L5:0")], cs)}
assert r["L1:0"].poison_from == "L5:0"                      # L1 dính độc
# đồng thời: cả hai cùng đánh -> cả hai nhận dmg
out=resolve_combat([Attack("L1:0","L2:0"), Attack("L2:0","L1:0")], cs)
assert {x.target_id for x in out} == {"L1:0","L2:0"}, out
print("OK")
PY
```
