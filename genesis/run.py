"""Genesis Zero — điểm vào.

Chạy vòng tick hoàn chỉnh với kiến trúc 6 pha tất định.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from collections.abc import Callable
from pathlib import Path


def configure_console_encoding() -> None:
    """Cấu hình stdout/stderr dùng UTF-8 errors=replace để tránh crash Unicode trên Windows (cp1252)."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                # Captured/closed streams need not expose a reconfigurable buffer.
                continue

from rich.live import Live

from genesis import config
from genesis.creature import (
    Creature,
)
from genesis.lawdsl import to_json
from genesis.lawgen import generate_cached
from genesis.logio import LogWriter
from genesis.oracle_run import run_oracle
from genesis.render import render_frame
from genesis.replay import ReplayStrategist
from genesis.strategist import LlmStrategist
from genesis.tick import SimState, build_match, tick
from genesis.world import (
    PLANT_GLYPH,
    TERRAIN_GLYPHS,
    World,
    spawn_plants,
)

DEBUG_RNG_SAMPLES = 20


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="genesis", description="Chạy một ván Genesis Zero")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--fps", type=float, default=10.0, help="khung hình/giây khi render")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--arm", default="STANDARD", help="nhánh thí nghiệm, xem law_config.ARMS")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--debug-rng", action="store_true",
                    help=f"in {DEBUG_RNG_SAMPLES} số ngẫu nhiên đầu tiên rồi thoát")
    ap.add_argument("--print-map", action="store_true",
                    help="in bản đồ địa hình rồi thoát")
    ap.add_argument("--llm", default=None,
                    help="'all', hoặc danh sách id/loài ngăn bằng dấu phẩy: L1:0,L2")
    ap.add_argument("--llm-url", default="http://localhost:8080",
                    help="llama-server endpoint gốc (B-03)")
    ap.add_argument("--controller", default=None, choices=["reflex"],
                    help="ép dùng tầng phản xạ, bỏ qua --llm (nhánh đối chứng của X-04)")
    ap.add_argument("--replay", type=Path, default=None,
                    help="dựng lại một ván có LLM từ log (B-06)")
    ap.add_argument("--truth", type=Path, default=None,
                    help="ghi bộ luật ẩn ra JSON cho bộ chấm (B-10)")
    ap.add_argument("--hunch", action="store_true",
                    help="bật LINH CẢM (B-14) — chỗ để đoán mà không phải tin. "
                         "TẮT mặc định: bật lên là đổi luật chơi, nên con số của "
                         "ván bật không so được với ván tắt")
    ap.add_argument("--no-laws", action="store_true",
                    help="chạy WORLD_FLAT: không sinh luật ẩn (nhánh đối chứng X-07)")
    args = ap.parse_args(argv)
    if args.out is None:
        args.out = Path("runs") / f"{args.seed}-{int(time.time())}.jsonl"
    return args


def _m0_loop(
    world: World,
    creatures: list[Creature],
    log: LogWriter | None,
    rng: random.Random,
    ticks: int,
    on_tick: Callable[[World, list[Creature], int], None] | None = None,
    match_seed: int = 0,
    laws: list | None = None,
    strategist=None,
) -> None:
    """Vòng lặp chạy sim qua tick(). Giữ tương thích cho các test gọi _m0_loop."""
    state = SimState(match_seed=match_seed)
    for t in range(ticks):
        tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=strategist)
        if on_tick is not None:
            on_tick(world, creatures, t)


def select_creatures(spec: str | None, creatures: list[Creature]) -> list[str]:
    """'all' | 'L1' | 'L1:0,L2:3' -> danh sách creature_id, thứ tự chuẩn."""
    if not spec:
        return []
    ids = {c.id for c in creatures}
    if spec.strip() == "all":
        chosen = set(ids)
    else:
        chosen = set()
        for token in (t.strip() for t in spec.split(",") if t.strip()):
            if token in ids:
                chosen.add(token)
                continue
            matched = {cid for cid in ids if cid.rpartition(":")[0] == token}
            if not matched:
                # Gõ nhầm một id thì ván chạy toàn phản xạ mà không có gì báo —
                # đúng kiểu hỏng im lặng làm hỏng cả một buổi đo.
                raise SystemExit(f"--llm: không có sinh vật hay loài nào tên {token!r}")
            chosen |= matched
    return sorted(chosen, key=lambda cid: (cid.rpartition(":")[0], int(cid.rpartition(":")[2])))


