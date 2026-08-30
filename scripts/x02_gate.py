#!/usr/bin/env python3
"""X-02 · Thí nghiệm gác cổng `WORLD_FLAT` vs `WORLD_LAW` (03 §10.1).

    python scripts/x02_gate.py --seeds 40 --ticks 400

Đây là **mốc gác cổng, không phải mốc báo cáo.** Chạy nó TRƯỚC khi đổ 40 giờ máy
vào Q1–Q6: nếu không qua thì mọi số liệu sau đó đều đo nhầm thứ, và ta cần biết
điều đó trong tuần đầu chứ không phải tháng sau.

Mệnh đề được kiểm: *model to = loài đầu bảng, vì nó quy nạp giỏi hơn nên sống dai
hơn **một cách có lý do**.* Hai nhánh khác nhau đúng một biến — có luật ẩn hay
không — và hai tiên đoán:

1. Ở `FLAT`, chênh lệch sinh tồn L1 − L5 **co lại rõ rệt** so với `LAW`.
2. Ở `LAW`, chênh lệch đó **có trung gian là `t_discover`**.

Tiên đoán (2) chỉ đo được khi có agent thật ghi Sổ Luật, nên script này dừng ở
(1) và nói thẳng ra điều đó. Chạy nó với `--controller reflex` (mặc định) cho ta
**đường cơ sở null**: nếu chênh lệch L1 − L5 đã lớn khi CHƯA con nào suy luận gì,
thì lợi thế ấy đến từ founder vector chứ không từ quy nạp — và ta phải biết con
số đó trước khi quy công cho model.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from genesis.batch import Run, run_many


def _mean(xs: list[float]) -> float:
    return statistics.fmean(xs) if xs else float("nan")


def _welch(a: list[float], b: list[float]) -> tuple[float, float]:
    """t và bậc tự do Welch. Hai nhóm khác phương sai — đừng dùng t gộp."""
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    va, vb = statistics.variance(a), statistics.variance(b)
    na, nb = len(a), len(b)
    se = (va / na + vb / nb) ** 0.5
    if se == 0:
        return float("nan"), float("nan")
    t = (_mean(a) - _mean(b)) / se
    df = (va / na + vb / nb) ** 2 / (
        (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    )
    return t, df


def gate(seeds: int, ticks: int, workers: int) -> dict:
    jobs = [
        Run(seed=s, arm="STANDARD", ticks=ticks, laws_on=on)
        for s in range(1, seeds + 1)
        for on in (True, False)
    ]
    rows = run_many(jobs, workers=workers)

    out: dict = {"seeds": seeds, "ticks": ticks, "by_world": {}}
    for world in ("LAW", "FLAT"):
        sub = [r for r in rows if r["world"] == world]
        by_sp = {}
        for r in sub:
            by_sp.setdefault(r["species_id"], []).append(r["alive_ratio"])
        top = max(by_sp, key=lambda k: founder_brain_of(rows, k))
        bot = min(by_sp, key=lambda k: founder_brain_of(rows, k))
        t, df = _welch(by_sp[top], by_sp[bot])
        out["by_world"][world] = {
            "per_species": {k: round(_mean(v), 4) for k, v in sorted(by_sp.items())},
            "top": top, "bottom": bot,
            "gap": round(_mean(by_sp[top]) - _mean(by_sp[bot]), 4),
            "welch_t": round(t, 3), "df": round(df, 1),
            "n_per_group": len(by_sp[top]),
        }
    g_law = out["by_world"]["LAW"]["gap"]
    g_flat = out["by_world"]["FLAT"]["gap"]
    out["shrink"] = round(g_law - g_flat, 4)
    # KHÔNG in phần trăm co lại: khi `gap` âm (điều thực sự xảy ra ở đường cơ sở
    # null) thì tỉ số phần trăm ra những con số như -452% và chỉ gây hiểu nhầm.
    out["verdict"] = _verdict(g_law, g_flat, out["by_world"])
    return out


def _verdict(g_law: float, g_flat: float, by_world: dict) -> str:
    t_flat = by_world["FLAT"]["welch_t"]
    if g_flat > 0 and abs(t_flat) > 2:
        return (
            "CẢNH BÁO: loài brain cao đã thắng ĐÁNG KỂ ngay ở thế giới KHÔNG có gì "
            "để khám phá. Lợi thế ấy đến từ founder vector hoặc từ tầng phản xạ, "
            "không từ quy nạp. Xem 03 §10.1 — thiết kế chưa đạt mục tiêu."
        )
    if g_flat <= 0:
        return (
            "TỐT cho đường cơ sở: ở FLAT, loài brain cao KHÔNG hề có lợi thế "
            f"(chênh {g_flat:+.4f}). Nghĩa là mọi khoảng cách L1−L5 đo được về sau, "
            "khi có model thật, là khoảng cách KIẾM ĐƯỢC chứ không phải được cho."
        )
    return "Chênh lệch ở FLAT nhỏ và không có ý nghĩa thống kê — đường cơ sở sạch."


def founder_brain_of(rows: list[dict], species: str) -> int:
    for r in rows:
        if r["species_id"] == species:
            return r["founder_brain"]
    return -1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    res = gate(a.seeds, a.ticks, a.workers)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n── Đọc kết quả ──", file=sys.stderr)
    print(
        "Đây là đường cơ sở NULL: chưa con nào suy luận gì, mọi chênh lệch đến từ\n"
        "founder vector và tầng phản xạ. Con số cần so về sau là chênh lệch khi CÓ\n"
        "model thật. Nếu chênh lệch lúc đó không lớn hơn đáng kể con số dưới đây,\n"
        "thì lợi thế của model to KHÔNG đến từ quy nạp — và [03 §10.1] nói rõ phải\n"
        "làm gì lúc ấy.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
