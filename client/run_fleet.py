#!/usr/bin/env python3
"""Chạy NHIỀU client cùng lúc vào một server (N-10b).

    python client/run_fleet.py --server http://localhost:8000 \
        --model-url http://localhost:8080 --n 3

Mỗi client là một **loài riêng**: tên riêng, tập tính riêng, `brain_tier` riêng.
Đó là điểm của chế độ mở — thế giới thú vị khi trong đó có nhiều thứ khác nhau,
không phải khi có nhiều bản sao của một thứ.

Dùng để làm gì:

* thử tại chỗ trước khi mời người thật (một máy đóng vai nhiều người chơi);
* lấp sảnh cho một ván cần đủ loài;
* đo tải: `--n 8` rồi nhìn `TICK_RATE` trong log server tự chậm lại.

**Một máy nhiều client KHÔNG thay được nhiều máy.** Ở đây mọi client dùng chung
một `llama-server`, mà decode gần như tuần tự (xem [S-02]) — nên `--n 8` không
cho tám lần thông lượng, nó chỉ chia đôi tám lần. Thứ thật sự mở rộng được là
**số máy**, và đó đúng là hình dạng docs/04 mô tả.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genesis_client import run  # noqa: E402

logger = logging.getLogger("fleet")

# Loài mẫu: tên và tập tính khác nhau rõ rệt để nhìn vào bảng là phân biệt được.
# `brain_tier` trải đều để thấy hiệu ứng của ngân sách token trong cùng một ván.
SPECIES = [
    ("Kiến Lửa", "Đi thành bầy, chia phần cho con yếu, tránh chỗ trống trải.", 4),
    ("Sói Xám", "Săn theo cặp, nhường xác cho con non, không bỏ đồng loại.", 3),
    ("Rùa Đá", "Chậm và chắc, chờ kẻ khác thử trước rồi mới làm theo.", 5),
    ("Cáo Cát", "Đi một mình, thử thứ lạ, chạy trước khi bị dồn.", 2),
    ("Dơi Đêm", "Chỉ ra ngoài lúc tối, nghe nhiều hơn nói.", 3),
    ("Nhím Gai", "Không gây sự, nhưng ai đụng vào thì nhớ mặt.", 1),
    ("Quạ Khoang", "Nhặt nhạnh, bắt chước, kể lại cho đồng loại.", 4),
    ("Thằn Lằn", "Phơi nắng, ăn tạp, không tin ai cả.", 0),
]


async def _fleet(a: argparse.Namespace) -> None:
    tasks = [
        asyncio.create_task(run(
            server=a.server, model_url=a.model_url,
            name=name, persona=persona, brain_tier=tier, pop=a.pop,
            model_name=a.model_name, params_b=a.params_b,
            hold_ms=a.hold_ms, max_rounds=a.rounds,
        ))
        for name, persona, tier in SPECIES[: a.n]
    ]
    # `gather` với `return_exceptions`: một client chết KHÔNG được kéo theo cả
    # đàn. Ở chế độ mở thì đó là chuyện bình thường — mạng rớt, máy ngủ.
    for name, res in zip([s[0] for s in SPECIES[: a.n]],
                         await asyncio.gather(*tasks, return_exceptions=True)):
        if isinstance(res, Exception):
            logger.warning("client %s dừng vì: %s", name, res)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="run_fleet")
    ap.add_argument("--server", default="http://localhost:8000")
    ap.add_argument("--model-url", default="http://localhost:8080")
    ap.add_argument("--n", type=int, default=3, help=f"số client, tối đa {len(SPECIES)}")
    ap.add_argument("--pop", type=int, default=2)
    ap.add_argument("--model-name", default="unknown")
    ap.add_argument("--params-b", type=float, default=0.0)
    ap.add_argument("--hold-ms", type=int, default=25000)
    ap.add_argument("--rounds", type=int, default=None,
                    help="dừng sau N vòng nhận việc (mặc định: chạy mãi)")
    a = ap.parse_args(argv)
    if not 1 <= a.n <= len(SPECIES):
        print(f"--n phải trong 1..{len(SPECIES)}", file=sys.stderr)
        return 2
    try:
        asyncio.run(_fleet(a))
    except KeyboardInterrupt:
        logger.info("đã dừng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
