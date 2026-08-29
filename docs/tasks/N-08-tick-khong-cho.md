# N-08 · Tick không chờ ai  ★

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-07 · **Chặn** N-09, N-12 |
| **File** | `net/match.py` · ~90 dòng · 2 giờ |
| **Giao cho model rẻ?** | ❌ đồng thời + thời gian thực |
| **Tài liệu gốc** | [04 §4](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
**Quyết định kỹ thuật quan trọng nhất của chế độ mở.** v4 tính cho LAN. Qua internet, độ trễ là 50 ms tới 5 giây và có người sẽ mất mạng giữa chừng. Sim không được phép chờ ai.

## 2. Chữ ký và bất biến
```python
async def tick_loop(self) -> None:
    while phase == RUNNING:
        t0 = time.monotonic()
        self.issue_work(tick)          # phát yêu cầu, KHÔNG chờ
        world.tick(...)                # phản xạ với goal ĐANG CÓ
        await sleep_until(t0 + tick_ms/1000)

def on_decision(self, item, payload, now_tick) -> str:
    k = now_tick - item.issued_tick
    if k <= LATE_TOLERANCE: apply(); log("THINK_LATENCY", k); return "applied"
    log("DECISION_LATE", k);                                   return "dropped"
```
**Bất biến 1 — chịu được trễ vì tầng chiến lược trả về goal có TTL 2–12 tick**, không trả nước đi. Goal về muộn 1–2 tick vẫn còn giá trị. Nếu client trả nước đi thì trễ một tick là hỏng — đây là lý do thứ hai (sau tiết kiệm token) khiến kiến trúc hai tầng là lựa chọn đúng.
**Bất biến 2 — điều chỉnh nhịp chung, không ưu đãi riêng.**
```python
# mỗi 20 tick
p90 = percentile(latency_ticks_gần_đây, 90)
tick_ms = clamp(tick_ms * (1.15 if p90 > LATE_TOLERANCE else 0.95), 3000, 10000)
```
Nới `LATE_TOLERANCE` riêng cho máy chậm thì con đó được nghĩ lâu hơn con khác — một ưu đãi vô hình không ai giải thích được sau này. **Nhịp là của thế giới, không phải của cá thể.**
**Bất biến 3 — quyết định trễ vẫn phải qua `validate()`.** Muộn không có nghĩa là được tin.

## 3. Bẫy
`sleep_until` phải dùng `time.monotonic()`, không phải `time.time()`. Đồng hồ hệ thống nhảy (NTP, đổi múi giờ) sẽ làm ván đứng hình hoặc chạy vọt, và bạn sẽ đổ lỗi cho mạng.

## 4. Nghiệm thu
```bash
python scripts/latency_sim.py --server http://localhost:8000 --profile mixed
# 5 client giả: 0.2s, 1s, 3s, 8s, và một client CHẾT hẳn giữa chừng
python - <<'PY'
import json,collections
r=[json.loads(l) for l in open('runs/latency_sim.jsonl')]
ticks=[x['t'] for x in r if x['kind']=='TICK']
assert max(ticks)>=200, "ván bị chặn bởi client chậm -> tick ĐANG chờ"
lat=collections.Counter(x['kind'] for x in r if x['kind'] in ('DECISION_LATE','NODE_DOWN'))
assert lat['DECISION_LATE']>0 and lat['NODE_DOWN']>0, lat
adj=[x['tick_ms'] for x in r if x['kind']=='TICK_RATE']
assert 3000<=min(adj) and max(adj)<=10000, adj
print("KHÔNG CHỜ AI OK", lat)
PY
# rút dây mạng một client giữa chừng -> sim chạy tiếp, loài đó hoang dã
```
