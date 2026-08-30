#!/usr/bin/env python3
"""Đo chi phí gọi Meshy 3D qua N ván mô phỏng (N-13).

Chạy N ván bằng build_match + tick (400 tick mỗi ván, KHÔNG luật, dùng
strategist mặc định), thu mesh_key của MỌI cá thể ở MỌI tick, rồi in ra
số khoá KHÁC NHAU đã gặp — đó là trần số lần gọi Meshy sau warmup.
In cả tổng số (ván × cá thể × tick) để thấy tỉ lệ cache hit.

Sử dụng:
    python scripts/mesh_cost_probe.py --matches 100
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from genesis.tick import build_match, tick
from net.mesh import mesh_key


def run_probe(num_matches: int) -> tuple[int, int, float]:
    seen_keys: set[str] = set()
    total_samples = 0
    ticks_per_match = 400

    t0 = time.perf_counter()
    for match_idx in range(num_matches):
        world, creatures, state, rng = build_match(seed=match_idx + 1)
        for tick_no in range(ticks_per_match):
            tick(world, creatures, tick_no, rng, state)
            for c in creatures:
                key = mesh_key(c.traits)
                seen_keys.add(key)
                total_samples += 1

    elapsed = time.perf_counter() - t0
    unique_keys = len(seen_keys)
    cache_hits = total_samples - unique_keys
    hit_rate = (cache_hits / total_samples * 100.0) if total_samples > 0 else 0.0

    print(f"=== KẾT QUẢ ĐO CHI PHÍ MESH (N={num_matches} ván) ===")
    print(f"Thời gian chạy: {elapsed:.2f} s")
    print(f"Tổng số mẫu quan sát (ván × cá thể × tick): {total_samples}")
    print(f"Số khoá mesh KHÁC NHAU gặp phải: {unique_keys}")
    print(f"Số lượt trúng cache (cache hits): {cache_hits}")
    print(f"Tỉ lệ trúng cache: {hit_rate:.2f}%")
    print(f"Trần số lần gọi Meshy sau warmup: {unique_keys}")

    return total_samples, unique_keys, hit_rate


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Đo trần số lần gọi Meshy và tỉ lệ cache hit qua N ván."
    )
    parser.add_argument(
        "--matches",
        type=int,
        default=10,
        help="Số ván cần chạy (mỗi ván 400 tick, mặc định: 10)",
    )
    args = parser.parse_args()
    if args.matches <= 0:
        print("Lỗi: --matches phải > 0", file=sys.stderr)
        sys.exit(1)

    run_probe(args.matches)


if __name__ == "__main__":
    main()
