"""Genesis Zero — client "kẻ thừa hành ngu ngốc" (N-10).

    pip install -e client/
    genesis-client --config client/config.example.toml

**Đây là thứ ta gửi cho người lạ**, nên nó là một gói ĐỘC LẬP, không phải một
module bên trong `genesis/`. Khác biệt ấy không phải chuyện thẩm mỹ:

* nó chỉ phụ thuộc `httpx` — cài trên máy người khác không kéo theo cả sim;
* nó **không thể** biết luật chơi kể cả khi ai đó muốn, vì các module ấy không
  có mặt trên máy đó;
* viết lại nó bằng Rust hay Go là chuyện một buổi chiều, vì tất cả những gì nó
  làm là ghép hai chuỗi rồi gọi HTTP.

Bản đầu đặt file này ở `genesis/client.py` và chứng minh bằng một bài test AST
rằng nó không import module sim nào. Bài test ấy đúng nhưng chưa đủ: nó biến một
**sự thật về đóng gói** thành một **quy ước phải nhớ**, và người gửi đi vẫn kèm
theo cả `lawdsl` lẫn `prompt`.

Client KHÔNG biết: LawDSL, bộ goal, bản đồ, cách chấm. Server gửi
`system_prompt`, `user_block` và `json_schema` sẵn sàng dùng. Nhờ thế client này
**không bao giờ phải cập nhật** khi luật chơi đổi.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import tomllib
from pathlib import Path
from typing import Any

import httpx

# Trần thời gian ngủ giữa hai lần hỏi khi đang xếp hàng, giây.
MAX_IDLE_WAIT = 15.0

logger = logging.getLogger("genesis-client")

HEARTBEAT_SECONDS = 10.0
FAILURES_BEFORE_PAUSE = 3
PAUSE_SECONDS = 30.0


async def ask_model(
    client: httpx.AsyncClient, model_url: str, slot: int,
    system: str, user: str, max_tokens: int, schema: dict,
) -> dict | None:
    """Gọi llama-server `/completion`. Lỗi thì trả None, không bao giờ ném.

    Bản sao rút gọn của `genesis.llm_client.ask`. Đây là chỗ DUY NHẤT trong dự
    án có bản sao cố ý: gói này phải đứng một mình. Hai bất biến phải giữ y hệt
    bản gốc — endpoint là `/completion` (chỉ nó nhận `id_slot`), và cùng một
    `creature_id` phải giữ **cùng một slot** suốt ván, nếu không prefix cache vô
    nghĩa và tốc độ sập.
    """
    root = model_url.rstrip("/")
    url = root if root.endswith("/completion") else f"{root}/completion"
    try:
        resp = await client.post(url, json={
            "prompt": system + user,      # thứ tự này, không chèn gì vào giữa
            "id_slot": slot,
            "cache_prompt": True,
            "json_schema": schema,
            "n_predict": max_tokens,
            "temperature": 0.7,
        })
        if resp.status_code != 200:
            logger.warning("model trả HTTP %d: %s", resp.status_code, resp.text[:150])
            return None
        data = resp.json()
        content = data.get("content")
        if not isinstance(content, str):
            logger.warning("phản hồi model thiếu trường 'content'")
            return None
        return {"json": json.loads(content), "n": int(data.get("tokens_predicted", 0))}
    except json.JSONDecodeError as exc:
        logger.warning("model trả JSON hỏng: %s", exc)
        return None
    except httpx.HTTPError as exc:
        logger.warning("lỗi mạng khi gọi model: %s", exc)
        return None


async def heartbeat_loop(srv: httpx.AsyncClient, headers: dict, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await srv.post("/v1/heartbeat", headers=headers,
                           json={"healthy": True, "queue_depth": 0, "model_ready": True})
        except httpx.HTTPError as exc:
            logger.warning("heartbeat hỏng: %s", exc)
        try:
            await asyncio.wait_for(stop.wait(), timeout=HEARTBEAT_SECONDS)
        except TimeoutError:
            pass


async def run(
    server: str = "http://localhost:8000",
    model_url: str = "http://localhost:8080",
    name: str = "Kiến Lửa",
    persona: str = "Sống theo đàn.",
    brain_tier: int = 3,
    pop: int = 2,
    model_name: str = "unknown",
    params_b: float = 0.0,
    league: str = "LEAGUE_LLM",
    hold_ms: int = 25000,
    poll_interval: float = 0.5,
    max_rounds: int | None = None,
    server_transport: httpx.AsyncBaseTransport | None = None,
    model_transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    stop = asyncio.Event()
    srv = httpx.AsyncClient(base_url=server.rstrip("/"), transport=server_transport,
                            timeout=hold_ms / 1000.0 + 10.0)
    mdl = httpx.AsyncClient(transport=model_transport, timeout=30.0)
    hb: asyncio.Task | None = None
    fails = 0
    try:
        j = (await srv.post("/v1/join", json={
            "display_name": name, "persona": persona, "model_name": model_name,
            "params_b": params_b, "brain_tier": brain_tier, "league": league,
            "pop_request": pop,
        })).json()
        headers = {"Authorization": f"Bearer {j['token']}"}
        if j.get("queued"):
            # Ván đang chạy thì loài mới KHÔNG chen vào giữa chừng — sinh vật ra
            # đời ở pha SEEDING. Nói thẳng, vì không nói thì client chỉ in
            # "brief ván m_00021: 0 cá thể" rồi im, và người mới sẽ tưởng hỏng.
            logger.info("đã vào: %s — ván %s đang chạy, bạn XẾP HÀNG chờ ván sau",
                        j["species_id"], "hiện tại")
        else:
            logger.info("đã vào: %s %s", j["species_id"], j["creature_ids"])
        hb = asyncio.create_task(heartbeat_loop(srv, headers, stop))

        match_id: str | None = None
        idle_wait = poll_interval
        idle_logged: object = object()      # khác mọi match_id -> in đúng một lần
        prompts: dict[str, str] = {}
        slots: dict[str, int] = {}
        rounds = 0

        while max_rounds is None or rounds < max_rounds:
            st = (await srv.get("/v1/state")).json()

            # Ván mới -> lấy lại brief MỘT LẦN. `system_prompt` sau đó là bất khả
            # xâm phạm: sửa một byte là prefix cache của chính máy này vô nghĩa.
            if st["match_id"] != match_id and st["phase"] in ("SEEDING", "RUNNING"):
                b = await srv.get("/v1/match/brief", headers=headers)
                if b.status_code == 200:
                    data = b.json()
                    match_id = data["match_id"]
                    prompts = {k: v["system_prompt"] for k, v in data["creatures"].items()}
                    slots = {k: v["id_slot_hint"] for k, v in data["creatures"].items()}
                    logger.info("brief ván %s: %d cá thể", match_id, len(prompts))

            if st["phase"] != "RUNNING" or not prompts:
                # Chờ thì chờ THƯA DẦN. Bản đầu hỏi `/v1/state` mỗi 0,5 s dù
                # đang xếp hàng: một ván 200 tick × 4 s là **1.600 lượt gọi**
                # cho đúng một câu trả lời "chưa tới lượt", và trần chống lạm
                # dụng của N-11 tồn tại chính để chặn kiểu ấy.
                if idle_logged != match_id:
                    logger.info("chờ ván sau (%s đang ở pha %s)…",
                                st["match_id"], st["phase"])
                    idle_logged = match_id
                await asyncio.sleep(min(idle_wait, MAX_IDLE_WAIT))
                idle_wait = min(idle_wait * 1.6, MAX_IDLE_WAIT)
                continue
            idle_wait = poll_interval
            idle_logged = None

            w = await srv.get("/v1/work", params={"hold_ms": hold_ms}, headers=headers)
            if w.status_code != 200:
                continue
            items = w.json().get("items", [])
            if not items:
                continue

            async def one(item: dict[str, Any]) -> bool:
                cid = item["creature_id"]
                r = await ask_model(mdl, model_url, slots.get(cid, 0),
                                    prompts.get(cid, ""), item["user_block"],
                                    item["max_tokens"], item["json_schema"])
                if r is None:
                    return False
                # Không tự đoán `deadline_tick` đã qua hay chưa: cứ tính xong thì
                # gửi, server tự bỏ nếu muộn (05 §3.3). Tự bỏ là tự làm mất một
                # quyết định lẽ ra còn kịp.
                try:
                    await srv.post("/v1/decision", headers=headers, json={
                        "work_id": item["work_id"], "tokens_used": r["n"],
                        "payload": r["json"],
                    })
                except httpx.HTTPError as exc:
                    logger.warning("gửi quyết định hỏng: %s", exc)
                return True

            oks = await asyncio.gather(*(one(i) for i in items))
            fails = 0 if any(oks) else fails + 1
            if fails >= FAILURES_BEFORE_PAUSE:
                logger.warning("model hỏng %d lượt liên tiếp, nghỉ %.0fs", fails, PAUSE_SECONDS)
                await asyncio.sleep(PAUSE_SECONDS)
                fails = 0
            rounds += 1
    finally:
        stop.set()
        if hb is not None:
            hb.cancel()
            try:
                await hb
            except asyncio.CancelledError:
                pass
        await srv.aclose()
        await mdl.aclose()


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="genesis-client")
    ap.add_argument("--config", type=Path)
    for flag, kind in (("--server", str), ("--model-url", str), ("--name", str),
                       ("--persona", str), ("--model-name", str), ("--league", str)):
        ap.add_argument(flag, type=kind)
    ap.add_argument("--brain-tier", type=int)
    ap.add_argument("--pop", type=int)
    ap.add_argument("--params-b", type=float)
    a = ap.parse_args(argv)

    cfg: dict[str, Any] = {}
    if a.config:
        cfg = tomllib.loads(a.config.read_text(encoding="utf-8"))
    # Cờ dòng lệnh đè file config; thiếu cả hai thì dùng mặc định của `run`.
    for key in ("server", "model_url", "name", "persona", "brain_tier", "pop",
                "model_name", "params_b", "league"):
        v = getattr(a, key, None)
        if v is not None:
            cfg[key] = v
    asyncio.run(run(**cfg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
