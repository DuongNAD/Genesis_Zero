# B-05 · Ghép LLM vào vòng tick, lệch pha

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-03, B-04, W-11 · **Chặn** B-06, B-11, B-13 |
| **File** | `genesis/world.py`, `genesis/strategist.py` · ~90 dòng · 2 giờ |
| **Giao cho model rẻ?** | ❌ đụng vòng tick |
| **Tài liệu gốc** | v4 Bước 17 |

## 1. Mục tiêu
Hai tầng chạy cùng nhau. Đây là chỗ dễ hiểu sai kiến trúc nhất.

## 2. Chữ ký và bất biến
```python
class Strategist(Protocol):
    def decide(self, c, world, seen, rng=None, tick_no=0, current=None) -> ActiveGoal | None: ...

class LlmStrategist:
    async def think(self, creatures, world, tick_no) -> None   # bắn cả đàn, gather
    def begin_tick(self, creatures, world, tick_no) -> None    # cầu nối đồng bộ
    def decide(...) -> ActiveGoal | None                       # chỉ tra bảng
    def observe(self, tick_no, world, creatures, events, state) -> None   # nạp sổ tay
```
**Hai nhịp, không phải một.** `decide` **không** gọi mạng: `begin_tick` bắn hết lượt gọi của tick rồi chờ xong, `decide` chỉ tra kết quả. Đó là cách duy nhất vừa `gather` được (bất biến 4) vừa giữ được bẫy §3.
**`current` có mặt trong chữ ký là có lý do:** vòng tick hỏi tầng chiến lược **mỗi tick**, không phải chỉ khi `ttl` hết — nếu không, câu trả lời của model về giữa chừng sẽ nằm chờ tới lúc goal cũ hết hạn, hoặc bị bỏ hẳn. Tầng nào không muốn đè thì nhìn `current` rồi trả `None`; `ReflexStrategist` làm đúng thế nên hành vi M0/M1 không đổi một tick nào.
**Bất biến 1:** LLM trả **goal**, không trả nước đi. Tầng phản xạ vẫn chạy **mọi tick**. Nếu bạn thấy mình gọi LLM mỗi tick cho mỗi con thì đã hiểu sai kiến trúc.
**Bất biến 2:** gọi khi `tick % think_interval == offset`, offset **rải đều** giữa các cá thể cùng loài. Cùng tổng tải, không dồn cục.
**Bất biến 3:** trừ `cost_think` theo **số token thực sự sinh ra**, không theo `max_tokens`.
**Bất biến 4:** `Strategist` là **Protocol**, không phải hàm. Ba hiện thực: `ReflexStrategist`, `LlmStrategist`, `RemoteClientStrategist`. Đường may thứ 1 của [04 §5](../04-THE-GIOI-MO.md) — xem [N-01](N-01-seam-strategist.md).

## 3. Bẫy
Thu hết kết quả LLM rồi **mới** sang pha resolve. Áp dụng goal ngay khi nó về, giữa pha thu intent, là phá bất biến đồng thời của W-11 — và test hoán vị thứ tự sẽ đỏ.

## 4. Nghiệm thu
```bash
python -m genesis.run --seed 44 --ticks 200 --llm L1:0 --out /tmp/b05.jsonl
python - <<'PY'
import json, collections
rows=[json.loads(l) for l in open('/tmp/b05.jsonl')]
calls=[r for r in rows if r["kind"]=="LLM_CALL"]
assert all(r["creature_id"]=="L1:0" for r in calls)
# KHÔNG kiểm `gaps == {3}`: `think_interval` phụ thuộc `brain`, mà `brain` dịch
# giữa ván (W-11) và về founder mỗi lần chết — nên khoảng cách KHÔNG hằng số.
# Bất biến thật là t % think_interval == offset, nên log mang theo hai số đó.
assert all(r["t"] % r["think_interval"] == r["offset"] for r in calls)
assert all(r["cost_think"] == round(r["tokens_used"]/50,4) for r in calls)
print("OK", len(calls), "lời gọi")
PY
pytest tests/test_llm_tick.py -q   # toàn bộ trên httpx.MockTransport: không model, không cổng
# trong đó `test_hoan_vi_thu_tu_khong_doi_ket_qua` là bất biến hoán vị của W-11,
# chạy lại VỚI tầng LLM cắm vào — đó mới là điều bẫy §3 nói tới.
```
