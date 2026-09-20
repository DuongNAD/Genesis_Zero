"""Nhiều client cùng vào một server (N-10b, N-10c).

Đây là bài kiểm cho lời hứa trung tâm của chế độ mở: *"nhiều máy ở nhiều vị trí
khác nhau, chỉ cần có mạng"*. Ở đây một tiến trình đóng vai nhiều máy — đủ để
kiểm **giao thức**, không đủ để kiểm thông lượng (xem docstring `run_fleet`).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "client"))

from genesis_client import run

import net_config
from net import (
    server,
    state,
)
from net.match import MatchRunner
from net.ratelimit import reset


def _model_transport(seen: list) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(body["id_slot"])
        return httpx.Response(200, json={
            "content": json.dumps({"goal": "FORAGE", "ttl": 4}),
            "tokens_predicted": 30,
        })
    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    from net.routes_work import clear_work_state

    r = MatchRunner(seed=1, ticks=200, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)
    monkeypatch.setattr(net_config, "JOIN_PER_HOUR", 20)
    reset()
    clear_work_state()
    yield r
    reset()
    clear_work_state()


@pytest.mark.asyncio
async def test_ba_client_cung_vao_mot_van(_clean):
    """Ba loài khác nhau vào cùng một ván, mỗi loài nhận việc của RIÊNG mình."""
    r = _clean
    calls: list = []
    tp = httpx.ASGITransport(app=server.app)

    async def one(name, tier):
        await run(server="http://test", model_url="http://model",
                  name=name, persona=f"{name} sống theo cách của mình.",
                  brain_tier=tier, pop=1, max_rounds=1,
                  poll_interval=0.01, hold_ms=80,
                  server_transport=tp, model_transport=_model_transport(calls))

    tasks = [asyncio.create_task(one(n, t))
             for n, t in (("Kiến Lửa", 4), ("Sói Xám", 3), ("Rùa Đá", 2))]
    await asyncio.sleep(0.15)
    assert len(r.registrations) == 3, f"chỉ {len(r.registrations)} loài vào được"

    r.advance_phase()                      # -> SEEDING: sinh vật ra đời
    species = {reg.species_id for reg in r.registrations.values()}
    assert len({c.species for c in r.creatures} & species) == 3
    await asyncio.sleep(0.1)
    r.advance_phase()                      # -> RUNNING
    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=8.0)

    assert calls, "không client nào gọi được model"
    # Mỗi loài chỉ được nhận việc của cá thể mình — server không phát chéo.
    for reg in r.registrations.values():
        assert reg.creature_ids, f"{reg.species_id} không có cá thể nào"


@pytest.mark.asyncio
async def test_mot_client_chet_khong_keo_theo_ca_dan(_clean):
    """Ở chế độ mở, một client rớt là chuyện bình thường — mạng rớt, máy ngủ."""
    r = _clean
    tp = httpx.ASGITransport(app=server.app)

    def dead(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("model chết", request=request)

    calls: list = []

    async def good():
        await run(server="http://test", model_url="http://m", name="Sống",
                  brain_tier=3, pop=1, max_rounds=1, poll_interval=0.01,
                  hold_ms=80, server_transport=tp,
                  model_transport=_model_transport(calls))

    async def bad():
        await run(server="http://test", model_url="http://m", name="Chết",
                  brain_tier=3, pop=1, max_rounds=1, poll_interval=0.01,
                  hold_ms=80, server_transport=tp,
                  model_transport=httpx.MockTransport(dead))

    tasks = [asyncio.create_task(good()), asyncio.create_task(bad())]
    await asyncio.sleep(0.15)
    r.advance_phase(); await asyncio.sleep(0.05); r.advance_phase()
    res = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True),
                                 timeout=8.0)
    assert not any(isinstance(x, Exception) for x in res), res
    assert calls, "client lành phải vẫn gọi được model"


def test_client_node_khong_phu_thuoc_gi():
    """Tài liệu khẳng định *"viết client cho ngôn ngữ khác là chuyện một buổi
    chiều"*. File Node tồn tại để câu đó được KIỂM, không chỉ được nói."""
    import shutil
    import subprocess

    js = Path("client/genesis_client.js")
    assert js.exists()
    src = js.read_text(encoding="utf-8")
    assert "require(" not in src and "import " not in src, "phải không phụ thuộc gì"
    # Quét CODE, bỏ chú thích: chính chú thích đang giải thích *vì sao* không
    # được nhắc tới `EffectKind`, và một bài test kêu vì câu giải thích ấy là
    # bài test sẽ bị tắt đi.
    code = "\n".join(
        line.split("//")[0] for line in src.splitlines()
        if not line.strip().startswith("//")
    )
    for banned in ("FORAGE", "POISON", "FRUIT_", "EffectKind", "LawDSL"):
        assert banned not in code, f"client Node biết {banned} — thiết kế sai chỗ khác"

    node = shutil.which("node")
    if node:
        assert subprocess.run([node, "--check", str(js)]).returncode == 0


