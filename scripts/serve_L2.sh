#!/usr/bin/env bash
# Dựng llama-server cho L2 (Llama-3.1-8B). Xem docs/tasks/S-02-llama-server.md
#
# BẪY -c: -c là TỔNG KV chia cho MỌI slot, không phải mỗi slot.
#         CTX phải = 3072 * SLOTS. Sai chỗ này KHÔNG báo lỗi — nó biểu hiện
#         thành "model tự dưng quên hết". Xem docs/02-SANDBOX-V4.md §3.
set -euo pipefail

MODEL="${MODEL:-models/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
SLOTS="${SLOTS:-8}"
# 4096, KHÔNG phải 3072. Prompt giữa ván ĐO ĐƯỢC là 2737–2826 token (sổ tay đầy
# + Sổ Luật + lời nghe được), chứ không phải ~800 như lúc sổ tay còn rỗng. Ở
# 3072 mỗi chỗ thì cuối ván bắt đầu tràn, và llama-server trả HTTP lỗi chứ
# không cắt bớt — nên nó hiện ra thành "model im lặng", không thành lỗi ngữ cảnh.
#
# Đo trên máy 34 GB (Qwen-7B q4, Metal), 40 tick, 15 con:
#   4 chỗ × 3072  ->  4 lời gọi,  43% trượt,  0 lần ghi Sổ Luật
#   8 chỗ × 1536  -> 33 lời gọi,  42% trượt,  hàng loạt "exceeds context"
#   8 chỗ × 4096  -> 70 lời gọi,  15% trượt,  4 lần ghi Sổ Luật
PER_SLOT="${PER_SLOT:-4096}"
CTX=$(( PER_SLOT * SLOTS ))
PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"     # 0.0.0.0 chỉ khi đã đọc docs/04-THE-GIOI-MO.md §7.5
NGL="${NGL:-99}"
# llama.cpp b9430 đổi `-fa` thành cờ CÓ GIÁ TRỊ (on|off|auto). Bản cũ `-fa`
# trần giờ nuốt mất tham số kế tiếp và server chết với một trang usage —
# không nói gì về nguyên nhân. Mặc định `auto` chạy đúng ở cả hai đời.
FLASH="${FLASH:--fa auto}"

[ -f "$MODEL" ] || { echo "Không thấy model: $MODEL" >&2; exit 1; }

echo "model=$MODEL slots=$SLOTS per_slot=$PER_SLOT -c=$CTX host=$HOST:$PORT"
exec llama-server -m "$MODEL" -ngl "$NGL" -c "$CTX" -np "$SLOTS" $FLASH \
     --host "$HOST" --port "$PORT"
