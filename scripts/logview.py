#!/usr/bin/env python3
"""Xem log JSONL của một ván. Lọc theo loại sự kiện, cá thể, khoảng tick."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from genesis.logio import COMMON_FIELDS, read_log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Xem log ván Genesis Zero")
    ap.add_argument("file", type=Path)
    ap.add_argument("--kind", action="append", help="lọc theo loại (dùng nhiều lần được)")
    ap.add_argument("--creature", help="lọc theo creature_id")
    ap.add_argument("--tick-range", help="A:B", default=None)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args(argv)

    rows = read_log(args.file)
    if args.kind:
        keep = set(args.kind)
        rows = [r for r in rows if r["kind"] in keep]
    if args.creature:
        rows = [r for r in rows if r.get("creature_id") == args.creature]
    if args.tick_range:
        lo, _, hi = args.tick_range.partition(":")
        lo_i = int(lo) if lo else 0
        hi_i = int(hi) if hi else 10**9
        rows = [r for r in rows if lo_i <= r["t"] <= hi_i]

    shown = rows[: args.limit]
    extra_keys: list[str] = []
    for r in shown:
        for k in r:
            if k not in COMMON_FIELDS and k not in extra_keys:
                extra_keys.append(k)

    table = Table(box=None, pad_edge=False, header_style="dim")
    table.add_column("t", justify="right", style="dim")
    table.add_column("kind")
    table.add_column("creature", style="dim")
    for k in extra_keys:
        table.add_column(k)
    for r in shown:
        table.add_row(
            str(r["t"]),
            r["kind"],
            r.get("creature_id") or "",
            *[("" if r.get(k) is None else str(r.get(k))) for k in extra_keys],
        )

    console = Console()
    console.print(table)
    console.print(f"[dim]{len(shown)} / {len(rows)} dòng[/dim]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
