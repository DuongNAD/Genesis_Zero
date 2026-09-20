"""Genesis Zero — genesis/util/log_cleanup.py
Quản lý, dọn dẹp và luân chuyển log chạy mô phỏng trong runs/ (Feature 19 / Milestone M3).

Tránh tràn đĩa do tích luỹ hàng trăm file {seed}-{timestamp}.jsonl từ các ván thử nghiệm.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

# Nhận diện các file nhật ký ván chạy:
# 1) {seed}-{timestamp}.jsonl (ví dụ: 42-1789709622.jsonl, -1-1789624337.jsonl)
# 2) m_XXXXX.jsonl (ví dụ: m_00001.jsonl)
# 3) {id}.jsonl thông thường
_RUN_LOG_PATTERN = re.compile(r"^(?:-?\d+-\d+|m_\d+|run_[\w\-]+)\.jsonl$")


def is_run_log_file(p: Path) -> bool:
    """Xác định xem một file có phải là file nhật ký ván đấu hay không."""
    if not p.is_file():
        return False
    name = p.name
    if _RUN_LOG_PATTERN.match(name):
        return True
    return bool(name.endswith(".jsonl") and not name.startswith("."))


def prune_run_logs(
    runs_dir: Path | str = "runs",
    keep_last: int = 50,
    max_age_days: float | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Dọn dẹp các file nhật ký ván đấu cũ trong `runs_dir`.

    Tham số:
        runs_dir: Thư mục chứa log (mặc định: 'runs')
        keep_last: Số lượng file log gần nhất được giữ lại (mặc định: 50)
        max_age_days: Tuổi tối đa tính bằng ngày. Nếu đặt, file cũ hơn sẽ bị xoá
                      kể cả khi chưa vượt quá keep_last.
        dry_run: Nếu True, chỉ trả về danh sách file sẽ bị xoá mà không thực sự xoá.

    Trả về:
        Danh sách các `Path` đã bị xoá (hoặc sẽ bị xoá nếu dry_run).
    """
    directory = Path(runs_dir)
    if not directory.is_dir():
        return []

    # Thu thập tất cả các file log ván đấu ở thư mục gốc của runs_dir (không đụng vào thư mục con)
    run_files: list[tuple[float, Path]] = []
    for entry in directory.iterdir():
        if entry.is_file() and is_run_log_file(entry):
            try:
                mtime = entry.stat().st_mtime
                run_files.append((mtime, entry))
            except OSError:
                continue

    if not run_files:
        return []

    # Sắp xếp theo mtime giảm dần (mới nhất đứng đầu)
    run_files.sort(key=lambda item: item[0], reverse=True)

    now = time.time()
    candidates_to_remove: set[Path] = set()

    # 1. Các file vượt quá `keep_last`
    if keep_last >= 0 and len(run_files) > keep_last:
        for _mtime, p in run_files[keep_last:]:
            candidates_to_remove.add(p)

    # 2. Các file vượt quá `max_age_days` (nếu có)
    if max_age_days is not None and max_age_days > 0:
        max_age_sec = max_age_days * 86400.0
        for mtime, p in run_files:
            if (now - mtime) > max_age_sec:
                candidates_to_remove.add(p)

    # 3. Tìm các file truth đi kèm (ví dụ: m_00001.truth.json cho m_00001.jsonl)
    truth_files_to_remove: list[Path] = []
    for jsonl_path in candidates_to_remove:
        stem = jsonl_path.stem
        truth_path = directory / f"{stem}.truth.json"
        if truth_path.is_file():
            truth_files_to_remove.append(truth_path)

    all_to_remove = sorted(candidates_to_remove) + sorted(truth_files_to_remove)
    pruned: list[Path] = []

    for path in all_to_remove:
        if not dry_run:
            try:
                path.unlink(missing_ok=True)
                pruned.append(path)
            except OSError:
                continue
        else:
            pruned.append(path)

    return pruned


__all__ = [
    "is_run_log_file",
    "prune_run_logs",
]
