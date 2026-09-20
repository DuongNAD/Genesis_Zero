"""Kiểm thử lớp gọi model (B-03).

Chạy trên `httpx.MockTransport`: không mở cổng, không cần model, dưới một giây.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from genesis.llm_client import ask


def _ok(payload: dict, tokens: int = 12):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"content": json.dumps(payload), "tokens_predicted": tokens}
        )
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_than_goi_dung_endpoint_va_ghim_slot():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"content": '{"goal":"FORAGE","ttl":5}', "tokens_predicted": 12}
        )

    r = await ask(
        "http://mock-llm", slot_id=3, system="SYS_", user="USR",
        max_tokens=64, schema={"type": "object"},
        transport=httpx.MockTransport(handler),
    )
    assert r["json"]["goal"] == "FORAGE"
    assert r["n"] == 12
    assert r["raw"] == '{"goal":"FORAGE","ttl":5}'
    # Bất biến 1: endpoint gốc, không phải /v1/chat/completions
    assert seen["path"] == "/completion"
    # Bất biến 2: id_slot + cache_prompt luôn có mặt
    assert seen["body"]["id_slot"] == 3
    assert seen["body"]["cache_prompt"] is True
    # system đứng TRƯỚC user, nếu không thì prefix cache không bao giờ trúng
    assert seen["body"]["prompt"] == "SYS_USR"
    assert seen["body"]["n_predict"] == 64


@pytest.mark.asyncio
async def test_base_url_da_co_completion_thi_khong_noi_hai_lan():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"content": "{}", "tokens_predicted": 1})

    await ask("http://x/completion", 0, "s", "u", 8, {},
              transport=httpx.MockTransport(handler))
    assert seen["path"] == "/completion"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resp",
    [
        httpx.Response(500, text="boom"),
        httpx.Response(200, json={"content": "khong phai json {"}),
        httpx.Response(200, json={"khong_co_content": 1}),
    ],
)
async def test_loi_thi_tra_none_khong_nem(resp):
    """Bất biến 3: người gọi rơi về phản xạ, ván không gãy."""
    r = await ask("http://x", 0, "s", "u", 8, {},
                  transport=httpx.MockTransport(lambda req: resp))
    assert r is None


@pytest.mark.asyncio
async def test_loi_mang_thi_tra_none():
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("không nối được", request=request)

    assert await ask("http://x", 0, "s", "u", 8, {},
                     transport=httpx.MockTransport(boom)) is None


@pytest.mark.asyncio
async def test_gather_that_su_song_song():
    """Bất biến 4: gather thật. Tuần tự biến 4 giây thành 15 giây mà không báo gì."""
    in_flight = 0
    peak = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.02)
        in_flight -= 1
        return httpx.Response(200, json={"content": '{"goal":"REST","ttl":3}',
                                         "tokens_predicted": 8})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        results = await asyncio.gather(*[
            ask("http://x", i, "S", f"U{i}", 32, {}, client=client) for i in range(5)
        ])
    assert peak == 5, f"chỉ có {peak} lời gọi chồng nhau — đang chạy tuần tự"
    assert all(r["json"]["goal"] == "REST" for r in results)


@pytest.mark.asyncio
async def test_client_dung_chung_khong_bi_dong_som():
    """Truyền client vào thì `ask` không được đóng nó — lời gọi sau còn dùng."""
    transport = _ok({"goal": "REST", "ttl": 3})
    async with httpx.AsyncClient(transport=transport) as client:
        assert await ask("http://x", 0, "s", "u", 8, {}, client=client) is not None
        assert not client.is_closed
        assert await ask("http://x", 0, "s", "u", 8, {}, client=client) is not None


def test_detect_backend():
    from genesis.llm_client import detect_backend

    assert detect_backend("http://localhost:11434") == "ollama"
    assert detect_backend("http://localhost:11434/api/chat") == "ollama"
    assert detect_backend("http://localhost:8000/v1") == "vllm"
    assert detect_backend("http://localhost:8001/chat/completions") == "vllm"
    assert detect_backend("http://localhost:8099") == "mock"
    assert detect_backend("http://localhost:8080") == "llama.cpp"


@pytest.mark.asyncio
async def test_ask_reflex_returns_none():
    assert await ask(backend="reflex") is None


@pytest.mark.asyncio
async def test_ask_ollama_backend_success_and_errors():
    # 1. Non-200 HTTP error
    resp_500 = httpx.Response(500, text="Ollama internal error")
    res_err = await ask(
        "http://localhost:11434", backend="ollama",
        transport=httpx.MockTransport(lambda r: resp_500),
    )
    assert res_err is None

    # 2. Invalid content structure
    resp_invalid = httpx.Response(200, json={"message": {"content": 12345}})
    res_inv = await ask(
        "http://localhost:11434", backend="ollama",
        transport=httpx.MockTransport(lambda r: resp_invalid),
    )
    assert res_inv is None

    # 3. Successful call
    resp_ok = httpx.Response(200, json={
        "message": {"content": '{"goal": "FORAGE"}'},
        "eval_count": 42,
        "eval_duration": 123456,
    })
    res_ok = await ask(
        "http://localhost:11434", backend="ollama", system="sys", user="usr",
        schema={"type": "object"},
        transport=httpx.MockTransport(lambda r: resp_ok),
    )
    assert res_ok is not None
    assert res_ok["json"]["goal"] == "FORAGE"
    assert res_ok["n"] == 42
    assert res_ok["timings"]["eval_duration"] == 123456


@pytest.mark.asyncio
async def test_ask_vllm_backend_errors_and_truncation():
    # 1. Non-200 HTTP error
    resp_404 = httpx.Response(404, text="vLLM endpoint not found")
    res_404 = await ask(
        "http://localhost:8000/v1", backend="vllm",
        transport=httpx.MockTransport(lambda r: resp_404),
    )
    assert res_404 is None

    # 2. Invalid content structure
    resp_no_content = httpx.Response(200, json={"choices": [{"message": {"content": None}}]})
    res_no_cnt = await ask(
        "http://localhost:8000/v1", backend="vllm",
        transport=httpx.MockTransport(lambda r: resp_no_content),
    )
    assert res_no_cnt is None

    # 3. Truncation due to length
    resp_length = httpx.Response(200, json={
        "choices": [{
            "message": {"content": '{"goal": "REST"}'},
            "finish_reason": "length",
        }],
    })
    res_length = await ask(
        "http://localhost:8000/v1", backend="vllm",
        transport=httpx.MockTransport(lambda r: resp_length),
    )
    assert res_length is None

    # 4. Truncation due to content_filter
    resp_filter = httpx.Response(200, json={
        "choices": [{
            "message": {"content": '{"goal": "REST"}'},
            "finish_reason": "content_filter",
        }],
    })
    res_filter = await ask(
        "http://localhost:8000/v1", backend="vllm",
        transport=httpx.MockTransport(lambda r: resp_filter),
    )
    assert res_filter is None


@pytest.mark.asyncio
async def test_ask_frontier_markdown_and_think_stripping():
    # 1. Strip <think>...</think> and ```json\n...\n```
    content_raw = (
        "<think>Let me decide the best goal.</think>\n"
        "```json\n"
        '{"goal": "REST", "ttl": 5}\n'
        "```"
    )
    resp_frontier = httpx.Response(200, json={
        "choices": [{
            "message": {"content": content_raw},
            "finish_reason": "stop",
        }],
        "usage": {
            "completion_tokens": 50,
            "completion_tokens_details": {"reasoning_tokens": 30},
        },
    })
    res_frontier = await ask(
        "http://localhost:8000/v1", backend="frontier",
        api_key="sk-test",
        transport=httpx.MockTransport(lambda r: resp_frontier),
    )
    assert res_frontier is not None
    assert res_frontier["json"]["goal"] == "REST"
    assert res_frontier["thinking_tokens"] == 30
    assert res_frontier["answer_tokens"] == 20

    # 2. Unclosed <think> tag -> returns None
    resp_unclosed = httpx.Response(200, json={
        "choices": [{
            "message": {"content": "<think>incomplete reasoning..."},
            "finish_reason": "stop",
        }],
    })
    res_unclosed = await ask(
        "http://localhost:8000/v1", backend="frontier",
        transport=httpx.MockTransport(lambda r: resp_unclosed),
    )
    assert res_unclosed is None

