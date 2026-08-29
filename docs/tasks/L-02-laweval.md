# L-02 · Cắm luật vào vòng tick

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | L-01, W-11 |
| **Chặn** | L-05, B-07 |
| **File** | `genesis/laweval.py`, `genesis/world.py` |
| **Ước lượng** | ~130 dòng · 2 giờ |
| **Giao cho model rẻ?** | ❌ tính đồng thời + thứ tự pha |
| **Tài liệu gốc** | [03 §11 L3](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Luật ẩn thật sự tác động lên thế giới. Sau việc này, ván chơi **có bí mật để khám phá**.

## 2. Đầu vào đã có
`Law` từ L-01, tham số `laws` đã có sẵn trong chữ ký `tick()` từ W-11 bất biến 4.

## 3. Việc phải làm
1. `evaluate(law, event, ctx) -> Effect | None`.
2. Hook vào **pha 4** của `tick()` — sau resolve, **trước** kiểm chết.
3. `apply_effect(creature, effect, world, rng)`.
4. Effect sửa **địa hình** (`SPREAD`, `SPAWN`) đi vào **pha 6**, không phải pha 4.
5. Ghi `LAW_FIRED` với `law_id / creature_id / tick / effect`.

## 4. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class LawEvent:
    kind: TriggerKind; actor_id: str; arg: str | None
    ctx: "Ctx"          # đủ trường cho MỌI cond có thể, không chỉ cond của luật này

def evaluate(law: Law, ev: LawEvent) -> Effect | None: ...
def apply_effect(c: Creature, e: Effect, world: World, rng) -> None: ...
def apply_world_effect(e: Effect, world: World, rng) -> None: ...   # pha 6
```
**Bất biến 1:** luật kích hoạt trong **cùng pha đồng thời** với chiến đấu. Thu hết `(creature, effect)` rồi mới áp dụng, đúng như intent ở W-11. Áp dụng tuần tự thì con đi trước ăn hiệu ứng trước và bạn mất tính đồng thời mà W-11 đã rất cẩn thận mới có.
**Bất biến 2:** `ctx` chứa **toàn bộ** ngữ cảnh, không chỉ trường mà luật hiện tại cần. L-04 dựa vào điều này — nếu `ctx` chỉ điền trường của luật thật thì mọi luật khác đánh giá thành `None` và ăn điểm oan bằng nhau.
**Bất biến 3:** `evaluate` là **hàm thuần**. Không đọc thế giới, không đọc `rng`. Mọi thứ nó cần đã ở trong `ev`. Đây là điều kiện để L-04 gọi được nó trên tình huống tổng hợp.

## 5. Bẫy
Thứ tự pha. `SPREAD(FIRE)` sửa địa hình → nếu chạy ở pha 4 thì lửa lan xong rồi mới kiểm chết, và con đứng trên ô vừa cháy chết ngay trong tick đó thay vì tick sau. Nhỏ, nhưng nó làm luật khó định danh hơn nhiều so với ý định thiết kế.

## 6. Nghiệm thu
```bash
# 1. tắt luật -> ván GIỐNG HỆT M1
python -m genesis.run --seed 77 --ticks 300 --no-render --laws none --out /tmp/off.jsonl
python -m genesis.run --seed 77 --ticks 300 --no-render --arm WORLD_FLAT --out /tmp/flat.jsonl
diff /tmp/off.jsonl /tmp/flat.jsonl && echo "TẮT LUẬT = M1 OK"

# 2. nạp tay ba luật ở 03 §2.4, mỗi luật phải kích hoạt
python -m genesis.run --seed 77 --ticks 400 --no-render --laws fixtures/three_laws.json --out /tmp/on.jsonl
python - <<'PY'
import json, collections
fired=collections.Counter(json.loads(l)["law_id"] for l in open('/tmp/on.jsonl')
                          if json.loads(l)["kind"]=="LAW_FIRED")
assert set(fired)=={"L0","L1","L2"}, fired
assert min(fired.values())>=5, fired
print("OK", fired)
PY

# 3. đồng thời vẫn giữ: chạy lại test hoán vị của W-11 nhưng CÓ luật
python -m pytest tests/test_tick_order.py -q -k laws
```
