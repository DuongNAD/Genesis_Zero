#!/usr/bin/env python3
"""Genesis Zero — x06_report: Gom toàn bộ dữ liệu thành báo cáo Q1–Q7 (X-06).

CLI: python scripts/x06_report.py --out runs/report-q/ [--data runs/]

Tài liệu tham chiếu: docs/03-LUAT-AN-V5.md §9 (bảng Q1–Q7) và §10.
Nguồn dữ liệu:
  - runs/*.csv (genesis.score) qua genesis.analyze.load_scores / summarize
  - runs/x02-null.json nếu có (cổng gác WORLD_FLAT)
  - runs/x03.json nếu có (ba nhánh prior)
  - runs/x04_arms.json nếu có (nhánh đối chứng)

BẤT BIẾN:
- TUYỆT ĐỐI KHÔNG bịa số.
- Thiếu dữ liệu thì ghi rõ "chưa đo được" và ghi rõ câu lệnh cần chạy để có.
- Hai lần chạy cùng dữ liệu cho file giống hệt nhau byte-for-byte.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from genesis.analyze import load_scores, summarize


def _fmt(val: Any) -> str:
    """Định dạng số nhất quán, tránh khác biệt biểu diễn float."""
    if val is None or val == "NA":
        return "NA"
    if isinstance(val, float):
        return f"{val:.4f}"
    return str(val)


def build_q_report(
    data_dir: Path | None = None,
    csv_files: list[Path] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Xây dựng nội dung báo cáo Markdown trả lời Q1–Q7 từ dữ liệu thực tế."""
    d_dir = Path(data_dir) if data_dir is not None else Path("runs")

    # 1. Tìm các file CSV
    actual_csvs: list[Path] = []
    if csv_files:
        actual_csvs = [Path(p) for p in csv_files if Path(p).exists()]
    elif d_dir.exists() and d_dir.is_dir():
        actual_csvs = sorted(d_dir.glob("*.csv"))

    rows = load_scores(actual_csvs) if actual_csvs else []
    summary = summarize(rows)
    ov = summary["overall"]

    # 2. Đọc file cổng gác x02-null.json nếu có
    x02_data: dict[str, Any] | None = None
    x02_paths = [
        d_dir / "x02-null.json",
        d_dir / "x02.json",
        Path("runs/x02-null.json"),
    ]
    for p in x02_paths:
        if p.exists() and p.is_file():
            try:
                x02_data = json.loads(p.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, OSError):
                pass

    # 3. Đọc file prior x03.json nếu có
    x03_data: list[dict[str, Any]] | dict[str, Any] | None = None
    x03_paths = [
        d_dir / "x03.json",
        Path("runs/x03.json"),
    ]
    for p in x03_paths:
        if p.exists() and p.is_file():
            try:
                x03_data = json.loads(p.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, OSError):
                pass

    # 4. Đọc file x04_arms.json nếu có
    x04_data: dict[str, Any] | None = None
    x04_paths = [
        d_dir / "x04_arms.json",
        d_dir / "x04.json",
        Path("runs/x04_arms.json"),
    ]
    for p in x04_paths:
        if p.exists() and p.is_file():
            try:
                x04_data = json.loads(p.read_text(encoding="utf-8"))
                break
            except (json.JSONDecodeError, OSError):
                pass

    lines: list[str] = [
        "# Báo cáo Nghiên cứu Toàn diện Q1–Q7 (Genesis Zero v5)",
        "",
        "> Tham chiếu chuẩn: `docs/03-LUAT-AN-V5.md §9` và `§10`.",
        "",
        "## 0. Nguồn dữ liệu & Hiện trạng",
        f"- **Thư mục dữ liệu:** `{d_dir}`",
        f"- **Số file điểm CSV:** {len(actual_csvs)} file ({ov['n_total']} dòng mẫu)",
        f"- **Cổng gác x02-null (WORLD_FLAT):** {'Đã có dữ liệu' if x02_data else 'Chưa có dữ liệu'}",
        f"- **Thí nghiệm prior x03:** {'Đã có dữ liệu' if x03_data else 'Chưa có dữ liệu'}",
        f"- **Thí nghiệm đối chứng x04 (Arms):** {'Đã có dữ liệu' if x04_data else 'Chưa có dữ liệu'}",
        "",
        "---",
        "",
        "## Q1: Model to có quy nạp nhanh và đúng hơn không?",
        "- **Đo bằng:** `t_discover`, `match`, `pred_acc` theo loài (`species_id` L1..L5).",
    ]

    # Q1 Nội dung
    if ov["n_total"] == 0:
        lines.extend([
            "- **Trạng thái:** **chưa đo được**",
            "- **Lý do:** Chưa có dữ liệu điểm số từ các ván chạy (`runs/*.csv`).",
            "- **Lệnh cần chạy để có dữ liệu:**",
            "  ```bash",
            "  for s in 1 2 3 4 5; do",
            "    python -m genesis.run --seed $s --ticks 400 --llm all \\",
            "      --llm-url http://127.0.0.1:8080 --no-render \\",
            "      --out runs/m-$s.jsonl --truth runs/m-$s.truth.json",
            "    python -m genesis.score runs/m-$s.jsonl runs/m-$s.truth.json \\",
            "      >> runs/scores.csv",
            "  done",
            "  python scripts/x06_report.py --data runs/ --out runs/report-q/",
            "  ```",
        ])
    else:
        lines.extend([
            f"- **Trạng thái:** **đã đo trên {ov['n_total']} mẫu** (tìm ra {ov['n_found']}/{ov['n_total']} lượt = {ov['found_ratio'] * 100:.1f}%)",
            "",
            "| Loài | Tổng mẫu | Tìm ra | Tỉ lệ tìm ra | Match TB | t_discover TB | exploit_lag TB | pred_acc TB | R_i TB | R_survive TB |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ])
        for sp, s in sorted(summary["by_species"].items()):
            lines.append(
                f"| {sp} | {s['n_total']} | {s['n_found']} | {s['found_ratio'] * 100:.1f}% | "
                f"{_fmt(s['mean_match'])} | {_fmt(s['mean_t_discover'])} | {_fmt(s['mean_exploit_lag'])} | "
                f"{_fmt(s['mean_pred_acc'])} | {_fmt(s['mean_R_i'])} | {_fmt(s['mean_R_survive'])} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## Q2: Giao tiếp có làm quần thể biết nhanh hơn không?",
        "- **Đo bằng:** `diffusion_t50`, `t_discover` gộp quần thể; so sánh VOCAL (STANDARD) vs SILENT.",
    ])

    # Q2 Nội dung
    if x04_data and "summary" in x04_data:
        s_arms = x04_data["summary"]
        lines.extend([
            "- **Trạng thái:** **đã đo qua thí nghiệm nhánh đối chứng (X-04)**",
            f"- **Số seed:** {x04_data.get('seeds')}, **Ticks:** {x04_data.get('ticks')}",
            "",
            "| Nhánh | alive_ratio TB | Tổng số chết | Match cao nhất | Số ván |",
            "|---|---|---|---|---|",
        ])
        for arm in ["LLM", "SILENT", "REFLEX", "RANDOM"]:
            sa = s_arms.get(arm, {})
            lines.append(
                f"| {arm} | {_fmt(sa.get('mean_alive_ratio'))} | {sa.get('total_deaths', 0)} | "
                f"{_fmt(sa.get('max_match'))} | {sa.get('n_runs', 0)} |"
            )
    else:
        lines.extend([
            "- **Trạng thái:** **chưa đo được**",
            "- **Lý do:** Chưa có dữ liệu so sánh có kiểm soát giữa nhánh STANDARD (bật TEACH/SPEAK) và SILENT (tắt SPEAK/TEACH).",
            "- **Lệnh cần chạy để có dữ liệu:**",
            "  ```bash",
            "  python scripts/x04_arms.py --seeds 15 --ticks 400 --out runs/x04_arms.json",
            "  ```",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Q3: Khi nào thì nói dối, và có lãi không?",
        "- **Đo bằng:** `deception_rate`, `deception_payoff` (docs/03 §6.4).",
        "- **Trạng thái:** **chưa đo được**",
        "- **Lý do:** Cần log chi tiết sự kiện TEACH từ model thật trong môi trường nhiều cá thể và đo lường khoảng cách giữa niềm tin trong Sổ Luật với nội dung phát ngôn.",
        "- **Lệnh cần chạy để có dữ liệu:**",
        "  ```bash",
        "  python scripts/deception_probe.py   # tách nói dối khỏi nhầm lẫn",
        "  python scripts/farm_attack.py --pattern all --n 5   # ghi công có farm được không",
        "  # rồi một ván có model thật, xem mục Q1",
        "  ```",
        "",
        "---",
        "",
        "## Q4: Prior rò rỉ bao nhiêu?",
        "- **Đo bằng:** `prior_leak = t_discover(INVERTED) − t_discover(ALIGNED)` giữa 3 nhánh prior (docs/03 §10.2).",
    ])

    # Q4 Nội dung
    if x03_data:
        if isinstance(x03_data, dict) and "prior_leak" in x03_data:
            lines.extend([
                "- **Trạng thái:** **đã đo với model thật**",
                f"- **prior_leak:** `{_fmt(x03_data['prior_leak'])}` tick",
            ])
        else:
            n_seeds_x03 = len(x03_data) if isinstance(x03_data, list) else 0
            lines.extend([
                "- **Trạng thái:** **chưa đo được với model thật (chỉ mới xác nhận phân tách bề mặt)**",
                f"- **Chi tiết:** Đã xác nhận trên {n_seeds_x03} seed rằng 3 nhánh `PRIOR_ALIGNED`, `PRIOR_INVERTED`, `PRIOR_NEUTRAL` có ánh xạ bề mặt phân biệt.",
                "- **Lý do:** Chưa chạy cùng model LLM thật qua `--llm-url`. Tầng phản xạ không đọc màu quả nên `prior_leak = 0` theo định nghĩa.",
                "- **Lệnh cần chạy để có số liệu:**",
                "  ```bash",
                "  python scripts/x03_prior.py --seeds 12 --ticks 400 --llm-url http://127.0.0.1:8000 --out runs/x03.json",
                "  ```",
            ])
    else:
        lines.extend([
            "- **Trạng thái:** **chưa đo được**",
            "- **Lý do:** Chưa có kết quả từ thí nghiệm 3 nhánh prior (`runs/x03.json`).",
            "- **Lệnh cần chạy để có dữ liệu:**",
            "  ```bash",
            "  python scripts/x03_prior.py --seeds 12 --ticks 400 --llm-url http://127.0.0.1:8000 --out runs/x03.json",
            "  ```",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Q5: Biết rồi có làm không?",
        "- **Đo bằng:** `exploit_lag`, tỉ lệ `exploited` (docs/03 §5.4 tầng 3).",
    ])

    # Q5 Nội dung
    if ov["n_total"] == 0:
        lines.extend([
            "- **Trạng thái:** **chưa đo được**",
            "- **Lý do:** Chưa có dữ liệu ghi nhận thời điểm tìm ra luật và hành vi trước/sau khám phá.",
            "- **Lệnh cần chạy để có dữ liệu:**",
            "  ```bash",
            "  # xem mục Q1 để biết lệnh sinh runs/scores.csv",
            "  ```",
        ])
    else:
        lines.extend([
            f"- **Trạng thái:** **đã đo trên {ov['n_exploit_lag_valid']} ca hợp lệ (loại {ov['n_exploit_lag_na']} ca thiếu mẫu n < 4)**",
            f"- **exploit_lag trung bình toàn bộ:** `{_fmt(ov['mean_exploit_lag'])}`",
            "",
            "| Loài | Tổng mẫu | Hợp lệ | Thiếu mẫu (NA) | exploit_lag TB |",
            "|---|---|---|---|---|",
        ])
        for sp, s in sorted(summary["by_species"].items()):
            lines.append(
                f"| {sp} | {s['n_total']} | {s['n_exploit_lag_valid']} | {s['n_exploit_lag_na']} | {_fmt(s['mean_exploit_lag'])} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## Q6: Nó có biết là nó không biết không?",
        "- **Đo bằng:** Brier score trên `conf` (`mean((conf/5 − đúng)²)`).",
        "- **Trạng thái:** **chưa đo được**",
        "- **Lý do:** Cần tập hợp các lượt `CODEX_OP` có khai báo `conf` (1..5) từ model thật để đối chiếu với độ chính xác thực tế (`match >= 0.8`).",
        "- **Lệnh cần chạy để có dữ liệu:**",
        "  ```bash",
        "  # xem mục Q1 để biết lệnh sinh runs/scores.csv",
        "  ```",
        "",
        "---",
        "",
        "## Q7: Lợi thế của não to đến từ quy nạp, hay chỉ đi kèm?",
        "- **Đo bằng:** Thí nghiệm gác cổng `WORLD_FLAT` vs `WORLD_LAW` (docs/03 §10.1).",
    ])

    # Q7 Nội dung
    if x02_data and "by_world" in x02_data:
        bw = x02_data["by_world"]
        law_info = bw.get("LAW", {})
        flat_info = bw.get("FLAT", {})
        lines.extend([
            "- **Trạng thái:** **đã có đường cơ sở null (không LLM)**",
            f"- **Số seeds:** {x02_data.get('seeds')}, **Số ticks:** {x02_data.get('ticks')}",
            f"- **Thế giới LAW:** Chênh lệch top ({law_info.get('top')}) − bottom ({law_info.get('bottom')}) = `{_fmt(law_info.get('gap'))}` (Welch t = `{_fmt(law_info.get('welch_t'))}`, df = `{_fmt(law_info.get('df'))}`)",
            f"- **Thế giới FLAT:** Chênh lệch top ({flat_info.get('top')}) − bottom ({flat_info.get('bottom')}) = `{_fmt(flat_info.get('gap'))}` (Welch t = `{_fmt(flat_info.get('welch_t'))}`, df = `{_fmt(flat_info.get('df'))}`)",
            f"- **Độ co lại chênh lệch (shrink = gap_LAW − gap_FLAT):** `{_fmt(x02_data.get('shrink'))}`",
            f"- **Kết luận đường cơ sở:** {x02_data.get('verdict', '')}",
            "",
            "> **Lưu ý:** Đây là đường cơ sở null đo khi chưa có suy luận LLM. Để trả lời hoàn chỉnh Q7, cần chạy với model thật trên cả hai thế giới và thực hiện hồi quy `survival ~ brain + t_discover`.",
        ])
    else:
        lines.extend([
            "- **Trạng thái:** **chưa đo được**",
            "- **Lý do:** Chưa có kết quả từ thí nghiệm gác cổng `WORLD_FLAT` vs `WORLD_LAW` (`runs/x02-null.json`).",
            "- **Lệnh cần chạy để có dữ liệu:**",
            "  ```bash",
            "  python scripts/x02_gate.py --seeds 40 --ticks 400 --out runs/x02-null.json",
            "  ```",
        ])

    lines.append("")
    report_text = "\n".join(lines)
    return report_text, summary


def generate_report(
    out_dir: Path,
    data_dir: Path | None = None,
    csv_files: list[Path] | None = None,
) -> Path:
    """Tạo báo cáo Q1–Q7 và ghi ra file Markdown."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_text, _ = build_q_report(data_dir=data_dir, csv_files=csv_files)
    target_file = out_dir / "report_q.md"
    target_file.write_text(report_text, encoding="utf-8")
    return target_file


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="scripts.x06_report",
        description="Gom toàn bộ dữ liệu thành báo cáo nghiên cứu Q1–Q7",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("runs/report-q"),
        help="Thư mục xuất báo cáo (mặc định: runs/report-q)",
    )
    ap.add_argument(
        "--data",
        type=Path,
        default=Path("runs"),
        help="Thư mục chứa dữ liệu CSV/JSON (mặc định: runs)",
    )
    ap.add_argument(
        "--csv",
        type=Path,
        nargs="*",
        default=None,
        help="Các file CSV chỉ định cụ thể nếu có",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_path = generate_report(out_dir=args.out, data_dir=args.data, csv_files=args.csv)
    print(f"Đã xuất báo cáo Q1–Q7 tại: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
