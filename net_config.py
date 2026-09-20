"""Genesis Zero — net_config.py (Backward-compatibility shim for net.config).

Đọc docs/05-GIAO-THUC.md. Toàn bộ cấu hình mạng đã được chuẩn hoá vào `net.config`.
File này giữ lại để đảm bảo tính tương thích ngược 100% cho các script và import cũ.
"""

from __future__ import annotations

import net.config as _config
from net.config import *  # noqa: F403

__all__ = list(_config.__all__)
