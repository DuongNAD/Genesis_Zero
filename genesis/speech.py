"""Genesis Zero — speech: kênh nói và trí nhớ về phản bội (B-11).

Ngôn ngữ, và **cái giá của nó**. Không có trí nhớ về phản bội thì không có tin
tưởng nào sinh ra được — đó là điều kiện cần, không phải tính năng thêm.

Ba ràng buộc của phiếu B-11 §2, cả ba bắt buộc:

1. `text` ≤ 60 ký tự. Không chặn thì chúng viết diễn văn và cháy ngân sách token.
2. Chỉ nghe được trong `sight_radius` của **người nghe**. Chat toàn cục là phối
   hợp tức thì là hết hay. Lấy `sense` của người nghe nghĩa là **`sense` cao =
   nghe lén giỏi** — một cái giá có thật cho một khả năng có thật.
3. Nói tốn energy, và mọi con trong `2 × sight_radius` nghe được **`signal`
   nhưng không nghe `text`**. Con mồi hú cảnh báo đồng loại thì đồng thời chỉ
   điểm vị trí mình. **Im lặng thành một chiến lược.**

Bất biến an ninh: `text` đến từ máy lạ và sẽ được đặt vào prompt của một sinh vật
thứ ba (docs/04 §7.4). Nó phải đi qua `sanitize_text` — cắt dài, bỏ ký tự điều
khiển, **và vô hiệu hoá tên enum DSL**. Chỗ cuối cùng ấy không phải đề phòng thừa:
`genesis.prompt._check_no_leak` **ném** khi thấy tên enum trong khối kể chuyện, nên
một client chỉ cần nói đúng chữ "POISON" là làm gãy ván của người khác.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field
import re
import unicodedata

from genesis import config
from genesis.lawdsl import CondKind, EffectKind, TriggerKind

TEXT_MAX = 60
COST_SPEAK = 2.0
SIGNAL_RANGE_MULT = 2
REPUTATION_MEMORY = 8

SIGNALS = ("ALARM", "AGGR", "SUBM", "NEUTRAL")

_DSL_NAMES = frozenset(
    [e.value for e in EffectKind] + [t.value for t in TriggerKind]
    + [c.value for c in CondKind]
)
_DSL_RE = re.compile(r"\b(" + "|".join(sorted(_DSL_NAMES, key=len, reverse=True)) + r")\b")
_CLASS_RE = re.compile(r"FRUIT_[A-Za-z0-9_]*|law_id")


def sanitize_text(text: object) -> str:
    """Làm sạch lời nói đến từ máy lạ trước khi nó vào prompt của kẻ khác.

    Bốn việc, mỗi việc vá một đường: bỏ ký tự điều khiển (xuống dòng là cách rẻ
    nhất để giả một khối prompt mới); cắt còn `TEXT_MAX`; vô hiệu hoá tên lớp; và
    vô hiệu hoá tên enum DSL. Cái cuối vừa chống rò vừa chống **gãy ván**: bộ
    canh của `genesis.prompt` ném khi thấy tên enum ở khối kể chuyện.
    """
    return _clean(text)[:TEXT_MAX]


def sanitize_free_text(text: object, limit: int) -> str:
    """Như `sanitize_text` nhưng theo trần độ dài của người gọi.

    Dùng cho `note` (ghi chú riêng, trần `NOTEPAD_MAX_CHARS`) — nó cũng do model
    viết và cũng đi vào khối E, nên cũng phải qua đây.
    """
    return _clean(text)[:limit]


def _clean(text: object) -> str:
    s = "" if text is None else str(text)
    s = "".join(ch for ch in s if not unicodedata.category(ch).startswith("C"))
    s = _CLASS_RE.sub("?", s)
    s = _DSL_RE.sub("?", s)
    return s.strip()


@dataclass(frozen=True)
class Say:
    signal: str
    text: str
    teach: int | None = None      # ô Sổ Luật muốn dạy -> B-12

    @staticmethod
    def parse(payload: object) -> "Say | None":
        if not isinstance(payload, dict):
            return None
        signal = payload.get("signal")
        if signal not in SIGNALS:
            signal = "NEUTRAL"
        teach = payload.get("teach")
        teach = teach if isinstance(teach, int) and not isinstance(teach, bool) else None
        return Say(signal=signal, text=sanitize_text(payload.get("text")), teach=teach)


def hearers(speaker, creatures, world) -> tuple[list, list]:
    """Trả (nghe đủ text, chỉ nghe signal).

    Bán kính lấy từ **người nghe**, không phải người nói — cùng khuôn mẫu với
    `world.visible` (W-08). Cùng loài nghe `text`; khác loài chỉ nhận `signal`,
    và tầm signal rộng gấp đôi.
    """
    from genesis.creature import creature_sort_key

    full: list = []
    sig: list = []
    for other in creatures:
        if other is speaker or not other.alive:
            continue
        d = world.dist(speaker.pos, other.pos)
        r = other.traits.sight_radius
        if d <= r and other.species == speaker.species:
            full.append(other)
        elif d <= SIGNAL_RANGE_MULT * r:
            sig.append(other)
    full.sort(key=creature_sort_key)
    sig.sort(key=creature_sort_key)
    return full, sig


_SIGNAL_VN = {
    "ALARM": "tiếng hú báo động",
    "AGGR": "tiếng gầm đe doạ",
    "SUBM": "tiếng rên phục tùng",
    "NEUTRAL": "một tiếng gọi",
}


def render_heard(speaker_id: str, say: Say, full: bool) -> str:
    """Một dòng cho khối "NGHE ĐƯỢC".

    Lời nói được **bọc trong dấu ngoặc kép và gán rõ chủ**, để prompt nói đúng
    bản chất của nó: đây là *lời một sinh vật khác*, không phải chỉ thị. Bỏ lớp
    bọc này là mở lại kênh tiêm lệnh mà toàn bộ tầng DSL sinh ra để đóng.
    """
    if not full or not say.text:
        return f"{speaker_id} phát ra {_SIGNAL_VN.get(say.signal, 'một tiếng gọi')}."
    return f'{speaker_id} phát ra {_SIGNAL_VN.get(say.signal, "một tiếng gọi")} và nói: "{say.text}"'


@dataclass
class Reputation:
    """Trí nhớ về kẻ khác. KHÔNG bị xoá khi chết — chết mất cơ thể, không mất trí nhớ."""

    heard: collections.deque = field(
        default_factory=lambda: collections.deque(maxlen=REPUTATION_MEMORY)
    )
    killed_by: list[str] = field(default_factory=list)

    def record_speech(self, speaker_id: str, signal: str, tick: int) -> None:
        self.heard.append({"speaker": speaker_id, "signal": signal,
                           "goal_next": None, "t": tick})

    def observe_goal(self, speaker_id: str, goal: str, tick: int) -> None:
        """Ghi việc kẻ nói ĐÃ LÀM ở tick sau. Đây là chỗ lời nói gặp hành động."""
        for rec in reversed(self.heard):
            if rec["speaker"] == speaker_id and rec["goal_next"] is None and rec["t"] < tick:
                rec["goal_next"] = goal
                return

    def record_killer(self, killer_id: str) -> None:
        if killer_id not in self.killed_by:
            self.killed_by.append(killer_id)

    def trust(self, speaker_id: str) -> float:
        """0..1. Kêu ALARM rồi đi HUNT là nói một đằng làm một nẻo.

        Chưa có dữ liệu thì trả 0.5 — "chưa biết", không phải "đáng tin".
        """
        if speaker_id in self.killed_by:
            return 0.0
        recs = [r for r in self.heard if r["speaker"] == speaker_id and r["goal_next"]]
        if not recs:
            return 0.5
        ok = sum(1 for r in recs if not _contradicts(r["signal"], r["goal_next"]))
        return round(ok / len(recs), 3)


def _contradicts(signal: str, goal: str) -> bool:
    if signal == "ALARM" and goal in ("HUNT", "GUARD"):
        return True
    if signal == "SUBM" and goal == "HUNT":
        return True
    return False
