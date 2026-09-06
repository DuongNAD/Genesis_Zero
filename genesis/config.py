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
    # ─── W-18 chặng B: hai tầng còn lại ────────────────────────────────
    "W1": 3,   # Cá  — tầng NƯỚC
    "A1": 2,   # Chim — tầng TRỜI
}

# Số ô môi trường sống tối thiểu cho MỖI cá thể. Quần thể co lại theo bản đồ:
# `HOANG_MAC` có ~19 ô nước nên nó nuôi được 1 con cá, `QUAN_DAO` có ~165 nên nó
# nuôi đủ. Thả cùng một số lượng lên mọi bản đồ là thả cá vào sa mạc — và M1 sẽ
# vỡ vì một lý do chẳng nói lên điều gì về thiết kế.
#
# Co theo dữ liệu chứ không bằng một bảng chép tay cho từng bản đồ: bảng chép
# tay là thứ sẽ lệch ngay lần đầu ai đó thêm một bản đồ.
CELLS_PER_CREATURE = 12

# ─── Founder vectors (6 trait, tổng luôn = 12, mỗi trait 0–5) ──
FOUNDERS = {
    #             brain  attack  armor  speed  sense  stomach
    "L1":        (4,     3,      1,     2,     1,     1),
    "L2":        (3,     4,      2,     1,     2,     0),
    "L3":        (3,     1,      1,     3,     3,     1),
    "L4":        (1,     1,      5,     1,     2,     2),
    "L5":        (0,     2,      0,     5,     3,     2),
    # Cá: nhanh và thính, gần như không có gì để chống đỡ. Nó sống bằng cách
    # thấy trước và bơi đi — và nước sâu là chỗ không ai theo được.
    "W1":        (1,     1,      0,     5,     4,     1),
    # Chim: thấy xa nhất bản đồ, nhanh, mỏng manh. Nó bay khắp nơi nhưng phải
    # hạ xuống mới chạm được, nên tầm nhìn là thứ nó đổi mọi điểm khác để lấy.
    "A1":        (2,     2,      0,     4,     4,     0),
}
TRAIT_NAMES = ("brain", "attack", "armor", "speed", "sense", "stomach")

# ─── Ba tầng (W-18) ─────────────────────────────────────────────────────────
# Tầng là thuộc tính của LOÀI, không phải một trait: nhét nó vào vector trait
# thì nó hội tụ, đúng lỗi W-12 đã dính một lần. Loài lạ (người chơi qua mạng)
# mặc định CẠN.
SPECIES_DOMAIN: dict[str, str] = {
    "L1": "CAN", "L2": "CAN", "L3": "CAN", "L4": "CAN", "L5": "CAN",
    "W1": "NUOC", "A1": "TROI",
}
# Ngưỡng mở khoá đường đi TRONG tầng cạn. Đây là "sư tử không trèo được cây,
# khỉ thì được" — và nó không hard-code loài nào cả, nó đọc vector trait.
#
# Với FOUNDERS hiện tại, ngưỡng 3 chia đàn đúng làm hai nhóm có thật:
#   trèo được : L5 (speed 5) · L3 (speed 3)
#   không trèo: L1 (2) · L2 (1) · L4 (1)
#   băng lửa  : L4 (armor 5) · chỉ mình nó
# Nên ổ sinh thái xuất hiện NGAY với năm loài sẵn có, không cần thêm loài nào.
# Đêm rút ngắn tầm nhìn bấy nhiêu ô (tối thiểu còn 1). `MAT_DEM` xoá hẳn khoản
# này — đó là toàn bộ giá trị của đặc điểm ấy.
#
# **0 = TẮT, và đó là mặc định.** Cơ chế đã dựng xong nhưng chưa bật, vì nó phá
# M1 và số đo nói rõ mức giá (5 seed × 400 tick, seed 1–5):
#
#   phạt 0 ô -> chết nhiều nhất 8 ✅ · chưa từng chết 0/75 ✅ · dịch min 2 ✅
#   phạt 1 ô -> chết nhiều nhất 8 ✅ · chưa từng chết 2/75 ❌
#   phạt 2 ô -> chết nhiều nhất 9 ❌ · chưa từng chết 3/75 ❌
#
# `plant_scale` KHÔNG cứu được: quét 0,90–1,00 không dịch nổi con số 2/75, vì hai
# con sống sót ấy không chết đói — chúng là cái đuôi cấu trúc mà [01-STATUS] đã
# ghi từ trước, không phải một vấn đề cân bằng thức ăn.
#
# Nên theo đúng kỷ luật đã dùng cho W-18 bất biến 5 và B-14 bất biến 6: cơ chế
# vào thế giới trước, bật lên sau, và có phép đo ở giữa. Bật bằng cách đặt lại
# hằng số này; `MAT_DEM` nằm im cho tới lúc ấy, và điều đó được nói thẳng ở
# `tests/test_features.py` thay vì giấu đi.
NIGHT_SIGHT_PENALTY = 0
CLIMB_SPEED = 3
FIRE_ARMOR = 3
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

