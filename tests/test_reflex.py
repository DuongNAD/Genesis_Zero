"""Genesis Zero — kiểm thử cho tầng phản xạ (W-09)."""

from __future__ import annotations

import collections
import inspect
import json
import random
from pathlib import Path

import genesis.reflex as R
from genesis import config
from genesis.creature import Creature
from genesis.reflex import (
    GOAL_TTL_MAX,
    GOAL_TTL_MIN,
    HP_LOW_RATIO,
    ActiveGoal,
    Goal,
    Intent,
    apply_intent,
    choose_goal,
    reflex_step,
)
from genesis.run import main
from genesis.traits import founder_traits
from genesis.world import Terrain, World, visible


def _mk_creature(
    cid: str,
    species: str,
    pos: tuple[int, int],
    hp: float | None = None,
    energy: float | None = None,
    alive: bool = True,
) -> Creature:
    traits = founder_traits(species)
    return Creature(
        id=cid,
        species=species,
        traits=traits,
        pos=pos,
        hp=float(config.HP_MAX if hp is None else hp),
        energy=traits.energy_max if energy is None else energy,
        alive=alive,
    )


def test_no_codex_in_reflex_module() -> None:
    """B2: Tầng phản xạ không bao giờ đọc Sổ Luật (không chứa chữ codex)."""
    assert "codex" not in inspect.getsource(R).lower()


