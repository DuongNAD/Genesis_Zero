# W-09 · Tầng phản xạ

| | |
|---|---|
| **Track** | World (v4 M1) |
| **Phụ thuộc** | W-08 |
| **Chặn** | W-11, N-01, N-02 |
| **File** | `genesis/reflex.py` |
| **Ước lượng** | ~110 dòng · 2 giờ |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 9 |

## 1. Mục tiêu
Một bộ điều khiển **hoàn chỉnh** chạy được cả ván không cần LLM. Ba vai, và cả ba đều dùng tới:
- ở M1 nó là bộ điều khiển duy nhất
- ở M2 nó là **nhánh đối chứng** — nếu LLM không hơn nó thì phải báo cáo đúng như vậy
- ở chế độ mở nó là **lưới an toàn** khi client rớt mạng ([04 §4](../04-THE-GIOI-MO.md))

## 2. Đầu vào đã có
`visible` từ W-08, `Traits` từ W-07.

## 3. Việc phải làm
1. `Goal` enum: `FORAGE HUNT FLEE FOLLOW REST WANDER GUARD`.
2. `ActiveGoal`: goal + target + ttl còn lại.
3. `reflex_step` theo thứ tự ưu tiên ở §4.
4. Pathfind **tham lam**: đi ô làm giảm `dist` nhiều nhất. Không cần A* trên lưới 24×24.

## 4. Chữ ký và bất biến
```python
class Goal(StrEnum): FORAGE; HUNT; FLEE; FOLLOW; REST; WANDER; GUARD

@dataclass
class ActiveGoal:
    goal: Goal; target: str | None; ttl: int

def reflex_step(c: Creature, world: World, creatures: list[Creature],
                goal: ActiveGoal, rng: random.Random) -> Intent:
    # 1. Override khẩn cấp: hp < 30% và có kẻ săn mồi trong tầm -> FLEE
    # 2. Nếu không: thực thi goal hiện tại thành nước đi
    # 3. Goal hết TTL và chưa có goal mới -> WANDER
```
**Bất biến 1:** `reflex_step` trả **Intent**, **không tự áp dụng**. Việc áp dụng ở W-11. Trộn hai thứ là con đường ngắn nhất tới bug không tái lập được.
**Bất biến 2:** thuần và tất định với `rng` cho trước. Cùng đầu vào → cùng Intent.
**Bất biến 3 (v5):** **tầng phản xạ không bao giờ đọc Sổ Luật.** Nếu reflex tự né quả độc khi codex ghi độc thì bạn đã hard-code việc khai thác và `exploit_lag` mất hết ý nghĩa ([03 §4.4](../03-LUAT-AN-V5.md)). Khai thác **phải** đi qua goal do LLM chọn.

## 5. Bẫy
Bất biến 3 sẽ rất cám dỗ vi phạm ở B-08, vì nó làm con vật "thông minh hơn" ngay lập tức. Đừng. Nó phá một trong ba tầng chấm điểm của v5.

## 6. Nghiệm thu
```bash
python -m genesis.run --seed 33 --ticks 400 --controller reflex --out /tmp/w09.jsonl
python - <<'PY'
import json, collections
rows=[json.loads(l) for l in open('/tmp/w09.jsonl')]
g=collections.Counter(r.get("goal") for r in rows if r["kind"]=="TICK" and r.get("goal"))
assert g["FORAGE"] > g["WANDER"], g       # đói thì đi ăn, không lang thang vô định
print("OK", g)
PY
```
Và nhìn bằng mắt 400 tick: đói thì đi ăn, yếu thì chạy. Nếu trông như đi ngẫu nhiên thì priority ở §4 chưa đúng.
