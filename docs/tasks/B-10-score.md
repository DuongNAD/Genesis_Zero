# B-10 · `score.py` — bảng điểm offline  ✦ CHỐT "ĐO ĐƯỢC"

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-08, B-09, L-06, L-05 · **Chặn** X-01, R-02 |
| **File** | `genesis/score.py` · ~180 dòng · 3 giờ |
| **Giao cho model rẻ?** | ⚠️ đọc JSONL và xuất CSV giao được; **công thức điểm tự viết** |
| **Tài liệu gốc** | [03 §5.5 §9.2](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Biến một ván thành các con số. Đây là mốc chứng minh cả bản v5 có sống được không.

## 2. Chữ ký và bất biến
```python
def score_match(log: Path, truth: Path) -> list[dict]:
    """Một dòng cho mỗi (ván, cá thể, luật)."""
```
Công thức, [03 §5.5](../03-LUAT-AN-V5.md):
```
t_i     = tick sớm nhất có entry match >= θ VÀ entry đó CÒN TRONG SỔ tới cuối ván
speed_i = clip(1 - t_i/T, 0, 1)
R_i     = w_i * match_final * (0.4 + 0.6*speed_i)
R       = ΣR_i + 0.5*R_pred + 0.3*R_exploit + 0.3*R_social + 0.1*R_survive
```
**Bất biến 1 — `score.py` không import `world.py`.** Nó đọc JSONL, chấm, xong. Ranh giới đó là thứ đảm bảo sim không bao giờ chạm được vào bảng chấm.
**Bất biến 2 — "còn tới cuối ván"** giết đoán-mò-rồi-bỏ. Trúng ở tick 30 rồi tick 40 xoá đi thì **không tính**.
**Bất biến 3 — sàn 0.4.** Tìm ra muộn vẫn hơn hẳn không tìm ra; không có sàn thì bạn mất tín hiệu ở phần đuôi, đúng chỗ RL cần nó nhất lúc đầu.
**Bất biến 4 — `exploit_lag` mẫu nhỏ ghi `NA`.** Đòi hỏi `n >= 4` lần xảy ra ở mỗi cửa sổ 60 tick. Đừng ghi 0 và **đừng nới ngưỡng để có số đẹp**.

## 3. Nghiệm thu — ✦ CHỐT "ĐO ĐƯỢC", cả hai điều kiện
```bash
for s in 1 2 3 4 5; do
  python -m genesis.run --seed $s --ticks 400 --arm STANDARD --llm all \
    --out runs/m25-$s.jsonl --truth runs/m25-$s.truth.json
  python -m genesis.score runs/m25-$s.jsonl runs/m25-$s.truth.json >> runs/m25.csv
done
python - <<'PY'
import csv
rows=list(csv.DictReader(open('runs/m25.csv')))
best=max(float(r["match"]) for r in rows)
assert best >= 0.8, f"KHÔNG AI tìm ra luật nào (cao nhất {best:.2f})"
print("ĐO ĐƯỢC: match cao nhất", best)
PY
# nhánh REFLEX PHẢI ra ~0 — nếu không thì có rò rỉ đáp án
for s in 1 2 3 4 5; do python -m genesis.run --seed $s --ticks 400 --controller reflex \
  --out runs/rf-$s.jsonl --truth runs/rf-$s.truth.json; done
python -c "
import csv,glob,subprocess
m=[float(r['match']) for f in glob.glob('runs/rf-*.csv') for r in csv.DictReader(open(f))]
assert max(m) < 0.15, f'REFLEX ăn điểm {max(m):.2f} -> RÒ RỈ ĐÁP ÁN, quay lại B-07'
print('SÀN REFLEX OK')"
```
> Không đạt điều kiện 1? Chẩn đoán **theo thứ tự**: sổ tay nghèo ([B-07](B-07-so-tay.md)) → luật hiếm kích hoạt ([L-05](L-05-gate-bc.md)) → từ vựng quá rộng ([B-02](B-02-prompt.md)).
> **Đừng chẩn đoán bằng cách đổi model.**

## 4. Lần chạy model thật đầu tiên — và lời dặn trên đã trả công

Qwen2.5-1.5B, seed 9, 200 tick: `match = 0.00` trên cả 45 dòng, và **`CODEX_OP = 0`**.
Theo đúng thứ tự trên:

1. **Luật có kích hoạt không?** 371 lần `LAW_FIRED`. Có.
2. **Sổ tay có nghèo không?** Không — đầy đủ chín chiều ngữ cảnh kể từ [B-07](B-07-so-tay.md).
3. Còn lại một chỗ: **`want_codex` bật 0/44 lần.**

Đọc `note` mà chính model tự viết thì thấy: *"nên ghi vào sổ luật nếu bạn đã tìm
ra sự thật đúng sai"*. **Nó biết mình nên ghi, nó chỉ không biết nút ở đâu.**
Khối A2 nói "hãy ghi vào Sổ Luật" nhưng không chỗ nào nói `want_codex` là cánh
cửa duy nhất, và trong schema đó chỉ là một cái tên trơ. Thêm một câu vào khối D
nói thẳng cơ chế: `want_codex` **0/44 → 3/18**, `CODEX_OP` **0 → 2**.

Nếu lúc ấy tôi đổi sang model 7B thì có lẽ nó cũng ghi được vài lần, tôi sẽ kết
luận "model nhỏ quá", và cái nút vẫn khuất ở đó cho mọi model.