def test_acceptance_criteria_and_invariants() -> None:
    """Kiểm tra toàn bộ khẳng định trong kịch bản nghiệm thu của phiếu việc."""
    w = World(24, 24, random.Random(1))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN

    # B1: reflex_step KHÔNG sửa gì
    c = _mk_creature("L1:0", "L1", (5, 5))
    w.plants.clear()
    w.plants[(8, 5)] = "FRUIT_A"
    snap = (c.pos, c.energy, dict(w.plants))
    it = reflex_step(c, w, [c], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    assert isinstance(it, Intent) and (c.pos, c.energy, dict(w.plants)) == snap
    assert len(it.path) <= c.traits.moves_per_tick and it.attack_id is None
    assert w.dist(it.path[-1], (8, 5)) < w.dist((5, 5), (8, 5))  # tiến về phía cây

    # FLEE: máu thấp + kẻ mạnh hơn trong tầm
    weak = _mk_creature("L3:0", "L3", (5, 5), hp=config.HP_MAX * 0.2)  # dmg 7
    strong = _mk_creature("L2:0", "L2", (7, 5))                         # dmg 16
    g = choose_goal(weak, w, visible(weak, w, [weak, strong]), random.Random(1))
    assert g.goal == Goal.FLEE and g.target == "L2:0", g
    it = reflex_step(weak, w, [weak, strong], g, random.Random(1))
    assert w.dist(it.path[-1], strong.pos) > w.dist(weak.pos, strong.pos)  # chạy XA ra

    # FORAGE khi đói
    hungry = _mk_creature("L1:0", "L1", (5, 5), energy=founder_traits("L1").energy_max * 0.2)
    assert choose_goal(hungry, w, [], random.Random(1)).goal == Goal.FORAGE

    # REST đứng yên
    full = _mk_creature("L1:0", "L1", (5, 5))
    it = reflex_step(full, w, [full], ActiveGoal(Goal.REST, None, 5), random.Random(1))
    assert it.path == ()

    # B9: goal ngoài GOALS_BY_BRAIN -> WANDER. L5 brain=0 không có GUARD/REST/FOLLOW
    l5 = _mk_creature("L5:0", "L5", (5, 5))
    allowed = set(config.GOALS_BY_BRAIN[l5.traits.brain])
    assert "GUARD" not in allowed
    for seed in range(40):
        assert choose_goal(l5, w, [], random.Random(seed)).goal in allowed

    # B3/B4: tất định và độc lập thứ tự list
    a, b = _mk_creature("L1:0", "L1", (5, 5)), _mk_creature("L4:0", "L4", (6, 6))
    g2 = ActiveGoal(Goal.WANDER, None, 5)
    assert reflex_step(a, w, [a, b], g2, random.Random(7)) == reflex_step(a, w, [b, a], g2, random.Random(7))


def test_choose_goal_priority_order() -> None:
    """Kiểm tra thứ tự ưu tiên 5 bậc của choose_goal."""
    w = World(24, 24, random.Random(1))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN

    # 1. FLEE ưu tiên cao nhất ngay cả khi đang đói (hp < 30% và energy < 40%)
    c = _mk_creature(
        "L3:0",
        "L3",
        (5, 5),
        hp=config.HP_MAX * (HP_LOW_RATIO - 0.05),
        energy=founder_traits("L3").energy_max * 0.2,
    )
    predator = _mk_creature("L1:0", "L1", (6, 5))  # L1 damage 13 > L3 damage 7
    seen = [predator]
    g = choose_goal(c, w, seen, random.Random(42))
    assert g.goal == Goal.FLEE
    assert g.target == predator.id
    assert GOAL_TTL_MIN <= g.ttl <= GOAL_TTL_MAX

    # 2. FORAGE khi energy < 40% energy_max (và không có nguy hiểm máu thấp)
    c.hp = float(config.HP_MAX)
    g = choose_goal(c, w, seen, random.Random(42))
    assert g.goal == Goal.FORAGE
    assert g.target is None

    # 3. HUNT khi energy > 80% energy_max và có con khác loài yếu hơn
    prey = _mk_creature("L4:0", "L4", (6, 5))  # L4 damage 7
    l2 = _mk_creature("L2:0", "L2", (5, 5), energy=founder_traits("L2").energy_max)
    g = choose_goal(l2, w, [prey], random.Random(42))
    assert g.goal == Goal.HUNT
    assert g.target == prey.id

    # 4. REST khi energy > 80% energy_max nhưng không có con yếu hơn
    g_no_prey = choose_goal(l2, w, [], random.Random(42))
    assert g_no_prey.goal == Goal.REST
    assert g_no_prey.target is None

    # 5. Chưa no thì luôn là FORAGE — không còn dải chết rơi vào WANDER
    c_mid = _mk_creature("L1:0", "L1", (5, 5), energy=founder_traits("L1").energy_max * 0.6)
    assert choose_goal(c_mid, w, [], random.Random(42)).goal == Goal.FORAGE
    # WANDER chỉ còn xuất hiện khi goal chọn ra không nằm trong GOALS_BY_BRAIN,
    # ví dụ L5 (brain 0) đã no, không có mồi -> REST không hợp lệ -> WANDER
    l5_full = _mk_creature("L5:0", "L5", (5, 5))
    assert "REST" not in config.GOALS_BY_BRAIN[l5_full.traits.brain]
    assert choose_goal(l5_full, w, [], random.Random(42)).goal == Goal.WANDER


def test_choose_goal_multiple_targets_tie_breaking() -> None:
    """Khi có nhiều kẻ thù / con mồi, chọn con gần nhất, phá hoà bằng creature_sort_key."""
    w = World(24, 24, random.Random(1))
    c = _mk_creature("L3:0", "L3", (10, 10), hp=config.HP_MAX * 0.2)  # dmg 7

    # Kẻ thù 1 ở xa (dist 3), Kẻ thù 2 ở gần (dist 1)
    s1 = _mk_creature("L1:0", "L1", (13, 10))  # dist 3
    s2 = _mk_creature("L2:0", "L2", (11, 10))  # dist 1
    g = choose_goal(c, w, [s1, s2], random.Random(1))
    assert g.goal == Goal.FLEE
    assert g.target == "L2:0"

    # Cùng khoảng cách: phá hoà bằng creature_sort_key
    s3 = _mk_creature("L1:1", "L1", (11, 10))  # dist 1
    # creature_sort_key("L1:1") < creature_sort_key("L2:0")
    g2 = choose_goal(c, w, [s2, s3], random.Random(1))
    assert g2.target == "L1:1"


def test_reflex_step_forage_behavior() -> None:
    """FORAGE: đi về cây gần nhất, không có cây thì WANDER, đến nơi thì dừng."""
    w = World(24, 24, random.Random(1))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN

    c = _mk_creature("L1:0", "L1", (5, 5))  # sight_radius = 3, moves_per_tick = 2
    w.plants[(7, 5)] = "FRUIT_A"  # dist 2
    w.plants[(8, 5)] = "FRUIT_A"  # dist 3

    # Đi về cây gần nhất (7, 5): bước 1 tới (6, 4) do phá hoà toạ độ, bước 2 tới (7, 5)
    it = reflex_step(c, w, [c], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    assert it.path == ((6, 4), (7, 5))
    assert w.dist(it.path[-1], (7, 5)) == 0

    # Khi đã đứng tại ô có cây -> path rỗng
    c.pos = (7, 5)
    it_at_plant = reflex_step(c, w, [c], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    assert it_at_plant.path == ()

    # Không có cây trong tầm nhìn -> WANDER
    w.plants.clear()
    w.plants[(20, 20)] = "FRUIT_A"  # dist > 3
    it_wander = reflex_step(c, w, [c], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    assert len(it_wander.path) == c.traits.moves_per_tick
    assert w.passable(it_wander.path[-1])


def test_reflex_step_hunt_and_flee() -> None:
    """HUNT tiến về con mồi, FLEE chạy xa kẻ địch, fallback nếu target biến mất."""
    w = World(24, 24, random.Random(1))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN

    hunter = _mk_creature("L2:0", "L2", (5, 5))   # moves = 1
    prey = _mk_creature("L3:0", "L3", (8, 5))     # moves = 2

    # HUNT: hunter tiến về phía prey
    it_hunt = reflex_step(hunter, w, [hunter, prey], ActiveGoal(Goal.HUNT, prey.id, 5), random.Random(1))
    assert it_hunt.path == ((6, 4),)
    assert w.dist(it_hunt.path[-1], prey.pos) < w.dist(hunter.pos, prey.pos)

    # FLEE: prey chạy xa hunter
    it_flee = reflex_step(prey, w, [hunter, prey], ActiveGoal(Goal.FLEE, hunter.id, 5), random.Random(1))
    assert w.dist(it_flee.path[-1], hunter.pos) > w.dist(prey.pos, hunter.pos)

    # Fallback khi target đã chết
    prey.alive = False
    it_fallback = reflex_step(hunter, w, [hunter, prey], ActiveGoal(Goal.HUNT, prey.id, 5), random.Random(1))
    assert len(it_fallback.path) == hunter.traits.moves_per_tick


def test_reflex_step_follow() -> None:
    """FOLLOW tiến về con cùng loài gần nhất trong tầm nhìn."""
    w = World(24, 24, random.Random(1))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN

    c1 = _mk_creature("L1:0", "L1", (5, 5))  # sight_radius = 3, moves_per_tick = 2
    c2 = _mk_creature("L1:1", "L1", (7, 5))  # cùng loài, dist 2
    c_other = _mk_creature("L2:0", "L2", (6, 5))  # khác loài, dist 1

    it_follow = reflex_step(c1, w, [c1, c2, c_other], ActiveGoal(Goal.FOLLOW, None, 5), random.Random(1))
    assert it_follow.path == ((6, 4), (7, 5))  # tiến về phía (7, 5) của c2

    # Không có con cùng loài -> WANDER
    it_no_friend = reflex_step(c1, w, [c1, c_other], ActiveGoal(Goal.FOLLOW, None, 5), random.Random(1))
    assert len(it_no_friend.path) == c1.traits.moves_per_tick


def test_apply_intent_execution() -> None:
    """apply_intent di chuyển sinh vật, trừ COST_MOVE, dừng nếu gặp ROCK."""
    w = World(10, 10, random.Random(1))
    for y in range(10):
        for x in range(10):
            w.grid[y][x] = Terrain.PLAIN
    w.grid[7][5] = Terrain.ROCK  # Ô (5, 7) có x=5, y=7 là ROCK

    c = _mk_creature("L1:0", "L1", (5, 5), energy=50.0)
    by_id = {c.id: c}

    # Đi 2 ô: ô (5, 6) passable, ô (5, 7) là ROCK -> chỉ đi 1 ô
    intent = Intent(creature_id=c.id, path=((5, 6), (5, 7)))
    steps = apply_intent(intent, by_id, w)
    assert steps == 1
    assert c.pos == (5, 6)
    assert c.energy == 50.0 - config.COST_MOVE

    # Con chết thì không đi
    c.alive = False
    intent_dead = Intent(creature_id=c.id, path=((5, 5),))
    assert apply_intent(intent_dead, by_id, w) == 0


def test_full_run_cli_goals_in_log(tmp_path: Path) -> None:
    """Chạy cli đầy đủ kiểm tra log TICK có chứa trường goals."""
    out_file = tmp_path / "w09.jsonl"
    main(["--seed", "33", "--ticks", "400", "--no-render", "--out", str(out_file)])

    rows = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    g: collections.Counter = collections.Counter()
    for r in rows:
        if r["kind"] == "TICK" and r.get("goals"):
            g.update(r["goals"])

    # Tiêu chí của phiếu W-09: đói thì đi ăn, KHÔNG lang thang vô định.
    # Bản đầu nới thành "> 0" cho cả hai — nới tiêu chí thì test hết tác dụng.
    assert g["FORAGE"] > g["WANDER"], dict(g)
    assert sum(g.values()) > 0
