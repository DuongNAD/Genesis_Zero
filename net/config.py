"""Genesis Zero — net/config.py
MỌI hằng số mạng và giao thức thế giới mở (docs/05-GIAO-THUC.md).
Chỉ hằng số, không logic.
"""

from __future__ import annotations

from pathlib import Path

# ─── Mặc định kết nối & cổng dịch vụ (N-04 / M3) ──────────────────────────
DEFAULT_HOST = "127.0.0.1"
MATCH_PORT = 8000
SPECTATE_PORT = 8000
DEFAULT_PORT = 8000

# ─── Meshy 3D (N-13) ────────────────────────────────────────────────────────
MESHY_URL = "https://api.meshy.ai/v2/text-to-3d"
MESHY_POLL_INTERVAL = 2.0         # giây giữa các lần poll
MESH_CACHE_DIR = Path("data/mesh_cache")
MESH_PER_CLIENT_PER_DAY = 10      # lượt sinh mới tối đa / client / 24h
MESH_GLOBAL_PER_DAY = 100         # lượt sinh mới tối đa toàn cục / 24h

# ─── Hằng số giao thức (05 §7) ──────────────────────────────────────────────
TICK_MS_DEFAULT = 4000            # server tự điều chỉnh trong [3000, 10000]
LATE_TOLERANCE = 2                # tick
HOLD_MS_MAX = 25_000
HEARTBEAT_MS = 10_000
HEARTBEAT_MISS = 3
FERAL_GRACE = 200                 # tick
BODY_MAX_BYTES = 8_192
OPEN_MATCH_TICKS = 200
LAB_MATCH_TICKS = 400

# ─── Vòng đời ván ở chế độ mở (N-04) ────────────────────────────────────────
# Thời lượng các pha KHÔNG chạy bằng tick, mà bằng giây đồng hồ tường: chúng là
# thời gian cho NGƯỜI (đọc bảng kết quả, kịp vào sảnh), không cho sim.
LOBBY_SECONDS = 20.0
SEEDING_SECONDS = 5.0
REVEAL_SECONDS = 25.0
COOLDOWN_SECONDS = 10.0

# Sảnh trống thì tự lấp bằng bot. Ván LUÔN chạy: bắt sảnh chờ đủ người là cách
# nhanh nhất để một dự án cộng đồng chết trong tuần đầu (04 §3).
MIN_SPECIES = 3

# ─── Giới hạn tham gia và sanitize (N-05) ───────────────────────────────────

DISPLAY_NAME_MAX_CHARS = 24
PERSONA_MAX_CHARS = 400


# ─── Nhịp thích ứng (N-08) ──────────────────────────────────────────────────
# Nhịp là của THẾ GIỚI, không của cá thể: khi mạng chậm thì cả ván chậm lại,
# không ai được nới `LATE_TOLERANCE` riêng. Nới riêng cho máy chậm nghĩa là con
# đó được nghĩ lâu hơn con khác — một ưu đãi vô hình không ai giải thích được
# sau này, và nó nằm đúng trong biến số mà thí nghiệm Q1 muốn đo.
TICK_MS_MIN = 3000
TICK_MS_MAX = 10000
TICK_RATE_EVERY = 20        # tick giữa hai lần điều chỉnh
TICK_RATE_UP = 1.15         # p90 vượt dung sai -> chậm lại
TICK_RATE_DOWN = 0.95       # dưới dung sai -> nhanh dần lên
LATENCY_WINDOW = 64         # số mẫu độ trễ gần nhất giữ lại

# ─── Trần chống lạm dụng khi phơi ra internet (N-11, 04 §7.5) ───────────────
JOIN_PER_HOUR = 5                 # lượt join tối đa / IP / giờ
DECISION_PER_MIN = 120
WORK_PER_MIN = 120
DEFAULT_PER_MIN = 240

# Số kết nối long-poll một token được giữ CÙNG LÚC. Không chặn thì một client
# mở hàng trăm `/work` và mỗi cái ngồi 25 giây — kiểu slow-loris, và nó không
# vi phạm trần "lượt/phút" nào cả vì nó chỉ gọi vài lần rồi giữ.
MAX_CONCURRENT_HOLDS = 4

# ─── Đề bài mỗi ván phải KHÁC (N-04) ────────────────────────────────────────
# Số ván gần nhất mà bộ luật mới không được trùng "chủ đề" với. Bằng độ dài vòng
# xoay bản đồ: đi hết một vòng bản đồ rồi mới có thể gặp lại một đề bài, nên
# không ai chơi hai ván liên tiếp cùng một câu hỏi.
LAW_NOVELTY_WINDOW = 5
# Bốc lại tối đa bấy nhiêu lần rồi CHẤP NHẬN trùng. Vòng lặp không giới hạn ở
# đây là server treo im lặng khi không gian luật của một bản đồ hẹp hơn cửa sổ.
LAW_NOVELTY_TRIES = 12

# Vòng xoay bản đồ ở chế độ mở (W-15). Theo `match_no`, không bốc ngẫu nhiên:
# "ván sau là bản đồ nào" nên đoán được, để người chơi biết mình đang chờ gì.
MAP_ROTATION = ("DONG_CO", "RUNG_RAM", "HOANG_MAC", "QUAN_DAO", "HEM_NUI")

__all__ = [
    "BODY_MAX_BYTES",
    "COOLDOWN_SECONDS",
    "DECISION_PER_MIN",
    "DEFAULT_HOST",
    "DEFAULT_PER_MIN",
    "DEFAULT_PORT",
    "DISPLAY_NAME_MAX_CHARS",
    "FERAL_GRACE",
    "HEARTBEAT_MISS",
    "HEARTBEAT_MS",
    "HOLD_MS_MAX",
    "JOIN_PER_HOUR",
    "LAB_MATCH_TICKS",
    "LATENCY_WINDOW",
    "LATE_TOLERANCE",
    "LAW_NOVELTY_TRIES",
    "LAW_NOVELTY_WINDOW",
    "LOBBY_SECONDS",
    "MAP_ROTATION",
    "MATCH_PORT",
    "MAX_CONCURRENT_HOLDS",
    "MESHY_POLL_INTERVAL",
    "MESHY_URL",
    "MESH_CACHE_DIR",
    "MESH_GLOBAL_PER_DAY",
    "MESH_PER_CLIENT_PER_DAY",
    "MIN_SPECIES",
    "OPEN_MATCH_TICKS",
    "PERSONA_MAX_CHARS",
    "REVEAL_SECONDS",
    "SEEDING_SECONDS",
    "SPECTATE_PORT",
    "TICK_MS_DEFAULT",
    "TICK_MS_MAX",
    "TICK_MS_MIN",
    "TICK_RATE_DOWN",
    "TICK_RATE_EVERY",
    "TICK_RATE_UP",
    "WORK_PER_MIN",
]
