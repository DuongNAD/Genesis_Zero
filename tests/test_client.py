"""Genesis Zero — tests/test_client: kiểm thử client kẻ thừa hành ngu ngốc (N-10)."""

from __future__ import annotations

import ast
import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

# Client là gói ĐỘC LẬP ở client/, không phải module trong genesis/ — xem
# docstring của client/genesis_client.py. Test phải nạp nó đúng như người lạ nạp.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "client"))
from genesis_client import run

from genesis.reflex import Goal
from net import server, state
from net.match import MatchRunner, Phase
from net.routes_join import clear_rate_limits
from net.routes_work import clear_work_state


@pytest.fixture(autouse=True)
def reset_state():
    clear_rate_limits()
    clear_work_state()
    yield
    clear_rate_limits()
    clear_work_state()


@pytest.mark.asyncio
async def test_client_full_cycle_brief_work_decision(monkeypatch):
    """Ca 1: Client join xong đi trọn một vòng: brief -> work -> decision, và state.runner.decisions có goal."""
    r = MatchRunner(seed=1, ticks=20, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)

    model_received_requests = []

    def model_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        model_received_requests.append(body)
        content = json.dumps({
            "goal": "FORAGE",
            "ttl": 5,
            "note": "tìm thức ăn",
        })
        return httpx.Response(
            200,
            json={"content": content, "tokens_predicted": 25},
        )

    server_transport = httpx.ASGITransport(app=server.app)
    model_transport = httpx.MockTransport(model_handler)

    client_task = asyncio.create_task(
        run(
            server_transport=server_transport,
            model_transport=model_transport,
            name="Kiến Thợ",
            persona="Cần mẫn",
            brain_tier=3,
            pop=1,
            max_rounds=1,
            poll_interval=0.01,
            hold_ms=100,
        )
    )

    # Chờ client join vào LOBBY
    for _ in range(100):
        if len(r.registrations) == 1:
            break
        await asyncio.sleep(0.01)
    assert len(r.registrations) == 1

    # Chuyển ván sang SEEDING -> client lấy brief
    r.advance_phase()
    assert r.phase is Phase.SEEDING
    await asyncio.sleep(0.05)

    # Chuyển ván sang RUNNING -> client lấy work và gửi decision
    r.advance_phase()
    assert r.phase is Phase.RUNNING

    await asyncio.wait_for(client_task, timeout=3.0)

    # Khẳng định client đã gọi model và server đã ghi nhận goal vào decisions
    assert len(model_received_requests) >= 1
    assert len(r.decisions) >= 1
    cid = next(iter(r.decisions))
    active_goal = r.decisions[cid]
    assert active_goal.goal == Goal.FORAGE
    assert active_goal.ttl == 5


@pytest.mark.asyncio
async def test_client_system_prompt_byte_exact(monkeypatch):
    """Ca 2: system_prompt client gửi cho model KHỚP TỪNG BYTE với /match/brief trả, và prompt bắt đầu ĐÚNG bằng system_prompt."""
    r = MatchRunner(seed=42, ticks=20, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)

    intercepted_prompts: list[str] = []

    def model_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        intercepted_prompts.append(body["prompt"])
        # "FORAGE" chứ không phải một tên bịa: goal lạ bị server từ chối ở
        # tầng ngữ nghĩa, và bài này sẽ xanh vì lý do sai.
        content = json.dumps({"goal": "FORAGE", "ttl": 3})
        return httpx.Response(
            200,
            json={"content": content, "tokens_predicted": 20},
        )

    server_transport = httpx.ASGITransport(app=server.app)
    model_transport = httpx.MockTransport(model_handler)

    client_task = asyncio.create_task(
        run(
            server_transport=server_transport,
            model_transport=model_transport,
            name="Kiến Lửa",
            persona="Sống theo đàn, cẩn trọng.",
            brain_tier=3,
            pop=1,
            max_rounds=1,
            poll_interval=0.01,
            hold_ms=100,
        )
    )

    for _ in range(100):
        if len(r.registrations) == 1:
            break
        await asyncio.sleep(0.01)
    assert len(r.registrations) == 1
    r.advance_phase()  # -> SEEDING
    await asyncio.sleep(0.05)
    r.advance_phase()  # -> RUNNING

    await asyncio.wait_for(client_task, timeout=3.0)

    # Lấy brief trực tiếp từ server để đối chiếu từng byte
    reg = next(iter(r.registrations.values()))
    async with httpx.AsyncClient(transport=server_transport, base_url="http://test") as tc:
        brief_resp = await tc.get(
            "/v1/match/brief",
            headers={"Authorization": f"Bearer {reg.token}"},
        )
    assert brief_resp.status_code == 200
    brief_data = brief_resp.json()

    assert len(intercepted_prompts) >= 1
    for prompt_sent in intercepted_prompts:
        # Tìm system_prompt tương ứng trong brief
        matching = [
            c_info["system_prompt"]
            for c_info in brief_data["creatures"].values()
            if prompt_sent.startswith(c_info["system_prompt"])
        ]
        assert len(matching) == 1, "Prompt gửi model phải bắt đầu ĐÚNG bằng system_prompt (không chèn gì trước)"
        expected_sys_prompt = matching[0]

        # Khớp từng byte
        actual_prefix = prompt_sent[:len(expected_sys_prompt)]
        assert actual_prefix == expected_sys_prompt
        assert actual_prefix.encode("utf-8") == expected_sys_prompt.encode("utf-8")


