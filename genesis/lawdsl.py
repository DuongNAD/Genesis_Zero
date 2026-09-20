"""Genesis Zero v5 — LawDSL: Kiểu dữ liệu, JSON serialization, GBNF grammar, và chuyển ngữ tiếng Việt."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum

from genesis import law_config
from genesis.surface import SurfaceMap

# ─── 1. StrEnum: Từ vựng §2.3 ────────────────────────────────────────────────

class TriggerKind(StrEnum):
    EAT = "EAT"
    DRINK = "DRINK"
    ATTACK = "ATTACK"
    HIT_BY = "HIT_BY"
    STEP_ON = "STEP_ON"
    ADJACENT = "ADJACENT"
    SPEAK = "SPEAK"
    REST = "REST"
    DEATH_NEAR = "DEATH_NEAR"
    PHASE_ENTER = "PHASE_ENTER"
    LOW_ENERGY = "LOW_ENERGY"


class CondKind(StrEnum):
    PHASE = "PHASE"
    TERRAIN = "TERRAIN"
    HP = "HP"
    ENERGY = "ENERGY"
    RECENT = "RECENT"
    COUNT = "COUNT"
    AGE = "AGE"
    WIND = "WIND"
    SUBJECT = "SUBJECT"
    ALONE = "ALONE"


class EffectKind(StrEnum):
    DAMAGE = "DAMAGE"
    HEAL = "HEAL"
    ENERGY_GAIN = "ENERGY_GAIN"
    ENERGY_DRAIN = "ENERGY_DRAIN"
    POISON = "POISON"
    STUN = "STUN"
    BLIND = "BLIND"
    SPEED_UP = "SPEED_UP"
    SPEED_DOWN = "SPEED_DOWN"
    ARMOR_UP = "ARMOR_UP"
    ARMOR_DOWN = "ARMOR_DOWN"
    REVEAL = "REVEAL"
    SPAWN = "SPAWN"
    SPREAD = "SPREAD"
    TELEPORT = "TELEPORT"


class Mag(StrEnum):
    SMALL = "SMALL"
    MED = "MED"
    BIG = "BIG"


class Dur(StrEnum):
    INSTANT = "INSTANT"
    SHORT = "SHORT"
    LONG = "LONG"


# ─── 2. Dataclass: Cấu trúc Luật ─────────────────────────────────────────────

@dataclass(frozen=True)
class Trigger:
    kind: TriggerKind
    arg: str | None = None
    k: int | None = None
    n: int | None = None
    r: int | None = None


@dataclass(frozen=True)
class Cond:
    kind: CondKind
    arg: str | None = None
    k: int | None = None
    op: str | None = None
    n: int | None = None
    r: int | None = None


@dataclass(frozen=True)
class Effect:
    kind: EffectKind
    mag: Mag | None = None
    dur: Dur | None = None
    r: int | None = None
    arg: str | None = None
    dir: str | None = None


@dataclass(frozen=True)
class Law:
    trigger: Trigger
    conds: tuple[Cond, ...]
    effect: Effect

    def __post_init__(self) -> None:
        cond_tuple = tuple(self.conds) if self.conds is not None else ()
        if len(cond_tuple) > 2:
            raise ValueError("Law conds cannot exceed 2")
        # Bất biến B1: Sắp xếp theo (kind.value, arg or "") để AND giao hoán
        sorted_conds = tuple(sorted(cond_tuple, key=lambda c: (c.kind.value, c.arg or "")))
        object.__setattr__(self, "conds", sorted_conds)

    def tier(self) -> str:
        if self.effect.kind in (EffectKind.SPREAD, EffectKind.SPAWN, EffectKind.TELEPORT) or self.trigger.kind == TriggerKind.ADJACENT:
            return "D4"
        if len(self.conds) == 0:
            return "D1"
        if len(self.conds) == 1:
            return "D2"
        if len(self.conds) == 2:
            return "D3"
        return "D4"


# ─── 3. JSON Serialization / Deserialization ─────────────────────────────────

def _trigger_to_dict(t: Trigger) -> dict:
    d: dict = {"kind": t.kind.value}
    if t.arg is not None:
        d["arg"] = t.arg
    if t.k is not None:
        d["k"] = t.k
    if t.n is not None:
        d["n"] = t.n
    if t.r is not None:
        d["r"] = t.r
    return d


def _trigger_from_dict(d: dict) -> Trigger:
    return Trigger(
        kind=TriggerKind(d["kind"]),
        arg=d.get("arg"),
        k=d.get("k"),
        n=d.get("n"),
        r=d.get("r"),
    )


def _cond_to_dict(c: Cond) -> dict:
    d: dict = {"kind": c.kind.value}
    if c.arg is not None:
        d["arg"] = c.arg
    if c.k is not None:
        d["k"] = c.k
    if c.op is not None:
        d["op"] = c.op
    if c.n is not None:
        d["n"] = c.n
    if c.r is not None:
        d["r"] = c.r
    return d


def _cond_from_dict(d: dict) -> Cond:
    return Cond(
        kind=CondKind(d["kind"]),
        arg=d.get("arg"),
        k=d.get("k"),
        op=d.get("op"),
        n=d.get("n"),
        r=d.get("r"),
    )


def _effect_to_dict(e: Effect) -> dict:
    d: dict = {"kind": e.kind.value}
    if e.mag is not None:
        d["mag"] = e.mag.value if isinstance(e.mag, Mag) else str(e.mag)
    if e.dur is not None:
        d["dur"] = e.dur.value if isinstance(e.dur, Dur) else str(e.dur)
    if e.r is not None:
        d["r"] = e.r
    if e.arg is not None:
        d["arg"] = e.arg
    if e.dir is not None:
        d["dir"] = e.dir
    return d


def _effect_from_dict(d: dict) -> Effect:
    mag_raw = d.get("mag")
    dur_raw = d.get("dur")
    return Effect(
        kind=EffectKind(d["kind"]),
        mag=Mag(mag_raw) if mag_raw is not None else None,
        dur=Dur(dur_raw) if dur_raw is not None else None,
        r=d.get("r"),
        arg=d.get("arg"),
        dir=d.get("dir"),
    )


def to_json(law: Law) -> dict:
    return {
        "trigger": _trigger_to_dict(law.trigger),
        "conds": [_cond_to_dict(c) for c in law.conds],
        "effect": _effect_to_dict(law.effect),
    }


def from_json(d: dict) -> Law:
    trigger = _trigger_from_dict(d["trigger"])
    conds = tuple(_cond_from_dict(c) for c in d.get("conds", []))
    effect = _effect_from_dict(d["effect"])
    return Law(trigger=trigger, conds=conds, effect=effect)


# ─── 4. Vocab theo Brain §8 ──────────────────────────────────────────────────

@dataclass(frozen=True)
class Vocab:
    triggers: tuple[TriggerKind, ...]
    conds: tuple[CondKind, ...]
    effects: tuple[EffectKind, ...]
    max_conds: int


_BRAIN_0_1_TRIGGERS = (
    TriggerKind.EAT,
    TriggerKind.DRINK,
    TriggerKind.ATTACK,
    TriggerKind.HIT_BY,
    TriggerKind.STEP_ON,
)

_BRAIN_0_1_EFFECTS = (
    EffectKind.DAMAGE,
    EffectKind.HEAL,
    EffectKind.ENERGY_GAIN,
    EffectKind.ENERGY_DRAIN,
    EffectKind.POISON,
    EffectKind.STUN,
)

_BRAIN_2_3_TRIGGERS = (
    TriggerKind.EAT,
    TriggerKind.DRINK,
    TriggerKind.ATTACK,
    TriggerKind.HIT_BY,
    TriggerKind.STEP_ON,
    TriggerKind.SPEAK,
    TriggerKind.REST,
    TriggerKind.LOW_ENERGY,
)

_BRAIN_2_3_CONDS = (
    CondKind.PHASE,
    CondKind.TERRAIN,
    CondKind.HP,
    CondKind.ENERGY,
    CondKind.RECENT,
)

_BRAIN_2_3_EFFECTS = (
    EffectKind.DAMAGE,
    EffectKind.HEAL,
    EffectKind.ENERGY_GAIN,
    EffectKind.ENERGY_DRAIN,
    EffectKind.POISON,
    EffectKind.STUN,
    EffectKind.BLIND,
    EffectKind.SPEED_UP,
    EffectKind.SPEED_DOWN,
)


def vocab_for_brain(brain: int) -> Vocab:
    if brain <= 1:
        return Vocab(
            triggers=_BRAIN_0_1_TRIGGERS,
            conds=(),
            effects=_BRAIN_0_1_EFFECTS,
            max_conds=0,
        )
    if brain <= 3:
        return Vocab(
            triggers=_BRAIN_2_3_TRIGGERS,
            conds=_BRAIN_2_3_CONDS,
            effects=_BRAIN_2_3_EFFECTS,
            max_conds=1,
        )
    return Vocab(
        triggers=tuple(TriggerKind),
        # Lọc bằng IMPLEMENTED_CONDS ở ĐÂY, một chỗ duy nhất, để bộ sinh luật,
        # JSON schema và khối D của prompt không bao giờ nói ba thứ khác nhau.
        conds=tuple(c for c in CondKind if c.value in law_config.IMPLEMENTED_CONDS),
        effects=tuple(EffectKind),
        max_conds=2,
    )


# ─── 5. random_law ───────────────────────────────────────────────────────────

# Trường mà MỖI hệ quả thật sự mang. `random_law` ở dưới sinh đúng theo bảng
# này; `strategist._effect_schema` đọc đúng bảng này để BẮT BUỘC model nêu chúng.
#
# Vì sao phải bắt buộc: `verify.agree` nhân điểm trên từng chiều mà luật THẬT có
# định nghĩa, và thiếu một chiều thì chiều ấy ăn **0**, kéo cả tích về 0. Nên
# một luật đúng trigger, đúng điều kiện, đúng loại hệ quả, mà quên `dur` thì
# vẫn ăn đúng 0 điểm.
#
# Đo trên toàn bộ mục Sổ Luật ghi trong ngày: **235 mục, chỉ 23% nêu cả `mag`
# lẫn `dur`**. Tức 77% dữ liệu thu được **không thể ăn điểm về mặt cấu trúc** —
# kể cả mục `WHEN DRINK THEN DAMAGE` của Qwen-14B, đúng nguyên văn luật thật.
EFFECT_FIELDS: dict[str, tuple[str, ...]] = {
    "DAMAGE": ("mag", "dur"), "HEAL": ("mag", "dur"),
    "ENERGY_GAIN": ("mag", "dur"), "ENERGY_DRAIN": ("mag", "dur"),
    "POISON": ("mag", "dur"),
    "SPEED_UP": ("mag", "dur"), "SPEED_DOWN": ("mag", "dur"),
    "ARMOR_UP": ("mag", "dur"), "ARMOR_DOWN": ("mag", "dur"),
    "STUN": ("dur",), "BLIND": ("dur",),
    "REVEAL": ("r", "dur"),
    "TELEPORT": ("r",),
    "SPAWN": ("arg", "r"),
    "SPREAD": ("arg",),
}


def random_law(rng: random.Random, vocab: Vocab | None = None) -> Law:
    if vocab is None:
        vocab = vocab_for_brain(5)

    # 1. Trigger
    t_kind = rng.choice(vocab.triggers)
    if t_kind == TriggerKind.EAT:
        t = Trigger(kind=t_kind, arg=rng.choice(["FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D", "CORPSE"]))
    elif t_kind in (TriggerKind.ATTACK, TriggerKind.HIT_BY):
        t = Trigger(kind=t_kind, arg=rng.choice(["SAME_SP", "OTHER_SP", "ANY"]))
    elif t_kind == TriggerKind.STEP_ON:
        t = Trigger(kind=t_kind, arg=rng.choice(["PLAIN", "WATER", "BUSH", "ROCK", "FIRE"]))
    elif t_kind == TriggerKind.ADJACENT:
        t = Trigger(kind=t_kind, arg=rng.choice(["SAME_SP", "OTHER_SP", "ANY"]), n=rng.choice([1, 2, 3]))
    elif t_kind == TriggerKind.SPEAK:
        t = Trigger(kind=t_kind, arg=rng.choice(["ALARM", "AGGR", "SUBM", "NEUTRAL"]))
    elif t_kind == TriggerKind.REST:
        t = Trigger(kind=t_kind, k=rng.choice([2, 3, 4, 5]))
    elif t_kind == TriggerKind.DEATH_NEAR:
        t = Trigger(kind=t_kind, r=rng.choice([1, 2, 3]))
    elif t_kind == TriggerKind.PHASE_ENTER:
        t = Trigger(kind=t_kind, arg=rng.choice(["DAY", "NIGHT"]))
    else:  # DRINK, LOW_ENERGY
        t = Trigger(kind=t_kind)

    # 2. Conds
    conds: list[Cond] = []
    if vocab.max_conds > 0 and len(vocab.conds) > 0:
        n_conds = rng.randint(0, min(vocab.max_conds, len(vocab.conds)))
        if n_conds > 0:
            selected_kinds = rng.sample(list(vocab.conds), n_conds)
            for c_kind in selected_kinds:
                if c_kind == CondKind.PHASE:
                    c = Cond(kind=c_kind, arg=rng.choice(["DAY", "NIGHT"]))
                elif c_kind == CondKind.TERRAIN:
                    c = Cond(kind=c_kind, arg=rng.choice(["PLAIN", "WATER", "BUSH", "ROCK", "FIRE"]))
                elif c_kind in (CondKind.HP, CondKind.ENERGY):
                    c = Cond(kind=c_kind, arg=rng.choice(["LOW", "MID", "HIGH"]))
                elif c_kind == CondKind.RECENT:
                    c = Cond(kind=c_kind, arg=rng.choice(["DRINK", "EAT", "ATTACK", "HIT_BY", "STEP_ON", "SPEAK", "REST"]), k=rng.randint(3, 15))
                elif c_kind == CondKind.COUNT:
                    c = Cond(kind=c_kind, arg=rng.choice(["SAME_SP", "OTHER_SP", "ANY"]), r=rng.choice([1, 2, 3]), op=rng.choice([">=", "<="]), n=rng.choice([1, 2, 3]))
                elif c_kind == CondKind.AGE:
                    c = Cond(kind=c_kind, arg=rng.choice(["YOUNG", "OLD"]))
                elif c_kind == CondKind.WIND:
                    c = Cond(kind=c_kind, arg=rng.choice(["WITH", "AGAINST"]))
                elif c_kind == CondKind.SUBJECT:
                    c = Cond(kind=c_kind, arg=rng.choice(["ARMOR>=3", "SPEED>=3", "BRAIN<=1", "SAME_SP"]))
                elif c_kind == CondKind.ALONE:
                    c = Cond(kind=c_kind, r=2)
                else:
                    c = Cond(kind=c_kind)
                conds.append(c)

    # 3. Effect
    e_kind = rng.choice(vocab.effects)
    if e_kind in (
        EffectKind.DAMAGE, EffectKind.HEAL, EffectKind.ENERGY_GAIN, EffectKind.ENERGY_DRAIN,
        EffectKind.POISON, EffectKind.SPEED_UP, EffectKind.SPEED_DOWN, EffectKind.ARMOR_UP, EffectKind.ARMOR_DOWN
    ):
        e = Effect(kind=e_kind, mag=rng.choice(list(Mag)), dur=rng.choice(list(Dur)))
    elif e_kind in (EffectKind.STUN, EffectKind.BLIND):
        e = Effect(kind=e_kind, dur=rng.choice(list(Dur)))
    elif e_kind == EffectKind.REVEAL:
        e = Effect(kind=e_kind, r=rng.choice([1, 2, 3]), dur=rng.choice(list(Dur)))
    elif e_kind == EffectKind.SPAWN:
        e = Effect(kind=e_kind, arg=rng.choice(["FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D", "CORPSE"]), r=rng.choice([1, 2, 3]))
    elif e_kind == EffectKind.SPREAD:
        e = Effect(kind=e_kind, arg=rng.choice(["FIRE", "WATER", "BUSH"]))
    elif e_kind == EffectKind.TELEPORT:
        e = Effect(kind=e_kind, r=rng.choice([1, 2, 3]))
    else:
        e = Effect(kind=e_kind)

    return Law(trigger=t, conds=tuple(conds), effect=e)


# ─── 6. to_gbnf ──────────────────────────────────────────────────────────────

def to_gbnf(vocab: Vocab) -> str:
    lines: list[str] = [
        'root ::= law',
        'law ::= "{" ws "\\"trigger\\"" ws ":" ws trigger ws "," ws "\\"conds\\"" ws ":" ws conds ws "," ws "\\"effect\\"" ws ":" ws effect ws "}"',
        'ws ::= [ \\t\\n\\r]*',
    ]

    # Trigger choices
    trig_rule_names = ["trigger_" + tk.value.lower() for tk in vocab.triggers]
    lines.append("trigger ::= " + " | ".join(trig_rule_names))

    for tk in vocab.triggers:
        rule_name = "trigger_" + tk.value.lower()
        if tk == TriggerKind.EAT:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"EAT\\"" ws "," ws "\\"arg\\"" ws ":" ws fruit_or_corpse ws "}"'
        elif tk == TriggerKind.DRINK:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"DRINK\\"" ws "}"'
        elif tk in (TriggerKind.ATTACK, TriggerKind.HIT_BY):
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + tk.value + '\\"" ws "," ws "\\"arg\\"" ws ":" ws sp_target ws "}"'
        elif tk == TriggerKind.STEP_ON:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"STEP_ON\\"" ws "," ws "\\"arg\\"" ws ":" ws terrain_type ws "}"'
        elif tk == TriggerKind.ADJACENT:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"ADJACENT\\"" ws "," ws "\\"arg\\"" ws ":" ws sp_target ws "," ws "\\"n\\"" ws ":" ws int_1_3 ws "}"'
        elif tk == TriggerKind.SPEAK:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"SPEAK\\"" ws "," ws "\\"arg\\"" ws ":" ws signal_type ws "}"'
        elif tk == TriggerKind.REST:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"REST\\"" ws "," ws "\\"k\\"" ws ":" ws int_2_5 ws "}"'
        elif tk == TriggerKind.DEATH_NEAR:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"DEATH_NEAR\\"" ws "," ws "\\"r\\"" ws ":" ws int_1_3 ws "}"'
        elif tk == TriggerKind.PHASE_ENTER:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"PHASE_ENTER\\"" ws "," ws "\\"arg\\"" ws ":" ws phase_type ws "}"'
        elif tk == TriggerKind.LOW_ENERGY:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"LOW_ENERGY\\"" ws "}"'
        else:
            body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + tk.value + '\\"" ws "}"'
        lines.append(rule_name + " ::= " + body)

    # Conds
    if vocab.max_conds == 0 or len(vocab.conds) == 0:
        lines.append('conds ::= "[" ws "]"')
    else:
        cond_rule_names = ["cond_" + ck.value.lower() for ck in vocab.conds]
        lines.append("cond ::= " + " | ".join(cond_rule_names))
        for ck in vocab.conds:
            c_rule = "cond_" + ck.value.lower()
            if ck == CondKind.PHASE:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"PHASE\\"" ws "," ws "\\"arg\\"" ws ":" ws phase_type ws "}"'
            elif ck == CondKind.TERRAIN:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"TERRAIN\\"" ws "," ws "\\"arg\\"" ws ":" ws terrain_type ws "}"'
            elif ck in (CondKind.HP, CondKind.ENERGY):
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + ck.value + '\\"" ws "," ws "\\"arg\\"" ws ":" ws level_type ws "}"'
            elif ck == CondKind.RECENT:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"RECENT\\"" ws "," ws "\\"arg\\"" ws ":" ws recent_action ws "," ws "\\"k\\"" ws ":" ws int_3_15 ws "}"'
            elif ck == CondKind.COUNT:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"COUNT\\"" ws "," ws "\\"arg\\"" ws ":" ws sp_target ws "," ws "\\"r\\"" ws ":" ws int_1_3 ws "," ws "\\"op\\"" ws ":" ws op_cmp ws "," ws "\\"n\\"" ws ":" ws int_1_3 ws "}"'
            elif ck == CondKind.AGE:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"AGE\\"" ws "," ws "\\"arg\\"" ws ":" ws age_type ws "}"'
            elif ck == CondKind.WIND:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"WIND\\"" ws "," ws "\\"arg\\"" ws ":" ws wind_type ws "}"'
            elif ck == CondKind.SUBJECT:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"SUBJECT\\"" ws "," ws "\\"arg\\"" ws ":" ws subject_type ws "}"'
            elif ck == CondKind.ALONE:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"ALONE\\"" ws "," ws "\\"r\\"" ws ":" ws "2" ws "}"'
            else:
                c_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + ck.value + '\\"" ws "}"'
            lines.append(c_rule + " ::= " + c_body)

        if vocab.max_conds == 1:
            lines.append('conds ::= "[" ws "]" | "[" ws cond ws "]"')
        else:
            lines.append('conds ::= "[" ws "]" | "[" ws cond ws "]" | "[" ws cond ws "," ws cond ws "]"')

    # Effects
    eff_rule_names = ["effect_" + ek.value.lower() for ek in vocab.effects]
    lines.append("effect ::= " + " | ".join(eff_rule_names))

    for ek in vocab.effects:
        e_rule = "effect_" + ek.value.lower()
        if ek in (
            EffectKind.DAMAGE, EffectKind.HEAL, EffectKind.ENERGY_GAIN, EffectKind.ENERGY_DRAIN,
            EffectKind.POISON, EffectKind.SPEED_UP, EffectKind.SPEED_DOWN, EffectKind.ARMOR_UP, EffectKind.ARMOR_DOWN
        ):
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + ek.value + '\\"" ws "," ws "\\"mag\\"" ws ":" ws mag ws "," ws "\\"dur\\"" ws ":" ws dur ws "}"'
        elif ek in (EffectKind.STUN, EffectKind.BLIND):
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + ek.value + '\\"" ws "," ws "\\"dur\\"" ws ":" ws dur ws "}"'
        elif ek == EffectKind.REVEAL:
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"REVEAL\\"" ws "," ws "\\"r\\"" ws ":" ws int_1_3 ws "," ws "\\"dur\\"" ws ":" ws dur ws "}"'
        elif ek == EffectKind.SPAWN:
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"SPAWN\\"" ws "," ws "\\"arg\\"" ws ":" ws fruit_or_corpse ws "," ws "\\"r\\"" ws ":" ws int_1_3 ws "}"'
        elif ek == EffectKind.SPREAD:
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"SPREAD\\"" ws "," ws "\\"arg\\"" ws ":" ws terrain_type ws "}"'
        elif ek == EffectKind.TELEPORT:
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"TELEPORT\\"" ws "," ws "\\"r\\"" ws ":" ws int_1_3 ws "}"'
        else:
            e_body = '"{" ws "\\"kind\\"" ws ":" ws "\\"' + ek.value + '\\"" ws "}"'
        lines.append(e_rule + " ::= " + e_body)

    # Domain rules
    lines.append('mag ::= ' + ' | '.join('"\\"' + m.value + '\\""' for m in Mag))
    lines.append('dur ::= ' + ' | '.join('"\\"' + d.value + '\\""' for d in Dur))
    lines.append('fruit_or_corpse ::= "\\"FRUIT_A\\"" | "\\"FRUIT_B\\"" | "\\"FRUIT_C\\"" | "\\"FRUIT_D\\"" | "\\"CORPSE\\""')
    lines.append('sp_target ::= "\\"SAME_SP\\"" | "\\"OTHER_SP\\"" | "\\"ANY\\""')
    lines.append('terrain_type ::= "\\"PLAIN\\"" | "\\"WATER\\"" | "\\"BUSH\\"" | "\\"ROCK\\"" | "\\"FIRE\\""')
    lines.append('signal_type ::= "\\"ALARM\\"" | "\\"AGGR\\"" | "\\"SUBM\\"" | "\\"NEUTRAL\\""')
    lines.append('phase_type ::= "\\"DAY\\"" | "\\"NIGHT\\""')
    lines.append('level_type ::= "\\"LOW\\"" | "\\"MID\\"" | "\\"HIGH\\""')
    lines.append('age_type ::= "\\"YOUNG\\"" | "\\"OLD\\""')
    lines.append('wind_type ::= "\\"WITH\\"" | "\\"AGAINST\\""')
    lines.append('subject_type ::= "\\"ARMOR>=3\\"" | "\\"SPEED>=3\\"" | "\\"BRAIN<=1\\"" | "\\"SAME_SP\\""')
    lines.append('recent_action ::= "\\"DRINK\\"" | "\\"EAT\\"" | "\\"ATTACK\\"" | "\\"HIT_BY\\"" | "\\"STEP_ON\\"" | "\\"SPEAK\\"" | "\\"REST\\""')
    lines.append('op_cmp ::= "\\">=\\"" | "\\"<=\\""')
    lines.append('int_1_3 ::= [1-3]')
    lines.append('int_2_5 ::= [2-5]')
    lines.append('int_3_15 ::= [3-9] | "1" [0-5]')

    return "\n".join(lines)


# ─── 7. to_vietnamese ────────────────────────────────────────────────────────

_TERRAIN_VN: dict[str, str] = {
    "PLAIN": "đồng cỏ",
    "WATER": "ô nước",
    "BUSH": "bụi cây",
    "ROCK": "mỏm đá",
    "FIRE": "ô lửa",
}

_SP_TARGET_VN: dict[str, str] = {
    "SAME_SP": "đồng loại",
    "OTHER_SP": "loài khác",
    "ANY": "sinh vật bất kỳ",
}

_SIGNAL_VN: dict[str, str] = {
    "ALARM": "báo động",
    "AGGR": "đe dọa",
    "SUBM": "phục tùng",
    "NEUTRAL": "trung tính",
}

_LEVEL_VN: dict[str, str] = {
    "LOW": "thấp",
    "MID": "trung bình",
    "HIGH": "cao",
}

_MAG_VN: dict[Mag, str] = {
    Mag.SMALL: "nhẹ",
    Mag.MED: "vừa",
    Mag.BIG: "nặng",
}

_DUR_LOOKUP: dict[str, str] = {
    "INSTANT": "tức thì",
    "SHORT": "ngắn hạn",
    "LONG": "dài hạn",
}

_RECENT_ACT_VN: dict[str, str] = {
    "DRINK": "uống nước",
    "EAT": "ăn",
    "ATTACK": "tấn công",
    "HIT_BY": "bị tấn công",
    "STEP_ON": "bước đi",
    "SPEAK": "phát tín hiệu",
    "REST": "nghỉ ngơi",
}


# Bất biến B3: MỌI tra cứu phải rơi về hằng số cố định, TUYỆT ĐỐI không rơi về `arg`.
# `arg` có thể đến từ một luật do người chơi khác DẠY (B-12) và câu render ra sẽ nằm
# trong prompt của người thứ ba. Rơi về `arg` là mở lại đúng kênh tiêm lệnh mà DSL
# sinh ra để đóng (04 §7.4). Số thì ép về int, chuỗi lạ thì thành "?".
_UNKNOWN = "?"


def _num(v: object, default: int) -> str:
    """Ép về int rồi mới đưa vào câu — chặn chuỗi lạ lọt qua trường số."""
    if isinstance(v, (int, float, str, bytes, bytearray)):
        try:
            return str(int(v))
        except (TypeError, ValueError, OverflowError):
            return str(default)
    return str(default)



def _resolve_item(arg: str | None, sm: SurfaceMap) -> str:
    if not arg:
        return "vật phẩm"
    if arg.startswith("FRUIT_"):
        # .get chứ không phải surface_of: một lớp lạ (luật do kẻ khác DẠY, hay bảng
        # bề mặt của ván khác) phải ra "?" chứ không được ném KeyError giữa lúc
        # đang dựng prompt. L-01 bịt đường rơi về `arg` thô nhưng bỏ sót đường này.
        return sm.cls_to_surface.get(arg, _UNKNOWN)
    if arg == "CORPSE":
        return "xác chết"
    return _UNKNOWN


def trigger_to_vn(t: Trigger, sm: SurfaceMap) -> str:
    """Công khai: dùng lại ở genesis/oracle.py. Đừng viết bản thứ hai."""
    if t.kind == TriggerKind.EAT:
        item = _resolve_item(t.arg, sm)
        return "ăn " + item
    if t.kind == TriggerKind.DRINK:
        return "uống nước"
    if t.kind in (TriggerKind.ATTACK, TriggerKind.HIT_BY):
        target = _SP_TARGET_VN.get(t.arg or "", _UNKNOWN)
        if t.kind == TriggerKind.ATTACK:
            return "tấn công " + target
        return "bị " + target + " tấn công"
    if t.kind == TriggerKind.STEP_ON:
        terr = _TERRAIN_VN.get(t.arg or "", _UNKNOWN)
        return "bước vào " + terr
    if t.kind == TriggerKind.ADJACENT:
        target = _SP_TARGET_VN.get(t.arg or "", _UNKNOWN)
        n_str = _num(t.n, 1)
        return "có " + n_str + " " + target + " đứng cạnh liên tiếp"
    if t.kind == TriggerKind.SPEAK:
        sig = _SIGNAL_VN.get(t.arg or "", _UNKNOWN)
        return "phát tín hiệu " + sig
    if t.kind == TriggerKind.REST:
        return "đứng yên " + _num(t.k, 2) + " lượt"
    if t.kind == TriggerKind.DEATH_NEAR:
        return "có sinh vật chết trong bán kính " + _num(t.r, 1)
    if t.kind == TriggerKind.PHASE_ENTER:
        p = "ban ngày" if t.arg == "DAY" else "ban đêm"
        return "bước vào " + p
    if t.kind == TriggerKind.LOW_ENERGY:
        return "năng lượng tụt dưới 25%"
    return _UNKNOWN


def _cond_to_vn(c: Cond, sm: SurfaceMap) -> str:
    if c.kind == CondKind.PHASE:
        p = "ban ngày" if c.arg == "DAY" else "ban đêm"
        return "đang là " + p
    if c.kind == CondKind.TERRAIN:
        terr = _TERRAIN_VN.get(c.arg or "", _UNKNOWN)
        return "đang đứng trên " + terr
    if c.kind in (CondKind.HP, CondKind.ENERGY):
        metric = "máu" if c.kind == CondKind.HP else "năng lượng"
        lvl = _LEVEL_VN.get(c.arg or "", _UNKNOWN)
        return metric + " ở mức " + lvl
    if c.kind == CondKind.RECENT:
        act = _RECENT_ACT_VN.get(c.arg or "", _UNKNOWN)
        return "trong " + _num(c.k, 3) + " lượt qua đã " + act
    if c.kind == CondKind.COUNT:
        target = _SP_TARGET_VN.get(c.arg or "", _UNKNOWN)
        op_str = "ít nhất" if c.op == ">=" else "tối đa"
        return "có " + op_str + " " + _num(c.n, 1) + " " + target + " trong bán kính " + _num(c.r, 1)
    if c.kind == CondKind.AGE:
        return "tuổi trẻ" if c.arg == "YOUNG" else "tuổi già"
    if c.kind == CondKind.WIND:
        return "thuận chiều gió" if c.arg == "WITH" else "ngược chiều gió"
    if c.kind == CondKind.SUBJECT:
        if c.arg == "ARMOR>=3":
            return "giáp ≥ 3"
        if c.arg == "SPEED>=3":
            return "tốc độ ≥ 3"
        if c.arg == "BRAIN<=1":
            return "não ≤ 1"
        if c.arg == "SAME_SP":
            return "là đồng loại"
        return _UNKNOWN
    if c.kind == CondKind.ALONE:
        return "đứng một mình trong bán kính " + _num(c.r, 2)
    return _UNKNOWN


def _effect_to_vn(e: Effect, sm: SurfaceMap) -> str:
    mag_str = _MAG_VN.get(e.mag, "") if e.mag else ""
    dur_str = _DUR_LOOKUP.get(e.dur.value if isinstance(e.dur, Dur) else (e.dur or ""), "") if e.dur else ""
    mag_dur = ""
    if mag_str and dur_str:
        mag_dur = " (mức " + mag_str + ", " + dur_str + ")"
    elif mag_str:
        mag_dur = " (mức " + mag_str + ")"
    elif dur_str:
        mag_dur = " (" + dur_str + ")"

    if e.kind == EffectKind.DAMAGE:
        return "chịu sát thương" + mag_dur
    if e.kind == EffectKind.HEAL:
        return "hồi máu" + mag_dur
    if e.kind == EffectKind.ENERGY_GAIN:
        return "hồi năng lượng" + mag_dur
    if e.kind == EffectKind.ENERGY_DRAIN:
        return "mất năng lượng" + mag_dur
    if e.kind == EffectKind.POISON:
        return "nhiễm độc" + mag_dur
    if e.kind == EffectKind.STUN:
        return "bị choáng" + mag_dur
    if e.kind == EffectKind.BLIND:
        return "bị mù" + mag_dur
    if e.kind == EffectKind.SPEED_UP:
        return "tăng tốc độ" + mag_dur
    if e.kind == EffectKind.SPEED_DOWN:
        return "giảm tốc độ" + mag_dur
    if e.kind == EffectKind.ARMOR_UP:
        return "tăng giáp" + mag_dur
    if e.kind == EffectKind.ARMOR_DOWN:
        return "giảm giáp" + mag_dur
    if e.kind == EffectKind.REVEAL:
        return "lộ vị trí trong bán kính " + _num(e.r, 1) + mag_dur
    if e.kind == EffectKind.SPAWN:
        item = _resolve_item(e.arg, sm)
        return "mọc " + item + " trong bán kính " + _num(e.r, 1)
    if e.kind == EffectKind.SPREAD:
        terr = _TERRAIN_VN.get(e.arg or "", _UNKNOWN)
        dir_str = " theo gió" if e.dir == "WIND" else ""
        return "lan " + terr + dir_str
    if e.kind == EffectKind.TELEPORT:
        return "dịch chuyển ngẫu nhiên trong bán kính " + _num(e.r, 1)
    return _UNKNOWN


def to_vietnamese(law: Law, sm: SurfaceMap) -> str:
    parts = ["KHI " + trigger_to_vn(law.trigger, sm)]
    parts.extend("VÀ " + _cond_to_vn(c, sm) for c in law.conds)
    parts.append("THÌ " + _effect_to_vn(law.effect, sm))

    return " ".join(parts)