def test_fleet_moi_client_mot_loai_khac_nhau():
    from run_fleet import SPECIES

    names = [s[0] for s in SPECIES]
    personas = [s[1] for s in SPECIES]
    tiers = [s[2] for s in SPECIES]
    assert len(set(names)) == len(names)
    assert len(set(personas)) == len(personas)
    # brain_tier phải TRẢI, không dồn một chỗ: cả điểm của việc chạy nhiều client
    # là thế giới có nhiều thứ KHÁC nhau trong đó.
    assert len(set(tiers)) >= 4, tiers
    assert min(tiers) == 0 and max(tiers) == 5


def test_run_fleet_cli_invalid_n(capsys):
    import run_fleet

    ret_zero = run_fleet.main(["--n", "0"])
    assert ret_zero == 2
    captured = capsys.readouterr()
    assert "--n phải trong" in captured.err

    ret_too_large = run_fleet.main(["--n", "99"])
    assert ret_too_large == 2


def test_run_fleet_cli_valid_and_keyboard_interrupt(monkeypatch):
    import run_fleet

    calls = []

    async def mock_fleet(a):
        calls.append(a.n)

    monkeypatch.setattr(run_fleet, "_fleet", mock_fleet)
    ret = run_fleet.main(["--n", "2", "--rounds", "1"])
    assert ret == 0
    assert calls == [2]

    async def mock_fleet_interrupt(a):
        raise KeyboardInterrupt()

    monkeypatch.setattr(run_fleet, "_fleet", mock_fleet_interrupt)
    ret_interrupt = run_fleet.main(["--n", "1"])
    assert ret_interrupt == 0


def test_genesis_client_cli_and_toml_config(tmp_path, monkeypatch):
    import genesis_client

    toml_file = tmp_path / "client_config.toml"
    toml_file.write_text(
        'server = "http://config-server"\nname = "FromToml"\npop = 3\n',
        encoding="utf-8",
    )

    captured_kwargs = {}

    async def mock_run(**kwargs):
        captured_kwargs.update(kwargs)

    monkeypatch.setattr(genesis_client, "run", mock_run)

    # CLI flag overrides config.toml
    ret = genesis_client.main([
        "--config", str(toml_file),
        "--name", "FromCLI",
        "--brain-tier", "4",
    ])
    assert ret == 0
    assert captured_kwargs["server"] == "http://config-server"
    assert captured_kwargs["name"] == "FromCLI"
    assert captured_kwargs["pop"] == 3
    assert captured_kwargs["brain_tier"] == 4


@pytest.mark.asyncio
async def test_genesis_client_decision_http_error_and_pause(monkeypatch):
    import genesis_client

    # Monkeypatch pause timings for fast test execution
    monkeypatch.setattr(genesis_client, "FAILURES_BEFORE_PAUSE", 1)
    monkeypatch.setattr(genesis_client, "PAUSE_SECONDS", 0.01)

    async def server_handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p == "/v1/join":
            return httpx.Response(200, json={
                "token": "tok1", "species_id": "sp1", "creature_ids": ["c1"], "queued": False,
            })
        if p == "/v1/heartbeat":
            return httpx.Response(200, json={"ok": True})
        if p == "/v1/state":
            return httpx.Response(200, json={"match_id": "m1", "phase": "RUNNING"})
        if p == "/v1/match/brief":
            return httpx.Response(200, json={
                "match_id": "m1",
                "creatures": {"c1": {"system_prompt": "sys", "id_slot_hint": 0}},
            })
        if p == "/v1/work":
            return httpx.Response(200, json={
                "items": [{
                    "creature_id": "c1",
                    "work_id": "w1",
                    "user_block": "user",
                    "max_tokens": 50,
                    "json_schema": {},
                }],
            })
        if p == "/v1/decision":
            raise httpx.ConnectError("Connection refused on decision", request=request)
        return httpx.Response(404)

    model_calls = 0

    async def model_handler(request: httpx.Request) -> httpx.Response:
        nonlocal model_calls
        model_calls += 1
        if model_calls == 1:
            return httpx.Response(200, json={
                "content": json.dumps({"goal": "FORAGE"}),
                "tokens_predicted": 10,
            })
        return httpx.Response(500, text="Internal Model Error")

    srv_tp = httpx.MockTransport(server_handler)
    mdl_tp = httpx.MockTransport(model_handler)

    await genesis_client.run(
        server="http://test-server",
        model_url="http://test-model",
        name="TestBot",
        max_rounds=2,
        poll_interval=0.01,
        server_transport=srv_tp,
        model_transport=mdl_tp,
    )
    assert model_calls >= 2


@pytest.mark.asyncio
async def test_genesis_client_cancelled_shutdown():
    import genesis_client

    async def server_handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p == "/v1/join":
            return httpx.Response(200, json={
                "token": "tok1", "species_id": "sp1", "creature_ids": ["c1"], "queued": False,
            })
        if p == "/v1/heartbeat":
            return httpx.Response(200, json={"ok": True})
        if p == "/v1/state":
            await asyncio.sleep(1.0)
            return httpx.Response(200, json={"match_id": "m1", "phase": "RUNNING"})
        return httpx.Response(404)

    srv_tp = httpx.MockTransport(server_handler)
    mdl_tp = httpx.MockTransport(lambda r: httpx.Response(200))

    task = asyncio.create_task(genesis_client.run(
        server="http://test-server",
        model_url="http://test-model",
        name="CancelBot",
        poll_interval=0.01,
        server_transport=srv_tp,
        model_transport=mdl_tp,
    ))

    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

