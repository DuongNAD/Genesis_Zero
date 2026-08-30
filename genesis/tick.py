"""Genesis Zero — tick: vòng lặp thời gian 6 pha tất định."""

from __future__ import annotations

from dataclasses import astuple, dataclass, field
import hashlib
import random
from typing import TYPE_CHECKING

from genesis import config, law_config
from genesis.adapt import award_adapt, maybe_shift, reset_body
from genesis.lineage import rebirth
from genesis.combat import (
    MELEE_RANGE,
    Attack,
    apply_combat,
    resolve_combat,
    tick_poison,
    tick_regen,
)
from genesis.creature import (
    Creature,
    creature_sort_key,
    kill,
    resolve_eat,
    spawn_population,
    try_respawn,
    upkeep_and_check_death,
)
from genesis.reflex import (
    ActiveGoal,
    Intent,
    apply_intent,
    choose_goal,
    reflex_step,
)
from genesis.speech import COST_SPEAK, hearers
from genesis.strategist import ReflexStrategist, Strategist
from genesis.lawdsl import Law, TriggerKind
from genesis.lawhook import apply_creature_effect, build_ctx, collect_law_effects
from genesis.laweval import LawEvent
from genesis.surface import roll_surface_map
from genesis.world import (
    Terrain,
    World,
    decay_corpses,
    phase_at,
    spawn_plants,
    visible,
)

if TYPE_CHECKING:
    from genesis.logio import LogWriter


@dataclass
class SimState:
    match_seed: int
    active_goals: dict[str, ActiveGoal] = field(default_factory=dict)
    # creature_id -> {tên trigger: tick gần nhất} — nguồn cho cond RECENT
    last_did: dict[str, dict[str, int]] = field(default_factory=dict)
    # creature_id -> số tick đứng yên LIÊN TIẾP; nguồn cho trigger REST(k)
    rest_streak: dict[str, int] = field(default_factory=dict)


def creature_rng(match_seed: int, tick_no: int, creature_id: str) -> random.Random:
    """Luồng ngẫu nhiên RIÊNG cho một con ở một tick."""
    h = hashlib.md5(f"{match_seed}:{tick_no}:{creature_id}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def build_match(
    seed: int,
    prior_arm: str = "PRIOR_FREE",
    laws: list | None = None,
    map_name: str | None = None,
) -> tuple[World, list[Creature], SimState, random.Random]:
    """Dựng thế giới + quần thể + state từ một seed. Dùng chung cho run và test.

    `prior_arm` khác `PRIOR_FREE` thì ánh xạ bề mặt được CHỌN theo bộ luật (X-03,
    03 §10.2) chứ không bốc ngẫu nhiên — nên phải truyền `laws` vào.
    """
    rng = random.Random(seed)
    # Bất biến B2: hoán vị bề mặt phải dùng luồng ĐỘC LẬP THẬT.
    # Bẫy: `random.Random(seed)` lần hai KHÔNG độc lập — nó là đúng cùng một dãy số.
    # Bề mặt khi đó tương quan hoàn toàn với địa hình/thức ăn và tạo manh mối không cố ý.
    # Dẫn xuất một seed khác hẳn bằng md5.
    s_seed = int(hashlib.md5(f"surface:{seed}".encode()).hexdigest()[:16], 16)
    s_rng = random.Random(s_seed)
    if prior_arm == "PRIOR_FREE":
        surface_map = roll_surface_map(s_rng)
    else:
        from genesis.prior import prior_surface_map
        surface_map = prior_surface_map(laws or [], prior_arm, s_rng)
    world = World(config.GRID_W, config.GRID_H, rng, surface_map=surface_map,
                  map_name=map_name)
    creatures = spawn_population(world, rng)
    state = SimState(match_seed=seed)
    # Ba đặc điểm bốc thăm cho mỗi loài (W-19), tất định theo `(loài, seed)`.
    # Tất định là bắt buộc: bộ đệm hình 3D khoá theo chuỗi mô tả, `--replay`
    # dựng lại ván cũ, và bộ chấm so hai ván với nhau — bốc lại mỗi lần chạy
    # thì cả ba đường ấy gãy cùng lúc.
    from genesis.features import kit_of, roll_for_species

    world.kits = {sp: kit_of(roll_for_species(sp, seed))
                  for sp in sorted({c.species for c in creatures})}

    return world, creatures, state, rng


