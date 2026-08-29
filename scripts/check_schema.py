#!/usr/bin/env python3
"""Xác minh llama-server: json_schema có ép được cấu trúc, và prefix cache có ăn.

Đây là bài kiểm tra của S-02. Chạy nó TRƯỚC khi viết bất kỳ dòng nào của B-03 —
nếu json_schema không hoạt động thì cả kiến trúc hai tầng phải nghĩ lại.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time

import httpx

SCHEMA = {
    "type": "object",
    "properties": {
        "note": {"type": "string", "maxLength": 90},
        "goal": {"type": "string",
                 "enum": ["FORAGE", "HUNT", "FLEE", "FOLLOW", "REST", "WANDER", "GUARD"]},
        "ttl": {"type": "integer", "minimum": 2, "maximum": 12},
    },
    "required": ["note", "goal", "ttl"],
    "additionalProperties": False,
}

SYSTEM = (
    "Bạn là một sinh vật trong một thế giới lưới 24x24. Di chuyển tốn năng lượng; "
    "hết năng lượng thì chết. Bạn chỉ trả về một ý đồ, không trả về nước đi.\n\n"
)


async def one(client: httpx.AsyncClient, url: str, slot: int, state: str) -> tuple[bool, float, int]:
    t0 = time.monotonic()
    try:
        r = await client.post(f"{url}/completion", json={
            "prompt": SYSTEM + state,
            "id_slot": slot,
            "cache_prompt": True,
            "json_schema": SCHEMA,
            "n_predict": 140,
            "temperature": 0.7,
        }, timeout=30.0)
        r.raise_for_status()
        body = r.json()
        obj = json.loads(body["content"])
        ok = set(obj) <= {"note", "goal", "ttl"} and obj["goal"] in SCHEMA["properties"]["goal"]["enum"]
        n = body.get("tokens_predicted", 0)
    except Exception as exc:                       # noqa: BLE001 — báo, không nuốt
        print(f"  lỗi: {type(exc).__name__}: {exc}", file=sys.stderr)
        return False, time.monotonic() - t0, 0
    return ok, time.monotonic() - t0, n


async def run(url: str, n: int) -> int:
    async with httpx.AsyncClient() as client:
        h = await client.get(f"{url}/health", timeout=10.0)
        print(f"/health -> {h.status_code}")

        print(f"\n1. {n} lời gọi tuần tự, cùng id_slot=0")
        okc, times = 0, []
        for i in range(n):
            ok, dt, _ = await one(client, url, 0, f"Tick {i}. Năng lượng 60. Thấy một cây cỏ ở gần.")
            okc += ok
            times.append(dt)
        print(f"   JSON hợp lệ: {okc}/{n}")
        print(f"   lần 1: {times[0]:.2f}s · trung vị các lần sau: {statistics.median(times[1:]):.2f}s")
        ratio = statistics.median(times[1:]) / times[0] if times[0] else 1
        print(f"   prefix cache: {'ĂN' if ratio < 0.34 else 'CHƯA ĂN'} (tỉ lệ {ratio:.2f}, cần < 0.34)")

        print("\n2. 5 lời gọi song song vs 1 lời gọi")
        t0 = time.monotonic()
        await one(client, url, 0, "Tick X. Năng lượng 60.")
        solo = time.monotonic() - t0
        t0 = time.monotonic()
        await asyncio.gather(*(one(client, url, i % 2, f"Tick {i}. Năng lượng 60.") for i in range(5)))
        par = time.monotonic() - t0
        print(f"   1 lời gọi {solo:.2f}s · 5 song song {par:.2f}s (tỉ lệ {par/solo:.2f}, cần < 1.5)")

    return 0 if okc == n else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--n", type=int, default=50)
    a = ap.parse_args(argv)
    return asyncio.run(run(a.url.rstrip("/"), a.n))


if __name__ == "__main__":
    raise SystemExit(main())
