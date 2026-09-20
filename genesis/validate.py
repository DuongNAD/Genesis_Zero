"""Genesis Zero — validate: xác thực ngữ nghĩa phía server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from genesis import config, law_config
from genesis.lawdsl import Law
from genesis.world import visible

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.surface import SurfaceMap
    from genesis.world import World


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str | None = None


def validate_decide(
    payload: dict,
    c: Creature,
    world: World,
    seen: list[Creature],
) -> Verdict:
    """Xác thực quyết định định kỳ (kind='decide')."""
    goal = payload.get("goal")
    allowed_goals = config.GOALS_BY_BRAIN.get(c.traits.brain, [])
    if goal not in allowed_goals:
        return Verdict(ok=False, reason="SEMANTIC_GOAL_NOT_ALLOWED_FOR_BRAIN")

    ttl = payload.get("ttl")
    if (
        ttl is None
        or isinstance(ttl, bool)
        or not isinstance(ttl, int)
        or ttl < 2
        or ttl > 12
    ):
        return Verdict(ok=False, reason="SEMANTIC_TTL_RANGE")

    target = payload.get("target")
    if goal in ("HUNT", "FOLLOW") and not target:
        return Verdict(ok=False, reason="SEMANTIC_GOAL_NEEDS_TARGET")

    if target:
        # target tồn tại
        if not any(other.id == target for other in seen):
            return Verdict(ok=False, reason="SEMANTIC_TARGET_NOT_FOUND")

        # target đang nhìn thấy (dùng visible() của W-08)
        vis = visible(c, world, seen)
        if not any(other.id == target for other in vis):
            return Verdict(ok=False, reason="SEMANTIC_TARGET_NOT_VISIBLE")

    return Verdict(ok=True)


# Miền giá trị hợp lệ của `arg` theo từng `kind`. Enum phẳng trong schema chỉ
# chặn được chuỗi BỊA RA; nó không nói được "TERRAIN thì arg phải là địa hình".
# Không chặn nốt ở đây thì `KHI ... VÀ đang đứng trên DAY THÌ ...` vào được sổ,
# chiếm một ô, và `to_vietnamese` render nó thành "đang đứng trên ?".
ARG_DOMAIN: dict[str, tuple[str, ...]] = {
    "TERRAIN": ("PLAIN", "WATER", "BUSH", "ROCK", "FIRE"),
    "STEP_ON": ("PLAIN", "WATER", "BUSH", "ROCK", "FIRE"),
    "PHASE": ("DAY", "NIGHT"),
    "PHASE_ENTER": ("DAY", "NIGHT"),
    "HP": ("LOW", "MID", "HIGH"),
    "ENERGY": ("LOW", "MID", "HIGH"),
    "AGE": ("YOUNG", "OLD"),
    "WIND": ("WITH", "AGAINST"),
    "ATTACK": ("SAME_SP", "OTHER_SP", "ANY"),
    "HIT_BY": ("SAME_SP", "OTHER_SP", "ANY"),
    "ADJACENT": ("SAME_SP", "OTHER_SP", "ANY"),
    "COUNT": ("SAME_SP", "OTHER_SP", "ANY"),
    "SPEAK": ("ALARM", "AGGR", "SUBM", "NEUTRAL"),
    "RECENT": ("EAT", "DRINK", "ATTACK", "HIT_BY", "STEP_ON", "SPEAK", "REST"),

    # ── MIỀN RỖNG = "kind này KHÔNG nhận arg nào cả" ──────────────────────
    # 13 hiệu ứng dưới đây, `lawdsl.random_law` **không bao giờ** đặt `arg`:
    # chúng mang `mag`/`dur`/`r`. Luật thật có `arg=None`, nên một mục sổ ghi
    # `ENERGY_GAIN(DAY)` **không thể khớp** với bất cứ luật nào — nó tiêu một ô
    # sổ để đổi lấy 0 điểm vĩnh viễn.
    #
    # Vì sao phải nêu tường minh: `legal_args` gộp MỌI giá trị hợp lệ vào một
    # enum phẳng để chặn model tự bịa chuỗi (nó từng viết bề mặt bằng tiếng
    # Trung). Cái giá là model được phép rút bất kỳ giá trị nào trong 40 giá trị
    # ấy cho bất kỳ ô nào — và ván seed 55 cho thấy nó làm đúng thế: 5/9 mục sổ
    # được NHẬN là `ARMOR_UP(TERRAIN)`, `HEAL(EAT)`, `ENERGY_GAIN(DAY)`.
    "DAMAGE": (), "HEAL": (), "ENERGY_GAIN": (), "ENERGY_DRAIN": (),
    "POISON": (), "STUN": (), "BLIND": (),
    "SPEED_UP": (), "SPEED_DOWN": (), "ARMOR_UP": (), "ARMOR_DOWN": (),
    "REVEAL": (), "TELEPORT": (),
    "SPREAD": ("FIRE", "WATER", "BUSH"),
    # SPAWN ĐỂ MỞ: nó nhận BỀ MẶT, mà bề mặt đổi mỗi ván —
    # `CODEX_UNKNOWN_SURFACE` bên dưới lo ca đó.

    # Trigger/cond không mang arg. EAT để mở vì cũng nhận bề mặt.
    "DRINK": (), "REST": (), "LOW_ENERGY": (), "DEATH_NEAR": (), "ALONE": (),
    "SUBJECT": ("ARMOR>=3", "SPEED>=3", "BRAIN<=1", "SAME_SP"),
}


def arg_fits_kind(kind: str | None, arg: str | None) -> bool:
    """`arg` có thuộc miền của `kind` không. `EAT`/`SPAWN` để mở vì chúng nhận
    BỀ MẶT, mà bề mặt đổi mỗi ván — `CODEX_UNKNOWN_SURFACE` lo ca đó.

    **Vắng mặt khác rỗng.** `kind` không có trong `ARG_DOMAIN` nghĩa là "chưa nêu
    miền, để mở"; miền **rỗng** nghĩa là "kind này không nhận arg nào". Bản cũ
    viết `arg in domain if domain else True`, và tuple rỗng là falsy, nên hai ca
    ấy sập vào làm một — mọi hiệu ứng đều lọt.
    """
    if not kind or arg is None:
        return True
    domain = ARG_DOMAIN.get(str(kind))
    if domain is None:
        return True
    return arg in domain


def validate_codex(
    payload: dict,
    c: Creature,
    sm: SurfaceMap | None,
    tick: int,
    last_claim: int,
) -> Verdict:
    """Xác thực thao tác sổ luật (kind='codex')."""
    codex_size = law_config.CODEX_SIZE_BY_BRAIN.get(c.traits.brain, 1)
    slot = payload.get("slot")
    if (
        slot is None
        or isinstance(slot, bool)
        or not isinstance(slot, int)
        or slot < 0
        or slot >= codex_size
    ):
        return Verdict(ok=False, reason="CODEX_BAD_SLOT")

    if tick - last_claim < law_config.CLAIM_COOLDOWN:
        return Verdict(ok=False, reason="CODEX_COOLDOWN")

    law = payload.get("law")
    if law is not None:
        if isinstance(law, dict):
            trigger = law.get("trigger", {})
            effect = law.get("effect", {})
            t_kind = trigger.get("kind")
            t_arg = trigger.get("arg")
            e_kind = effect.get("kind")
            e_arg = effect.get("arg")
        elif isinstance(law, Law):
            t_kind = (
                law.trigger.kind.value
                if hasattr(law.trigger.kind, "value")
                else str(law.trigger.kind)
            )
            t_arg = law.trigger.arg
            e_kind = (
                law.effect.kind.value
                if hasattr(law.effect.kind, "value")
                else str(law.effect.kind)
            )
            e_arg = law.effect.arg
        else:
            t_kind = getattr(getattr(law, "trigger", None), "kind", None)
            t_arg = getattr(getattr(law, "trigger", None), "arg", None)
            e_kind = getattr(getattr(law, "effect", None), "kind", None)
            e_arg = getattr(getattr(law, "effect", None), "arg", None)

        if not arg_fits_kind(t_kind, t_arg) or not arg_fits_kind(e_kind, e_arg):
            return Verdict(ok=False, reason="CODEX_ARG_KIND_MISMATCH")
        conds = law.get("conds") if isinstance(law, dict) else getattr(law, "conds", ())
        for c_item in conds or ():
            ck = c_item.get("kind") if isinstance(c_item, dict) else getattr(c_item, "kind", None)
            ca = c_item.get("arg") if isinstance(c_item, dict) else getattr(c_item, "arg", None)
            if not arg_fits_kind(getattr(ck, "value", ck), ca):
                return Verdict(ok=False, reason="CODEX_ARG_KIND_MISMATCH")

        if sm is not None:
            if t_kind == "EAT" and t_arg and t_arg != "CORPSE":
                if sm.class_of(t_arg) is None:
                    return Verdict(ok=False, reason="CODEX_UNKNOWN_SURFACE")
            if e_kind == "SPAWN" and e_arg and e_arg != "CORPSE":
                if sm.class_of(e_arg) is None:
                    return Verdict(ok=False, reason="CODEX_UNKNOWN_SURFACE")

    return Verdict(ok=True)


def validate_hunch(
    payload: dict,
    c: Creature,
    sm: SurfaceMap | None,
    tick: int,
    last_write: int,
) -> Verdict:
    """Xác thực thao tác linh cảm (kind='hunch') — B-14.

    Dùng LẠI `validate_codex` cho phần luật: một linh cảm và một mục Sổ Luật có
    cùng hình dạng, chỉ khác chỗ chứa và khác giá. Viết bản kiểm thứ hai ở đây
    là dựng lại đúng cái mẫu lỗi mà [N-16] vừa dọn xong — hai bản của một khái
    niệm, rồi một bản mục.

    Chỉ hai thứ khác: trần ô lấy từ `HUNCH_BY_BRAIN`, và cooldown là
    `HUNCH_COOLDOWN` (riêng — dùng chung với `CLAIM_COOLDOWN` thì nêu một giả
    thuyết lại cạnh tranh với ghi một kết luận, đúng thứ B-14 dựng lên để gỡ).
    """
    size = law_config.HUNCH_BY_BRAIN.get(c.traits.brain, 1)
    slot = payload.get("slot")
    if (
        slot is None
        or isinstance(slot, bool)
        or not isinstance(slot, int)
        or slot < 0
        or slot >= size
    ):
        return Verdict(ok=False, reason="HUNCH_BAD_SLOT")

    if tick - last_write < law_config.HUNCH_COOLDOWN:
        return Verdict(ok=False, reason="HUNCH_COOLDOWN")

    op = payload.get("op")
    if op not in ("SET", "DROP"):
        return Verdict(ok=False, reason="HUNCH_UNKNOWN_OP")
    # `SET` mà không kèm luật là một lượt nghĩ đổ đi. `HunchBook.apply` cũng bắt
    # ca này, nhưng bắt ở đây thì model nhận đúng mã lỗi thay vì một `ok=True`
    # rồi hỏng ở tầng dưới với một lý do khác.
    if op == "SET" and payload.get("law") is None:
        return Verdict(ok=False, reason="HUNCH_MISSING_LAW")

    # Phần luật: mượn nguyên bộ kiểm của Sổ Luật, rồi đổi tên mã lỗi. Truyền
    # `last_claim` bằng một giá trị đã qua cooldown vì cooldown đã kiểm ở trên,
    # và truyền `slot=0` vì trần ô cũng đã kiểm ở trên.
    borrowed = validate_codex(
        {"law": payload.get("law"), "slot": 0},
        c, sm, tick, tick - law_config.CLAIM_COOLDOWN,
    )
    if not borrowed.ok:
        reason = borrowed.reason.replace("CODEX_", "HUNCH_", 1) if borrowed.reason else None
        return Verdict(ok=False, reason=reason)
    return Verdict(ok=True)


def validate_shift(payload: dict, c: Creature) -> Verdict:
    """Xác thực dịch chuyển trait (kind='shift')."""
    frm = payload.get("from")
    to = payload.get("to")
    if frm not in config.TRAIT_NAMES or to not in config.TRAIT_NAMES:
        return Verdict(ok=False, reason="SEMANTIC_SHIFT_INVALID_TRAIT")
    if getattr(c.traits, frm) <= config.TRAIT_MIN:
        return Verdict(ok=False, reason="SEMANTIC_SHIFT_AT_MIN")
    if getattr(c.traits, to) >= config.TRAIT_MAX:
        return Verdict(ok=False, reason="SEMANTIC_SHIFT_AT_MAX")
    return Verdict(ok=True)
