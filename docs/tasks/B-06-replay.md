# B-06 · Replay từ log  ✦ CHỐT M2

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-05, S-04 · **Chặn** — |
| **File** | `genesis/replay.py`, `genesis/run.py` · ~70 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | v4 Bước 18 |

## 1. Mục tiêu
Tính tất định từ seed **không còn giữ được** khi có LLM — sampling ở `temperature > 0` đã ngẫu nhiên, timeout mạng càng không. Bù bằng replay từ log.

**Ranh giới cần nhớ và đừng hứa quá:** M0–M1 tái lập từ **seed**. M2 trở đi chỉ tái lập từ **log**.

## 2. Chữ ký và bất biến
```python
def prompt_hash(system: str, user: str) -> str: ...     # md5, chỉ hash này vào log

class ReplayStrategist:
    """Đọc quyết định từ log thay vì gọi model."""
    def __init__(self, log_path: Path, prompt_fn: PromptFn | None = None): ...
    def decide(self, c, world, seen, rng=None, tick_no=0) -> ActiveGoal | None: ...
```
**Bất biến 1:** mỗi `LLM_CALL` ghi `prompt_hash` (md5) + response **thô**. Không ghi prompt đầy đủ — log sẽ phình gấp 20 lần.
**Bất biến 2:** replay so `prompt_hash`; lệch → dừng và báo rõ tick nào, **đừng chạy tiếp**. Replay lệch âm thầm là thứ tệ hơn không có replay.
**Bất biến 3:** tra đúng khoá `(t, creature_id)` và **không phá huỷ** — gọi hai lần cùng một lượt phải ra cùng một kết quả. Thiếu bản ghi thì trả `None` để rơi về phản xạ; **không** mượn quyết định của lượt khác. Hai bản ghi trùng khoá trong log thì báo lỗi ngay lúc nạp, đừng chọn bừa một cái.
**Bất biến 4:** không truyền `prompt_fn` thì không kiểm được bất biến 2, và lớp này phải **nói thẳng ra** (`self.verifying is False`) thay vì im lặng bỏ qua.

**Bất biến 5 — hợp đồng đầy đủ: MỌI tác dụng phụ chạm tới prompt của một lượt sau đều phải nằm trong log VÀ được phát lại.** Không phải chỉ `goal`. Bốn thứ, và mỗi thứ chỉ lộ ra khi có một **model thật** đi vào đúng nhánh đó — model giả không viết `note`, không nói, không ghi sổ, nên cả ba lỗ hổng đều xanh:

| Cái gì | Chạm tới đâu | Triệu chứng khi quên |
|---|---|---|
| `goal` | ý đồ con vật | lệch ngay |
| `note` | khối GHI CHÚ RIÊNG lượt sau | lệch ở lượt gọi **thứ hai** |
| `say` | energy người nói **và** khối NGHE ĐƯỢC của người nghe | lệch khi có ai đó nghe |
| `CODEX_OP` · `TRAIT_SHIFT` | khối SỔ LUẬT; `brain` đổi thì khối D đổi | lệch sau lần ghi sổ / dịch trait đầu tiên |

Cộng: replay phải biết lượt đó **hỏi gì** (`kind_asked`). Một lượt `codex` hay `shift` cũng trả JSON, và coi mọi phản hồi là `decide` nghĩa là áp một goal mà ván thật đã **vứt đi** — hai ván khớp tới t=57 rồi lệch đúng ở t=60, tick đầu tiên có một lời gọi khác `decide`.

> Bản đầu (giao cho model rẻ) có đúng đường mà bất biến 3 cấm: `pop()` khỏi hàng đợi theo `creature_id`, thiếu bản ghi cho lượt này thì lấy tạm bản ghi kế tiếp. Mọi test xanh, và file kết quả trông như thật — nhưng là một ván khác.

## 3. Nghiệm thu — ✦ CHỐT M2, cả bốn điều kiện
```bash
python -m genesis.run --seed 60 --ticks 400 --llm L1:0 --out /tmp/live.jsonl
python -m genesis.run --replay /tmp/live.jsonl --out /tmp/rep.jsonl
diff <(jq -c 'del(.wallclock)' /tmp/live.jsonl) <(jq -c 'del(.wallclock)' /tmp/rep.jsonl) && echo "REPLAY OK"
python - <<'PY'
import json, collections, glob
rows=[json.loads(l) for l in open('/tmp/live.jsonl')]
k=collections.Counter(r["kind"] for r in rows)
calls=k["LLM_CALL"]
assert k["LLM_MISS"]/calls < 0.01, "JSON hợp lệ phải >= 99%"
assert k["LLM_SEMANTIC_FAIL"]/calls < 0.05, "SEMANTIC_FAIL phải < 5%"
print("OK", k)
PY
# điều kiện 4: con dùng LLM sống KHÔNG TỆ HƠN con reflex cùng loài, qua 5 seed
python scripts/compare_arms.py --seeds 1,2,3,4,5 --a "llm L1:0" --b "reflex L1:1"
```
> Nếu LLM **tệ hơn** reflex thì báo cáo đúng như vậy (v4 §11.5). Đó mới là điều làm dự án đáng tin.
