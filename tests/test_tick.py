"""Genesis Zero — kiểm thử cho genesis/tick.py (W-11)."""

from __future__ import annotations

import collections
import inspect
from pathlib import Path
import random
import subprocess
import sys
import json

import pytest

from genesis import config
from genesis.creature import Creature
from genesis.reflex import Intent
from genesis.run import main
from genesis.tick import SimState, build_match, creature_rng, tick
import genesis.tick as T
from genesis.traits import founder_traits
from genesis.world import World


def test_signature_and_dataclasses() -> None:
    """Chữ ký tick có tham số laws mặc định None và SimState hợp lệ."""
    sig = inspect.signature(tick)
    assert "laws" in sig.parameters
    assert sig.parameters["laws"].default is None

    st = SimState(match_seed=42)
    assert st.match_seed == 42
    assert isinstance(st.active_goals, dict)


def test_build_match_returns_four_elements() -> None:
    """build_match dựng world, creatures, state, rng từ seed."""
    w, cs, st, rng = build_match(seed=99)
    assert isinstance(w, World)
    assert isinstance(cs, list)
    assert len(cs) == sum(config.POPULATION.values())
    assert isinstance(st, SimState)
    assert st.match_seed == 99
    assert isinstance(rng, random.Random)


def test_creature_rng_determinism_across_processes() -> None:
    """creature_rng tất định giữa các tiến trình qua md5."""
    cmd = [
        sys.executable,
        "-c",
        "from genesis.tick import creature_rng; print(creature_rng(1, 2, 'L1:0').random())",
    ]
    out = [
        subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
        for _ in range(3)
    ]
    assert len(set(out)) == 1, out


def test_list_permutation_invariance() -> None:
    """B2 & Bài kiểm tra quan trọng nhất: Hoán vị list -> kết quả Y HỆT."""
    def run(shuffle_seed: int | None = None, ticks: int = 200) -> list:
        w, cs, st, rng = build_match(seed=99)
        if shuffle_seed is not None:
            random.Random(shuffle_seed).shuffle(cs)
        for t in range(ticks):
            tick(w, cs, t, rng, st)
        return sorted(
            (
                c.id,
                round(c.energy, 6),
                round(c.hp, 6),
                c.pos,
                c.alive,
                c.age,
                c.dead_until,
                c.poison_ticks,
            )
            for c in cs
        )

    base = run(None)
    for s in (1, 5, 42):
        assert run(s) == base, f"THU TU LIST ANH HUONG KET QUA (shuffle seed {s})"


def test_phase1_is_pure() -> None:
    """B1: Pha 1 thu thập intent không sửa bất cứ trạng thái nào của world hay sinh vật."""
    w, cs, st, rng = build_match(seed=7)
    snap = [(c.id, c.pos, c.energy, c.hp) for c in cs]
    intents = T._collect_intents(w, cs, 0, st)
    assert isinstance(intents, list)
    assert all(isinstance(it, Intent) for it in intents)
    assert snap == [(c.id, c.pos, c.energy, c.hp) for c in cs], "pha 1 da sua trang thai"


def test_creatures_grow_mid_match() -> None:
    """B3: Danh sách creatures dài ra giữa ván vẫn chạy bình thường."""
    w, cs, st, rng = build_match(seed=3)
    for t in range(50):
        tick(w, cs, t, rng, st)
    tr = founder_traits("L1")
    cs.append(
        Creature(
            id="NEW:0",
            species="NEW",
            traits=tr,
            pos=(1, 1),
            hp=50.0,
            energy=tr.energy_max,
        )
    )
    for t in range(50, 100):
        tick(w, cs, t, rng, st)
    assert any(c.id == "NEW:0" for c in cs)


def test_acceptance_log_and_event_types(tmp_path: Path) -> None:
    """B6: Log một chỗ duy nhất cuối pha 6, có đủ các sự kiện ATTACK, EAT, DEATH, RESPAWN, TICK."""
    out_file = tmp_path / "w11.jsonl"
    # `--no-laws`: đây là bài kiểm VÒNG TICK (W-11), không phải kiểm một bộ luật ẩn.
    # Từ B-05, `genesis.run` sinh luật theo mặc định, và luật đổi động lực học của
    # ván — seed 44 với luật hiện tại chết đói hết, không con nào chết vì đánh nhau.
    # Ghim thế giới M1 ở đây, còn ảnh hưởng của luật lên cân bằng có bài đo riêng.
    main(["--seed", "44", "--ticks", "400", "--no-render", "--no-laws", "--out", str(out_file)])

    rows = [
        json.loads(line)
        for line in out_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    k = collections.Counter(r["kind"] for r in rows)
    for need in ("TICK", "EAT", "DEATH", "RESPAWN", "ATTACK", "RUN_START", "RUN_END"):
        assert k[need] > 0, (need, dict(k))

    causes = collections.Counter(r.get("cause") for r in rows if r["kind"] == "DEATH")
    assert causes.get("combat", 0) > 0 and causes.get("starve", 0) > 0, causes

    g: collections.Counter = collections.Counter()
    for r in rows:
        if r["kind"] == "TICK" and r.get("goals"):
            g.update(r["goals"])
    assert g["FORAGE"] > g["WANDER"], dict(g)


def test_reproducibility_and_pure_render(tmp_path: Path) -> None:
    """Tái lập + render thuần."""
    t1 = tmp_path / "t1.jsonl"
    t2 = tmp_path / "t2.jsonl"
    t3 = tmp_path / "t3.jsonl"

    main(["--seed", "21", "--ticks", "200", "--no-render", "--out", str(t1)])
    main(["--seed", "21", "--ticks", "200", "--no-render", "--out", str(t2)])
    assert t1.read_bytes() == t2.read_bytes()

    main(["--seed", "21", "--ticks", "200", "--fps", "500", "--out", str(t3)])
    assert t1.read_bytes() == t3.read_bytes()


def test_two_independent_mechanisms_pin_invariance() -> None:
    """Ghim RIÊNG hai cơ chế giữ tính bất biến thứ tự.

    Đo bằng tiến trình riêng cho thấy MỖI cơ chế tự nó đã đủ:
    bỏ sắp xếp mà giữ creature_rng -> vẫn bất biến; ngược lại cũng vậy;
    bỏ cả hai -> vỡ. Vì thế `test_list_permutation_invariance` KHÔNG phân biệt
    được chúng: gỡ một cái đi thì test đó vẫn xanh và ta âm thầm mất lớp dự phòng.
    Hai khẳng định dưới đây ghim từng cơ chế một.
    """
    from genesis.creature import creature_sort_key

    # Cơ chế 1: pha 1 duyệt theo thứ tự chuẩn, bất kể thứ tự list đầu vào
    w, cs, st, _ = build_match(seed=5)
    random.Random(3).shuffle(cs)
    intents = T._collect_intents(w, cs, 0, st)
    by_id = {c.id: c for c in cs}
    keys = [creature_sort_key(by_id[it.creature_id]) for it in intents]
    assert keys == sorted(keys), "pha 1 không còn duyệt theo creature_sort_key"

    # Cơ chế 2: luồng ngẫu nhiên phụ thuộc danh tính con, không phải vị trí trong list
    a = creature_rng(1, 2, "L1:0").random()
    b = creature_rng(1, 2, "L1:1").random()
    c = creature_rng(1, 3, "L1:0").random()
    assert a != b, "creature_rng không phụ thuộc creature_id"
    assert a != c, "creature_rng không phụ thuộc tick"
    assert a == creature_rng(1, 2, "L1:0").random(), "creature_rng không tất định"
