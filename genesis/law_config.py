"""Genesis Zero v5 — hằng số tầng luật. config.py của v4 giữ nguyên."""

# ─── Sandbox mở rộng ────────────────────────────────
PHASE_LEN        = 40      # tick mỗi pha ngày/đêm
FRUIT_KINDS      = 4       # FRUIT_A..D
FRUIT_SURFACES   = [("đỏ","tròn"), ("xanh","dài"), ("vàng","gai"), ("tím","dẹt")]
WIND_DIRS        = ["N","E","S","W"]
WATER_DRINKABLE  = True
FIRE_BASE_SPREAD = False   # chỉ lan khi có luật SPREAD

# ─── Lấy mẫu tình huống (L-04) ──────────────────────
N_SITUATIONS = 400
SITUATION_STRATA = {"fires": 0.4, "near_miss": 0.4, "unrelated": 0.2}

# ─── Bốc thăm luật (L-03) ──────────────────────────
LAWS_PER_MATCH   = {"SOLO_LAB": 1, "STANDARD": 3, "HARSH": 4}
TIER_PLAN        = {"SOLO_LAB": ["D1"], "STANDARD": ["D1", "D2", "D3|D4"],
                    "HARSH": ["D2","D2","D3","D4"],
                    # Nhánh cho X-03: cùng kế hoạch tier với STANDARD, nhưng
                    # `generate` bắt buộc phải có ÍT NHẤT một luật `EAT(quả)` có
                    # hệ quả rõ hại hoặc rõ lành. Không có ràng buộc đó thì phép
                    # đo prior không có chỗ bám: đếm thật trên 39 seed STANDARD,
                    # chỉ **3** seed sinh ra một luật ăn quả — 92% số ván không
                    # đo được `prior_leak`, và ta sẽ tưởng là hiệu ứng bằng 0.
                    "PRIOR": ["D1", "D2", "D3|D4"]}
ARMS_REQUIRING_FRUIT_LAW = ("PRIOR",)
MATCH_THETA      = 0.8     # ngưỡng "coi như đã tìm ra" (03 §5.5)
SPEED_FLOOR      = 0.4     # tìm ra muộn vẫn hơn hẳn không tìm ra
EXPLOIT_WINDOW   = 60      # cửa sổ đo exploit_lag, tính bằng tick
EXPLOIT_MIN_N    = 4       # dưới ngưỡng này thì ghi NA, KHÔNG ghi 0
R_WEIGHTS        = {"pred": 0.5, "exploit": 0.3, "social": 0.3, "survive": 0.1}
LAW_WEIGHT       = {"D1": 1.0, "D2": 1.5, "D3": 2.2, "D4": 2.2}
REQUIRE_SOLO_LAW = True
REQUIRE_COOP_LAW = True
LAWGEN_MAX_RETRY = 200

# ─── Gate B & C (L-05) ──────────────────────────────
SOLVE_ROLLOUTS       = 200
SOLVE_TICKS          = 400
SOLVE_MAX_FIRST_FIRE = 0.25   # × ticks
SOLVE_MIN_FIRES      = 5
# Trần kích hoạt, tính trên tỉ lệ con-lượt của một ván thật.
# Một luật kích hoạt gần như MỌI lúc cũng không học được y như luật không bao giờ
# kích hoạt — sổ tay khi đó không có tương phản, mọi dòng cùng một hệ quả, và một
# câu trả lời hằng số ("chuyện đó luôn xảy ra") ăn điểm mà không hiểu gì.
# Đo thật, 24 luật trên 8 seed: trung vị 0,035 con-lượt, chỉ 1 luật vượt 0,30 —
# `KHI bước vào đồng cỏ THÌ dịch chuyển` ở 0,552, vì PLAIN là địa hình áp đảo.
SOLVE_MAX_FIRE_RATE  = 0.25
SOLVE_MAX_P_NEVER    = 0.05
IDENT_MIN_NEAR_MISS  = 3

# ─── Hệ quả mà VÒNG TICK thật sự áp dụng được (L-02) ────────────────
# Bốc luật ngoài danh sách này thì "luật thật" nói một đằng còn thế giới làm một nẻo,
# và agent không có cách nào học được — đề bài thành không giải được, âm thầm.
# Mở rộng danh sách khi hiện thực thêm hệ quả trong genesis/lawhook.py.
IMPLEMENTED_EFFECTS = (
    "DAMAGE", "HEAL", "ENERGY_GAIN", "ENERGY_DRAIN", "POISON", "STUN", "TELEPORT", "SPAWN",
)

# Trigger mà VÒNG TICK thật sự phát ra (L-02). Cùng lý do với IMPLEMENTED_EFFECTS:
# sinh trigger mà sim không phát thì luật không bao giờ kích hoạt và agent không thể học.
# SPEAK chờ B-11 (kênh nói); DEATH_NEAR chờ khi cần.
IMPLEMENTED_TRIGGERS = (
    "EAT", "DRINK", "ATTACK", "HIT_BY", "STEP_ON", "REST", "LOW_ENERGY",
    "ADJACENT", "PHASE_ENTER",
)

# Cond mà SỔ TAY diễn đạt được (B-07). Cùng lý do với hai danh sách trên: một cond
# không có mặt trong ngữ cảnh sổ tay là một cond agent không quan sát được, nên
# luật dùng nó là câu đố không có lời giải — và không có gì báo.
#
# SUBJECT bị loại vì hai lẽ, và nó vốn là cond được sinh NHIỀU NHẤT (3/12 trên 9
# seed): `build_ctx` điền nó từ trait của chính người quan sát và ghim
# `SAME_SP: True`, tức là nó đang mô tả nhầm người; và sổ tay không có chỗ nào nói
# về trait của kẻ khác. Muốn mở lại thì sửa `build_ctx` cho đúng đối tượng và thêm
# một chiều "kẻ đó" vào `ctx_to_pairs` trước đã.
IMPLEMENTED_CONDS = (
    "PHASE", "TERRAIN", "HP", "ENERGY", "RECENT", "COUNT", "AGE", "WIND", "ALONE",
)

