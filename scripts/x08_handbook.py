#!/usr/bin/env python3
"""X-08 · Cẩm nang có thay được huấn luyện không?

    python scripts/x08_handbook.py --seeds 3 --ticks 200 \
        --llm-url http://127.0.0.1:8080

Mệnh đề cần kiểm, và nó **đo được**:

> Nếu cho agent một **cẩm nang phương pháp** (không phải đáp án) đọc ở đầu mỗi
> ván, `t_discover` có rút ngắn không?

Nếu có, thì [R-03](../docs/tasks/R-03) — huấn luyện — chỉ còn là **tối ưu hoá**,
không phải điều kiện cần: cùng một model, cùng một trọng số, chỉ khác một đoạn
văn trong prompt. Đó là câu hỏi nên hỏi **trước** khi đổ giờ GPU vào RL, và nó
rẻ hơn RL vài bậc độ lớn.

Hai nhánh, khác nhau đúng một biến:

| nhánh | cẩm nang |
|---|---|
| `KHONG_CAM_NANG` | không có gì |
| `CO_CAM_NANG` | bốn bài học phương pháp ở `handbook.SEED_LESSONS` |

**Cẩm nang tuyệt đối không chứa một luật cụ thể nào** — `sanitize_lesson` cưỡng
chế điều đó. Nếu nó chứa, thì nhánh `CO_CAM_NANG` chỉ đang đọc đáp án và phép đo
không nói gì cả.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from genesis.handbook import SEED_LESSONS, Handbook
from genesis.lawgen import generate_cached
from genesis.logio import LogWriter
from genesis.score import score_match
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick


def one_match(seed: int, ticks: int, url: str, out: Path, with_handbook: bool,
              ids: list[str], transport=None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    tag = "co" if with_handbook else "khong"
    log_p, truth_p = out / f"{tag}-{seed}.jsonl", out / f"{tag}-{seed}.truth.json"

    laws = generate_cached(seed, arm="STANDARD")
    world, creatures, state, rng = build_match(seed, laws=laws)
    with LogWriter(log_p, f"hb_{tag}_{seed}") as log:
        log.write(0, "RUN_START", seed=seed, ticks=ticks, arm="STANDARD",
                  n_laws=len(laws))
        strat = LlmStrategist(url, ids, log=log, transport=transport)
        if with_handbook:
            hb = Handbook("*", n_matches=5)
            for lesson in SEED_LESSONS:
                hb.add(lesson)
            text = hb.render()
            for c in creatures:
                strat.handbooks[c.species] = text
        for t in range(ticks):
            tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=strat)
        log.write(ticks, "RUN_END", ticks=ticks)

    from genesis.lawdsl import to_json

    truth_p.write_text(json.dumps({
        "seed": seed, "arm": "STANDARD", "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }, ensure_ascii=False), encoding="utf-8")

    rows = score_match(log_p, truth_p)
    found = [r for r in rows if str(r.get("found")).lower() in ("true", "1")]
    return {
        "seed": seed, "handbook": with_handbook,
        "n_found": len(found),
        "best_match": max((float(r["match"]) for r in rows), default=0.0),
        "mean_t_discover": statistics.fmean(int(r["t_discover"]) for r in found)
        if found else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--llm-url", default="http://127.0.0.1:8080")
    ap.add_argument("--ids", default="L1:0,L1:1,L2:0,L5:0")
    ap.add_argument("--out", type=Path, default=Path("runs/handbook"))
    a = ap.parse_args(argv)

    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    rows = []
    for seed in range(1, a.seeds + 1):
        for hb in (False, True):
            r = one_match(seed, a.ticks, a.llm_url, a.out, hb, ids)
            rows.append(r)
            print(f"  seed {seed} · cẩm nang {'CÓ ' if hb else 'KHÔNG'} · "
                  f"tìm ra {r['n_found']} · match cao nhất {r['best_match']:.2f} · "
                  f"t_discover {r['mean_t_discover']}", flush=True)

    (a.out / "x08.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    for hb in (False, True):
        sub = [r for r in rows if r["handbook"] is hb]
        ts = [r["mean_t_discover"] for r in sub if r["mean_t_discover"] is not None]
        print(f"{'CÓ ' if hb else 'KHÔNG'} cẩm nang: tìm ra "
              f"{sum(r['n_found'] for r in sub)} luật · "
              f"t_discover trung bình {statistics.fmean(ts) if ts else 'NA'}")
    print(
        "\nĐọc kết quả: nếu CÓ cẩm nang rút ngắn `t_discover` đáng kể thì huấn\n"
        "luyện là tối ưu hoá, không phải điều kiện cần — cùng model, cùng trọng\n"
        "số, chỉ khác một đoạn văn. Nếu không đổi gì, thì phương pháp không\n"
        "truyền được bằng lời và R-03 mới là con đường.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