# ─── Rong: thức ăn của TẦNG NƯỚC (W-18 §6) ─────────────────────────────────
# Tầng nước hiện không có nguồn thức ăn nào — quả chỉ mọc trên PLAIN, nên một
# con cá thả xuống chết đói dù có bao nhiêu nước. Đây là điều kiện CẦN của chặng
# B, không phải phần tô điểm.
#
# **MỘT lớp duy nhất, không có bề mặt.** Quả có bốn lớp `FRUIT_A..D` và được hoán
# vị bề mặt mỗi ván vì chúng là **đề bài** — luật ẩn nói về chúng. Rong thì không:
# nó là thức ăn, không phải câu đố. Cho nó bốn lớp là làm miền `EAT` rộng gấp
# đôi, mà quy nạp đang hỏng sẵn.
ALGAE_ENERGY = 32
ALGAE_RESPAWN = 2
# BẬT từ chặng B: giờ đã có tầng nước (`W1`) và rong là thứ DUY NHẤT nó ăn
# được. Trước chặng B thì nó tắt, vì lúc ấy nó chỉ cho loài cạn bốc trúng
# `LUONG_CU` thêm một nền kinh tế — hay, nhưng không phải mục đích, và nó vỡ M1:
#
# Giá trị hiện tại đến từ bốn vòng quét trên thế giới BẢY LOÀI (5 seed × 400
# tick), và nó là điểm tốt nhất tìm được:
#
#   rong 10 ô/20 -> chết nhiều nhất 10 ❌ · chưa từng chết  5/100 · cá chết 6,7
#   rong 22 ô/28 -> chết nhiều nhất  8 ✅ · chưa từng chết 10/100 · cá chết 3,7
#   rong 28 ô/30 -> chết nhiều nhất  8 ✅ · chưa từng chết  3/100 · cá chết 4,4
#   rong 32 ô/32 -> chết nhiều nhất  7 ✅ · chưa từng chết  8/100 · dịch min 1 ❌
#
# **CẬP NHẬT sau khi sửa lỗi cá-chui-qua-đá và thêm râu cảm ứng:** M1 tụt tiếp,
# và tôi để nguyên vì cả hai đều là thay đổi ĐÚNG. Điểm hiện tại `36/32`:
#
#   max chết 9 ❌ (L4 và W1) · chưa từng chết 7/100 ❌ · dịch min 1 ❌ (đúng 1 con cá)
#
# Quét thêm `28/30`, `44/34`, và `quả ×0,95` đều không hội tụ. Chẩn đoán theo
# loài cho thấy đây KHÔNG phải một bài toán hai nút thức ăn:
#
#   L4 (giáp 5) vừa có con chết 9 lần vừa có 3 con chưa từng chết — một dựng
#   người feast-or-famine, và không nút thức ăn nào sửa được phương sai trong
#   nội bộ một loài.
#   `dịch min 1` là ĐÚNG MỘT con cá trên 100.
#
# Nên M1 cần một lượt tune riêng cho thế giới bảy loài, đúng như phiếu W-12 đã
# dặn từ đầu ("bạn sẽ sửa vài chục lần"). Đó là việc của người chủ dự án, không
# phải thứ vặn kèm trong một buổi thêm tính năng.
#
# **KHÔNG nới tiêu chí.** Chưa đạt thì ghi là chưa đạt.
# Điều kiện 1 và 3 thì đạt. Ba con ấy là 1 `L5` (cái đuôi lịch sử, đã ghi từ
# trước) và 2 con cá — cá gặp may chứ không bất tử: chúng vẫn chết 14 lần vì
# đánh nhau và 33 lần vì đói trong cùng phép đo.
#
# Một điều đáng nói về chính tiêu chí: "không con nào chưa từng chết" là một
# mệnh đề về ĐUÔI của phân phối, nên nó khó dần theo số cá thể. Thế giới cũ đạt
# 0/75; thế giới mới có 100 suất. Đó không phải cái cớ để nới, nhưng nó là lý do
# nên hỏi lại tiêu chí ấy có còn nói đúng điều nó định nói không.
ALGAE_MAX = 36
ALGAE_CLASS = "ALGAE"

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
#
# 42 → 56 sau khi ĐO LẠI trên ván thật. Trần 432 (= 8 × 42 + 96) đã kéo số dòng
# chấm được từ 15–21/45 lên **56–60/60**, nhưng vẫn còn **4 lượt đứt** ở đúng
# con số ấy trong ba ván. Lý do là thứ chỉ thấy được khi đọc log thật: model
# **không phải lúc nào cũng in gọn** — nó nhả ra hàng chục ký tự tab và xuống
# dòng giữa cây JSON, và khoảng trắng ăn token thật. Đây là lần thứ hai đúng
# nguyên nhân ấy làm đứt một lượt gọi (lần đầu ở `codex`, xem `_budget`).
#
# 56 cho trần 544. Rộng tay là đúng ở đây: một lượt đứt mất TRẮNG cả câu trả
# lời, còn một trần rộng chỉ tốn phần token thật sự sinh ra — `cost_think` tính
# theo token THỰC SINH chứ không theo trần (B-05 bất biến 3).
TOKEN_PER_ORACLE_ANSWER = 56

