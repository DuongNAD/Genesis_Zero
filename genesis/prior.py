"""Genesis Zero — prior: ba nhánh đo **rò rỉ tri thức có sẵn** (X-03, 03 §10.2).

    prior_leak = t_discover(INVERTED) − t_discover(ALIGNED)

Nếu `prior_leak` lớn thì điểm ở nhánh `ALIGNED` phần lớn là **nhớ bài**, không
phải suy luận — và khi đó `PRIOR_NEUTRAL` mới là nhánh chuẩn để báo cáo Q1.

Ba nhánh có **cùng cấu trúc luật**, khác đúng một thứ: ánh xạ lớp → bề mặt.

| Nhánh | Ánh xạ |
|---|---|
| `PRIOR_ALIGNED`  | quả đỏ độc, quả xanh lành — đúng trực giác |
| `PRIOR_INVERTED` | quả đỏ bổ nhất, quả xanh hại — ngược trực giác |
| `PRIOR_NEUTRAL`  | tên vô nghĩa (`quả zim`, `quả kar`) |

Điểm tinh tế: nhánh `ALIGNED`/`INVERTED` **không thể** chọn ngẫu nhiên rồi hy
vọng. Ánh xạ phải được chọn **theo chính bộ luật của ván đó**: quả nào bị luật
gán hệ quả có hại thì ở `ALIGNED` nó mang bề mặt trông nguy hiểm nhất còn chưa
dùng, ở `INVERTED` thì mang bề mặt trông lành nhất. Bốc ngẫu nhiên thì một nửa
số ván sẽ tự "aligned" và phép đo mất hết độ tương phản.
"""

from __future__ import annotations

import random

from genesis import law_config
from genesis.lawdsl import EffectKind, Law, TriggerKind
from genesis.surface import SurfaceMap

ARMS = ("PRIOR_FREE", "PRIOR_ALIGNED", "PRIOR_INVERTED", "PRIOR_NEUTRAL")

# Thứ tự "trông nguy hiểm" theo trực giác người/model, nguy hiểm nhất trước.
# Đây là một giả định về prior, và nó **phải** được viết ra chỗ nào đó để còn
# tranh luận được — chứ không nằm ẩn trong một phép bốc ngẫu nhiên.
DANGER_ORDER = ("đỏ", "tím", "vàng", "xanh")

# Tên không gợi gì. Không dùng màu, không dùng hình: đó là cả điểm của nhánh này.
NEUTRAL_SURFACES = ("quả zim", "quả kar", "quả vez", "quả nuq")

HARMFUL = frozenset({
    EffectKind.DAMAGE, EffectKind.POISON, EffectKind.ENERGY_DRAIN,
    EffectKind.STUN, EffectKind.BLIND, EffectKind.SPEED_DOWN,
    EffectKind.ARMOR_DOWN,
})
BENIGN = frozenset({
    EffectKind.HEAL, EffectKind.ENERGY_GAIN, EffectKind.SPEED_UP,
    EffectKind.ARMOR_UP,
})


def _default_surfaces() -> list[str]:
    return [f"quả {c} {s}" for c, s in law_config.FRUIT_SURFACES]


def _by_danger(surfaces: list[str]) -> list[str]:
    """Sắp bề mặt theo mức "trông nguy hiểm", nguy hiểm nhất trước."""
    def rank(s: str) -> int:
        for i, colour in enumerate(DANGER_ORDER):
            if colour in s:
                return i
        return len(DANGER_ORDER)
    return sorted(surfaces, key=rank)


def fruit_valence(laws: list[Law]) -> dict[str, str]:
    """lớp quả -> "harm" | "good", theo hệ quả mà luật gán cho việc ĂN nó.

    Chỉ xét trigger `EAT`: đó là chỗ duy nhất mà một *bề mặt* gắn với một *hệ
    quả*, tức chỗ duy nhất prior về màu sắc có thể giúp hoặc hại.
    """
    out: dict[str, str] = {}
    for law in laws:
        t = law.trigger
        if t.kind is not TriggerKind.EAT or not t.arg or not t.arg.startswith("FRUIT_"):
            continue
        if law.effect.kind in HARMFUL:
            out[t.arg] = "harm"
        elif law.effect.kind in BENIGN:
            out.setdefault(t.arg, "good")
    return out


def prior_surface_map(laws: list[Law], arm: str, rng: random.Random) -> SurfaceMap:
    """Ánh xạ lớp → bề mặt cho một nhánh prior."""
    if arm not in ARMS:
        raise ValueError(f"nhánh prior lạ: {arm!r}, phải thuộc {ARMS}")

    classes = [f"FRUIT_{chr(ord('A') + i)}" for i in range(law_config.FRUIT_KINDS)]

    if arm == "PRIOR_NEUTRAL":
        pool = list(NEUTRAL_SURFACES[: len(classes)])
        rng.shuffle(pool)
        return SurfaceMap(cls_to_surface=dict(zip(classes, pool)))

    pool = _default_surfaces()
    if arm == "PRIOR_FREE":
        rng.shuffle(pool)
        return SurfaceMap(cls_to_surface=dict(zip(classes, pool)))

    val = fruit_valence(laws)
    ranked = _by_danger(pool)          # nguy hiểm nhất trước
    if arm == "PRIOR_INVERTED":
        ranked = list(reversed(ranked))

    mapping: dict[str, str] = {}
    # Quả có hệ quả HẠI lấy trước, từ đầu danh sách; quả LÀNH lấy từ cuối.
    harmful = [c for c in classes if val.get(c) == "harm"]
    good = [c for c in classes if val.get(c) == "good"]
    rest = [c for c in classes if c not in harmful and c not in good]

    head, tail = 0, len(ranked) - 1
    for c in harmful:
        mapping[c] = ranked[head]; head += 1
    for c in good:
        mapping[c] = ranked[tail]; tail -= 1
    leftover = ranked[head:tail + 1]
    rng.shuffle(leftover)
    for c, s in zip(rest, leftover):
        mapping[c] = s
    return SurfaceMap(cls_to_surface=mapping)
