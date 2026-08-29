# W-12 · Điểm thích nghi và dịch trait  ✦ CHỐT M1

| | |
|---|---|
| **Track** | World (v4 M1) |
| **Phụ thuộc** | W-11 |
| **Chặn** | W-13, B-01, B-13 |
| **File** | `genesis/creature.py`, `genesis/traits.py` |
| **Ước lượng** | ~45 dòng · 1 giờ + **nhiều giờ tune** |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 12 |

## 1. Mục tiêu
Tiến hoá nhìn thấy được. **Và đây là mốc tune — mốc quan trọng nhất của cả dự án.** Bạn sẽ sửa `config.py` vài chục lần ở đây, và mọi thứ phía sau xây trên nền này.

## 2. Đầu vào đã có
`Traits.shift` từ W-07, vòng tick từ W-11, `config.ADAPT_ON_*`.

## 3. Việc phải làm
1. Cộng `adapt_points`: +1 mỗi 3 lần ăn · +1 mỗi trận thắng · +1 mỗi 50 tick sống liên tục.
2. Đủ 1 điểm → dịch trait. Ở M1 chọn bằng if-else: **dồn vào trait thấp nhất**. LLM chọn ở [B-13](B-13-dich-trait-llm.md).
3. Chết → mất sạch `adapt_points` và mọi điểm đã dịch → về founder vector. **Giữ trí nhớ.**

## 4. Chữ ký và bất biến
```python
def award_adapt(c: Creature, reason: str) -> None: ...
def maybe_shift(c: Creature, rng: random.Random) -> tuple[str,str] | None: ...
def reset_body(c: Creature) -> None:
    """Về founder vector. KHÔNG chạm trí nhớ, KHÔNG chạm Sổ Luật."""
```
**Bất biến:** `reset_body` chỉ chạm cơ thể. Chết mất cơ thể, không mất hiểu biết ([03 §4.4](../03-LUAT-AN-V5.md)). Ở M1 chưa có Sổ Luật, nhưng đặt tên hàm là `reset_body` chứ không phải `reset` để sau này không ai gọi nhầm.

## 5. Bẫy
`think_interval` và `token_budget` đổi khi `brain` dịch → ở v5 nó làm **vỡ prefix cache** ([03 §7.5](../03-LUAT-AN-V5.md)). Ghi log `PREFIX_INVALIDATED` ngay từ đây. Nếu nhiều hơn ~5 lần/ván thì tần suất dịch trait đang quá cao và nó sẽ ăn hết throughput ở M2.

## 6. Nghiệm thu — ✦ CHỐT M1, cả ba điều kiện
```bash
for s in 1 2 3 4 5; do python -m genesis.run --seed $s --ticks 400 --no-render --out runs/m1-$s.jsonl; done
python - <<'PY'
import json, glob, collections
deaths, shifts, seen = collections.Counter(), collections.Counter(), set()
for f in glob.glob('runs/m1-*.jsonl'):
    per = collections.Counter()
    for l in open(f):
        r = json.loads(l); cid = r.get("creature_id")
        if cid: seen.add(cid)
        if r["kind"] == "DEATH":      per[cid] += 1
        if r["kind"] == "TRAIT_SHIFT": shifts[(f,cid)] += 1
    for k,v in per.items(): deaths[k] = max(deaths[k], v)
    for cid in seen:
        assert per[cid] > 0, f"{cid} CHƯA TỪNG CHẾT ở {f} -> thế giới quá dễ"
worst = deaths.most_common(1)[0]
assert worst[1] <= 8, f"{worst} chết quá 8 lần -> damage hoặc upkeep quá gắt"
lo = min(shifts.values())
assert lo >= 2, f"có con chỉ dịch {lo} điểm -> adapt quá chậm"
print("M1 ĐẠT:", "chết nhiều nhất", worst[1], "| dịch ít nhất", lo)
PY
```

> **Đừng đi tiếp khi ba điều kiện chưa đạt.** Không con nào chết quá 8 lần · không con nào chưa từng chết · mỗi con dịch ≥2 điểm. Mọi thứ sau đó xây trên nền này, và tune lại ở tháng thứ ba nghĩa là chạy lại mọi thí nghiệm.
