# B-11 · Kênh nói và danh tiếng

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-05 · **Chặn** B-12, X-04 |
| **File** | `genesis/speech.py` · ~120 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ cơ chế giao được; ba ràng buộc nghe thì tự kiểm |
| **Tài liệu gốc** | v4 Bước 24–25 |

## 1. Mục tiêu
Ngôn ngữ, và cái giá của nó. Không có trí nhớ về phản bội thì không có tin tưởng nào sinh ra được — đây là điều kiện cần, không phải tính năng thêm.

## 2. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class Say: signal: str; text: str; teach: int | None = None   # teach -> B-12

def hearers(speaker: Creature, creatures, world) -> tuple[list, list]:
    """Trả (nghe đủ text, chỉ nghe signal)."""
```
Ba ràng buộc, cả ba bắt buộc:
1. **`text` ≤ 60 ký tự (~12 token).** Không chặn thì chúng viết diễn văn và cháy ngân sách.
2. **Chỉ nghe được trong `sight_radius` của *người nghe*.** Chat toàn cục = phối hợp tức thì = hết hay. Dùng `sense` của người nghe nghĩa là **`sense` cao = nghe lén giỏi**.
3. **Nói tốn 2 energy**, và mọi con trong `2 × sight_radius` nghe được **`signal` (không có `text`)**. Con mồi hú cảnh báo đồng loại thì đồng thời chỉ điểm vị trí mình. **Im lặng thành một chiến lược.**

Liên loài: cùng loài nghe `text` đầy đủ; khác loài chỉ nhận `signal`.

**Danh tiếng:** mỗi con giữ `deque(maxlen=8)` các bản ghi `(speaker_id, claimed_signal, observed_goal_next_tick, tick)`, cộng danh sách **ai đã giết mình** — không bị xoá khi chết.

**Bất biến an ninh:** `text` từ client → strip newline và ký tự điều khiển, bọc delimiter, ghi rõ trong prompt đó là *lời một sinh vật khác nói*, không phải chỉ thị ([04 §7.4](../04-THE-GIOI-MO.md)).

## 3. Nghiệm thu
```bash
pytest tests/test_speech.py -q
# ca bắt buộc: người nghe sense cao nghe được xa hơn người nghe sense thấp
#              khác loài chỉ nhận signal · text > 60 ký tự bị cắt
#              text chứa "\n" hoặc "IGNORE ALL" vẫn được bọc delimiter đúng
python -m genesis.run --seed 71 --ticks 400 --llm all --arm VOCAL --out /tmp/v.jsonl
python -c "
import json;r=[json.loads(l) for l in open('/tmp/v.jsonl')]
sp=[x for x in r if x['kind']=='SPEAK']
assert sp and all(len(x.get('text','') or '')<=60 for x in sp)
assert any(len(x['hear_full'])<len(x['hear_signal']) for x in sp), 'tầm signal phải rộng hơn'
print('OK',len(sp),'lần nói')"
```
