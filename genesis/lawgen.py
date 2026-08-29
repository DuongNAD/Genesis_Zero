"""Genesis Zero v5 — lawgen: Bốc thăm luật và Gate A, B, C (L-03, L-05)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import statistics
from typing import TYPE_CHECKING

from genesis import config
from genesis import law_config as lc
from genesis.lawdsl import Cond, CondKind, Law, TriggerKind, random_law, from_json, to_json

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class SolveStats:
    t_first_fire: float          # tick trung vị luật kích hoạt lần đầu
    n_fire: float                # số lần kích hoạt trung bình trong T tick
    p_never: float               # tỉ lệ rollout luật không kích hoạt lần nào
    n_near_miss: dict[int, float]  # chỉ số cond -> số ca gần trượt trung bình


_ALL_TRIGGERS = tuple(TriggerKind)
_FRUITS_CORPSE = ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D", "CORPSE")
_TERRAINS = ("PLAIN", "WATER", "BUSH", "ROCK", "FIRE")
_LEVELS = ("LOW", "MID", "HIGH")
_PHASES = ("DAY", "NIGHT")
_AGES = ("YOUNG", "OLD")
_WINDS = ("WITH", "AGAINST")
_SIGNALS = ("ALARM", "AGGR", "SUBM", "NEUTRAL")
_RECENT_ACTIONS = ("DRINK", "EAT", "ATTACK", "HIT_BY", "STEP_ON", "SPEAK", "REST")
_SUBJECT_KEYS = ("ARMOR>=3", "SPEED>=3", "BRAIN<=1", "SAME_SP")
_SP_CHOICES = ("SAME_SP", "OTHER_SP", "ANY")


def _check_cond_direct(
    c: Cond,
    phase: str,
    terrain: str,
    hp_band: str,
    energy_band: str,
    age_band: str,
    wind_rel: str,
    alone: bool,
    rec_dict: dict[str, int],
    c_s: list[int],
    c_o: list[int],
    c_any: list[int],
    subj_dict: dict[str, bool],
) -> bool:
    ck = c.kind
    if ck == CondKind.PHASE:
        return phase == c.arg
    if ck == CondKind.TERRAIN:
        return terrain == c.arg
    if ck == CondKind.HP:
        return hp_band == c.arg
    if ck == CondKind.ENERGY:
        return energy_band == c.arg
    if ck == CondKind.RECENT:
        return rec_dict.get(c.arg, 10**9) <= (c.k if c.k is not None else 0)
    if ck == CondKind.COUNT:
        r = c.r if c.r is not None else 1
        val = c_s[r] if c.arg == "SAME_SP" else (c_o[r] if c.arg == "OTHER_SP" else c_any[r])
        n = c.n if c.n is not None else 0
        return val >= n if c.op == ">=" else val <= n
    if ck == CondKind.AGE:
        return age_band == c.arg
    if ck == CondKind.WIND:
        return wind_rel == c.arg
    if ck == CondKind.SUBJECT:
        return subj_dict.get(c.arg, False)
    if ck == CondKind.ALONE:
        return alone
    return False


def measure(law: Law, rollouts: int, ticks: int, rng: random.Random) -> SolveStats:
    """Đo lường độ kích hoạt và số ca gần trượt của luật qua mô phỏng rollout tình huống.

    Tất định với rng cho trước (Bất biến B1).
    Chạy trực tiếp trên chuỗi biến ngẫu nhiên tương đương chính xác để tối ưu tốc độ (Bất biến B2).
    """
    first_fires: list[int] = []
    total_fires: list[int] = []
    num_conds = len(law.conds)
    sum_near_miss: dict[int, int] = {i: 0 for i in range(num_conds)}

    lt = law.trigger
    lt_kind = lt.kind
    lt_arg = lt.arg
    lt_n = lt.n
    lt_k = lt.k
    lt_r = lt.r
    conds = law.conds

    rec_dict: dict[str, int] = {}
    subj_dict: dict[str, bool] = {}
    c_s = [0, 0, 0, 0]
    c_o = [0, 0, 0, 0]
    c_any = [0, 0, 0, 0]

    for _ in range(rollouts):
        ff: int | None = None
        fires = 0
        for tick in range(1, ticks + 1):
            k = rng.choice(_ALL_TRIGGERS)
            arg, n, kk, r = None, None, None, None
            if k == TriggerKind.EAT:
                arg = rng.choice(_FRUITS_CORPSE)
            elif k in (TriggerKind.ATTACK, TriggerKind.HIT_BY):
                arg = rng.choice(_SP_CHOICES)
            elif k == TriggerKind.STEP_ON:
                arg = rng.choice(_TERRAINS)
            elif k == TriggerKind.ADJACENT:
                arg = rng.choice(_SP_CHOICES)
                n = rng.choice((1, 2, 3))
            elif k == TriggerKind.SPEAK:
                arg = rng.choice(_SIGNALS)
            elif k == TriggerKind.REST:
                kk = rng.choice((2, 3, 4, 5))
            elif k == TriggerKind.DEATH_NEAR:
                r = rng.choice((1, 2, 3))
            elif k == TriggerKind.PHASE_ENTER:
                arg = rng.choice(_PHASES)

            c_s[1] = rng.randint(0, 3)
            c_s[2] = rng.randint(0, 4)
            c_s[3] = rng.randint(0, 5)
            c_o[1] = rng.randint(0, 3)
            c_o[2] = rng.randint(0, 4)
            c_o[3] = rng.randint(0, 5)
            c_any[1] = c_s[1] + c_o[1]
            c_any[2] = c_s[2] + c_o[2]
            c_any[3] = c_s[3] + c_o[3]

            phase = rng.choice(_PHASES)
            terrain = rng.choice(_TERRAINS)
            hp_band = rng.choice(_LEVELS)
            energy_band = rng.choice(_LEVELS)
            age_band = rng.choice(_AGES)
            wind_rel = rng.choice(_WINDS)
            alone = rng.choice((True, False))
            rec_dict["DRINK"] = rng.randint(0, 30)
            rec_dict["EAT"] = rng.randint(0, 30)
            rec_dict["ATTACK"] = rng.randint(0, 30)
            rec_dict["HIT_BY"] = rng.randint(0, 30)
            rec_dict["STEP_ON"] = rng.randint(0, 30)
            rec_dict["SPEAK"] = rng.randint(0, 30)
            rec_dict["REST"] = rng.randint(0, 30)
            subj_dict["ARMOR>=3"] = rng.choice((True, False))
            subj_dict["SPEED>=3"] = rng.choice((True, False))
            subj_dict["BRAIN<=1"] = rng.choice((True, False))
            subj_dict["SAME_SP"] = rng.choice((True, False))

            trig_match = (k == lt_kind)
            if trig_match and lt_arg is not None:
                if lt_kind in (TriggerKind.ATTACK, TriggerKind.HIT_BY, TriggerKind.ADJACENT):
                    if lt_arg == "ANY":
                        trig_match = (arg in ("SAME_SP", "OTHER_SP", "ANY"))
                    else:
                        trig_match = (arg == lt_arg)
                else:
                    trig_match = (arg == lt_arg)
            if trig_match and lt_n is not None:
                trig_match = (n is not None and n >= lt_n)
            if trig_match and lt_k is not None:
                trig_match = (kk is not None and kk >= lt_k)
            if trig_match and lt_r is not None:
                trig_match = (r is not None and r <= lt_r)

            if trig_match:
                if num_conds > 0:
                    h0 = _check_cond_direct(
                        conds[0], phase, terrain, hp_band, energy_band, age_band, wind_rel, alone, rec_dict, c_s, c_o, c_any, subj_dict
                    )
                    if num_conds == 1:
                        if h0:
                            if ff is None:
                                ff = tick
                            fires += 1
                        else:
                            sum_near_miss[0] += 1
                    else:
                        h1 = _check_cond_direct(
                            conds[1], phase, terrain, hp_band, energy_band, age_band, wind_rel, alone, rec_dict, c_s, c_o, c_any, subj_dict
                        )
                        if h0 and h1:
                            if ff is None:
                                ff = tick
                            fires += 1
                        elif not h0 and h1:
                            sum_near_miss[0] += 1
                        elif h0 and not h1:
                            sum_near_miss[1] += 1
                else:
                    if ff is None:
                        ff = tick
                    fires += 1

        if ff is None:
            ff = ticks
        first_fires.append(ff)
        total_fires.append(fires)

    t_first_fire = float(statistics.median(first_fires))
    n_fire = float(sum(total_fires) / rollouts) if rollouts > 0 else 0.0
    p_never = float(sum(1 for f in total_fires if f == 0) / rollouts) if rollouts > 0 else 0.0
    n_near_miss = {i: float(sum_near_miss[i] / rollouts) for i in range(num_conds)}

    return SolveStats(
        t_first_fire=t_first_fire,
        n_fire=n_fire,
        p_never=p_never,
        n_near_miss=n_near_miss,
    )


def gate_b(s: SolveStats, ticks: int) -> bool:
    """Gate B: Kiểm tra tính khả giải của luật (kích hoạt đủ sớm, đủ nhiều, ít khi không xảy ra)."""
    return (
        s.t_first_fire <= lc.SOLVE_MAX_FIRST_FIRE * ticks
        and s.n_fire >= lc.SOLVE_MIN_FIRES
        and s.p_never <= lc.SOLVE_MAX_P_NEVER
    )


def gate_c(s: SolveStats, law: Law) -> bool:
    """Gate C: Kiểm tra tính định danh được của từng điều kiện qua số ca gần trượt.

    Bất biến B3: Gate C sửa ở ĐẦU VÀO (chỉ phát ra đề giải được), KHÔNG nới ở chỗ chấm điểm.
    Mọi điều kiện của luật phải có đủ số ca đối chứng gần trượt (near-miss) để thuật toán học phân biệt được.
    Luật không có điều kiện (D1) luôn thoả mãn Gate C.
    """
    if not law.conds:
        return True
    for i in range(len(law.conds)):
        if s.n_near_miss.get(i, 0.0) < lc.IDENT_MIN_NEAR_MISS:
            return False
    return True


def observable(law: Law, min_sense: int) -> bool:
    """Gate A: Luật chỉ quan sát được khi các tham số bán kính không vượt quá tầm nhìn tối thiểu."""
    max_r = config.SIGHT_BASE + min_sense
    if law.trigger.kind == TriggerKind.DEATH_NEAR:
        if law.trigger.r is not None and law.trigger.r > max_r:
            return False
    for c in law.conds:
        if c.kind == CondKind.COUNT:
            if c.r is not None and c.r > max_r:
                return False
    return True


def statable(law: Law, brain: int) -> bool:
    """Gate D: một con `brain` có PHÁT BIỂU ĐƯỢC luật này không.

    Song sinh với `observable` (Gate A). Gate A hỏi "có nhìn thấy được không";
    Gate D hỏi "có nói ra được không". Cả hai chặn cùng một kiểu bất công: một
    đề bài mà thí sinh không thể trả lời, dù có suy ra đúng.

    Vì sao cần. `_generate_law_for_tier` gọi `random_law(rng)` **không truyền
    vocab**, tức bốc từ từ vựng brain 5. Nhưng `vocab_for_brain` cắt từ vựng
    theo brain: `ADJACENT` và `PHASE_ENTER` chỉ có từ brain 4 trở lên, và
    `max_conds` là 0 với brain 0–1. Ván seed 55 sinh ra
    `ADJACENT(OTHER_SP) -> POISON`, luật **nổ nhiều nhất ván (324 lần)**, mà
    **4/5 loài không có chữ `ADJACENT` trong từ vựng** — chúng chịu hệ quả suốt
    ván và không cách nào ghi nó vào Sổ Luật.

    Từ vựng theo brain là CHỦ Ý (`vocab_for_brain`): loài não to nói được nhiều
    hơn, đó là một phần phần thưởng của brain. Cái không phải chủ ý là một ván
    mà loài não nhỏ **không có mục tiêu nào** để nhắm. Nên gate này ràng ở mức
    BỘ LUẬT, không ở từng luật — xem `generate`.
    """
    from genesis.lawdsl import vocab_for_brain

    v = vocab_for_brain(brain)
    if law.trigger.kind not in v.triggers:
        return False
    if law.effect.kind not in v.effects:
        return False
    if len(law.conds) > v.max_conds:
        return False
    return all(c.kind in v.conds for c in law.conds)


def min_founder_brain() -> int:
    """Brain thấp nhất trong đàn khai sinh — thí sinh yếu nhất phải giải được gì đó."""
    from genesis.traits import founder_traits

    return min(founder_traits(sp).brain for sp in config.POPULATION)


# Số điều kiện tối thiểu mà một luật thuộc tier ấy mang. `D4` cũng gán cho
# ADJACENT/SPREAD/SPAWN/TELEPORT nên nó không thuần theo số điều kiện; lấy 2 là
# cận dưới đúng cho nhánh "hai điều kiện".
_TIER_CONDS = {"D1": 0, "D2": 1, "D3": 2, "D4": 2}


def gate_d_brain(arm: str) -> int:
    """Brain mà Gate D dùng làm ngưỡng, suy từ TIER PLAN của nhánh.

    Không phải lúc nào cũng là brain 0. Nhánh `HARSH` có kế hoạch `D2 D2 D3 D4`
    — **không có tier D1 nào** — mà brain 0–1 có `max_conds = 0`, nên không một
    luật HARSH nào brain 0 phát biểu nổi. Đòi brain 0 ở đó là đòi một điều bất
    khả, và `generate` sẽ đốt hết 200 lượt thử rồi ném lỗi (đã xảy ra: 4 bài
    test đỏ cùng lúc).

    Ngưỡng đúng là: **con yếu nhất còn có thể nói được một luật ở tier DỄ NHẤT
    của nhánh này**. STANDARD có D1 nên ngưỡng là 0; HARSH dễ nhất là D2 nên
    ngưỡng là 2.
    """
    from genesis.lawdsl import vocab_for_brain

    plan = lc.TIER_PLAN[arm]
    tiers = [t for spec in plan for t in spec.split("|")]
    need = min(_TIER_CONDS.get(t, 2) for t in tiers)
    for b in range(config.TRAIT_MIN, config.TRAIT_MAX + 1):
        if vocab_for_brain(b).max_conds >= need:
            return max(min_founder_brain(), b)
    return config.TRAIT_MAX


def requires_cooperation(law: Law) -> bool:
    """Xác định luật có đòi hỏi hợp tác xã hội hay không (§6.3)."""
    if law.trigger.kind == TriggerKind.ADJACENT and law.trigger.n is not None and law.trigger.n >= 1:
        return True
    for c in law.conds:
        if c.kind == CondKind.COUNT and c.op == ">=" and c.n is not None and c.n >= 1:
            return True
        if c.kind == CondKind.SUBJECT and c.arg == "SAME_SP":
            return True
    return False


def is_solo_exploitable(law: Law) -> bool:
    """Luật khai thác được một mình (ngược lại với đòi hỏi hợp tác)."""
    return not requires_cooperation(law)


def split_arm(arm: str) -> tuple[str, str | None]:
    """`"STANDARD@RUNG_RAM"` -> `("STANDARD", "RUNG_RAM")`.

    Cổng khả giải chạy một ván THẬT, nên nó phải chạy trên **đúng bản đồ** sẽ
    dùng: sa mạc gần như không có ô nước, và một luật `DRINK` được duyệt trên
    đồng cỏ sẽ là câu đố không có lời giải ở đó. Nhét bản đồ vào tên nhánh cho
    khoá đệm tự tách theo cặp (bản đồ, seed) mà không phải thêm tham số vào mọi
    chỗ gọi.
    """
    base, _, map_name = arm.partition("@")
    return base, (map_name or None)


def live_fire_counts(laws: list[Law], seed: int, ticks: int,
                     map_name: str | None = None) -> list[int]:
    """Đếm số lần MỖI luật kích hoạt trong một ván THẬT.

    Bẫy — vì sao không dùng tình huống tổng hợp: `measure()` bốc ngữ cảnh ĐỀU và
    trigger ĐỀU, tức là đo trên một thế giới không có thật. Sim thật lệch hẳn:
    `ROCK` không đi qua được nên `STEP_ON(ROCK)` không bao giờ xảy ra, `REST(5)`
    hiếm, `ADJACENT(n=3)` hiếm. Đo thật cho thấy cổng dựa trên `measure` chặn được
    3/15 luật chết trong khi để lọt 5/15 — tức là tệ hơn không có cổng.
    Sim chỉ mất ~0.19 s cho 400 tick nên chạy ván thật rẻ hơn nhiều so với sai lầm.
    """
    from genesis.tick import build_match, tick as run_tick   # nhập trong thân: tránh vòng

    world, creatures, state, rng = build_match(seed=seed, map_name=map_name)
    counts = [0] * len(laws)
    for t in range(ticks):
        before = _FIRE_PROBE.copy()
        run_tick(world, creatures, t, rng, state, laws=laws, log=_ProbeLog(counts))
    return counts


class _ProbeLog:
    """Log giả: chỉ đếm LAW_FIRED, không ghi gì ra đĩa."""

    def __init__(self, counts: list[int]) -> None:
        self.counts = counts

    def write(self, t: int, kind: str, **fields) -> None:
        if kind == "LAW_FIRED":
            lid = fields.get("law_id", "")
            if lid.startswith("L") and lid[1:].isdigit():
                i = int(lid[1:])
                if 0 <= i < len(self.counts):
                    self.counts[i] += 1


_FIRE_PROBE: list[int] = []


def _generate_law_for_tier(rng: random.Random, target_tier: str, min_sense: int) -> Law:
    for _ in range(500):
        law = random_law(rng)
        # Chỉ nhận hệ quả mà VÒNG TICK áp dụng được. Bốc ngoài danh sách thì "luật thật"
        # nói một đằng còn thế giới làm một nẻo — đề bài không giải được, và im lặng.
        if law.effect.kind.value not in lc.IMPLEMENTED_EFFECTS:
            continue
        if law.trigger.kind.value not in lc.IMPLEMENTED_TRIGGERS:
            continue
        if law.tier() == target_tier and observable(law, min_sense):
            return law
    raise RuntimeError(f"Failed to generate observable law for tier {target_tier}")


def _fruit_law_for_tier(rng: random.Random, tier: str, min_sense: int) -> Law | None:
    """Một luật `EAT(quả)` có hệ quả rõ hại hoặc rõ lành, đúng tier yêu cầu."""
    from genesis.prior import fruit_valence

    for _ in range(400):
        law = _generate_law_for_tier(rng, tier, min_sense)
        if fruit_valence([law]):
            return law
    return None


def _statable_law_for_tier(rng: random.Random, tier: str, min_sense: int,
                           brain: int) -> Law | None:
    """Một luật cùng tier mà con `brain` PHÁT BIỂU ĐƯỢC."""
    for _ in range(400):
        law = _generate_law_for_tier(rng, tier, min_sense)
        if statable(law, brain):
            return law
    return None


def generate(
    seed: int,
    arm: str = "STANDARD",
    world_cfg: dict | None = None,
    check_solvable: bool = True,
) -> list[Law]:
    """Sinh bộ luật cho ván đấu theo TIER_PLAN và các cổng kiểm định Gate A, Gate B, Gate C, §6.3."""
    arm, map_name = split_arm(arm)
    if arm not in lc.TIER_PLAN:
        raise ValueError(f"Unknown arm '{arm}', expected one of {list(lc.TIER_PLAN.keys())}")

    plan = lc.TIER_PLAN[arm]
    min_sense = 1
    if world_cfg and "min_sense" in world_cfg:
        min_sense = int(world_cfg["min_sense"])
    min_brain = gate_d_brain(arm)
    if world_cfg and "min_brain" in world_cfg:
        min_brain = int(world_cfg["min_brain"])

    rng = random.Random(seed)

    for _ in range(lc.LAWGEN_MAX_RETRY):
        laws: list[Law] = []
        for tier_spec in plan:
            if "|" in tier_spec:
                target_tier = rng.choice(tier_spec.split("|"))
            else:
                target_tier = tier_spec
            law = _generate_law_for_tier(rng, target_tier, min_sense)
            laws.append(law)

        # Đảm bảo không trùng luật
        if len(set(laws)) != len(laws):
            continue

        # Gate A: Tất cả luật phải quan sát được
        if not all(observable(l, min_sense) for l in laws):
            continue

        # Gate D: ít nhất một luật phải PHÁT BIỂU ĐƯỢC bởi con não nhỏ nhất.
        # Ràng ở mức BỘ, không ở từng luật: bắt mọi luật phải nói được ở brain 0
        # sẽ ép cả ván về 5 trigger và 0 điều kiện, tức xoá luôn phần thưởng từ
        # vựng của brain. Ràng ở mức bộ giữ được cả hai: loài não to vẫn có
        # những luật riêng nó nói được, còn loài não nhỏ luôn có ÍT NHẤT một
        # mục tiêu nhắm được.
        #
        # LÁI chứ không loại — cùng lý do như luật ăn quả ở dưới: bốc lại cả bộ
        # cho tới khi tình cờ đủ là quá hiếm (đo: 16/40 seed thiếu, và seed 12
        # đốt hết 200 lượt thử mà không ra). Thay đúng một luật bằng luật cùng
        # tier nói được, rồi để MỌI cổng phía dưới xét lại cả bộ như thường.
        if sum(statable(l, min_brain) for l in laws) < lc.LAWSET_MIN_STATABLE:
            # Thay đúng luật ở tier DỄ NHẤT của bộ, không phải luật cuối: một
            # luật D3/D4 mang hai điều kiện, mà brain 0 có `max_conds = 0` —
            # không bản thay nào của tier ấy nói được, và ta đốt hết 200 lượt
            # thử rồi ném lỗi (đã xảy ra ở seed 12).
            i = min(range(len(laws)), key=lambda k: _TIER_CONDS.get(laws[k].tier(), 2))
            fixed = _statable_law_for_tier(rng, laws[i].tier(), min_sense, min_brain)
            if fixed is None:
                continue
            laws = laws[:i] + [fixed] + laws[i + 1:]
            if len(set(laws)) != len(laws):
                continue
            if sum(statable(l, min_brain) for l in laws) < lc.LAWSET_MIN_STATABLE:
                continue

        # Gate B THẬT: mọi luật phải kích hoạt đủ nhiều — VÀ đủ ít — trong một
        # ván THẬT. Trần cũng cần thiết như sàn: xem lc.SOLVE_MAX_FIRE_RATE.
        if check_solvable:
            counts = live_fire_counts(laws, seed, lc.SOLVE_LIVE_TICKS, map_name)
            if min(counts) < lc.SOLVE_MIN_FIRES:
                continue
            budget = lc.SOLVE_LIVE_TICKS * sum(config.POPULATION.values())
            if max(counts) > lc.SOLVE_MAX_FIRE_RATE * budget:
                continue

        # X-03 cần một luật gắn BỀ MẶT với HỆ QUẢ — chỗ duy nhất prior về màu
        # sắc có thể giúp hoặc hại.
        if arm in lc.ARMS_REQUIRING_FRUIT_LAW:
            from genesis.prior import fruit_valence
            if not fruit_valence(laws):
                # LÁI chứ không loại: bốc lại cả bộ cho tới khi tình cờ có một
                # luật ăn quả là quá hiếm (3/39 seed), và seed 7 đã đốt hết 200
                # lượt thử mà không ra. Thay đúng luật đầu bằng một luật ăn quả
                # cùng tier, rồi để MỌI cổng phía dưới xét lại cả bộ như thường.
                fixed = _fruit_law_for_tier(rng, laws[0].tier(), min_sense)
                if fixed is None:
                    continue
                laws = [fixed] + laws[1:]
                if len(set(laws)) != len(laws):
                    continue

        # Ràng buộc §6.3 cho STANDARD: ≥1 đơn độc và ≥1 hợp tác
        if arm == "STANDARD":
            if lc.REQUIRE_SOLO_LAW and not any(is_solo_exploitable(l) for l in laws):
                continue
            if lc.REQUIRE_COOP_LAW and not any(requires_cooperation(l) for l in laws):
                continue

        # Gate C (định danh được) — vẫn dùng tình huống tổng hợp vì nó hỏi về KHÔNG GIAN
        # GIẢ THUYẾT (có đủ ca gần trượt để phân biệt cond không), không về động lực học
        # của thế giới. Giới hạn đã biết: nó không phản ánh phân bố thật của sim; nếu
        # sau này thấy luật qua Gate C mà agent vẫn không suy ra được cond, đây là chỗ xem.
        if check_solvable:
            if not all(gate_c(measure(l, 40, 200, rng), l) for l in laws):
                continue

        return laws

    raise RuntimeError(
        f"Failed to generate valid laws after {lc.LAWGEN_MAX_RETRY} retries for arm '{arm}' (seed={seed})"
    )



# ─── Bộ nhớ đệm bộ luật ──────────────────────────────────────────────────────

DEFAULT_CACHE_DIR = Path(".cache/laws")


def generate_cached(
    seed: int, arm: str = "STANDARD", cache_dir: Path | None = None
) -> list[Law]:
    """`generate` có nhớ, khoá theo (arm, seed).

    Cổng khả giải chạy MỘT VÁN THẬT 200 tick cho mỗi bộ luật (L-05), mất 2–6,5 s.
    Trước khi có lớp này, mỗi lần gọi `genesis.run` đều trả lại khoản đó: bộ test
    phình từ 20 s lên 118 s chỉ vì `run.py` bắt đầu sinh luật. Với R-01 (hàng
    nghìn rollout trên vài chục seed) thì nó sẽ là phần lớn thời gian máy chạy.

    Đệm được là vì `generate` tất định theo (seed, arm) — cùng khoá thì cùng bộ
    luật, không có gì để mất. `test_cache_khop_ban_sinh_moi` ghim điều đó.
    """
    d = DEFAULT_CACHE_DIR if cache_dir is None else Path(cache_dir)
    path = d / f"{arm}-{seed}.json"
    if path.exists():
        try:
            return [from_json(x) for x in json.loads(path.read_text(encoding="utf-8"))]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Đệm hỏng thì sinh lại, đừng nổ. Nhưng cũng đừng im lặng nuốt: file
            # hỏng sẽ bị ghi đè ngay bên dưới.
            pass
    laws = generate(seed, arm=arm)
    d.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps([to_json(law) for law in laws], ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(path)   # đổi tên nguyên tử: hai tiến trình song song không ghi đè nhau nửa chừng
    return laws