def main(argv: list[str] | None = None) -> int:
    configure_console_encoding()
    args = parse(argv)

    # ĐÚNG MỘT bộ sinh ngẫu nhiên cho cả ván. Truyền nó xuống, không tạo cái thứ hai.
    rng = random.Random(args.seed)

    if args.debug_rng:
        for _ in range(DEBUG_RNG_SAMPLES):
            print(rng.random())
        return 0

    if args.print_map:
        world = World(config.GRID_W, config.GRID_H, rng)
        # Sinh cây tới khi đạt trần để bản đồ có cây nhìn thấy được
        while len(world.plants) < config.PLANT_MAX:
            if spawn_plants(world, rng) == 0:
                break
        for y in range(world.h):
            row = [
                PLANT_GLYPH if (x, y) in world.plants else TERRAIN_GLYPHS[world.grid[y][x]]
                for x in range(world.w)
            ]
            print("".join(row))
        return 0

    world, creatures, state, rng = build_match(args.seed)

    laws = None if args.no_laws else generate_cached(args.seed, arm=args.arm)
    if args.truth is not None and laws is not None:
        args.truth.parent.mkdir(parents=True, exist_ok=True)
        args.truth.write_text(
            json.dumps(
                {
                    "seed": args.seed,
                    "arm": args.arm,
                    "laws": [to_json(law) for law in laws],
                    "surface_map": world.surface_map.cls_to_surface,
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )

    strategist = None
    if args.replay is not None:
        # Dựng một "tâm trí" y hệt ván thật để replay so được prompt_hash.
        mind = LlmStrategist(args.llm_url, [c.id for c in creatures])
        strategist = ReplayStrategist(args.replay, mind=mind)
    elif args.controller != "reflex":
        chosen = select_creatures(args.llm, creatures)
        if chosen:
            strategist = LlmStrategist(args.llm_url, chosen, log=None)
            strategist.minds.hunch_enabled = bool(args.hunch)

    match_id = f"m_{args.seed:05d}"
    with LogWriter(args.out, match_id) as log:
        log.write(0, "RUN_START", seed=args.seed, ticks=args.ticks, arm=args.arm,
                  grid=[config.GRID_W, config.GRID_H],
                  n_laws=0 if laws is None else len(laws))
        if strategist is not None and hasattr(strategist, "log"):
            strategist.log = log
        if args.no_render:
            _m0_loop(world, creatures, log, rng, args.ticks, on_tick=None,
                     match_seed=args.seed, laws=laws, strategist=strategist)
        else:
            frame_delay = 1.0 / args.fps if args.fps > 0 else 0.0
            refresh_rate = max(1, int(round(args.fps))) if args.fps > 0 else 10
            with Live(render_frame(world, creatures, 0), refresh_per_second=refresh_rate, auto_refresh=False) as live:
                def on_tick(w: World, cs: list[Creature], t: int) -> None:
                    live.update(render_frame(w, cs, t), refresh=True)
                    if frame_delay > 0:
                        time.sleep(frame_delay)

                _m0_loop(world, creatures, log, rng, args.ticks, on_tick=on_tick,
                         match_seed=args.seed, laws=laws, strategist=strategist)
        # Tầng chấm thứ hai, MỘT LẦN, ở tick T−1 (B-09 bất biến 3). Đặt sau vòng
        # lặp vì nó phải hỏi về cả ván, và trước RUN_END vì nó là dữ liệu của ván.
        if laws and strategist is not None and hasattr(strategist, "slots"):
            asyncio.run(run_oracle(
                strategist, creatures, world, laws, args.ticks - 1, args.seed, log
            ))
        log.write(args.ticks, "RUN_END", ticks=args.ticks)

    if not args.no_render:
        print(f"seed={args.seed} ticks={args.ticks} arm={args.arm} -> {args.out}")
    return 0


def cli() -> None:
    configure_console_encoding()
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
