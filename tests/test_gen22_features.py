"""Tests cho các tính năng nâng cấp Genesis Zero Gen 22:
- Cognitive Schema Guardrail
- Hunch Bayesian Confidence
- 2D Toroidal Pheromone Field & Chemical Ecology
- Phylogenetic Cladogram & Genetic Divergence
- Open Science Dataset Exporter
- Multi-Tenant Arena Gateway
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi.testclient import TestClient

from genesis.hunch import Hunch, HunchBook
from genesis.lawdsl import (
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
)
from genesis.lineage import (
    PhylogeneticCladogram,
    genetic_divergence,
)
from genesis.reveal import law_from_surface_dict
from genesis.surface import roll_surface_map
from genesis.traits import Traits
from genesis.world import World
from net.server import app

# ── 1. Cognitive Schema Guardrail ──────────────────────────────────────────

def test_cognitive_schema_guardrail_auto_completes_mag_and_dur() -> None:
    """Kiểm tra bộ tiền kiểm tự động bù mag=MED và dur=SHORT khi LLM thiếu trường."""
    sm = roll_surface_map(random.Random(42))
    payload = {
        "trigger": {"kind": "DRINK"},
        "conds": [],
        "effect": {"kind": "DAMAGE"},  # Không có mag, dur
    }
    law = law_from_surface_dict(payload, sm)
    assert law.effect.kind == EffectKind.DAMAGE
    assert law.effect.mag == Mag.MED
    assert law.effect.dur in (Dur.SHORT, Dur.INSTANT)


def test_cognitive_schema_guardrail_auto_completes_teleport_radius() -> None:
    """Kiểm tra tự động bù r=1 cho hiệu ứng dịch chuyển."""
    sm = roll_surface_map(random.Random(42))
    payload = {
        "trigger": {"kind": "DRINK"},
        "conds": [],
        "effect": {"kind": "TELEPORT"},  # Không có r
    }
    law = law_from_surface_dict(payload, sm)
    assert law.effect.kind == EffectKind.TELEPORT
    assert law.effect.r == 1


# ── 2. Hunch Bayesian Confidence & Best Hunch ─────────────────────────────

def test_hunch_bayesian_confidence_calculation() -> None:
    """Độ tin cậy Laplace Bayes: (hit + 1) / (tried + 2)."""
    law = Law(Trigger(TriggerKind.DRINK), (), Effect(EffectKind.DAMAGE, Mag.MED, Dur.SHORT))
    h = Hunch(law=law, born_at=10, tried=0, hit=0)
    assert h.confidence == 0.5  # Prior trung tính

    h.tried = 4
    h.hit = 3
    # (3 + 1) / (4 + 2) = 4/6 = 0.6667
    assert round(h.confidence, 4) == 0.6667


def test_hunchbook_best_hunch_selection() -> None:
    """Chọn giả thuyết có niềm tin cao nhất đã được kiểm chứng."""
    hb = HunchBook(size=3)
    l1 = Law(Trigger(TriggerKind.DRINK), (), Effect(EffectKind.DAMAGE, Mag.MED, Dur.SHORT))
    l2 = Law(Trigger(TriggerKind.REST), (), Effect(EffectKind.HEAL, Mag.SMALL, Dur.INSTANT))

    hb.apply("SET", 0, l1, 10)
    hb.apply("SET", 1, l2, 10 + 20)  # law_config.HUNCH_COOLDOWN

    h0 = hb.entries()[0]
    h1 = hb.entries()[1]
    assert h0 is not None and h1 is not None

    h0.tried = 5
    h0.hit = 4  # conf = 5/7 = 0.714
    h1.tried = 5
    h1.hit = 1  # conf = 2/7 = 0.285

    best = hb.best_hunch(min_tried=2)
    assert best is not None
    assert best[0] == h0
    assert best[1] > 0.7


# ── 3. 2D Toroidal Pheromone Field ────────────────────────────────────────

def test_world_pheromone_field_emission_and_diffusion() -> None:
    """Kiểm tra giải phóng pheromone và khuếch tán hình xuyến."""
    rng = random.Random(42)
    world = World(24, 24, rng)

    assert "food" in world.pheromones
    assert "danger" in world.pheromones
    assert "kin" in world.pheromones

    # Ban đầu rỗng
    assert world.sample_pheromone("food", (5, 5)) == 0.0

    # Giải phóng tại (5, 5)
    world.emit_pheromone("food", (5, 5), 2.0)
    assert world.sample_pheromone("food", (5, 5)) == 2.0

    # Chạy một bước khuếch tán
    world.step_pheromones(diffusion=0.1, evaporation=0.05)

    # Ô nguồn giảm
    assert world.sample_pheromone("food", (5, 5)) < 2.0
    # Các ô lân cận nhận được nồng độ khuếch tán
    assert world.sample_pheromone("food", (5, 4)) > 0.0
    assert world.sample_pheromone("food", (5, 6)) > 0.0
    assert world.sample_pheromone("food", (4, 5)) > 0.0
    assert world.sample_pheromone("food", (6, 5)) > 0.0


def test_world_pheromone_gradient_direction() -> None:
    """Kiểm tra vector gradient chỉ hướng về nguồn pheromone cao nhất."""
    rng = random.Random(42)
    world = World(24, 24, rng)

    # Đặt nguồn thức ăn ở (10, 10)
    world.emit_pheromone("food", (10, 10), 5.0)

    # Sinh vật ở (9, 10) phải có gradient hướng về (1, 0)
    grad = world.pheromone_gradient("food", (9, 10))
    assert grad == (1, 0)

    # Sinh vật ở (10, 11) phải có gradient hướng về (0, -1)
    grad = world.pheromone_gradient("food", (10, 11))
    assert grad == (0, -1)


# ── 4. Phylogenetic Cladogram & Genetic Divergence ────────────────────────

def test_genetic_divergence_calculation() -> None:
    """Khoảng cách di truyền chuẩn hóa giữa hai vector traits."""
    t1 = Traits(stomach=2, speed=2, armor=2, attack=2, sense=2, brain=2)
    t2 = Traits(stomach=3, speed=2, armor=1, attack=2, sense=2, brain=2)

    # delta stomach = 1, delta armor = -1 -> dist = sqrt(1 + 1) = 1.4142
    div = genetic_divergence(t1, t2)
    assert div == 1.4142


def test_phylogenetic_cladogram_tracking() -> None:
    """Cây phả hệ ghi nhận sinh sản, tử vong và xuất cấu trúc phân cấp."""
    from genesis.creature import Creature

    clad = PhylogeneticCladogram()
    tr = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    c1 = Creature(id="sp_kien:0", species="kien", traits=tr, pos=(0, 0), hp=100, energy=80)

    # Ghi nhận thế hệ 0
    clad.record_birth("sp_kien:0_gen0", c1, tick=1)

    # Ghi nhận thế hệ 1 (con)
    c1.generation = 1
    clad.record_birth("sp_kien:0_gen1", c1, tick=50, parent_id="sp_kien:0_gen0")

    # Con chết
    clad.record_death("sp_kien:0_gen1", tick=80, cause="starve")

    tree = clad.export_tree()
    assert tree["total_nodes"] == 2
    assert len(tree["roots"]) == 1
    root = tree["roots"][0]
    assert root["id"] == "sp_kien:0_gen0"
    assert len(root["children"]) == 1
    child = root["children"][0]
    assert child["id"] == "sp_kien:0_gen1"
    assert child["cause"] == "starve"
    assert child["died_at"] == 80


# ── 5. Open Science Dataset Exporter ───────────────────────────────────────

def test_export_scientific_dataset(tmp_path: Path) -> None:
    """Kiểm tra xuất file dataset từ log match."""
    from scripts.export_scientific_dataset import parse_and_export_trajectories

    log_file = tmp_path / "sample_match.jsonl"
    out_file = tmp_path / "dataset.jsonl"

    rows = [
        {"kind": "STEP", "t": 1, "creature_id": "c1", "species": "ant", "hp": 100, "energy": 80, "pos": [2, 3], "action": "MOVE"},
        {"kind": "DECIDE", "t": 2, "creature_id": "c1", "species": "ant", "hp": 99, "energy": 78, "goal": "FORAGE"},
        {"kind": "CODEX_OP", "t": 5, "creature_id": "c1", "op": "SET", "slot": 0, "law": {"trigger": {"kind": "DRINK"}}},
    ]
    with log_file.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    meta = parse_and_export_trajectories(log_file, None, out_file, split="test")
    assert meta["exported_records"] == 3
    assert out_file.exists()

    exported = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines()]
    assert len(exported) == 3
    assert exported[0]["creature_id"] == "c1"
    assert exported[0]["dataset_version"] == "2.2.0"


# ── 6. Multi-Tenant Arena Routes ──────────────────────────────────────────

def test_arena_registration_and_leaderboard() -> None:
    """Kiểm tra các endpoint REST của đấu trường multi-tenant."""
    client = TestClient(app)

    # 1. Đăng ký agent A
    res_a = client.post("/v1/arena/register", json={
        "team_name": "DeepMind Explorer",
        "model_name": "Claude-3.7-Thinking",
        "agent_type": "llm",
    })
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["ok"] is True
    agent_id_a = data_a["agent"]["agent_id"]

    # 2. Đăng ký agent B
    res_b = client.post("/v1/arena/register", json={
        "team_name": "Stanford Evolution",
        "model_name": "DeepSeek-R1",
        "agent_type": "llm",
    })
    assert res_b.status_code == 200

    # 3. Lấy leaderboard
    res_lb = client.get("/v1/arena/leaderboard")
    assert res_lb.status_code == 200
    lb = res_lb.json()["leaderboard"]
    assert len(lb) >= 2

    # 4. Lấy matches
    res_m = client.get("/v1/arena/matches")
    assert res_m.status_code == 200
    assert "matches" in res_m.json()
