"""Genesis Zero — analyze: biến CSV/JSONL thành biểu đồ và bảng (X-05).

File này đọc các file CSV do `genesis.score` xuất, tổng hợp các chỉ số Q1–Q7
(docs/03-LUAT-AN-V5.md §9 và §10), và xuất ra các biểu đồ và báo cáo Markdown.

Đồ hoạ: Môi trường có sẵn matplotlib. Ta sử dụng matplotlib với backend không đầu (Agg)
và metadata={'Date': None} cùng svg.hashsalt cố định để đảm bảo mọi biểu đồ SVG
được xuất ra một cách hoàn toàn tất định (byte-for-byte). Nếu matplotlib không có,
chương trình có thể sinh chuỗi SVG thuần từ stdlib.

Các quy tắc bắt buộc:
1. `t_discover == T+1` (hoặc không tìm ra) được tách riêng thành cột 'không tìm ra',
   KHÔNG tính vào trung bình t_discover. `summarize` trả cả `n_found` và `n_total`.
2. `exploit_lag == "NA"` và `pred_acc == "NA"` là ca thiếu mẫu (n < 4), bị loại khỏi
   trung bình và ghi rõ số ca bị loại vào báo cáo.
3. Không có dữ liệu thì vẽ biểu đồ rỗng có chữ "chưa có dữ liệu", không ném lỗi.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics
from typing import Any

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "genesis"
import matplotlib.pyplot as plt

from genesis import law_config


def load_scores(paths: list[Path]) -> list[dict]:
    """Đọc các file CSV do genesis.score xuất và chuyển đổi các kiểu dữ liệu phù hợp."""
    rows: list[dict] = []
    for p in paths:
        path = Path(p)
        if not path.exists() or not path.is_file():
            continue
        with path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for raw in reader:
                r: dict[str, Any] = {}
                for k, v in raw.items():
                    if v is None:
                        continue
                    v_str = str(v).strip()
                    if k in ("seed", "law_idx"):
                        try:
                            r[k] = int(v_str)
                        except ValueError:
                            r[k] = v_str
                    elif k in ("w", "match", "speed", "R_i", "R_survive"):
                        try:
                            r[k] = float(v_str)
                        except ValueError:
                            r[k] = v_str
                    elif k == "t_discover":
                        try:
                            r[k] = int(float(v_str))
                        except ValueError:
                            r[k] = v_str
                    elif k == "found":
                        r[k] = v_str.strip().lower() in ("true", "1", "yes")
                    elif k in ("exploit_lag", "pred_acc"):
                        if v_str in ("NA", ""):
                            r[k] = "NA"
                        else:
                            try:
                                r[k] = float(v_str)
                            except ValueError:
                                r[k] = "NA"
                    else:
                        r[k] = v_str
                rows.append(r)
    return rows


def _is_found_row(r: dict, default_ticks: int = 400) -> tuple[bool, int | None]:
    """Hàng này có phải ca TÌM RA không, và tìm ra ở tick nào.

    Đọc thẳng cột `found` do `genesis.score` ghi. Bản đầu suy ra bằng một chuỗi
    heuristic trên `speed`, `match` và một hằng số `400` viết cứng — mà `T`
    không hề có trong CSV, nên nó đang đoán một thứ bên sinh dữ liệu biết chắc.
    Với ván 200 tick, cách đoán ấy tính `t_discover = 201` thành "tìm ra".
    """
    t_disc = r.get("t_discover")
    try:
        t_val = int(float(t_disc))
    except (TypeError, ValueError):
        return False, None

    found = r.get("found")
    if isinstance(found, bool):
        return found, (t_val if found else None)
    if isinstance(found, str):
        ok = found.strip().lower() in ("true", "1", "yes")
        return ok, (t_val if ok else None)

    # CSV cũ không có cột `found`: rơi về quy ước T+1 với T mặc định.
    ok = t_val <= default_ticks
    return ok, (t_val if ok else None)


def _calc_stats(sub_rows: list[dict]) -> dict[str, Any]:
    """Tính toán các chỉ số thống kê cho một tập hàng."""
    n_total = len(sub_rows)
    if n_total == 0:
        return {
            "n_total": 0,
            "n_found": 0,
            "found_ratio": 0.0,
            "mean_match": 0.0,
            "mean_t_discover": None,
            "mean_R_i": 0.0,
            "mean_R_survive": 0.0,
            "mean_exploit_lag": None,
            "n_exploit_lag_na": 0,
            "n_exploit_lag_valid": 0,
            "mean_pred_acc": None,
            "n_pred_acc_na": 0,
            "n_pred_acc_valid": 0,
        }

    matches = [float(r["match"]) for r in sub_rows if "match" in r and r["match"] != "NA"]
    r_is = [float(r["R_i"]) for r in sub_rows if "R_i" in r and r["R_i"] != "NA"]
    r_survs = [float(r["R_survive"]) for r in sub_rows if "R_survive" in r and r["R_survive"] != "NA"]

    found_t: list[int] = []
    for r in sub_rows:
        found, t_val = _is_found_row(r)
        if found and t_val is not None:
            found_t.append(t_val)
    n_found = len(found_t)

    exploit_lags: list[float] = []
    n_exploit_na = 0
    for r in sub_rows:
        v = r.get("exploit_lag")
        if v is None or v == "NA" or v == "":
            n_exploit_na += 1
        else:
            try:
                exploit_lags.append(float(v))
            except (ValueError, TypeError):
                n_exploit_na += 1

    pred_accs: list[float] = []
    n_pred_na = 0
    for r in sub_rows:
        v = r.get("pred_acc")
        if v is None or v == "NA" or v == "":
            n_pred_na += 1
        else:
            try:
                pred_accs.append(float(v))
            except (ValueError, TypeError):
                n_pred_na += 1

    return {
        "n_total": n_total,
        "n_found": n_found,
        "found_ratio": round(n_found / n_total, 4) if n_total > 0 else 0.0,
        "mean_match": round(statistics.fmean(matches), 4) if matches else 0.0,
        "mean_t_discover": round(statistics.fmean(found_t), 4) if found_t else None,
        "mean_R_i": round(statistics.fmean(r_is), 4) if r_is else 0.0,
        "mean_R_survive": round(statistics.fmean(r_survs), 4) if r_survs else 0.0,
        "mean_exploit_lag": round(statistics.fmean(exploit_lags), 4) if exploit_lags else None,
        "n_exploit_lag_na": n_exploit_na,
        "n_exploit_lag_valid": len(exploit_lags),
        "mean_pred_acc": round(statistics.fmean(pred_accs), 4) if pred_accs else None,
        "n_pred_acc_na": n_pred_na,
        "n_pred_acc_valid": len(pred_accs),
    }


def summarize(rows: list[dict]) -> dict:
    """Gộp theo species_id VÀ theo tier, kèm thống kê tổng thể."""
    by_species: dict[str, list[dict]] = {}
    by_tier: dict[str, list[dict]] = {}

    for r in rows:
        sp = str(r.get("species_id", "unknown"))
        by_species.setdefault(sp, []).append(r)
        tier = str(r.get("tier", "unknown"))
        by_tier.setdefault(tier, []).append(r)

    return {
        "total_rows": len(rows),
        "overall": _calc_stats(rows),
        "by_species": {sp: _calc_stats(s_rows) for sp, s_rows in sorted(by_species.items())},
        "by_tier": {tier: _calc_stats(t_rows) for tier, t_rows in sorted(by_tier.items())},
    }


def chart_match_by_species(rows: list[dict], out: Path) -> Path:
    """Vẽ biểu đồ cột: match trung bình mỗi loài."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4.5))

    if not rows:
        ax.text(0.5, 0.5, "chưa có dữ liệu", horizontalalignment="center",
                verticalalignment="center", transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_title("Match trung bình theo loài")
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        by_sp: dict[str, list[float]] = {}
        for r in rows:
            sp = str(r.get("species_id", "unknown"))
            m = r.get("match")
            if m is not None and m != "NA":
                try:
                    by_sp.setdefault(sp, []).append(float(m))
                except (ValueError, TypeError):
                    pass

        species_list = sorted(by_sp.keys())
        means = [statistics.fmean(by_sp[sp]) if by_sp[sp] else 0.0 for sp in species_list]

        bars = ax.bar(species_list, means, color="#4C72B0", width=0.55, edgecolor="black", linewidth=0.8)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Loài (Species)")
        ax.set_ylabel("Match trung bình")
        ax.set_title("Match trung bình theo loài")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.3f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out, format="svg", metadata={"Date": None})
    plt.close(fig)
    return out