# ─── Tiến hoá & Sinh sản (M1_EVO) ────────────────────────────
REPRODUCTION_ENABLED = True     # Bật/tắt cơ chế sinh sản và đột biến gen
POPULATION_GLOBAL_MAX = 35      # Trần cá thể sống trên toàn bản đồ
POPULATION_SPECIES_MAX = 7      # Trần cá thể sống cho mỗi loài
REPRODUCE_ENERGY_RATIO = 0.80   # Ngưỡng năng lượng sinh sản (80% energy_max)
REPRODUCE_MIN_AGE = 30          # Tuổi trưởng thành tối thiểu (30 tick)
REPRODUCE_MIN_STREAK = 20       # Chuỗi sống sót tối thiểu (20 tick)
REPRODUCE_COOLDOWN = 25         # Thời gian hồi sau khi sinh (25 tick)
REPRODUCE_COST = 35.0           # Năng lượng trừ vào bố mẹ khi sinh con
CHILD_START_ENERGY = 30.0       # Năng lượng khởi đầu của con non
CROWDING_RADIUS = 2             # Bán kính Chebyshev kiểm tra mật độ địa phương
CROWDING_MAX_NEIGHBORS = 4      # Ngưỡng cá thể lân cận tối đa (>=4 thì dừng sinh)
MUTATE_TRAIT_PROB = 0.40        # Xác suất đột biến trait (zero-sum shift)
MUTATE_FEAT_PROB = 0.15         # Xác suất đột biến 1 đặc điểm sinh học
