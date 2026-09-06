"""Genesis Zero — tests/test_domain_passability.py: Kiểm thử toàn diện tính hợp lệ về địa hình theo tầng sinh thái.

Kiểm tra:
1. `try_respawn()`: Sinh vật nước chỉ hồi sinh ở ô nước, sinh vật cạn ở ô cạn, chim ở ô hợp lệ.
2. `random_step()`: Bước đi ngẫu nhiên tôn trọng tuyệt đối miền địa hình của từng loài/tầng.
3. `EffectKind.TELEPORT`: Dịch chuyển tức thời không bao giờ ném cá lên cạn hay ném thú xuống biển sâu.
4. `net.match.MatchRunner`: Khởi tạo và thả loài đăng ký qua mạng vào đúng ô passable theo loài/đặc điểm.
5. Canh chừng tĩnh: Không có lời gọi `world.passable(` trần (thiếu creature) trong `creature.py`, `lawhook.py`, `match.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from genesis import config
from genesis.creature import Creature, kill, random_step, try_respawn
from genesis.domain import Domain, domain_of
from genesis.lawdsl import Effect, EffectKind, Mag
from genesis.lawhook import apply_creature_effect
from genesis.tick import build_match
from genesis.traits import Traits, founder_traits
from genesis.world import Terrain
from net.match import MatchRunner, Registration


def _make_creature(species: str, pos: tuple[int, int] = (0, 0), traits: Traits | None = None) -> Creature:
    tr = traits if traits is not None else founder_traits(species)
    return Creature(
        id=f"{species}:0",
        species=species,
        traits=tr,
        pos=pos,
        hp=float(config.HP_MAX),
        energy=tr.energy_max,
    )


def test_static_guard_no_naked_passable_calls() -> None:
    """Canh chừng tĩnh: world.passable( PHẢI nhận creature trong creature.py, lawhook.py, match.py."""
    root = Path(__file__).resolve().parent.parent
    targets = [
        root / "genesis" / "creature.py",
        root / "genesis" / "lawhook.py",
        root / "net" / "match.py",
    ]
    for target in targets:
        src = target.read_text(encoding="utf-8")
        lines = [
            ln for ln in src.splitlines()
            if not ln.strip().startswith("#") and "def passable(" not in ln
        ]
        for idx, line in enumerate(lines, 1):
            if "world.passable(" in line:
                # Phải truyền c, creature, mau, who, sample, hoặc một đối số thứ hai
                has_creature_arg = any(
                    token in line
                    for token in (", c)", ", creature", ", mau)", ", who)", ", sample)", ", c,")
                )
                assert has_creature_arg, (
                    f"{target.name}:{idx} gọi world.passable không truyền sinh vật: {line.strip()}"
                )


@pytest.mark.parametrize("map_name", ("DONG_CO", "QUAN_DAO", "HOANG_MAC", "RUNG_RAM", "HEM_NUI"))
def test_respawn_respects_creature_domain(map_name: str) -> None:
    """Sinh vật chết và hồi sinh PHẢI rơi vào đúng ô passable của loài nó."""
    world, _, _, rng = build_match(seed=42, map_name=map_name)

    # Thử trên các loài đại diện 3 tầng: W1 (Nước), L1/L5 (Cạn), A1 (Trời)
    for sp in ("W1", "L1", "L5", "A1"):
        c = _make_creature(sp)
        # Giả lập chết
        kill(c, world, tick=10, cause="test")
        assert not c.alive
        assert c.dead_until == 10 + config.RESPAWN_DELAY

        # Thử respawn khi chưa hết hạn
        assert not try_respawn(c, world, tick=10 + config.RESPAWN_DELAY - 1, rng=rng)
        assert not c.alive

        # Hồi sinh thành công khi đến hạn (nếu bản đồ có ô sống cho loài đó)
        has_living_cells = any(
            world.passable((x, y), c)
            for y in range(world.h)
            for x in range(world.w)
        )
        respawned = try_respawn(c, world, tick=10 + config.RESPAWN_DELAY, rng=rng)
        if has_living_cells:
            assert respawned is True
            assert c.alive is True
            assert world.passable(c.pos, c) is True
            terrain = world.grid[c.pos[1]][c.pos[0]]
            if domain_of(sp) is Domain.NUOC:
                assert terrain in (Terrain.WATER, Terrain.DEEP), (
                    f"Cá W1 hồi sinh ở ô không phải nước: {terrain} tại {c.pos}"
                )
            elif domain_of(sp) is Domain.CAN and not (world.kits.get(sp) and Domain.NUOC in getattr(world.kits[sp], "extra_domains", ())):
                assert terrain != Terrain.DEEP, (
                    f"Thú cạn {sp} hồi sinh ở biển sâu: {terrain} tại {c.pos}"
                )


def test_random_step_respects_domain() -> None:
    """random_step chỉ di chuyển qua các ô passable với con vật đó."""
    world, _, _, rng = build_match(seed=101, map_name="QUAN_DAO")

    # 1. Thử cá W1: tìm ô nước có hàng xóm và cho nó đi ngẫu nhiên 50 bước
    water_cells = [
        (x, y) for y in range(world.h) for x in range(world.w)
        if world.grid[y][x] in (Terrain.WATER, Terrain.DEEP)
    ]
    assert water_cells, "QUAN_DAO phải có nước"
    fish = _make_creature("W1", pos=water_cells[0])
    for _ in range(50):
        fish.energy = 100.0  # giữ năng lượng không hết
        random_step(fish, world, rng)
        assert world.passable(fish.pos, fish) is True
        assert world.grid[fish.pos[1]][fish.pos[0]] in (Terrain.WATER, Terrain.DEEP)

    # 2. Thử thú cạn L2
    plain_cells = [
        (x, y) for y in range(world.h) for x in range(world.w)
        if world.grid[y][x] == Terrain.PLAIN
    ]
    assert plain_cells, "QUAN_DAO phải có đất liền"
    beast = _make_creature("L2", pos=plain_cells[0])
    for _ in range(50):
        beast.energy = 100.0
        random_step(beast, world, rng)
        assert world.passable(beast.pos, beast) is True


def test_teleport_effect_respects_domain() -> None:
    """Hiệu ứng TELEPORT của luật ẩn chỉ dịch chuyển sinh vật tới ô passable của nó."""
    world, _, _, rng = build_match(seed=202, map_name="QUAN_DAO")
    teleport_effect = Effect(kind=EffectKind.TELEPORT, mag=Mag.SMALL, r=5)

    # Thử trên cá
    water_cells = [
        (x, y) for y in range(world.h) for x in range(world.w)
        if world.grid[y][x] in (Terrain.WATER, Terrain.DEEP)
    ]
    fish = _make_creature("W1", pos=water_cells[0])
    for _ in range(30):
        applied = apply_creature_effect(fish, teleport_effect, rng, world)
        assert applied == "TELEPORT"
        assert world.passable(fish.pos, fish) is True
        assert world.grid[fish.pos[1]][fish.pos[0]] in (Terrain.WATER, Terrain.DEEP)

    # Thử trên thú cạn
    plain_cells = [
        (x, y) for y in range(world.h) for x in range(world.w)
        if world.grid[y][x] == Terrain.PLAIN
    ]
    beast = _make_creature("L1", pos=plain_cells[0])
    for _ in range(30):
        applied = apply_creature_effect(beast, teleport_effect, rng, world)
        assert applied == "TELEPORT"
        assert world.passable(beast.pos, beast) is True


def test_match_runner_spawn_registered_respects_domain() -> None:
    """MatchRunner._spawn_registered phải đặt sinh vật đăng ký vào ô hợp lệ theo tầng."""
    runner = MatchRunner(seed=303, log_dir=None)

    # Đăng ký cá người chơi (W1 thuộc tầng NUOC)
    reg_fish = Registration(
        client_id="client_fish",
        token="tok_1",
        species_id="W1",
        display_name="Player Fish",
        persona="Cá bơi lội",
        league="OPEN",
        brain_tier=2,
        pop=3,
        traits=founder_traits("W1"),
    )
    # Đăng ký chim người chơi
    reg_bird = Registration(
        client_id="client_bird",
        token="tok_2",
        species_id="A1",
        display_name="Player Bird",
        persona="Chim bay lượn",
        league="OPEN",
        brain_tier=2,
        pop=3,
        traits=founder_traits("A1"),
    )
    # Đăng ký thú cạn người chơi
    reg_land = Registration(
        client_id="client_land",
        token="tok_3",
        species_id="L1",
        display_name="Player Beast",
        persona="Thú chạy bộ",
        league="OPEN",
        brain_tier=2,
        pop=3,
        traits=founder_traits("L1"),
    )

    runner.registrations = {
        "client_fish": reg_fish,
        "client_bird": reg_bird,
        "client_land": reg_land,
    }

    # Chuyển pha LOBBY -> SEEDING sẽ gọi _seed_match() và _spawn_registered()
    runner.advance_phase()

    # Kiểm tra tất cả các cá được sinh ra trên bản đồ
    fish_creatures = [c for c in runner.creatures if c.species == "W1"]
    bird_creatures = [c for c in runner.creatures if c.species == "A1"]
    land_creatures = [c for c in runner.creatures if c.species == "L1"]

    assert len(fish_creatures) >= 3
    assert len(bird_creatures) >= 2
    assert len(land_creatures) >= 2

    for fc in fish_creatures:
        assert runner.world.passable(fc.pos, fc) is True
        assert runner.world.grid[fc.pos[1]][fc.pos[0]] in (Terrain.WATER, Terrain.DEEP)

    for lc in land_creatures:
        assert runner.world.passable(lc.pos, lc) is True

    for bc in bird_creatures:
        assert runner.world.passable(bc.pos, bc) is True