# Gate B chạy trên ván THẬT (L-02/L-05), không trên tình huống tổng hợp.
SOLVE_LIVE_TICKS = 200

# ─── B-01 / B-04 / B-08 / B-07 ────────────────────────
CODEX_SIZE_BY_BRAIN   = {0:1, 1:1, 2:2, 3:3, 4:3, 5:4}
EVENTS_BY_BRAIN       = {0:6, 1:8, 2:12, 3:16, 4:20, 5:24}
CLAIM_BUDGET_BY_BRAIN = {0:24, 1:44, 2:64, 3:84, 4:104, 5:124}
CLAIM_COOLDOWN        = 25

# ─── Linh cảm (B-14) ────────────────────────────────────────────────────────
# Nhiều ô hơn Sổ Luật — đó là cả điểm của cơ chế: chỗ để ĐOÁN mà không phải
# TIN. Nhưng vẫn ít, và vẫn theo `brain`: miễn phí thì chiến lược đúng là đăng
# ký hết mọi luật có thể rồi đọc bảng đếm, và `match` sẽ đo tốc độ vét cạn chứ
# không đo năng lực quy nạp.
HUNCH_BY_BRAIN        = {0:2, 1:2, 2:3, 3:4, 4:5, 5:6}
# Riêng, KHÔNG dùng chung `CLAIM_COOLDOWN`. Dùng chung thì nêu một giả thuyết
# cạnh tranh trực tiếp với việc ghi một kết luận, và ta vừa dựng cơ chế này lên
# đúng để hai việc ấy thôi cạnh tranh nhau.
HUNCH_COOLDOWN        = 10
# Sang đời sau, bảng đếm co lại còn bấy nhiêu — KHÔNG bị xoá.
#
# Đây là con số quan trọng nhất của B-14, và nó được chọn bằng phép đo chứ không
# bằng cảm giác. Đo trên seed 55 và 26 (Qwen-7B, 200 tick): mỗi con chết **4,4–4,9
# lần một ván**, tuổi thọ trung bình **35–39 tick**, và tuổi trung vị của con vật
# **lúc nó ghi Sổ Luật là 27 tick**. Nghĩa là model được yêu cầu quy nạp một luật
# qua một lỗ khoá 27 tick, lặp đi lặp lại, không có cách nào cộng dồn.
#
# Xoá sạch bảng đếm khi chết thì linh cảm thừa hưởng đúng cái lỗ khoá ấy và
# không mua được gì. Giữ nguyên thì đời sau ăn không một hiểu biết nó chưa từng
# quan sát. Co lại một nửa giữ được TỈ LỆ (thứ đã học) mà bỏ bớt SỐ LẦN (thứ đã
# tự tay đo) — cùng logic với `CODEX_CONF_DECAY_PER_GEN`.
HUNCH_DECAY_PER_GEN   = 0.5
COST_CLAIM            = 4.0
NOTEPAD_MAX_CHARS     = 200
# Trần số dòng ở khối "NGHE ĐƯỢC". Không chặn thì một loài ồn ào đẩy hết sổ tay
# của kẻ khác ra khỏi context — một đường DoS bằng chính kênh giao tiếp.
HEARD_MAX             = 6
ORACLE_QUERIES        = 8      # B-09: hỏi ở tick T-1, một lần, 8 câu mỗi luật
# Khối B do chủ client viết (docs/03 §8). Trần ký tự là ranh giới tin cậy:
# persona đến từ máy lạ, nên nó bị chặn độ dài VÀ bị soi rò rỉ như mọi khối khác.
PERSONA_MAX_CHARS     = 400


# Số lời gọi model chạy song song khi server không nói `/props.total_slots`.
# 4 = mặc định `-np` của scripts/serve_L2.sh. Đặt cao hơn số chỗ thật thì lời
# gọi xếp hàng trong server và `timeout` của httpx đếm cả thời gian chờ.
LLM_PARALLEL_FALLBACK = 4

# Hạn chờ MỘT ĐỢT lời gọi model, giây. `strategist.think` còn nhân số này với
# số đợt (`ceil(số việc / số chỗ)`), nên đây là hạn cho một đợt đầy.
#
# 45, không phải 20. Đo trên máy 34 GB (Qwen-7B q4, Metal, 8 chỗ × 4096):
#   1 lời gọi           3.5 s
#   8 lời gọi song song 19.9 s   <- một đợt đầy đã sát hạn 20 s cũ
#   15 lời gọi          32.0 s
# Hạn 20 s nghĩa là **một đợt đầy trượt khoảng một nửa**, và trượt ở đây không
# kêu: nó thành "con vật không nghĩ lượt này". Ván seed 55 mất 28% lượt nghĩ vì
# đúng chuyện này, và một ván mất gần một phần ba lượt nghĩ thì không còn đo
# được năng lực quy nạp của model nữa.
LLM_TIMEOUT_S = 45.0

# Gate D: số luật tối thiểu trong một bộ mà con NÃO NHỎ NHẤT phát biểu được.
# 1, không phải "tất cả": bắt mọi luật nói được ở brain 0 sẽ ép cả ván về 5
# trigger và 0 điều kiện, tức xoá luôn phần thưởng từ vựng của brain — mà từ
# vựng rộng hơn chính là thứ brain đổi lấy bằng 4 điểm trait.
LAWSET_MIN_STATABLE = 1
