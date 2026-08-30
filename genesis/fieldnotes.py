"""Genesis Zero — fieldnotes: Sổ tay sự kiện thực địa cho sinh vật (B-07)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from genesis.lawdsl import EffectKind

_EFFECT_NAMES = [e.value for e in EffectKind]
_FORBIDDEN_PATTERN = re.compile(
    r"\b("
    + "|".join(
        _EFFECT_NAMES
        + [f"FRUIT_{c}" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        + ["law_id"]
    )
    + r")\b|FRUIT_[A-Za-z0-9_]+",
    re.IGNORECASE,
)


def sanitize_outcome(text: str) -> str:
    """Loại bỏ mọi tên EffectKind và FRUIT_[A-D]/FRUIT_* nội bộ khỏi mô tả outcome."""
    if not text:
        return ""
    return _FORBIDDEN_PATTERN.sub("[ẩn]", text)


def _format_ctx(ctx: tuple[tuple[str, str], ...]) -> str:
    items: list[str] = []
    for k, v in ctx:
        k_str = k.strip() if k else ""
        v_str = v.strip() if v else ""
        if k_str and v_str:
            items.append(f"{k_str} {v_str}")
        elif v_str:
            items.append(v_str)
        elif k_str:
            items.append(k_str)
    return f"[{', '.join(items)}]"


@dataclass(frozen=True)
class Note:
    t: int
    who: str            # "TÔI" hoặc "THẤY <creature_id>"
    action: str         # định tính, tiếng Việt
    outcome: str        # định tính; "không thấy gì" nếu không có gì
    ctx: tuple[tuple[str, str], ...]   # LUÔN đầy đủ, ví dụ (("pha","đêm"),("địa hình","đồng cỏ"))

    def __post_init__(self) -> None:
        norm_ctx: list[tuple[str, str]] = []
        if isinstance(self.ctx, dict):
            for k, v in self.ctx.items():
                norm_ctx.append((str(k), str(v)))
        elif isinstance(self.ctx, (list, tuple)):
            for item in self.ctx:
                if isinstance(item, (list, tuple)):
                    if len(item) == 2:
                        norm_ctx.append((str(item[0]), str(item[1])))
                    elif len(item) == 1:
                        norm_ctx.append(("", str(item[0])))
                    elif len(item) == 0:
                        continue
                    else:
                        norm_ctx.append((str(item[0]), str(item[1])))
                elif isinstance(item, str):
                    norm_ctx.append(("", item))
                else:
                    norm_ctx.append(("", str(item)))
        else:
            norm_ctx.append(("", str(self.ctx)))
        object.__setattr__(self, "ctx", tuple(norm_ctx))
        object.__setattr__(self, "outcome", sanitize_outcome(self.outcome))


class FieldNotes:
    def __init__(self, cap: int) -> None:
        self.cap: int = max(1, cap)
        self._items: list[tuple[int, Note]] = []
        self._counter: int = 0

    NORMAL_QUOTA_RATIO = 0.25

    @staticmethod
    def _is_normal(n: Note) -> bool:
        return not n.outcome or n.outcome.strip() == "không thấy gì"

    def record(self, n: Note) -> None:
        self._counter += 1
        self._items.append((self._counter, n))
        if len(self._items) <= self.cap:
            return

        # Bất biến 1 của phiếu B-07: bất thường trước, của mình trước, mới trước.
        # Nhưng nó có mặt trái mà phiếu chưa nói: khi luật kích hoạt liên tục, MỌI
        # dòng đều bất thường và những dòng "không thấy gì" bị đẩy ra hết. Lúc ấy
        # sổ tay chỉ còn ví dụ DƯƠNG. Đọc thật một cuốn như thế (seed 7, 200 tick):
        # 20/20 dòng là "uống nước → nhiễm độc", và từ đó không tài nào phân biệt
        # được "uống nước thì độc" với "uống nước BAN ĐÊM thì độc" — đúng thứ mà
        # cond của luật hỏi. Nên giữ lại một phần tư chỗ cho đối chứng.
        quota = max(1, int(self.cap * self.NORMAL_QUOTA_RATIO))
        normals = [i for i, (_, note) in enumerate(self._items) if self._is_normal(note)]
        pool = range(len(self._items))
        if 0 < len(normals) <= quota:
            abnormals = [i for i in pool if i not in set(normals)]
            if abnormals:
                pool = abnormals
        min_idx = min(pool, key=lambda i: self._priority(self._items[i]))
        self._items.pop(min_idx)

    @staticmethod
    def _priority(item: tuple[int, Note]) -> tuple[int, int, int, int]:
        order, note = item
        is_abnormal = 1 if (note.outcome and note.outcome.strip() != "không thấy gì") else 0
        is_self = 1 if note.who == "TÔI" else 0
        return (is_abnormal, is_self, note.t, order)

    def render(self, k: int) -> str:
        k = max(0, k)
        if not self._items or k == 0:
            return ""
        # Chọn top k theo độ ưu tiên, NHƯNG chừa chỗ cho đối chứng.
        # Cùng lý do như ở `record`: một danh sách toàn ví dụ dương không phân
        # biệt được "uống nước thì độc" với "uống nước ban đêm thì độc".
        by_prio = sorted(self._items, key=self._priority, reverse=True)
        quota = max(1, int(k * self.NORMAL_QUOTA_RATIO))
        normals = [it for it in by_prio if self._is_normal(it[1])][:quota]
        rest = [it for it in by_prio if it not in normals]
        sorted_by_prio = (rest[: max(0, k - len(normals))] + normals)[:k]
        # Sắp xếp k dòng chọn được theo thứ tự thời gian mới nhất trước
        sorted_by_time = sorted(sorted_by_prio, key=lambda item: (item[1].t, item[0]), reverse=True)
        lines = [
            f"t{n.t} {n.who} {n.action} → {n.outcome} {_format_ctx(n.ctx)}"
            for _, n in sorted_by_time
        ]
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()
