"""Genesis Zero — handbook: cẩm nang PHƯƠNG PHÁP, sống qua nhiều ván (W-16).

Có ba tầng trí nhớ trong dự án này, và trộn chúng vào nhau là hỏng cả ba:

| Tầng | Nội dung | Sống bao lâu | Cơ chế |
|---|---|---|---|
| Sổ tay ([B-07]) | *"t382 TÔI ăn quả đỏ → mất máu"* | trong ván | vòng đệm |
| Sổ Luật ([B-08]) | *"KHI ăn quả đỏ THÌ nhiễm độc"* | trong ván | vài ô cố định |
| **Cẩm nang** (file này) | *"thử một thứ một lúc"* | **qua nhiều ván** | file trên đĩa |

**Vì sao cẩm nang KHÔNG được chứa một luật cụ thể nào.** Luật ẩn **đổi mỗi ván**,
và bề mặt bị hoán vị lại mỗi ván ([W-13]). Một câu như *"quả đỏ thì độc"* chép
sang ván sau là **sai**, và tệ hơn — nếu nó tình cờ đúng thì agent ăn điểm mà
không quy nạp gì, và cả phép đo mất nghĩa. Cẩm nang chỉ được chứa **cách làm**:

    ✅  "Đổi một biến một lúc; đổi hai thì không quy được nhân quả."
    ✅  "Màu sắc bị xáo lại mỗi ván — đừng tin trực giác về màu."
    ❌  "Quả đỏ thì độc."                     <- luật cụ thể, ván sau là sai
    ❌  "FRUIT_A gây POISON."                 <- rò tên lớp

`sanitize_lesson` cưỡng chế điều đó: nó **từ chối** mọi câu có bề mặt, tên lớp,
hay tên enum DSL. Không phải khuyên — từ chối.

**Đây là lựa chọn rẻ hơn RL, và nó nên được thử TRƯỚC.** [03 §11.6] đề xuất dựng
dữ liệu SFT hậu nghiệm sau `REVEAL`; cẩm nang là bản không cần huấn luyện của
đúng ý đó — biết đáp án rồi thì viết lại **bài học về cách tìm**, rồi đọc nó ở
ván sau. Nếu cẩm nang đủ để rút ngắn `t_discover` thì [R-03] chỉ còn là tối ưu
hoá, không phải điều kiện cần. Đó là một mệnh đề **đo được**, và
`scripts/x08_handbook.py` đo nó.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from genesis import law_config
from genesis.lawdsl import CondKind, EffectKind, TriggerKind

MAX_LESSONS = 8
MAX_CHARS = 120

_DSL = frozenset(
    [e.value for e in EffectKind] + [t.value for t in TriggerKind]
    + [c.value for c in CondKind]
)
_DSL_RE = re.compile(r"\b(" + "|".join(sorted(_DSL, key=len, reverse=True)) + r")\b")
_CLASS_RE = re.compile(r"FRUIT_[A-Za-z0-9_]*|law_id")
# Mọi bề mặt CÓ THỂ xuất hiện, không chỉ bề mặt của ván này: cẩm nang sống qua
# nhiều ván, nên nó phải sạch với mọi hoán vị bề mặt, không riêng hoán vị hiện tại.
_SURFACES = tuple(f"quả {c} {s}" for c, s in law_config.FRUIT_SURFACES)
_COLOURS = tuple(c for c, _ in law_config.FRUIT_SURFACES)


class LessonRejected(ValueError):
    """Bài học mang nội dung của MỘT ván. Từ chối, không vá âm thầm."""


def sanitize_lesson(text: object) -> str:
    """Trả về bài học đã kiểm, hoặc ném `LessonRejected`.

    Ném chứ không lọc: một câu bị lọc mất nửa nghĩa thì tệ hơn không có câu nào,
    và người viết cần biết mình vừa viết một thứ không được phép.
    """
    s = " ".join(str(text or "").split())
    if not s:
        raise LessonRejected("bài học rỗng")
    if len(s) > MAX_CHARS:
        raise LessonRejected(f"dài {len(s)} ký tự, trần là {MAX_CHARS}")
    m = _CLASS_RE.search(s)
    if m:
        raise LessonRejected(f"chứa định danh nội bộ {m.group(0)!r}")
    m = _DSL_RE.search(s)
    if m:
        raise LessonRejected(f"chứa tên enum DSL {m.group(0)!r} — đó là nội dung một ván")
    for surface in _SURFACES:
        if surface in s:
            raise LessonRejected(f"chứa bề mặt {surface!r} — bề mặt bị xáo lại mỗi ván")
    low = s.lower()
    for colour in _COLOURS:
        if f"quả {colour}" in low:
            raise LessonRejected(f"nói về 'quả {colour}' — màu bị xáo lại mỗi ván")
    return s


@dataclass
class Handbook:
    """Cẩm nang của MỘT loài. Ít dòng, và mỗi dòng phải kiếm được chỗ của nó."""

    species_id: str
    lessons: list[str] = field(default_factory=list)
    n_matches: int = 0

    def add(self, text: object) -> bool:
        """Thêm một bài học. Trả False nếu trùng ý đã có."""
        s = sanitize_lesson(text)
        if any(s.lower() == old.lower() for old in self.lessons):
            return False
        self.lessons.append(s)
        # Đầy thì bỏ dòng CŨ NHẤT: bài học mới đến từ ván gần đây nhất, và một
        # cẩm nang không bao giờ quên là một cẩm nang đóng băng ở ván đầu tiên.
        del self.lessons[:-MAX_LESSONS]
        return True

    def render(self) -> str:
        if not self.lessons:
            return ""
        head = (f"[CẨM NANG] — ngươi đã sống qua {self.n_matches} thế giới. "
                f"Thế giới này có luật KHÁC, nhưng cách tìm thì vẫn thế:")
        return head + "\n" + "\n".join(f"- {x}" for x in self.lessons)

    # ── đĩa ──────────────────────────────────────────────────────────────
    @classmethod
    def load(cls, species_id: str, d: Path) -> "Handbook":
        p = Path(d) / f"{species_id}.json"
        if not p.exists():
            return cls(species_id=species_id)
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls(species_id=species_id)
        hb = cls(species_id=species_id, n_matches=int(raw.get("n_matches", 0)))
        for line in raw.get("lessons", []):
            try:
                hb.add(line)
            except LessonRejected:
                # File cũ có thể mang một dòng bẩn (viết tay, hoặc từ bản trước
                # khi có kiểm). Bỏ dòng đó, giữ phần còn lại — đừng vứt cả cẩm nang.
                continue
        return hb

    def save(self, d: Path) -> Path:
        d = Path(d)
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{self.species_id}.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"species_id": self.species_id, "n_matches": self.n_matches,
             "lessons": self.lessons}, ensure_ascii=False, indent=1,
        ), encoding="utf-8")
        tmp.replace(p)
        return p


# Bốn bài học khởi đầu. Chúng là **phương pháp**, không phải đáp án — và chúng
# nói đúng những thứ mà một model chưa từng chơi sẽ đoán sai.
SEED_LESSONS = (
    "Đổi một thứ một lúc. Đổi hai thì không quy được cái nào gây ra cái nào.",
    "Bề ngoài bị xáo lại mỗi thế giới. Trực giác về màu sắc ở đây là bẫy.",
    "Chuyện không xảy ra cũng là bằng chứng. Hãy nhớ cả những lần không có gì.",
    "Ghi vào Sổ Luật sớm còn hơn chờ chắc: sổ sửa được, thời gian thì không.",
)
