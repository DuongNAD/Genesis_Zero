"""Genesis Zero — net/state: một chỗ duy nhất giữ ván đang chạy.

Vì sao file này tồn tại: các route cần `MatchRunner`, và bản đầu lấy nó bằng
`import net.server as server` **ở giữa thân file** — mà `net/server.py` lại
import các route. Vòng import đó chỉ chạy được khi `net.server` tình cờ được nạp
trước; `import net.routes_decision` trực tiếp là `ImportError` ngay. Loại vòng
bằng cách để singleton ở một module mà cả hai phía đều import xuống dưới, chứ
không phải bằng cách sắp xếp thứ tự import cho khéo.

Dùng `state.runner`, đừng `from net.state import runner`: bản `from ... import`
chụp lấy giá trị tại thời điểm import, nên test thay `state.runner` sẽ không có
tác dụng và ta sẽ mất một buổi tìm hiểu vì sao.
"""

from __future__ import annotations

from net.match import MatchRunner

runner: MatchRunner = MatchRunner()


def set_runner(new: MatchRunner) -> MatchRunner:
    """Thay ván đang chạy (test, hoặc khởi động lại tiến trình)."""
    global runner
    runner = new
    return runner