@pytest.mark.asyncio
async def test_client_corrupted_model_json_handled_silently(monkeypatch):
    """Ca 3: Model trả JSON hỏng -> client KHÔNG gửi /decision và KHÔNG sập."""
    r = MatchRunner(seed=1, ticks=20, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)

    decision_posts: list[httpx.Request] = []

    # Bọc server transport để phát hiện nếu client có gọi POST /v1/decision
    base_server_transport = httpx.ASGITransport(app=server.app)

    async def custom_server_handle(request: httpx.Request) -> httpx.Response:
        if "/v1/decision" in str(request.url):
            decision_posts.append(request)
        return await base_server_transport.handle_async_request(request)

    server_transport = httpx.MockTransport(custom_server_handle)

    def model_handler(request: httpx.Request) -> httpx.Response:
        # Trả về JSON cụt / không parse được
        return httpx.Response(
            200,
            json={"content": "{ broken: json ...", "tokens_predicted": 5},
        )

    model_transport = httpx.MockTransport(model_handler)

    client_task = asyncio.create_task(
        run(
            server_transport=server_transport,
            model_transport=model_transport,
            name="Kiến Đen",
            brain_tier=2,
            pop=1,
            max_rounds=1,
            poll_interval=0.01,
            hold_ms=100,
        )
    )

    for _ in range(100):
        if len(r.registrations) == 1:
            break
        await asyncio.sleep(0.01)
    assert len(r.registrations) == 1
    r.advance_phase()  # -> SEEDING
    await asyncio.sleep(0.05)
    r.advance_phase()  # -> RUNNING

    await asyncio.wait_for(client_task, timeout=3.0)

    # Client không sập và KHÔNG gửi decision nào
    assert len(decision_posts) == 0, "Khi JSON hỏng, client tuyệt đối không gửi /decision"
    assert len(r.decisions) == 0


def test_client_ast_no_forbidden_sim_imports():
    """Ca 4: Quét AST file genesis/client.py: khẳng định nó KHÔNG import module sim nào trong danh sách cấm."""
    client_path = Path("client/genesis_client.py")
    assert client_path.exists(), "File client/genesis_client.py phải tồn tại"

    tree = ast.parse(client_path.read_text(encoding="utf-8"), filename=str(client_path))

    forbidden_modules = {
        "genesis.lawdsl",
        "genesis.prompt",
        "genesis.world",
        "genesis.tick",
        "genesis.strategist",
        "genesis.reflex",
        "genesis.codex",
        "genesis.fieldnotes",
        "genesis.reveal",
        "genesis.validate",
        "genesis.creature",
        "genesis.traits",
        "genesis.logio",
        "genesis.lawgen",
        "genesis.law_config",
        "genesis.config",
    }

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)

    # 1. Không import bất kỳ module nào trong danh sách cấm
    for forbidden in forbidden_modules:
        assert forbidden not in imported_modules, f"client KHÔNG được import {forbidden}"
        assert not any(
            m.startswith(forbidden + ".") for m in imported_modules
        ), f"client KHÔNG được import module con của {forbidden}"

    # 2. Import duy nhất từ genesis phải là genesis.llm_client
    # Gói độc lập: KHÔNG import gì từ genesis, kể cả llm_client. Nó có bản sao
    # rút gọn của `ask` — bản sao cố ý DUY NHẤT trong dự án, xem docstring.
    genesis_imports = {m for m in imported_modules if m == "genesis" or m.startswith("genesis.")}
    assert not genesis_imports, f"client phải đứng MỘT MÌNH, nhưng import: {genesis_imports}"

    # 3. Không import từ net.*
    net_imports = {m for m in imported_modules if m == "net" or m.startswith("net.") or m.startswith("net_config")}
    assert len(net_imports) == 0, f"client KHÔNG được import từ net: {net_imports}"
