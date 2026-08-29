# L-05 · Gate B (khả giải) và Gate C (định danh được)

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | L-03, L-04, W-11 |
| **Chặn** | B-10 |
| **File** | `genesis/lawgen.py`, `genesis/refpolicy.py` |
| **Ước lượng** | ~140 dòng · 2–3 giờ |
| **Giao cho model rẻ?** | ❌ suy luận thống kê tinh vi; model sẽ gật đầu rồi làm sai |
| **Tài liệu gốc** | [03 §3.3 §3.4](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Chỉ phát ra **đề bài giải được**. Gate B chặn luật không bao giờ kích hoạt. Gate C chặn luật mà agent không có cách nào phân biệt với một luật đơn giản hơn — bỏ Gate C là chấm oan agent hàng loạt vì một suy luận đúng đắn.

## 2. Đầu vào đã có
`generate` từ L-03, `sample_situations` từ L-04, vòng tick từ W-11.

## 3. Việc phải làm
1. **Chính sách tham chiếu tò mò**: random walk có xác suất thực hiện mỗi hành động châm ngòi.
2. 200 rollout headless — không render, không log, không LLM.
3. Đo `t_first_fire`, `n_fire`, `p_never`, `n_near_miss`.
4. Vòng **tự sửa** trước khi bốc lại: tăng mật độ item, nới `RECENT(k)`, hạ `n` trong `COUNT`.

## 4. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class SolveStats:
    t_first_fire: float; n_fire: float; p_never: float
    n_near_miss: dict[int, float]          # theo chỉ số cond

def measure(law: Law, world_cfg: dict, rollouts: int, rng) -> SolveStats: ...
def gate_b(s: SolveStats, T: int) -> bool: ...
def gate_c(s: SolveStats) -> bool: ...
def repair(law: Law, s: SolveStats, world_cfg: dict) -> tuple[Law, dict] | None: ...
```
Ngưỡng lấy từ `law_config`:

| | Nhận khi |
|---|---|
| `t_first_fire` | ≤ 0.25 · T |
| `n_fire` | ≥ 5 |
| `p_never` | ≤ 5% |
| `n_near_miss` mỗi cond | ≥ 3 |

**Bất biến 1:** chính sách tham chiếu là **random tò mò**, không phải reflex ở W-09. Reflex có thiên lệch (đói mới đi ăn) nên nó ước lượng thấp cho luật liên quan tới ăn và ước lượng cao cho luật liên quan tới đánh. Random tò mò cũng có thiên lệch nhưng **đồng đều**.
**Bất biến 2:** Gate C đo **trên chính 200 rollout đó** — miễn phí, và đảm bảo hai gate nhìn cùng một thực tại.

## 5. Bẫy
- **Tốc độ.** 200 rollout × 400 tick phải chạy **dưới 10 giây**, nếu không LawGen thành nút cổ chai của mọi ván và bạn sẽ bị cám dỗ tắt gate. Không render, không log, không kiểm bất biến. Chậm quá thì hạ 400 → 200 tick và ngoại suy tuyến tính `t_first_fire`; sai số chấp nhận được ở tầng gác cổng.
- **Đừng sửa ở chỗ chấm điểm.** Cám dỗ sẽ là nới điểm cho luật không định danh được. Đừng: hai agent gặp bằng chứng khác nhau sẽ bị chấm bằng hai thước khác nhau và điểm hết so sánh được. Sửa ở **đầu vào** ([03 §3.4](../03-LUAT-AN-V5.md)).

## 6. Nghiệm thu
```bash
python - <<'PY'
import random, time
from genesis.lawgen import generate
t0=time.time()
for i in range(200): generate(i, "STANDARD", {})     # đã bật cả 3 gate
dt=(time.time()-t0)/200
assert dt < 10, f"{dt:.1f}s mỗi bộ luật -> quá chậm"
print(f"OK {dt:.2f}s/bộ")
PY
# luật cố ý không khả giải phải bị chặn
python - <<'PY'
from genesis.lawdsl import *
from genesis.lawgen import measure, gate_b
bad = Law(Trigger(TriggerKind.ADJACENT,"ANY",n=3), (), Effect(EffectKind.HEAL, Mag.SMALL, Dur.LONG))
import random; s = measure(bad, {}, 200, random.Random(0))
assert not gate_b(s, 400), s     # 3 con cạnh nhau trên bản đồ 15 con: quá hiếm
print("GATE B CHẶN ĐÚNG", s)
PY
# luật không định danh được phải bị chặn
python scripts/gate_c_probe.py    # dựng thế giới nơi quả A CHỈ mọc ban đêm, luật có PHASE(NIGHT)
```

## Gate D — luật phải PHÁT BIỂU ĐƯỢC

Song sinh với Gate A. Gate A hỏi *"có nhìn thấy được không"*; Gate D hỏi
*"có nói ra được không"*. Cả hai chặn cùng một kiểu bất công: **một đề bài mà
thí sinh không thể trả lời, dù có suy ra đúng.**

### Lỗ hổng

`_generate_law_for_tier` gọi `random_law(rng)` **không truyền vocab**, tức bốc
từ từ vựng brain 5. Nhưng `vocab_for_brain` cắt từ vựng theo brain:

| brain | trigger | ADJACENT | PHASE_ENTER | max_conds |
|---|---|---|---|---|
| 0–1 | 5 | ✗ | ✗ | 0 |
| 2–3 | 8 | ✗ | ✗ | 1 |
| 4–5 | 11 | ✓ | ✓ | 2 |

Ván seed 55 sinh ra `ADJACENT(OTHER_SP) → POISON`. Nó **nổ 324 lần — nhiều
nhất ván** — và **4/5 loài không có chữ `ADJACENT` trong từ vựng**. Chúng chịu
hệ quả suốt 200 tick và không cách nào ghi nó vào Sổ Luật.

Đếm trên 40 seed STANDARD: **16 seed (40%) không có luật nào brain 0 phát biểu
nổi.** Ba con L5 trong những ván ấy không có mục tiêu nào để nhắm.

### Ràng ở mức BỘ, không ở từng luật

Từ vựng theo brain là **chủ ý** — loài não to nói được nhiều hơn, đó là một
phần phần thưởng cho 4 điểm trait đổ vào brain. Bắt *mọi* luật phải nói được ở
brain 0 sẽ ép cả ván về 5 trigger và 0 điều kiện, tức xoá luôn phần thưởng ấy.

Nên gate ràng ở mức bộ: **ít nhất `LAWSET_MIN_STATABLE = 1` luật** phải phát
biểu được bởi con não nhỏ nhất. Loài não to vẫn có luật riêng nó nói được;
loài não nhỏ luôn có ít nhất một mục tiêu.
`test_gate_d_khong_xoa_phan_thuong_tu_vung_cua_brain` khoá cả hai chiều.

### Ngưỡng suy từ TIER PLAN, không phải hằng số 0

`HARSH` có kế hoạch `D2 D2 D3 D4` — **không tier D1 nào** — mà brain 0–1 có
`max_conds = 0`. Không một luật HARSH nào brain 0 phát biểu nổi, nên đòi brain 0
ở đó là đòi một điều bất khả: `generate` đốt hết 200 lượt thử rồi ném lỗi (đã
xảy ra, 4 bài test đỏ cùng lúc). `gate_d_brain(arm)` lấy tier **dễ nhất** của
nhánh rồi hỏi brain nhỏ nhất còn nói được tier ấy: STANDARD → 0, HARSH → 2.

### LÁI chứ không loại

Cùng lý do như luật ăn quả ở X-03: bốc lại cả bộ cho tới khi tình cờ đủ là quá
hiếm. Thay **luật ở tier dễ nhất của bộ** — không phải luật cuối, vì một luật
D3/D4 mang hai điều kiện thì không bản thay nào của tier ấy nói được ở brain 0
(seed 12 chết đúng vì thế) — rồi để mọi cổng phía dưới xét lại cả bộ.

### Gate D **không** cứu được seed 55

Phải nói thẳng: luật D1 của seed 55 là `DRINK → DAMAGE`, **brain 0 nói được**,
nổ **155 lần**, và hiện ra trong sổ tay sạch sẽ:

```
t99 TÔI uống nước → máu tụt hẳn xuống
t84 TÔI uống nước → máu tụt hẳn xuống
t64 TÔI uống nước → máu tụt hẳn xuống
```

Ba lần trên ba lần. **Không con nào ghi nó vào Sổ Luật.** Gate D bịt một lỗ
thật (40% số ván), nhưng lỗ ấy không phải nguyên nhân của `match = 0` ở đây.
