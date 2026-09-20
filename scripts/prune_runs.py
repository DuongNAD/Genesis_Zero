#!/usr/bin/env python3
"""Genesis Zero — scripts/prune_runs.py
Công cụ CLI dọn dẹp và luân chuyển nhật ký chạy mô phỏng trong thư mục runs/ (Feature 19 / M3).

Cách dùng:
    python scripts/prune_runs.py --dry-run
    python scripts/prune_runs.py --keep 50
    python scripts/prune_runs.py --max-days 7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from genesis.platform import configure_console_encoding
from genesis.util.log_cleanup import prune_run_logs


def main() -> int:
    configure_console_encoding()
    parser = argparse.ArgumentParser(
        description="Dọn dẹp các file log mô phỏng cũ trong runs/ để chống tràn đĩa."
    )
    parser.add_argument(
        "--runs-dir",
        type=str,
        default=str(ROOT / "runs"),
        help="Đường dẫn thư mục runs (mặc định: runs/)",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=50,
        help="Số lượng file log gần nhất cần giữ lại (mặc định: 50)",
    )
    parser.add_argument(
        "--max-days",
        type=float,
        default=None,
        help="Tuổi tối đa của file log (tính bằng ngày)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ kiểm tra và in danh sách file sẽ xoá mà không thực sự xoá",
    )

    args = parser.parse_args()
    runs_dir = Path(args.runs_dir)

    if not runs_dir.is_dir():
        print(f"[CẢNH] Thư mục '{runs_dir}' không tồn tại.")
        return 0

    mode_str = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode_str}Bắt đầu quét thư mục: {runs_dir}")
    print(f"  - Giữ lại: {args.keep} file gần nhất")
    if args.max_days:
        print(f"  - Giới hạn tuổi: {args.max_days} ngày")

    pruned = prune_run_logs(
        runs_dir=runs_dir,
        keep_last=args.keep,
        max_age_days=args.max_days,
        dry_run=args.dry_run,
    )

    if not pruned:
        print(f"✓ Thư mục {runs_dir.name}/ gọn gàng: 0 file cần dọn dẹp.")
    else:
        action = "Sẽ xoá" if args.dry_run else "Đã xoá"
        print(f"✓ {action} {len(pruned)} file log:")
        for p in pruned[:10]:
            print(f"  - {p.name}")
        if len(pruned) > 10:
            print(f"  ... và {len(pruned) - 10} file khác.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
