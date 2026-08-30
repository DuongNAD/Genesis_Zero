"""
Genesis Zero — config.py
MỌI hằng số nằm ở đây. Không rải rác nơi khác.

Tune W-12 (2026-08-28). Ba điều kiện M1 đạt trên 5 seed × 400 tick.
Đổi so với v4: ENERGY_BASE 60->85, ENERGY_PER_STOMACH 20->8, UPKEEP_STOMACH 0.05->0.25,
PLANT_RESPAWN 4->2, PLANT_MAX 40->15.
Lý do: `stomach` bị định giá quá rẻ (0.05 upkeep cho +20 energy), nên energy_max chênh
60-100 giữa các loài và tỉ lệ chết chênh 3x. Nén dải energy lại và tăng giá stomach thì
độ tản hẹp đi; giảm thức ăn để cung không còn gấp 1.9x cầu.
"""

# ─── Lưới ───────────────────────────────────────────────
GRID_W = 24
GRID_H = 24
TOROIDAL = True   # mép trái nối mép phải, trên nối dưới (v4 §1.4: "24 x 24, toroidal")

# Sinh địa hình: rải hạt rồi cho lan, để ra mảng vá liền khối chứ không phải nhiễu muối tiêu.
# Đã kiểm 5000 seed: mỗi loại địa hình luôn có >= 33 ô trên lưới 24x24.
TERRAIN_SEEDS_PER_TYPE = 4
TERRAIN_WALK_STEPS = 30

# ─── Quần thể ───────────────────────────────────────────
# Tháp sinh thái: apex ít, đáy tháp nhiều. Tổng 15 con.
POPULATION = {
    "L1": 2,   # Apex         — Gemma-2-9B
    "L2": 2,   # Phục kích    — Llama-3.1-8B
    "L3": 3,   # Thích nghi   — Mistral-7B
    "L4": 3,   # Giáp         — Phi-3.5-mini
    "L5": 5,   # Độc          — Qwen2.5-1.5B
}

# ─── Founder vectors (6 trait, tổng luôn = 12, mỗi trait 0–5) ──
FOUNDERS = {
    #             brain  attack  armor  speed  sense  stomach
    "L1":        (4,     3,      1,     2,     1,     1),
    "L2":        (3,     4,      2,     1,     2,     0),
    "L3":        (3,     1,      1,     3,     3,     1),
    "L4":        (1,     1,      5,     1,     2,     2),
    "L5":        (0,     2,      0,     5,     3,     2),
}
TRAIT_NAMES = ("brain", "attack", "armor", "speed", "sense", "stomach")
TRAIT_SUM = 12         # bất biến: tổng 6 trait luôn bằng con số này
TRAIT_MIN = 0
TRAIT_MAX = 5

# ─── Sinh tồn ──────────────────────────────────────────
HP_MAX = 50
HP_REGEN = 1           # +1 hp/tick khi energy > HP_REGEN_ENERGY_RATIO * energy_max
HP_REGEN_ENERGY_RATIO = 0.6

# ─── Công thức dẫn xuất (hệ số) ────────────────────────
# energy_max   = ENERGY_BASE + ENERGY_PER_STOMACH * stomach
ENERGY_BASE = 85
ENERGY_PER_STOMACH = 8

# token_budget = TOKEN_BASE + TOKEN_PER_BRAIN * brain
# Suy nghĩ tốn sức: cost_think = tokens_thuc_sinh / TOKENS_PER_ENERGY (B-05 bất biến 3).
TOKENS_PER_ENERGY = 50
# Đệm để JSON kịp ĐÓNG. Xem `genesis.strategist._budget`.
TOKEN_JSON_HEADROOM = 96
TOKEN_BASE = 32
TOKEN_PER_BRAIN = 36

# think_interval = max(THINK_MIN, THINK_BASE - brain)
THINK_BASE = 7
THINK_MIN = 2

# damage = DAMAGE_BASE + DAMAGE_PER_ATTACK * attack
DAMAGE_BASE = 4
DAMAGE_PER_ATTACK = 3

# dmg_taken_mult = 1 - ARMOR_REDUCTION * armor
ARMOR_REDUCTION = 0.12

# moves_per_tick = 1 + speed // SPEED_DIVISOR
SPEED_DIVISOR = 2

# sight_radius = SIGHT_BASE + sense
SIGHT_BASE = 2

# ─── Chi phí năng lượng ────────────────────────────────
# upkeep mỗi tick (tổ hợp tuyến tính 6 trait):
UPKEEP_BASE = 1.0
UPKEEP_BRAIN = 0.15
UPKEEP_ATTACK = 0.25
UPKEEP_ARMOR = 0.20
UPKEEP_SPEED = 0.30
UPKEEP_SENSE = 0.10
UPKEEP_STOMACH = 0.25

COST_MOVE = 0.5        # mỗi ô di chuyển
COST_ATTACK = 3.0      # mỗi lần tấn công
COST_SPEAK = 2.0       # mỗi lần nói
COST_THINK_DIVISOR = 50 # cost_think = tokens_used / 50

# ─── Thức ăn ───────────────────────────────────────────
PLANT_ENERGY = 30       # năng lượng nhận khi ăn plant
PLANT_RESPAWN = 2       # số plant mọc mỗi tick
PLANT_MAX = 15          # tối đa trên sân

