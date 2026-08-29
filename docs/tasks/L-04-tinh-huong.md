# L-04 · Không gian tình huống và lấy mẫu phân tầng

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | L-01 |
| **Chặn** | L-05, L-06, B-09 |
| **File** | `genesis/situations.py` |
| **Ước lượng** | ~120 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ dựng `Situation` giao được; **tỉ lệ phân tầng tự làm** |
| **Tài liệu gốc** | [03 §5.2](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Hạ tầng cho verifier. Làm **trước** khi cần, vì Gate B/C ở L-05 cũng dùng nó. Đây là chỗ quyết định điểm từng phần có công bằng không.

## 2. Đầu vào đã có
`LawEvent` và `Ctx` từ L-02 — dùng lại **đúng** kiểu đó, đừng định nghĩa song song.

## 3. Việc phải làm
1. `Situation` = `LawEvent` với `ctx` điền **đầy đủ mọi trường**.
2. `sample_situations(law, n=400, rng)` theo tỉ lệ 40 / 40 / 20.
3. Trong tầng "gần trượt", trải đều theo **từng chiều cond một**.

## 4. Chữ ký và bất biến
```python
Situation = LawEvent      # cùng kiểu, KHÔNG định nghĩa lại

def sample_situations(law: Law, n: int, rng: random.Random) -> list[Situation]: ...
def strata_of(law: Law, s: Situation) -> str: ...   # "fires" | "near_miss" | "unrelated"
```
Tỉ lệ, lấy từ `law_config.SITUATION_STRATA`:

| Tầng | Tỉ lệ | Nghĩa |
|---|---|---|
| `fires` | 40% | luật kích hoạt |
| `near_miss` | 40% | trigger đúng, **cond sai** |
| `unrelated` | 20% | không liên quan |

**Bất biến 1 — cái quan trọng nhất:** `ctx` điền **toàn bộ** trường cho mọi cond có thể, không chỉ cond của luật thật. Chỉ điền trường mà `L` cần thì mọi luật `C` nhắc tới trường khác đều ra `None` và ăn điểm oan bằng nhau.
**Bất biến 2:** trong `near_miss`, trải đều theo từng chiều: hỏng cond thứ nhất riêng, hỏng cond thứ hai riêng, hỏng cả hai. Không có nó thì "đoán trigger, kệ cond" ăn điểm cao ([03 §5.6](../03-LUAT-AN-V5.md)).
**Bất biến 3:** tất định theo `rng` — cùng luật + cùng seed → cùng bảng chấm, mọi lần chạy.

## 5. Bẫy
Với luật **0 cond** (D1) thì `near_miss` không tồn tại theo định nghĩa. Trường hợp này phân tầng thành 50 `fires` / 50 `unrelated`, và `acc₀` sẽ khác. Xử lý tường minh, đừng để nó rơi vào nhánh chia cho 0.

## 6. Nghiệm thu
```bash
python - <<'PY'
import random, collections
from genesis.lawgen import generate
from genesis.situations import sample_situations, strata_of
from genesis.laweval import evaluate
for seed in range(20):
    for law in generate(seed, "STANDARD", {}):
        ss = sample_situations(law, 400, random.Random(seed))
        c = collections.Counter(strata_of(law, s) for s in ss)
        if law.conds:
            for k, want in (("fires",.4),("near_miss",.4),("unrelated",.2)):
                assert abs(c[k]/400 - want) < 0.03, (law, c)
            # trải đều theo chiều cond
            miss = collections.Counter(s.meta["broken_cond"] for s in ss if strata_of(law,s)=="near_miss")
            assert max(miss.values())/min(miss.values()) < 1.5, miss
        # acc0 của giả thuyết NULL
        acc0 = sum(evaluate(law, s) is None for s in ss)/400
        assert 0.55 <= acc0 <= 0.65, (law, acc0)
print("OK")
PY
```
