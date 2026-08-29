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