_DEFAULT_STRATEGIST: Strategist = ReflexStrategist()


def _collect_intents(
    world: World,
    creatures: list[Creature],
    tick_no: int,
    state: SimState,
    strategist: Strategist | None = None,
) -> list[Intent]:
    """Pha 1: Thu thập intent cho mọi con còn sống, duyệt theo creature_sort_key."""
    strat = _DEFAULT_STRATEGIST if strategist is None else strategist
    intents: list[Intent] = []
    for c in sorted(creatures, key=creature_sort_key):
        if not c.alive:
            continue
        crng = creature_rng(state.match_seed, tick_no, c.id)
        seen = visible(c, world, creatures)
        g = state.active_goals.get(c.id)
        # Hỏi mỗi tick, không phải chỉ khi hết hạn: quyết định của LLM về lúc nào
        # thì đè lúc ấy (B-05 bất biến 1). Tầng nào không muốn đè thì trả None —
        # `ReflexStrategist` trả None đúng khi `current` còn hạn, nên hành vi M0/M1
        # không đổi một tick nào.
        decision = strat.decide(c, world, seen, crng, tick_no, g)
        if decision is not None:
            g = decision
        elif g is None or g.ttl <= 0:
            g = choose_goal(c, world, seen, crng)
        state.active_goals[c.id] = g
        g.ttl -= 1
        intent = reflex_step(c, world, creatures, g, crng)
        intents.append(intent)
    return intents


def _resolve_eating(
    world: World,
    creatures: list[Creature],
    log: LogWriter | None = None,
    tick: int = 0,
) -> list[dict]:
    """Giải quyết tranh chấp thức ăn tất định theo creature_sort_key."""
    by_pos: dict[tuple[int, int], list[Creature]] = {}
    for c in creatures:
        if c.alive:
            by_pos.setdefault(world.wrap(*c.pos), []).append(c)

    events: list[dict] = []
    for pos in sorted(world.fruits.keys()):
        occupants = by_pos.get(pos)
        if occupants:
            winner = min(occupants, key=creature_sort_key)
            fruit_cls = world.fruits.get(pos)
            gained = resolve_eat(winner, world)
            if gained > 0:
                award_adapt(winner, "eat")
                surface_str = (
                    world.surface_map.surface_of(fruit_cls)
                    if world.surface_map and fruit_cls
                    else "quả"
                )
                payload = {
                    "creature_id": winner.id,
                    "species_id": winner.species,
                    "energy": winner.energy,
                    "pos": list(winner.pos),
                    "fruit_surface": surface_str,
                    "fruit_class": fruit_cls,   # CHỈ dùng nội bộ, bị lọc trước khi ghi log
                }
                events.append(payload)
                if log is not None:
                    log.write(tick, "EAT", **payload)
    return events


