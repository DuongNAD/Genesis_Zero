#!/usr/bin/env python3
"""X-02 điều kiện (2): `t_discover` có phải TRUNG GIAN của lợi thế brain không?

    python scripts/x02_mediation.py runs/*.csv

Điều kiện (1) — chênh lệch sinh tồn co lại ở `WORLD_FLAT` — đo bằng
`scripts/x02_gate.py` và không cần model. Điều kiện (2) thì cần: nó hỏi liệu
chênh lệch ở `WORLD_LAW` có **đi qua** việc khám phá hay không.

    hồi quy 1:  survival ~ brain
    hồi quy 2:  survival ~ brain + t_discover

Nếu hệ số của `brain` **tụt đáng kể** ở hồi quy 2 thì `t_discover` là trung gian:
não to sống dai hơn *vì* nó tìm ra luật sớm hơn. Nếu không tụt, thì khám phá và
sinh tồn là hai thứ rời nhau, và [03 §10.1](../docs/03-LUAT-AN-V5.md) nói rõ phải
làm gì lúc ấy — nâng hệ số `R_survive`, hoặc sinh luật có tác động sinh tồn mạnh
hơn. **Không phải đổi model.**

Bình phương tối thiểu viết tay bằng phương trình chuẩn: ba biến thì `numpy.linalg`
là đủ, và một phụ thuộc `statsmodels` cho một phép hồi quy ba cột là không đáng.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def load(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for p in paths:
        with Path(p).open(encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    return rows


def ols(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Trả (hệ số, sai số chuẩn). Cột đầu của X là hằng số."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    if n <= k:
        return beta, np.full(k, np.nan)
    s2 = float(resid @ resid) / (n - k)
    cov = s2 * np.linalg.pinv(X.T @ X)
    return beta, np.sqrt(np.diag(cov))


def mediation(rows: list[dict]) -> dict:
    from genesis.traits import founder_traits

    # Một dòng mỗi (cá thể, luật) -> gộp về một dòng mỗi cá thể: sinh tồn là của
    # cá thể, không của từng luật, và đếm lặp sẽ thổi phồng cỡ mẫu.
    per: dict[str, dict] = {}
    for r in rows:
        cid = r["creature_id"]
        d = per.setdefault(cid, {"surv": float(r["R_survive"]), "t": [], "sp": r["species_id"]})
        found = str(r.get("found", "")).lower() in ("true", "1", "yes")
        if found:
            d["t"].append(int(float(r["t_discover"])))

    ids = sorted(per)
    if not ids:
        return {"n": 0, "error": "không có dòng nào"}

    surv = np.array([per[c]["surv"] for c in ids])
    brain = np.array([float(founder_traits(per[c]["sp"]).brain)
                      if per[c]["sp"] in ("L1", "L2", "L3", "L4", "L5") else np.nan
                      for c in ids])
    # Không tìm ra -> `t_discover` không xác định. Đưa `T+1` vào hồi quy là bịa
    # một con số cho một thứ chưa xảy ra; chỉ hồi quy trên các ca CÓ khám phá.
    t = np.array([min(per[c]["t"]) if per[c]["t"] else np.nan for c in ids])

    ok = ~np.isnan(brain)
    n_found = int((~np.isnan(t) & ok).sum())
    one = np.ones(ok.sum())
    b1, se1 = ols(np.column_stack([one, brain[ok]]), surv[ok])

    out = {
        "n": int(ok.sum()), "n_found": n_found,
        "beta_brain_alone": round(float(b1[1]), 5),
        "se_brain_alone": round(float(se1[1]), 5),
    }
    if n_found < 8:
        out["verdict"] = (
            f"CHƯA ĐO ĐƯỢC: chỉ {n_found} cá thể tìm ra được luật nào. "
            "Trung gian không đo được khi gần như không ai khám phá — cần một "
            "model đủ giỏi, KHÔNG phải một mẫu lớn hơn của cùng model."
        )
        return out

    m = ok & ~np.isnan(t)
    b2, se2 = ols(np.column_stack([np.ones(m.sum()), brain[m], t[m]]), surv[m])
    drop = 1 - abs(float(b2[1])) / max(abs(float(b1[1])), 1e-9)
    out.update({
        "beta_brain_with_t": round(float(b2[1]), 5),
        "se_brain_with_t": round(float(se2[1]), 5),
        "beta_t_discover": round(float(b2[2]), 6),
        "shrink_pct": round(100 * drop, 1),
        "verdict": (
            "TRUNG GIAN: hệ số brain tụt >= 40% khi thêm t_discover — não to sống "
            "dai hơn VÌ nó tìm ra luật sớm hơn."
            if drop >= 0.4 else
            "KHÔNG TRUNG GIAN: khám phá và sinh tồn rời nhau. Xem 03 §10.1 — nâng "
            "hệ số R_survive, hoặc sinh luật có tác động sinh tồn mạnh hơn. "
            "ĐỪNG đổi model."
        ),
    })
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+", type=Path)
    a = ap.parse_args(argv)
    res = mediation(load(a.csv))
    for k, v in res.items():
        print(f"{k:>20}: {v}")
    return 0 if res.get("n") else 1


if __name__ == "__main__":
    raise SystemExit(main())
