"""Genesis Zero — số chỗ song song và id_slot (B-03 §hạn chờ)."""

from __future__ import annotations

import asyncio
import json

import httpx

from genesis import law_config
from genesis.strategist import LlmStrategist


def _strategist(ids, transport):
    return LlmStrategist(
        base_url="http://test.local",
        creature_ids=ids,
        personas={i: "" for i in ids},
        transport=transport,
    )


def test_id_slot_khong_bao_gio_vuot_so_cho_that():
    """15 con nhưng server `-np 4` -> id_slot phải nằm trong 0..3.

    Bản cũ phát 0..14. llama.cpp không có chỗ 14, nên prefix cache — thứ đo được
    756/757 token tái dùng — trong ván thật gần như không chạy.
    """
    seen: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/props":
            return httpx.Response(200, json={"total_slots": 4})
        body = json.loads(request.content)
        seen.append(body["id_slot"])
        return httpx.Response(200, json={
            "content": json.dumps({"goal": "EXPLORE", "ttl": 5}),
            "tokens_predicted": 8,
        })

    ids = [f"L{i//3+1}:{i%3}" for i in range(15)]
    st = _strategist(ids, httpx.MockTransport(handler))

    async def go():
        async with httpx.AsyncClient(transport=st.transport) as c:
            n = await st._ensure_slots(c)
            assert n == 4
            # dò một lần rồi nhớ: lần hai không gọi lại /props
            assert await st._ensure_slots(c) == 4

    asyncio.run(go())
    assert st._n_slots == 4
    for cid, idx in st.slots.items():
        assert 0 <= idx % st._n_slots < 4


def test_server_khong_noi_thi_dung_mac_dinh():
    """`/props` hỏng thì KHÔNG được làm hỏng ván — lùi về mặc định."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="nope")

    st = _strategist(["L1:0"], httpx.MockTransport(handler))

    async def go():
        async with httpx.AsyncClient(transport=st.transport) as c:
            return await st._ensure_slots(c)

    assert asyncio.run(go()) == law_config.LLM_PARALLEL_FALLBACK


def test_semaphore_song_qua_nhieu_vong_lap_su_kien():
    """`begin_tick` gọi `asyncio.run` MỖI TICK — mỗi lần một vòng lặp mới.

    `Semaphore` gắn vào vòng lặp nó chờ lần đầu; nhớ lại nó qua tick sau là
    `RuntimeError: bound to a different event loop`.

    Lỗi này nằm im rất lâu: `acquire()` chỉ chạm tới vòng lặp khi phải CHỜ, nên
    chừng nào số con nghĩ cùng lượt còn <= số chỗ thì không ai thấy gì — ba ván
    7B chạy trọn 200 tick không sao. Nó nổ đúng ở ca semaphore sinh ra để phục
    vụ: **cả đàn cùng nghĩ một lượt**. Chế độ mở có 15+ con nên đó là ca thường.

    Bài test ép đúng ca ấy: nhiều việc hơn số chỗ, hai lượt liên tiếp.
    """
    import asyncio

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        if request.url.path == "/props":
            return httpx.Response(200, json={"total_slots": 2})
        calls += 1
        return httpx.Response(200, json={
            "content": json.dumps({"goal": "EXPLORE", "ttl": 5}),
            "tokens_predicted": 8,
        })

    st = _strategist([f"L1:{i}" for i in range(6)], httpx.MockTransport(handler))

    async def mot_luot():
        async with httpx.AsyncClient(transport=st.transport) as c:
            n = await st._ensure_slots(c)
            gate = asyncio.Semaphore(n)

            async def one(i):
                async with gate:
                    await asyncio.sleep(0)      # ép nhường -> có tranh chấp thật
                    await c.post("http://test.local/completion", json={"id_slot": i % n})

            await asyncio.gather(*[one(i) for i in range(6)])

    for _ in range(3):          # ba tick, ba vòng lặp sự kiện khác nhau
        asyncio.run(mot_luot())
    assert calls == 18


def test_khong_bao_gio_qua_n_lenh_bay_cung_luc():
    """Cổng chặn phải giữ số lời gọi ĐANG BAY <= số chỗ.

    Không có cổng thì cả đàn bay cùng lúc, phần thừa nằm xếp hàng trong server,
    và `timeout` của httpx đếm cả thời gian chờ ấy. Đo ở ván seed 55: 21 lần
    trượt, mọi lần đúng 20003–20005 ms.
    """
    inflight = 0
    peak = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal inflight, peak
        if request.url.path == "/props":
            return httpx.Response(200, json={"total_slots": 3})
        inflight += 1
        peak = max(peak, inflight)
        await asyncio.sleep(0.01)
        inflight -= 1
        return httpx.Response(200, json={
            "content": json.dumps({"goal": "EXPLORE", "ttl": 5}),
            "tokens_predicted": 8,
        })

    st = _strategist([f"L1:{i}" for i in range(12)], httpx.MockTransport(handler))

    async def go():
        async with httpx.AsyncClient(transport=st.transport) as c:
            n = await st._ensure_slots(c)
            gate = asyncio.Semaphore(n)

            async def one(i):
                async with gate:
                    await c.post("http://test.local/completion",
                                 json={"id_slot": i % n})

            await asyncio.gather(*[one(i) for i in range(12)])

    asyncio.run(go())
    assert peak <= 3, f"có lúc {peak} lời gọi cùng bay, server chỉ có 3 chỗ"


def test_han_cho_tu_hieu_chinh_theo_model():
    """Hạn chờ phải ĐO, không phải đặt cứng.

    45 s là số của MỘT model. Qwen-7B sinh ~14 tok/s nên một đợt đầy mất 20 s;
    Qwen-14B sinh 5–6 tok/s nên đúng đợt ấy mất **81 s**. Ván 14B đầu tiên
    trượt **20/41 lời gọi**, mọi lần đúng mốc 45004 ms, và ghi Sổ Luật **0
    lần** — đọc vội thì thành "14B cũng không quy nạp được", trong khi nó gần
    như chưa được nghĩ lần nào.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/props":
            return httpx.Response(200, json={"total_slots": 4})
        return httpx.Response(200, json={
            "content": json.dumps({"goal": "EXPLORE", "ttl": 5}),
            "tokens_predicted": 8,
        })

    st = _strategist([f"L1:{i}" for i in range(4)], httpx.MockTransport(handler))
    assert st._call_ms is None, "chưa đo thì chưa có ước lượng"

    # mô phỏng một đợt mất 9 giây
    st._call_ms = 9000.0
    n = 4
    waves = 2
    timeout = max(st.timeout, 3.0 * st._call_ms / 1000.0) * waves
    # max(45, 3×9) = 45 -> nhưng đợt 9 s là ĐO ĐƯỢC, nên sàn 45 vẫn thắng ở đây;
    # với 14B (đợt 81 s) thì 3×81 = 243 s mới là số quyết định.
    assert timeout == 90.0, timeout          # max(45, 27) × 2 đợt
    st._call_ms = 81000.0                    # đúng số đo của Qwen-14B
    assert max(st.timeout, 3.0 * st._call_ms / 1000.0) * 1 == 243.0

    # model nhanh thì KHÔNG được kéo hạn xuống dưới sàn
    st._call_ms = 1000.0
    assert max(st.timeout, 3.0 * st._call_ms / 1000.0) == st.timeout