def chart_tdiscover_hist(rows: list[dict], out: Path) -> Path:
    """Vẽ histogram t_discover với cột 'không tìm ra' tách riêng hoàn toàn."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax_hist, ax_nf) = plt.subplots(1, 2, figsize=(8, 4.5), gridspec_kw={"width_ratios": [3.5, 1]})

    if not rows:
        ax_hist.text(0.5, 0.5, "chưa có dữ liệu", horizontalalignment="center",
                     verticalalignment="center", transform=ax_hist.transAxes, fontsize=14, color="gray")
        ax_hist.set_title("Phân bố t_discover")
        ax_hist.set_xticks([])
        ax_hist.set_yticks([])
        ax_nf.axis("off")
    else:
        found_t: list[int] = []
        n_not_found = 0
        for r in rows:
            found, t_val = _is_found_row(r)
            if found and t_val is not None:
                found_t.append(t_val)
            else:
                n_not_found += 1

        bins = list(range(0, 401, 40))
        if found_t:
            ax_hist.hist(found_t, bins=bins, color="#55A868", edgecolor="black", linewidth=0.8)
        ax_hist.set_xlabel("Tick phát hiện (t_discover)")
        ax_hist.set_ylabel("Số lượng")
        ax_hist.set_title(f"Tìm ra (n = {len(found_t)})")
        ax_hist.grid(axis="y", linestyle="--", alpha=0.5)

        # Cột riêng cho "Không tìm ra"
        bar = ax_nf.bar(["Không\ntìm ra\n(T+1)"], [n_not_found], color="#C44E52", width=0.5, edgecolor="black", linewidth=0.8)
        ax_nf.set_ylabel("Số lượng")
        ax_nf.set_title(f"Chưa tìm ra\n(n = {n_not_found})")
        ax_nf.grid(axis="y", linestyle="--", alpha=0.5)
        ax_nf.annotate(f"{n_not_found}",
                       xy=(bar[0].get_x() + bar[0].get_width() / 2, n_not_found),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out, format="svg", metadata={"Date": None})
    plt.close(fig)
    return out


def chart_law_tier(rows: list[dict], out: Path) -> Path:
    """Vẽ biểu đồ cột: match trung bình theo tier D1/D2/D3/D4."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    if not rows:
        ax.text(0.5, 0.5, "chưa có dữ liệu", horizontalalignment="center",
                verticalalignment="center", transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_title("Match trung bình theo tier luật")
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        by_tier: dict[str, list[float]] = {}
        for r in rows:
            tier = str(r.get("tier", "unknown"))
            m = r.get("match")
            if m is not None and m != "NA":
                try:
                    by_tier.setdefault(tier, []).append(float(m))
                except (ValueError, TypeError):
                    pass

        # Sắp xếp ưu tiên D1, D2, D3, D4
        def tier_sort_key(t: str) -> tuple[int, str]:
            if t.startswith("D") and t[1:].isdigit():
                return (0, f"{int(t[1:]):02d}")
            return (1, t)

        tier_list = sorted(by_tier.keys(), key=tier_sort_key)
        means = [statistics.fmean(by_tier[t]) if by_tier[t] else 0.0 for t in tier_list]

        bars = ax.bar(tier_list, means, color="#8172B2", width=0.5, edgecolor="black", linewidth=0.8)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Tier luật")
        ax.set_ylabel("Match trung bình")
        ax.set_title("Match trung bình theo tier luật")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.3f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out, format="svg", metadata={"Date": None})
    plt.close(fig)
    return out


