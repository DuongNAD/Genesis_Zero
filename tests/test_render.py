"""Kiểm thử cho genesis/render.py và tích hợp hiển thị."""

from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import random
import subprocess
import sys
import unicodedata

import pytest
from rich.style import Style

from genesis import config
from genesis.creature import Creature, spawn_population
from genesis.traits import founder_traits
from genesis.render import (
    GLYPH_POOL,
    glyph_of,
    hue_of,
    render_frame,
    style_of,
)
import genesis.render as R
from genesis.run import _m0_loop, main, parse
from genesis.world import (
    CORPSE_GLYPH,
    PLANT_GLYPH,
    TERRAIN_GLYPHS,
    Terrain,
    World,
)


def test_glyph_pool_invariants() -> None:
    """B1: Glyph phải rộng đúng 1 ô, không alnum, không trùng ký tự địa hình."""
    assert len(GLYPH_POOL) >= 20
    for ch in GLYPH_POOL:
        assert len(ch) == 1
        assert unicodedata.east_asian_width(ch) not in ("W", "F"), (
            ch,
            unicodedata.name(ch, "?"),
        )
        assert not ch.isalnum(), ch
    taken = set(TERRAIN_GLYPHS.values()) | {PLANT_GLYPH, CORPSE_GLYPH}
    assert not (set(GLYPH_POOL) & taken), set(GLYPH_POOL) & taken


def test_no_random_in_render_module() -> None:
    """B2 & Nghiệm thu 4: render.py không chứa từ khoá ngẫu nhiên."""
    assert "random" not in inspect.getsource(R)


def test_glyph_and_hue_determinism() -> None:
    """B3: Glyph và hue phải tất định hoàn toàn theo md5 giữa các tiến trình."""
    cmd = [
        sys.executable,
        "-c",
        "from genesis.render import glyph_of, hue_of; print(glyph_of('L1'), hue_of('L1'))",
    ]
    out1 = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    out2 = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    assert out1 == out2
    g, h = out1.split()
    assert g == glyph_of("L1")
    assert int(h) == hue_of("L1")
    assert 0 <= hue_of("L1") < 360


def test_style_of_alive_and_dead() -> None:
    """B5: style_of trả về rich style hợp lệ, mờ khi năng lượng thấp hoặc đã chết."""
    traits = founder_traits("L1")
    c_full = Creature(id="L1:0", species="L1", traits=traits, pos=(0, 0), hp=50.0, energy=traits.energy_max)
    c_low = Creature(id="L1:0", species="L1", traits=traits, pos=(0, 0), hp=50.0, energy=10.0)
    c_dead = Creature(id="L1:0", species="L1", traits=traits, pos=(0, 0), hp=0.0, energy=0.0, alive=False)

    s_full = style_of(c_full, c_full.traits.energy_max)
    s_low = style_of(c_low, c_low.traits.energy_max)
    s_dead = style_of(c_dead, c_dead.traits.energy_max)

    # Style parse được bởi Rich
    assert Style.parse(s_full)
    assert Style.parse(s_low)
    assert Style.parse(s_dead)

    # Style con chết có dim
    assert "dim" in s_dead
    assert s_full != s_low


def test_render_frame_is_pure() -> None:
    """B2: render_frame là hàm thuần, không bao giờ sửa trạng thái thế giới hay sinh vật."""
    rng = random.Random(42)
    world = World(config.GRID_W, config.GRID_H, rng)
    world.plants[(1, 1)] = 0
    world.corpses[(2, 2)] = 0
    creatures = spawn_population(world, random.Random(42))

    w_grid_before = copy.deepcopy(world.grid)
    w_plants_before = dict(world.plants)
    w_corpses_before = dict(world.corpses)
    c_states_before = [(c.id, c.pos, c.hp, c.energy, c.age, c.alive, c.dead_until) for c in creatures]

    # Gọi render_frame nhiều lần
    for t in range(5):
        frame = render_frame(world, creatures, t)
        assert frame is not None

    assert world.grid == w_grid_before
    assert world.plants == w_plants_before
    assert world.corpses == w_corpses_before
    c_states_after = [(c.id, c.pos, c.hp, c.energy, c.age, c.alive, c.dead_until) for c in creatures]
    assert c_states_before == c_states_after


def test_m0_loop_on_tick_callback() -> None:
    """on_tick được gọi đúng số tick với các tham số tương ứng."""
    rng = random.Random(7)
    world = World(10, 10, rng)
    creatures = spawn_population(world, random.Random(7))
    ticks_called: list[int] = []

    def cb(w: World, cs: list[Creature], t: int) -> None:
        ticks_called.append(t)

    _m0_loop(world, creatures, None, random.Random(7), 5, on_tick=cb)
    assert ticks_called == [0, 1, 2, 3, 4]


def test_parse_fps_flag() -> None:
    """Cờ --fps được parse đúng với mặc định là 10."""
    args_default = parse(["--seed", "1"])
    assert args_default.fps == 10.0

    args_custom = parse(["--seed", "1", "--fps", "25.5"])
    assert args_custom.fps == 25.5


def test_run_render_vs_no_render_determinism(tmp_path: Path) -> None:
    """Nghiệm thu 2 & 3: chạy có render và không render cho JSONL giống hệt nhau."""
    f_norender = tmp_path / "norender.jsonl"
    f_render = tmp_path / "render.jsonl"

    main(["--seed", "15", "--ticks", "50", "--no-render", "--out", str(f_norender)])
    main(["--seed", "15", "--ticks", "50", "--fps", "200", "--out", str(f_render)])

    assert f_norender.read_bytes() == f_render.read_bytes()


def test_glyphs_are_distinct_across_species() -> None:
    """Glyph tồn tại để PHÂN BIỆT loài — không loài nào được trùng ký tự.

    Hồi quy: bản đầu băm độc lập rồi lấy mod, và md5 của "L1","L2","L3","L5"
    tình cờ cùng dư 12 nên bốn trong năm loài ra cùng ký tự ◍. Trên màn hình
    không cách nào phân biệt chúng.
    """
    from genesis.render import assign_glyphs

    sids = list(config.POPULATION)
    g = assign_glyphs(sids)
    assert set(g) == set(sids)
    assert len(set(g.values())) == len(sids), g          # đôi một khác nhau
    # tất định và độc lập thứ tự đầu vào
    assert assign_glyphs(sids) == assign_glyphs(list(reversed(sids)))
    # tới 30 loài vẫn không đụng
    many = [f"sp{i}" for i in range(len(GLYPH_POOL))]
    assert len(set(assign_glyphs(many).values())) == len(GLYPH_POOL)