def tick(
    world: World,
    creatures: list[Creature],
    tick_no: int,
    rng: random.Random,
    state: SimState,
    log: LogWriter | None = None,
    laws: list | None = None,
    strategist: Strategist | None = None,
) -> None:
    """Một bước thời gian. Sáu pha, đúng thứ tự."""
    strat = _DEFAULT_STRATEGIST if strategist is None else strategist

    # 0. NGHĨ — bắn cả đàn một lượt rồi CHỜ HẾT, trước khi thu intent.
    # Bẫy B-05 §3: áp goal ngay lúc nó về, giữa pha thu intent, là phá bất biến
    # đồng thời của W-11 — hai con cùng tick sẽ thấy hai thế giới khác nhau.
    begin = getattr(strat, "begin_tick", None)
    if begin is not None:
        begin(creatures, world, tick_no)

    # 1. THU INTENT — duyệt theo creature_sort_key. KHÔNG áp dụng gì cả.
    intents = _collect_intents(world, creatures, tick_no, state, strategist=strat)

    # 2. RESOLVE ĐỒNG THỜI: di chuyển -> uống nước -> chiến đấu -> ăn
    creatures_by_id: dict[str, Creature] = {c.id: c for c in creatures}
    for it in intents:
        apply_intent(it, creatures_by_id, world)

    drink_events: list[dict] = []
    for c in sorted(creatures, key=creature_sort_key):
        if not c.alive:
            continue
        wx, wy = world.wrap(*c.pos)
        if world.grid[wy][wx] == Terrain.WATER:
            c.last_drink_tick = tick_no
            drink_events.append({
                "creature_id": c.id,
                "species_id": c.species,
                "pos": list(c.pos),
            })

    attacks = [
        Attack(it.creature_id, it.attack_id)
        for it in intents
        if it.attack_id is not None
    ]
    combat_results = resolve_combat(attacks, creatures_by_id, world)
    apply_combat(combat_results, creatures_by_id)

    attack_events: list[dict] = []
    for res in combat_results:
        target = creatures_by_id[res.target_id]
        attack_events.append({
            "creature_id": target.id,
            "species_id": target.species,
            "target_id": res.target_id,
            "dmg": res.dmg,
            "poison_from": res.poison_from,
            "pos": list(target.pos),
        })

    # 2.5 NÓI — sau khi đã di chuyển (ai nghe được ai phụ thuộc vị trí CUỐI tick),
    # trước khi tính chi phí. Thu hết rồi mới phát: hai con cùng nói trong một
    # tick thì cả hai đều được nghe, không con nào nghe câu của con kia "sớm hơn".
    speak_events: list[dict] = []
    says = getattr(strat, "take_says", None)
    if says is not None:
        pending = says()
        for cid in sorted(pending, key=lambda k: creature_sort_key(creatures_by_id[k])
                          if k in creatures_by_id else (k, 0)):
            c = creatures_by_id.get(cid)
            if c is None or not c.alive:
                continue
            say = pending[cid]
            c.energy -= COST_SPEAK
            full, sig = hearers(c, creatures, world)
            speak_events.append({
                "creature_id": c.id, "species_id": c.species,
                "signal": say.signal, "text": say.text, "teach": say.teach,
                # Hai danh sách này là bằng chứng cho bất biến 3 của B-11: tầm
                # `signal` phải rộng hơn tầm `text`, và nghiệm thu đo đúng nó.
                "hear_full": [x.id for x in full],
                "hear_signal": [x.id for x in sig],
                "pos": list(c.pos),
            })

    eat_events = _resolve_eating(world, creatures, log=None, tick=tick_no)

    # 3. ÁP DỤNG CHI PHÍ: cost_attack cho kẻ đã vung đòn, tick_poison, tick_regen, upkeep
    for att in attacks:
        attacker = creatures_by_id.get(att.attacker_id)
        if attacker is not None and attacker.alive:
            attacker.energy -= config.COST_ATTACK

    death_causes: dict[str, str] = {}
    for c in sorted(creatures, key=creature_sort_key):
        if not c.alive:
            continue
        if c.hp <= 0:
            death_causes[c.id] = "combat"
            continue

        tick_poison(c)
        if c.hp <= 0:
            death_causes[c.id] = "poison"
            continue

        tick_regen(c)

        if upkeep_and_check_death(c, tick_no, world.kits.get(c.species)):
            death_causes[c.id] = "starve"

    # Thắng trận: mục tiêu chết vì đòn của mình trong tick đó -> award_adapt(c, "win")
    winning_attackers: set[str] = set()
    for att in attacks:
        if death_causes.get(att.defender_id) == "combat":
            attacker = creatures_by_id.get(att.attacker_id)
            defender = creatures_by_id.get(att.defender_id)
            if (
                attacker is not None
                and defender is not None
                and world.dist(attacker.pos, defender.pos) <= MELEE_RANGE
            ):
                winning_attackers.add(attacker.id)

    for attacker_id in sorted(winning_attackers, key=lambda cid: creature_sort_key(creatures_by_id[cid])):
        award_adapt(creatures_by_id[attacker_id], "win")

    # Cuối pha 3: mỗi con còn sống tích luỹ survive streak và maybe_shift
    shift_events: list[dict] = []
    for c in sorted(creatures, key=creature_sort_key):
        if not c.alive or c.id in death_causes:
            continue
        award_adapt(c, "survive")
        crng = creature_rng(state.match_seed, tick_no, c.id)
        # B-13: con nào có model thì CHÍNH NÓ quyết hướng dịch, và nếu nó chưa
        # trả lời (hoặc trả lời sai) thì lượt ấy **bỏ**, không rơi về giàn giáo
        # W-12. Rơi về thì hai chuyện xảy ra cùng lúc: câu trả lời sai vẫn được
        # đổi cơ thể (trái bất biến 1 của phiếu), và số liệu B-13 — vốn để đo
        # chữ ký hành vi của model — trộn lẫn với luật if-else của W-12.
        take = getattr(strat, "take_shift", None)
        owns = take is not None and c.id in getattr(strat, "slots", {})
        if owns:
            choice = take(c) if c.adapt_points >= 1 else None
            shifted = maybe_shift(c, crng, choice=choice) if choice else None
        else:
            shifted = maybe_shift(c, crng)
            choice = None
        if shifted is not None:
            frm, to = shifted
            shift_events.append({
                "creature_id": c.id,
                "species_id": c.species,
                "frm": frm,
                "to": to,
                "ok": True,
                "by": "llm" if choice is not None else "reflex",
                "why": getattr(strat, "shift_why", {}).pop(c.id, None),
                "traits": list(astuple(c.traits)),
            })

    # 4. LUẬT ẨN — thu hết (cá thể, hệ quả) rồi mới áp dụng, giữ tính đồng thời của W-11.
    law_events: list[dict] = []
    _minds = getattr(strat, "minds", None)
    # Linh cảm (B-14) cần chính bộ `LawEvent` mà pha này dựng, nên pha phải chạy
    # cả khi KHÔNG có luật nào. Và ca ấy không phải ca hiếm — nó là `WORLD_FLAT`,
    # nhánh đối chứng của X-02. Ở đó mọi linh cảm đều `đúng 0 / thử N`, và đó là
    # thông tin thật: thế giới ấy không có gì để tìm. Bỏ qua pha này khi
    # `laws` rỗng thì `WORLD_FLAT` cho ra bảng đếm TRỐNG, trông y hệt "chưa thử"
    # thay vì "đã thử và không có gì".
    _hunch_on = _minds is not None and getattr(_minds, "hunch_enabled", False)
    if laws or _hunch_on:
        ate = {e["creature_id"] for e in eat_events}
        drank = {e["creature_id"] for e in drink_events}
        attacked = {a.attacker_id for a in attacks}
        was_hit = {a.defender_id for a in attacks}
        rested = {it.creature_id for it in intents if not it.path}
        moved_to = {it.creature_id: (it.path[-1] if it.path else None) for it in intents}

        pairs: list[tuple[Creature, LawEvent]] = []
        rest_k: list[tuple[Creature, int]] = []
        for c in sorted(creatures, key=creature_sort_key):
            if not c.alive or c.id in death_causes:
                continue
            did = state.last_did.setdefault(c.id, {})
            fired: list[tuple[TriggerKind, str | None]] = []
            if c.id in ate:
                fired.append((TriggerKind.EAT, next(
                    (e.get("fruit_class") for e in eat_events if e["creature_id"] == c.id), None)))
            if c.id in drank:
                fired.append((TriggerKind.DRINK, None))
            # Phải phát ĐÚNG quan hệ loài. Phát "ANY" thì luật đòi OTHER_SP không bao
            # giờ khớp, và luật đó thành không giải được mà không có gì báo.
            for a in attacks:
                if a.attacker_id == c.id:
                    d = creatures_by_id.get(a.defender_id)
                    rel = "SAME_SP" if d is not None and d.species == c.species else "OTHER_SP"
                    fired.append((TriggerKind.ATTACK, rel))
                if a.defender_id == c.id:
                    at = creatures_by_id.get(a.attacker_id)
                    rel = "SAME_SP" if at is not None and at.species == c.species else "OTHER_SP"
                    fired.append((TriggerKind.HIT_BY, rel))
            # REST phải kèm SỐ LƯỢT đứng yên liên tiếp: trigger_matches so `ev.k >= t.k`.
            # Phát k=None thì mọi luật REST(k) không bao giờ khớp — im lặng không giải được.
            if any(e["creature_id"] == c.id for e in speak_events):
                sig = next(e["signal"] for e in speak_events if e["creature_id"] == c.id)
                fired.append((TriggerKind.SPEAK, sig))
            if c.id in rested:
                state.rest_streak[c.id] = state.rest_streak.get(c.id, 0) + 1
                rest_k.append((c, state.rest_streak[c.id]))
            else:
                state.rest_streak[c.id] = 0
            if moved_to.get(c.id) is not None:
                wx, wy = world.wrap(*c.pos)
                fired.append((TriggerKind.STEP_ON, str(world.grid[wy][wx])))
            if c.energy < 0.25 * c.traits.energy_max:
                fired.append((TriggerKind.LOW_ENERGY, None))
            if tick_no % law_config.PHASE_LEN == 0:
                fired.append((TriggerKind.PHASE_ENTER, phase_at(tick_no)))

            recent = {k: tick_no - v for k, v in did.items()}
            ctx = build_ctx(c, world, tick_no, creatures, recent)
            # ADJACENT: phát kèm SỐ ĐẾM thật để trigger_matches so `ev.n >= t.n`.
            # Không phát thì mọi luật hợp tác (§6.3) không bao giờ kích hoạt.
            for cls in ("SAME_SP", "OTHER_SP", "ANY"):
                cnt = ctx.counts[cls][1]
                if cnt >= 1:
                    pairs.append((c, LawEvent(kind=TriggerKind.ADJACENT, arg=cls, n=cnt, ctx=ctx)))
            for c2, kk in rest_k:
                if c2 is c:
                    did["REST"] = tick_no
                    pairs.append((c, LawEvent(kind=TriggerKind.REST, k=kk, ctx=ctx)))
            for kind, arg in fired:
                did[kind.value] = tick_no
                pairs.append((c, LawEvent(kind=kind, arg=arg, ctx=ctx)))

        crng = creature_rng(state.match_seed, tick_no, "LAW")
        # Cái gì THẬT SỰ giáng xuống từng con trong tick này. Linh cảm (B-14)
        # được chấm trên tập này chứ không trên hệ quả của riêng luật nó đoán —
        # nên bảng đếm có nhiễu, và đó đúng là sự lẫn lộn nhân quả mà một nhà
        # khoa học thật phải gỡ.
        happened: dict[str, set] = {}
        for c, eff, law_idx in collect_law_effects(list(laws or ()), pairs):
            name = apply_creature_effect(c, eff, crng, world)
            if name is not None:
                happened.setdefault(c.id, set()).add(eff.kind)
                law_events.append({
                    "creature_id": c.id, "species_id": c.species,
                    "law_id": f"L{law_idx}", "effect": name, "pos": list(c.pos),
                })

        # Đếm linh cảm SAU khi đã áp xong hết hệ quả, không phải trong lúc áp:
        # đếm giữa chừng thì con duyệt trước thấy một thế giới khác con duyệt
        # sau, và đó là đúng thứ tính đồng thời mà W-11 dựng cả pha 4 để giữ.
        if _hunch_on:
            for c, ev in pairs:
                hb = _minds.hunches.get(c.id)
                if hb is not None:
                    hb.observe(ev, frozenset(happened.get(c.id, ())))

    # 5. CHẾT / HỒI SINH: hp<=0 -> kill(cause) ; reset_body(c) ; try_respawn
    deaths_by_cause: dict[str, int] = {}
    death_events: list[dict] = []
    for c in sorted(creatures, key=creature_sort_key):
        cause = death_causes.get(c.id)
        if cause is not None:
            kill(c, world, tick_no, cause)
            # Chết là TRUYỀN LẠI, không phải về nguyên trạng (W-17).
            #
            # `reset_body` kéo mọi con về vector khai sinh, và đo được là nó xoá
            # **63/83 lần dịch trait (76%)** trong một ván 200 tick — cơ chế
            # thích nghi của W-12 chạy đúng mà không tích luỹ được gì.
            #
            # Cờ tắt được vì phải có nhánh đối chứng: không so với hành vi cũ
            # thì không biết cơ chế này thêm được gì hay chỉ làm mọi thứ ồn hơn.
            if config.LINEAGE_ENABLED:
                crng_birth = creature_rng(state.match_seed, tick_no, c.id)
                truoc = rebirth(c, cause, crng_birth)
            else:
                truoc = c.traits
                reset_body(c)
            c.ticks_alive_streak = 0
            state.active_goals.pop(c.id, None)
            deaths_by_cause[cause] = deaths_by_cause.get(cause, 0) + 1
            death_events.append({
                "creature_id": c.id,
                "species_id": c.species,
                "age": c.age,
                "pos": list(c.pos),
                "cause": cause,
                # Đời sau và vector trước/sau: nhánh phân tích đọc chính hai
                # trường này để đo trôi dạt, nên chúng phải ở trong log chứ
                # không dựng lại được từ ngoài.
                "generation": c.generation,
                "traits_before": [getattr(truoc, n) for n in config.TRAIT_NAMES],
                "traits_after": [getattr(c.traits, n) for n in config.TRAIT_NAMES],
            })

    respawn_events: list[dict] = []
    for c in sorted(creatures, key=creature_sort_key):
        crng = creature_rng(state.match_seed, tick_no, c.id)
        if try_respawn(c, world, tick_no, crng):
            respawn_events.append({
                "creature_id": c.id,
                "species_id": c.species,
                "pos": list(c.pos),
            })

    # 6. THẾ GIỚI: spawn_plants, decay_corpses | rồi GHI LOG một chỗ duy nhất
    spawn_plants(world, rng, tick_no)
    decay_corpses(world, tick_no)

    observe = getattr(strat, "observe", None)
    if observe is not None:
        # Sổ tay phải biết con vật ĐÃ ĐI hay ĐỨNG YÊN. Bản đầu suy ra bằng "không
        # ăn, không uống, không bị đánh thì coi như đứng yên" — nên mọi dòng ghi
        # "TÔI đứng yên" kể cả lúc nó vừa chạy 2 ô, và `STEP_ON` là một trigger
        # THẬT trong DSL: ghi sai chỗ đó là dạy agent một thế giới không có thật.
        move_events = [
            {"creature_id": it.creature_id, "moved": bool(it.path)}
            for it in intents
        ]
        observe(tick_no, world, creatures, {
            "eat": eat_events, "drink": drink_events, "attack": attack_events,
            "law": law_events, "death": death_events, "move": move_events,
            "speak": speak_events,
        }, state)

    if log is not None:
        if tick_no % law_config.PHASE_LEN == 0:
            log.write(tick_no, "PHASE_CHANGE", phase=phase_at(tick_no))
        for drk_ev in drink_events:
            log.write(tick_no, "DRINK", **drk_ev)
        for sp_ev in speak_events:
            log.write(tick_no, "SPEAK", **sp_ev)
        for att_ev in attack_events:
            log.write(tick_no, "ATTACK", **att_ev)
        for eat_ev in eat_events:
            log.write(tick_no, "EAT", **{k: v for k, v in eat_ev.items() if k != "fruit_class"})
        for lw_ev in law_events:
            log.write(tick_no, "LAW_FIRED", **lw_ev)
        for shift_ev in shift_events:
            log.write(tick_no, "TRAIT_SHIFT", **shift_ev)
        for death_ev in death_events:
            log.write(tick_no, "DEATH", **death_ev)
        for respawn_ev in respawn_events:
            log.write(tick_no, "RESPAWN", **respawn_ev)

        alive_count = sum(1 for c in creatures if c.alive)
        goals_count: dict[str, int] = {}
        for c in sorted(creatures, key=creature_sort_key):
            if c.alive and c.id in state.active_goals:
                goal_name = state.active_goals[c.id].goal.value
                goals_count[goal_name] = goals_count.get(goal_name, 0) + 1

        log.write(
            tick_no,
            "TICK",
            alive=alive_count,
            goals=goals_count,
            deaths_by_cause=deaths_by_cause,
        )