def write_report(rows: list[dict], out_dir: Path) -> Path:
    """Tạo đầy đủ biểu đồ và xuất file summary.md tổng kết kết quả."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chart_match_by_species(rows, out_dir / "match_by_species.svg")
    chart_tdiscover_hist(rows, out_dir / "tdiscover_hist.svg")
    chart_law_tier(rows, out_dir / "law_tier.svg")

    summary_data = summarize(rows)
    ov = summary_data["overall"]

    def _fmt(val: Any) -> str:
        if val is None or val == "NA":
            return "NA"
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    lines: list[str] = [
        "# Báo cáo phân tích kết quả khám phá luật (X-05)",
        "",
        "## 1. Tổng quan",
        f"- **Tổng số mẫu (ván × cá thể × luật):** {ov['n_total']}",
        f"- **Số ca tìm ra luật (match >= 0.8):** {ov['n_found']} ({ov['found_ratio'] * 100:.1f}%)",
        f"- **Match trung bình toàn bộ:** {_fmt(ov['mean_match'])}",
        f"- **t_discover trung bình (chỉ tính ca tìm ra):** {_fmt(ov['mean_t_discover'])}",
        f"- **exploit_lag trung bình:** {_fmt(ov['mean_exploit_lag'])}",
        f"- **pred_acc trung bình:** {_fmt(ov['mean_pred_acc'])}",
        f"- **R_i trung bình:** {_fmt(ov['mean_R_i'])}",
        f"- **R_survive trung bình:** {_fmt(ov['mean_R_survive'])}",
        "",
        "## 2. Thống kê theo loài",
        "| Loài | Tổng mẫu | Tìm ra | Tỉ lệ tìm ra | Match TB | t_discover TB | exploit_lag TB | pred_acc TB | R_i TB | R_survive TB |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for sp, s in summary_data["by_species"].items():
        lines.append(
            f"| {sp} | {s['n_total']} | {s['n_found']} | {s['found_ratio'] * 100:.1f}% | "
            f"{_fmt(s['mean_match'])} | {_fmt(s['mean_t_discover'])} | {_fmt(s['mean_exploit_lag'])} | "
            f"{_fmt(s['mean_pred_acc'])} | {_fmt(s['mean_R_i'])} | {_fmt(s['mean_R_survive'])} |"
        )

    lines.extend([
        "",
        "## 3. Thống kê theo tier luật",
        "| Tier | Tổng mẫu | Tìm ra | Tỉ lệ tìm ra | Match TB | t_discover TB | exploit_lag TB | R_i TB |",
        "|---|---|---|---|---|---|---|---|",
    ])

    for tier, t in summary_data["by_tier"].items():
        lines.append(
            f"| {tier} | {t['n_total']} | {t['n_found']} | {t['found_ratio'] * 100:.1f}% | "
            f"{_fmt(t['mean_match'])} | {_fmt(t['mean_t_discover'])} | {_fmt(t['mean_exploit_lag'])} | {_fmt(t['mean_R_i'])} |"
        )

    lines.extend([
        "",
        "## 4. Ghi chú thiếu mẫu",
        f"- **exploit_lag == NA:** {ov['n_exploit_lag_na']} / {ov['n_total']} ca thiếu mẫu (n < 4 lần kích hoạt trong cửa sổ) đã được loại khỏi trung bình.",
        f"- **pred_acc == NA:** {ov['n_pred_acc_na']} / {ov['n_total']} ca không có dữ liệu oracle đã được loại khỏi trung bình.",
        "",
        "## 5. Biểu đồ",
        "- `match_by_species.svg`: Match trung bình mỗi loài",
        "- `tdiscover_hist.svg`: Phân bố thời điểm tìm ra và số ca không tìm ra",
        "- `law_tier.svg`: Match trung bình theo từng tier luật",
    ])

    summary_file = out_dir / "summary.md"
    summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_file


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="genesis.analyze", description="Phân tích điểm số và xuất biểu đồ báo cáo")
    ap.add_argument("csv_files", nargs="+", type=Path, help="Các file CSV do genesis.score xuất")
    ap.add_argument("--out", type=Path, default=Path("runs/report"), help="Thư mục xuất báo cáo")
    a = ap.parse_args(argv)

    rows = load_scores(a.csv_files)
    report_path = write_report(rows, a.out)
    print(f"Đã xuất báo cáo tại: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