CORPSE_ENERGY = 45      # năng lượng từ xác
CORPSE_DECAY = 15       # xác biến mất sau 15 tick

# ─── Hồi sinh ─────────────────────────────────────────
RESPAWN_DELAY = 20      # tick chờ trước khi hồi sinh
RESPAWN_ENERGY_RATIO = 0.5  # hồi sinh với 50% energy_max

# ─── Thích nghi ───────────────────────────────────────
ADAPT_ON_EAT = 3        # +1 adapt_point mỗi 3 lần ăn
ADAPT_ON_WIN = 1        # +1 adapt_point mỗi trận thắng
ADAPT_ON_SURVIVE = 50   # +1 adapt_point mỗi 50 tick sống liên tục

# ─── Khả năng đặc biệt (cố định theo loài) ────────────
POISON_DAMAGE = 3       # L5: sát thương độc mỗi tick
POISON_DURATION = 5     # L5: độc kéo dài 5 tick
CARRION_PENALTY = 0.5   # loài khác ăn xác thối chỉ nhận 50% energy
# L4 ăn xác thối nhận 100% (không bị penalty)

# ─── Goal theo brain (v4) ─────────────────────────────
# Sinh vật đơn giản có vốn hành vi đơn giản.
# brain thấp → ít goal hơn → giảm LLM_SEMANTIC_FAIL cho model nhỏ.
GOALS_NEEDING_TARGET = ("HUNT", "FOLLOW")
GOALS_BY_BRAIN = {
    # brain 0–1: bản năng thuần tuý
    0: ["FORAGE", "FLEE", "WANDER", "HUNT"],
    1: ["FORAGE", "FLEE", "WANDER", "HUNT"],
    # brain 2–3: biết nghỉ, biết theo đàn
    2: ["FORAGE", "FLEE", "WANDER", "HUNT", "REST", "FOLLOW"],
    3: ["FORAGE", "FLEE", "WANDER", "HUNT", "REST", "FOLLOW"],
    # brain 4–5: biết gác, chiến thuật cao
    4: ["FORAGE", "FLEE", "WANDER", "HUNT", "REST", "FOLLOW", "GUARD"],
    5: ["FORAGE", "FLEE", "WANDER", "HUNT", "REST", "FOLLOW", "GUARD"],
}

# ─── Prompt (v4: 4 khối) ─────────────────────────────
# Khối A: CƠ CHẾ   — server viết, giống hệt cho mọi client   ~180 token
# Khối B: LOÀI     — chủ client viết lúc /join, cap ký tự     ~100 token
# Khối C: CƠ THỂ   — server sinh từ vector trait               ~60 token
# Khối D: TRẠNG THÁI — đổi mỗi lần gọi (user message)
#
# Nguyên tắc: NÓI cơ chế (nhân quả định tính), GIẤU đối thủ (chỉ số loài khác).
# Không đưa công thức số — model sẽ làm toán thay vì hành xử như sinh vật.
PROMPT_PERSONA_MAX_CHARS = 400  # cap cho mô tả loài từ client (khối B)
PROMPT_SAY_MAX_CHARS = 60       # cap tin nhắn say (chống prompt injection)

# ─── Phân tán (M3+) ───────────────────────────────────
SPECIES_ENDPOINTS = {
    "L1": {"url": "http://192.168.1.11:8080", "slots": [0, 1]},
    "L2": {"url": "http://192.168.1.10:8080", "slots": [0, 1]},
    "L3": {"url": "http://192.168.1.10:8081", "slots": [0, 1, 2]},
    "L4": {"url": "http://192.168.1.12:8084", "slots": [0, 1, 2]},
    "L5": {"url": "http://192.168.1.13:8085", "slots": [0, 1, 2, 3, 4]},
}

# ─── Log (chuẩn bị sẵn cho M6) ────────────────────────
LOG_FIELDS_EXTRA = {
    "client_id": None,   # luôn null ở Lab mode
    "model_name": None,  # luôn null ở Lab mode
}

# ─── W-17: chết là truyền lại ────────────────────────────────────────────────
# Bật thì `tick` gọi `lineage.rebirth` thay cho `adapt.reset_body`: đời sau giữ
# vector trait ĐÃ DỊCH của bố mẹ (kèm một điểm đột biến lệch theo nguyên nhân
# chết) thay vì về vector khai sinh.
#
# Tắt được vì phải có nhánh đối chứng. Đo trên seed 55, 200 tick, khi còn tắt:
# 64 lượt chết, 83 lần dịch trait, **63 lần bị xoá (76%)**.
LINEAGE_ENABLED = True

# Mỗi đời, độ tin cậy mọi mục Sổ Luật thừa kế giảm đi ngần này.
# Không có nó thì một cú đoán may truyền qua mười đời trông y hệt một tri thức:
# cháu phải tự kiểm lại thứ ông nó tin.
CODEX_CONF_DECAY_PER_GEN = 1

# Token cho MỘT đáp án oracle. Đo bằng cách in thật một đáp án đầy đủ
# `{"q": 0, "effect": {"kind", "mag", "dur"}}` có xuống dòng và thụt lề: 90 ký
# tự, ~30 token. Nhân `ORACLE_QUERIES` ra ngân sách của cả lượt hỏi.
TOKEN_PER_ORACLE_ANSWER = 42
