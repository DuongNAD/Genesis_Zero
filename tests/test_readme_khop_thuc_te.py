"""Genesis Zero — README phải nói ĐÚNG SỐ, và bài kiểm này giữ nó khỏi trôi.

## Vì sao có file này

README ghi "554 test" ở hai chỗ trong khi thực tế là 640, và "62 phiếu việc"
trong khi có 65. Không ai nói dối: con số đúng vào ngày viết, rồi kho lớn lên và
không ai quay lại sửa.

Đó là một lỗi nhỏ với một hệ quả không nhỏ. README là thứ đầu tiên người lạ đọc,
và một con số sai ở dòng đầu dạy họ rằng **các con số khác trong kho cũng có thể
sai**. Với một dự án mà toàn bộ giá trị nằm ở chỗ *"những con số ở đây đo được và
kiểm lại được"*, đó là một cái giá đắt cho một phép đếm.

Cách sửa không phải là sửa số rồi hứa sẽ nhớ. Cách sửa là **để cái đếm tự nói khi
nó lệch**.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _so_test_thuc_te() -> int:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    return sum(int(m.group(1))
               for m in re.finditer(r"^tests/.*: (\d+)$", out, re.MULTILINE))


def test_so_test_trong_README_khop_thuc_te():
    """Cho phép lệch một khoảng nhỏ — con số là để định cỡ, không phải để đếm.

    Ngưỡng 5% chứ không phải bằng tuyệt đối: đòi bằng tuyệt đối thì mỗi lần thêm
    một bài kiểm lại phải sửa README, và một bài kiểm buộc người ta sửa tài liệu
    mỗi commit sẽ bị tắt trong tuần đầu.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Bắt HẸP, không bắt rộng. Bản đầu dùng `(\d+)\s*(?:mục|test)` và nó tóm
    # luôn "235 mục Sổ Luật" — một con số về dữ liệu đo được, chẳng liên quan gì
    # tới số bài kiểm. Một bài canh bắt nhầm thì sẽ bị người ta tắt đi, và lúc ấy
    # nó tệ hơn không có.
    ghi = [int(g) for m in
           re.finditer(r"(\d{3,4})\s*mục, xanh|#\s*(\d{3,4})\s*test", readme)
           for g in (m.group(1), m.group(2)) if g]

    assert ghi, "README không còn nêu số test — nếu bỏ hẳn thì xoá luôn bài kiểm này"

    that = _so_test_thuc_te()
    for n in ghi:
        assert abs(n - that) <= max(5, that * 0.05), (
            f"README ghi {n} test, thực tế {that}. Sửa README, đừng sửa ngưỡng.")


def test_so_phieu_viec_trong_README_khop_thuc_te():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    that = len([p for p in (ROOT / "docs" / "tasks").glob("*.md")
                if p.stem != "_MAU"])
    ghi = [int(m.group(1)) for m in re.finditer(r"(\d{2,3})\s*phiếu", readme)]
    for n in ghi:
        assert abs(n - that) <= 3, (
            f"README ghi {n} phiếu việc, thực tế {that}")
