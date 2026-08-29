"""Genesis Zero — codex: Sổ Luật và cơ chế ghi nhận niềm tin (B-08)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from genesis import law_config
from genesis.lawdsl import Law
from genesis.validate import Verdict

if TYPE_CHECKING:
    from genesis.surface import SurfaceMap


@dataclass
class CodexEntry:
    law: Law
    conf: int
    written_at: int
    source: str          # "self" | creature_id đã dạy


class Codex:
    def __init__(self, size: int) -> None:
        self.size: int = max(0, size)
        self._entries: list[CodexEntry | None] = [None] * self.size
        self.last_claim: int = -law_config.CLAIM_COOLDOWN

    def decay_confidence(self, amount: int) -> int:
        """Giảm `conf` mọi mục; mục rơi xuống <= 0 thì XOÁ. Trả số mục bị xoá.

        Gọi mỗi khi dòng dõi sang đời mới (W-17). Không có bước này thì một cú
        đoán may truyền qua mười đời trông y hệt một tri thức đã kiểm chứng —
        cháu phải tự tin lại thứ ông nó tin, chứ không được thừa kế sự chắc chắn.
        """
        n = 0
        for i, e in enumerate(self._entries):
            if e is None:
                continue
            conf = e.conf - amount
            if conf <= 0:
                self._entries[i] = None
                n += 1
            else:
                self._entries[i] = CodexEntry(
                    law=e.law, conf=conf, written_at=e.written_at, source=e.source
                )
        return n

    def apply(
        self,
        op: str,
        slot: int,
        law: Law | None,
        conf: int,
        tick: int,
        source: str = "self",
    ) -> Verdict:
        """Áp dụng thao tác ghi Sổ Luật (SET, DROP, CONF).

        Bất biến B2: KHÔNG PHẢN HỒI về tính đúng/sai của luật thật trong thế giới.
        Chỉ trả Verdict về tính hợp lệ cú pháp, phạm vi slot và cooldown.
        """
        # B1: Kiểm tra slot trong phạm vi [0, self.size)
        if slot < 0 or slot >= self.size:
            return Verdict(ok=False, reason="CODEX_BAD_SLOT")

        # B2: Cooldown giữa các lần thao tác
        if tick - self.last_claim < law_config.CLAIM_COOLDOWN:
            return Verdict(ok=False, reason="CODEX_COOLDOWN")

        if op == "SET":
            if law is None:
                return Verdict(ok=False, reason="CODEX_MISSING_LAW")
            conf_val = max(1, min(5, int(conf)))
            entry = CodexEntry(
                law=law,
                conf=conf_val,
                written_at=tick,
                source=source,
            )
            self._entries[slot] = entry
            self.last_claim = tick
            return Verdict(ok=True)

        elif op == "DROP":
            self._entries[slot] = None
            self.last_claim = tick
            return Verdict(ok=True)

        elif op == "CONF":
            if self._entries[slot] is None:
                return Verdict(ok=False, reason="CODEX_EMPTY_SLOT")
            conf_val = max(1, min(5, int(conf)))
            self._entries[slot].conf = conf_val
            self.last_claim = tick
            return Verdict(ok=True)

        else:
            return Verdict(ok=False, reason="CODEX_UNKNOWN_OP")

    def entries(self) -> list[CodexEntry | None]:
        """Trả về danh sách các ô trong sổ."""
        return list(self._entries)

    def resize(self, new_size: int) -> None:
        """B4: Khi codex_size giảm (brain tụt) thì KHÔNG cắt sổ đang có.

        Giữ nguyên các ô đang có trong _entries, chỉ cập nhật self.size để chặn ghi thêm.
        Nếu new_size tăng, mở rộng _entries với None.
        """
        new_size = max(0, new_size)
        self.size = new_size
        if new_size > len(self._entries):
            self._entries.extend([None] * (new_size - len(self._entries)))
