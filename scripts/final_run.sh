#!/usr/bin/env bash
# Genesis Zero — chạy chuỗi thí nghiệm chốt và in ra phán quyết.
#
#     bash scripts/final_run.sh [MODEL_GGUF] [SEEDS...]
#
# Trả lời đúng một câu hỏi: **có model nào tìm ra được một luật không?**
# Mọi mục còn dở của dự án (B-10 điều kiện 1, X-02 điều kiện 2, X-08, R-03
# kết quả) đều chặn ở đúng câu ấy — xem docs/01-STATUS.md.
set -euo pipefail

MODEL="${1:-models/qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf}"
shift || true
SEEDS=("${@:-55 26 32}")
SEEDS=(${SEEDS[@]})
PORT="${PORT:-8080}"
TICKS="${TICKS:-200}"

# 14B tốn ~192 KB KV mỗi token (48 lớp × 8 đầu KV), gấp 3,4 lần 7B. Với 4096
# token mỗi chỗ thì 8 chỗ = 6,3 GB KV + 9 GB model = 15,3 GB.
SLOTS="${SLOTS:-8}"
PER_SLOT="${PER_SLOT:-4096}"

[ -f "$MODEL" ] || { echo "Không thấy model: $MODEL" >&2; exit 1; }

echo "== dựng server: $SLOTS chỗ × $PER_SLOT token =="
pkill -f "[l]lama-server" 2>/dev/null || true
sleep 2
llama-server -m "$MODEL" -ngl 99 -c $((PER_SLOT * SLOTS)) -np "$SLOTS" \
  -fa auto --host 127.0.0.1 --port "$PORT" > /tmp/genesis-llama.log 2>&1 &
until curl -sf "http://127.0.0.1:$PORT/props" > /dev/null; do sleep 3; done
echo "   server lên: $(curl -s http://127.0.0.1:$PORT/props | python -c 'import json,sys; print(json.load(sys.stdin)["total_slots"], "chỗ")')"

mkdir -p runs
for s in "${SEEDS[@]}"; do
  echo "== seed $s =="
  python -m genesis.run --seed "$s" --ticks "$TICKS" --arm STANDARD --llm all \
    --llm-url "http://127.0.0.1:$PORT" \
    --out "runs/final-$s.jsonl" --truth "runs/final-$s.truth.json" > /dev/null
  python -m genesis.score "runs/final-$s.jsonl" "runs/final-$s.truth.json" \
    > "runs/final-$s.csv"
done

echo
echo "══ PHÁN QUYẾT ══"
python - "${SEEDS[@]}" <<'PY'
import csv, json, sys, collections
best = 0.0; found = 0; rows_all = 0
for s in sys.argv[1:]:
    rows = list(csv.DictReader(open(f"runs/final-{s}.csv")))
    rows_all += len(rows)
    b = max(float(r["match"]) for r in rows)
    f = sum(r["found"] == "True" for r in rows)
    best = max(best, b); found += f
    L = [json.loads(l) for l in open(f"runs/final-{s}.jsonl") if l.strip()]
    ops = [r for r in L if r.get("kind") == "CODEX_OP" and r.get("ok")]
    subj = collections.Counter(o["law"]["trigger"]["kind"] for o in ops if o.get("law"))
    print(f"  seed {s}: match cao nhất {b:.3f} · found {f}/{len(rows)} · "
          f"ghi sổ {len(ops)} · chủ đề {dict(subj.most_common(3))}")
print()
if best >= 0.8:
    print(f"  ✅ ĐO ĐƯỢC — match cao nhất {best:.3f}, {found}/{rows_all} dòng tìm ra luật.")
    print("     B-10 điều kiện 1 ĐẠT. Chạy tiếp X-02 và X-08 để khép nốt.")
elif best > 0:
    print(f"  🟨 CÓ TÍN HIỆU nhưng chưa đạt ngưỡng 0,8 — cao nhất {best:.3f}.")
    print("     Chẩn đoán THEO THỨ TỰ (B-10 §3): sổ tay nghèo -> luật hiếm kích")
    print("     hoạt -> từ vựng quá rộng. ĐỪNG chẩn đoán bằng cách đổi model.")
else:
    print("  ❌ VẪN 0.000. Trước khi đổ lỗi cho model, kiểm bộ chấm:")
    print("     python scripts/fake_model_server.py --port 8099 --cheat-seed 55 &")
    print("     python -m genesis.run --seed 55 --ticks 200 --llm all \\")
    print("       --llm-url http://127.0.0.1:8099 --out runs/cheat.jsonl \\")
    print("       --truth runs/cheat.truth.json")
    print("     Chế độ ấy phải ra match = 1.000. Nếu không, lỗi ở bộ chấm.")
PY
