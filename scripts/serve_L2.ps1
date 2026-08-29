# Genesis Zero — dựng llama-server trên Windows (PowerShell).
# Bản song sinh của scripts/serve_L2.sh. Xem docs/tasks/S-02-llama-server.md
#
#   .\scripts\serve_L2.ps1
#   .\scripts\serve_L2.ps1 -Slots 16 -Model models\qwen2.5-14b-instruct-q4_k_m.gguf
#
# BẪY -c: -c là TỔNG KV chia cho MỌI slot, không phải mỗi slot.
#         CTX = PerSlot * Slots. Sai chỗ này KHÔNG báo lỗi rõ — llama-server
#         trả HTTP lỗi chứ không cắt bớt, nên nó hiện ra thành "model tự dưng
#         im lặng". Xem docs/02-SANDBOX-V4.md §3.

param(
    [string]$Model   = "models\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
    [int]$Slots      = 8,
    # 4096, KHÔNG phải 3072. Prompt giữa ván ĐO ĐƯỢC là 2737–2826 token (sổ tay
    # đầy + Sổ Luật + lời nghe được), chứ không phải ~800 như lúc sổ tay rỗng.
    [int]$PerSlot    = 4096,
    [int]$Port       = 8080,
    # 0.0.0.0 chỉ khi đã đọc docs/04-THE-GIOI-MO.md §7.5
    [string]$ServerHost = "127.0.0.1",
    [int]$Ngl        = 99,
    # llama.cpp b9430 đổi `-fa` thành cờ CÓ GIÁ TRỊ (on|off|auto). Bản cũ `-fa`
    # trần giờ nuốt mất tham số kế tiếp và server chết với một trang usage.
    [string]$Flash   = "auto"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Model)) {
    Write-Error "Không thấy model: $Model"
    exit 1
}

$Ctx = $PerSlot * $Slots

# Ước lượng VRAM để báo TRƯỚC khi CUDA ném OOM giữa chừng. ~56 KB mỗi token với
# Qwen-7B (28 lớp × 4 đầu KV × 128 × 2 × 2 byte); model 14B tốn ~192 KB/token,
# nên tăng Slots trên model lớn tốn gấp hơn ba lần.
$KvGb = [math]::Round($Ctx * 57344 / 1GB, 2)
Write-Host "slot=$Slots  mỗi slot=$PerSlot token  -c $Ctx  ->  KV ~$KvGb GB (chưa kể model)"

llama-server -m $Model -ngl $Ngl -c $Ctx -np $Slots -fa $Flash --host $ServerHost --port $Port
