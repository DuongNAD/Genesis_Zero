"""Regression dossier trên MatchRunner thật, không chạy vòng nền hoặc gọi model."""

from dataclasses import astuple

import pytest
from fastapi.testclient import TestClient

from genesis.lawdsl import Dur
from net import server, state
from net.match import MatchRunner, Phase
from net.telemetry import CreatureTelemetry, creature_telemetry, envelope


@pytest.fixture
def dossier_env(monkeypatch):
    runner = MatchRunner(seed=1, ticks=5, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", runner)
    # Không vào lifespan: test tự điều khiển pha/tick, tránh chạy sim song song.
    client = TestClient(server.app)
    yield client, runner
    client.close()


def test_dossier_vong_doi_that(dossier_env):
    client, runner = dossier_env
    assert client.get("/v1/spectate/dossier").json()["creatures"] == []
    runner.advance_phase()
    assert runner.phase is Phase.SEEDING
    for phase in (Phase.SEEDING, Phase.RUNNING):
        if phase is Phase.RUNNING:
            runner.advance_phase()
            runner.step()
            assert runner.tick_no == 1
        assert runner.phase is phase
        response = client.get("/v1/spectate/dossier")
        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == str(phase)
        assert data["creatures"]
        assert len(data["creatures"]) == len(runner.creatures)
        frame = runner.frame(runner.tick_no, [])
        assert all(frame[key] == value for key, value in envelope(runner.match_id).items())
        profiles = {row["id"]: row for row in data["creatures"]}
        for creature in runner.creatures:
            telemetry = creature_telemetry(runner, creature)
            assert set(telemetry) == CreatureTelemetry.__required_keys__
            assert telemetry in frame["creatures"]
            assert telemetry["tr"] == list(astuple(creature.traits))
            assert telemetry["gen"] == creature.generation
            assert telemetry["e_max"] == creature.traits.energy_max
            profile = profiles[creature.id]
            for key in ("id", "species", "domain", "features", "gen", "e_max"):
                assert profile[key] == telemetry[key]
            assert profile["dt_traits"] == telemetry["d_tr"]


def test_dossier_thuoc_tinh_mo_rong(dossier_env):

    client, runner = dossier_env
    runner.advance_phase()                       # -> SEEDING
    data = client.get("/v1/spectate/dossier").json()

    # Danh sách loài và cá thể không rỗng, khớp runner thật.
    assert data["species"] and data["creatures"]
    species_ids = {row["species"] for row in data["species"]}
    assert species_ids == {c.species for c in runner.creatures}

    # Lưu ý trung thực: codex là GIẢ THUYẾT, không phải chân lý đã xác thực.
    for sp in data["species"]:
        assert "founder_traits" in sp and "alive_count" in sp
    for row in data["creatures"]:
        for rule in row["inferred_rules"]:
            assert rule["status"] == "Giả thuyết chưa xác minh"
            assert "law_id" not in rule
        assert "law_id" not in row
    assert "law_id" not in str(data)


def test_dossier_loi_gioi_seeding_khong_ro_luat(dossier_env):
    """Bất biến 5: trước REVEAL, dossier không chứa law_id từ bất kỳ đường nào."""
    client, runner = dossier_env
    runner.advance_phase()                       # -> SEEDING
    runner._laws.clear()                         # đề bài chỉ nội bộ server
    from genesis.lawdsl import Effect, EffectKind, Law, Mag, Trigger, TriggerKind

    runner._laws.extend([
        Law(Trigger(TriggerKind.DRINK), (),
            Effect(EffectKind.ENERGY_GAIN, Mag.BIG, Dur.INSTANT)),
    ])
    data = client.get("/v1/spectate/dossier").json()
    assert "law_id" not in str(data), "bất biến 5: không lộ law_id trước REVEAL"


def test_dossier_founder_traits_rong_khi_traits_none(dossier_env):
    """reg.traits là None (server chưa cấp) -> founder_traits phải là danh sách RỖNG, không bịa."""
    client, runner = dossier_env
    runner.advance_phase()                       # -> SEEDING
    reg = next(iter(runner.registrations.values()), None)
    if reg is None:
        from net.match import Registration

        c = runner.creatures[0]
        reg = Registration(client_id="test", token="t", species_id=c.species,
                           display_name="T", persona="", league="A",
                           brain_tier=3, pop=1, traits=None)
        runner.registrations["test"] = reg
    reg.traits = None
    data = client.get("/v1/spectate/dossier").json()
    sp = next(s for s in data["species"] if s["species"] == reg.species_id)
    assert sp["founder_traits"] == []


@pytest.mark.parametrize("phase", [Phase.SEEDING, Phase.RUNNING])
@pytest.mark.parametrize("confidence", [1, 5])
def test_dossier_codex_entries_va_loc_theo_id(dossier_env, phase, confidence, monkeypatch):
    """Dùng API công khai `Codex.entries()`, và lọc theo creature_id vẫn về đúng cá thể."""
    from genesis.codex import Codex
    from genesis.lawdsl import Effect, EffectKind, Law, Mag, Trigger, TriggerKind

    client, runner = dossier_env
    runner.advance_phase()                       # -> SEEDING
    if phase is Phase.RUNNING:
        runner.advance_phase()
        runner.step()
    assert runner.phase is phase
    c = runner.creatures[0]
    codex = Codex(size=2)  # Ô trống cũng phải được bỏ qua an toàn.
    runner.minds.codices[c.id] = codex
    law = Law(Trigger(TriggerKind.EAT, "FRUIT_A"), (),
              Effect(EffectKind.ENERGY_GAIN, Mag.BIG, Dur.INSTANT))
    assert codex.apply("SET", 0, law, confidence, tick=runner.tick_no).ok
    entries = codex.entries
    calls = []

    def public_entries():
        calls.append(True)
        return entries()

    monkeypatch.setattr(codex, "entries", public_entries)
    data = client.get("/v1/spectate/dossier").json()
    assert calls, "dossier phải đọc qua API công khai Codex.entries()"
    assert runner.laws_public() == []
    assert "law_id" not in str(data)
    row = next(r for r in data["creatures"] if r["id"] == c.id)
    assert row["inferred_rules"], "codex có 1 mục mà dossier không thấy"
    rule = row["inferred_rules"][0]
    from genesis.lawdsl import to_vietnamese

    assert len(row["inferred_rules"]) == 1
    assert rule == {
        "text": to_vietnamese(law, runner.world.surface_map),
        "conf": confidence,
        "written_at": runner.tick_no,
        "source": "self",
        "status": "Giả thuyết chưa xác minh",
    }

    filtered = client.get("/v1/spectate/dossier", params={"creature_id": c.id}).json()
    assert [r["id"] for r in filtered["creatures"]] == [c.id]
    species = client.get("/v1/spectate/dossier", params={"creature_id": c.species}).json()
    assert {r["id"] for r in species["creatures"]} == {
        cr.id for cr in runner.creatures if cr.species == c.species
    }
    missing = client.get("/v1/spectate/dossier", params={"creature_id": "missing"}).json()
    assert missing["creatures"] == []


def test_frame_metadata_qua_hai_van(dossier_env):
    client, runner = dossier_env
    keys = []
    for _ in range(2):
        runner.advance_phase()
        assert runner.phase is Phase.SEEDING
        runner.advance_phase()
        runner.step()
        frame = runner.frames[-1]
        assert frame["schema_version"] == "1.0"
        assert frame["match_id"] == runner.match_id
        keys.append((frame["match_id"], frame["t"]))
        runner.advance_phase()
        assert runner.phase is Phase.REVEAL
        assert runner.laws_public()
        for revealed in runner.reveal_frames():
            assert revealed["match_id"] == runner.match_id
            assert revealed["schema_version"] == "1.0"
        runner.advance_phase()
        runner.advance_phase()
    assert keys[0][1] == keys[1][1]
    assert keys[0][0] != keys[1][0]

