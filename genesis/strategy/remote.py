"""Genesis Zero — genesis/strategy/remote.py
Hiện thực chiến lược cho client mạng từ xa (RemoteClientStrategist).
"""

from __future__ import annotations

import collections
import queue
import random
from typing import TYPE_CHECKING, Any

from genesis import speech
from genesis.minds import Minds
from genesis.reflex import ActiveGoal

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.world import World


class RemoteClientStrategist:
    """Đọc quyết định từ hàng đợi do client từ xa gửi về.

    Nếu hàng đợi trống hoặc chưa có quyết định cho sinh vật c, trả None
    để vòng tick tiếp tục bằng phản xạ / giữ goal cũ.
    """

    def __init__(self, queue_dict: dict[str, Any] | None = None) -> None:
        self.queue: dict[str, Any] = queue_dict if queue_dict is not None else {}
        # Trí nhớ và tầng xã hội. `MatchRunner` gán bản của nó đè lên; bản mặc
        # định ở đây chỉ để lớp này đứng một mình được trong test.
        self.minds = Minds()
        # ── ngang bằng với `LlmStrategist` (N-16) ────────────────────────
        # Vòng tick hỏi ba thứ này bằng `getattr`, nên thiếu chúng thì đường
        # mạng **im lặng** chơi một trò khác: không nói được câu nào, và hướng
        # dịch trait rơi về giàn giáo if-else của W-12 thay vì do model của
        # người chơi chọn. Không lỗi, không log, chỉ khác.
        self.pending_say: dict[str, speech.Say] = {}
        self.shift_choice: dict[str, tuple[str, str]] = {}
        self.shift_why: dict[str, str | None] = {}
        self.want_shift: set[str] = set()
        # `creature_id -> adapt_points lúc đã hỏi`. Cùng lý do với bản cục bộ:
        # không có bảng này thì một câu trả lời sai làm con vật hỏi lại **mãi
        # mãi**, và mọi lượt nghĩ của nó từ đó đổ vào một câu hỏi nó liên tục
        # trả lời sai.
        self._shift_asked: dict[str, int] = {}
        # `slots` là cách `genesis.tick` hỏi "con này có model không". Rỗng lúc
        # dựng; `MatchRunner._spawn_registered` điền id của sinh vật do người
        # chơi thật điều khiển. Bot của server KHÔNG có mặt ở đây — chúng không
        # có ai để hỏi hướng dịch, nên chúng phải rơi về W-12.
        self.slots: dict[str, int] = {}

    def take_says(self) -> dict[str, speech.Say]:
        """Lấy VÀ xoá hàng chờ nói. Một câu nói là của MỘT tick."""
        out, self.pending_say = self.pending_say, {}
        return out

    def take_shift(self, c) -> tuple[str, str] | None:
        """Hướng dịch trait do model của người chơi chọn (B-13 ở chế độ mở).

        Giống bản cục bộ từng chữ, và đó là chủ ý: hai bản khác nhau ở đây nghĩa
        là hai chế độ thưởng cho hai chiến lược khác nhau, mà `brain` — thứ
        quyết định dung lượng Sổ Luật — lại chính là trait đáng tranh nhất.
        """
        got = self.shift_choice.pop(c.id, None)
        if got is not None:
            self._shift_asked.pop(c.id, None)
            return got
        if self._shift_asked.get(c.id) == c.adapt_points:
            return None          # đã hỏi ở đúng mức điểm này và hỏng: bỏ lượt
        self._shift_asked[c.id] = c.adapt_points
        self.want_shift.add(c.id)
        return None

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        if c.id not in self.queue:
            return None

        val = self.queue[c.id]
        if isinstance(val, ActiveGoal):
            del self.queue[c.id]
            return val
        if isinstance(val, list):
            if val:
                return val.pop(0)
            return None
        if isinstance(val, collections.deque):
            if val:
                return val.popleft()
            return None
        if isinstance(val, queue.Queue):
            try:
                return val.get_nowait()
            except queue.Empty:
                return None
        if val is not None:
            del self.queue[c.id]
            return val
        return None


__all__ = ["RemoteClientStrategist"]
