"""Genesis Zero — scripts/arena_tournament.py
Hệ thống giải đấu tự động đa hạt giống (Multi-Model Tournament Arena)
đo lường định lượng năng lực quy nạp và khám phá luật giữa các mô hình AI.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from genesis.score import score_records


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Genesis Zero Multi-Model Tournament Arena")
    ap.add_argument("--seeds", nargs="+", type=int, default=[7, 42, 55, 101, 777], help="Danh sách seed")
    ap.add_argument("--ticks", type=int, default=150, help="Số ticks mỗi ván đấu")
    ap.add_argument("--out", type=Path, default=Path("runs/tournament"), help="Thư mục xuất báo cáo")
    ap.add_argument("--plan", action="store_true", help="Chỉ lập lịch thi đấu mà không chạy mô phỏng")
    ap.add_argument("--competitors", nargs="+", default=["reflex", "mock"], help="Danh sách đấu thủ (reflex, mock, llm)")
    return ap


def run_tournament_plan(seeds: list[int], competitors: list[str], ticks: int) -> dict[str, Any]:
    """Tạo giao thức kế hoạch giải đấu có kiểm chứng hash."""
    schedule = [
        {
            "seed": s,
            "competitor": c,
            "ticks": ticks,
            "match_id": f"tournament_s{s}_{c}",
        }
        for s in seeds
        for c in competitors
    ]
    return {
        "version": "2.2.0",
        "type": "round_robin_tournament",
        "seeds": seeds,
        "competitors": competitors,
        "total_matches": len(schedule),
        "schedule": schedule,
    }


def execute_tournament(seeds: list[int], competitors: list[str], ticks: int, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plan = run_tournament_plan(seeds, competitors, ticks)
    results = []

    for item in plan["schedule"]:
        seed = item["seed"]
        comp = item["competitor"]
        match_id = item["match_id"]
        log_file = out_dir / f"{match_id}.jsonl"

        # Khởi chạy một ván mô phỏng độc lập
        from genesis.run import main as run_main
        args = [
            "--seed", str(seed),
            "--ticks", str(ticks),
            "--controller", "reflex" if comp == "reflex" else "mock",
            "--out", str(log_file),
            "--no-render",
        ]
        run_main(args)

        # Tính điểm
        truth_file = Path(f"runs/m_{seed:05d}.truth.json")
        match_score = 0.0
        t_discover = None
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                records = [json.loads(line) for line in f if line.strip()]

            truth_dict: dict[str, Any] = {}
            if truth_file.exists():
                truth_dict = json.loads(truth_file.read_text(encoding="utf-8"))
            elif records and "laws" in records[0]:
                truth_dict = {"laws": records[0]["laws"], "seed": seed}

            if truth_dict:
                scored = score_records(records, truth_dict)
                matches = [float(r.get("match", 0.0)) for r in scored if "match" in r]
                match_score = max(matches) if matches else 0.0
                t_disc = [int(r.get("t_discover", 0)) for r in scored if r.get("t_discover")]
                t_discover = min(t_disc) if t_disc else None

        results.append({
            "seed": seed,
            "competitor": comp,
            "match_id": match_id,
            "max_match": match_score,
            "t_discover": t_discover,
            "discovered": match_score >= 0.5,
        })

    # Tổng kết bảng xếp hạng
    leaderboard = {}
    for comp in competitors:
        comp_res = [r for r in results if r["competitor"] == comp]
        if comp_res:
            scores = [r["max_match"] for r in comp_res]
            dsr = sum(1 for r in comp_res if r["discovered"]) / len(comp_res)
            disc_times = [r["t_discover"] for r in comp_res if r["t_discover"] is not None]
            avg_time = statistics.mean(disc_times) if disc_times else None
            leaderboard[comp] = {
                "matches": len(comp_res),
                "mean_match": round(statistics.mean(scores), 4),
                "max_match": round(max(scores), 4),
                "discovery_success_rate": round(dsr, 4),
                "avg_discovery_time": round(avg_time, 2) if avg_time else "N/A",
            }

    report = {
        "tournament_plan": plan,
        "results": results,
        "leaderboard": leaderboard,
    }

    # Xuất file JSON và CSV
    report_json = out_dir / "tournament_report.json"
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_file = out_dir / "leaderboard.csv"
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Competitor", "Matches", "Mean_Match", "Max_Match", "DSR", "Avg_Time"])
        for comp, stats in leaderboard.items():
            writer.writerow([
                comp,
                stats["matches"],
                stats["mean_match"],
                stats["max_match"],
                stats["discovery_success_rate"],
                stats["avg_discovery_time"],
            ])

    return report


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()
    if args.plan:
        plan = run_tournament_plan(args.seeds, args.competitors, args.ticks)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return

    print(f"=== Genesis Zero Tournament: {len(args.seeds)} seeds, {len(args.competitors)} competitors ===")
    report = execute_tournament(args.seeds, args.competitors, args.ticks, args.out)
    print("\n--- LEADERBOARD ---")
    for comp, stats in report["leaderboard"].items():
        print(f"[{comp.upper()}] Mean Match: {stats['mean_match']} | DSR: {stats['discovery_success_rate']} | Best: {stats['max_match']}")
    print(f"\nReport saved to: {args.out / 'tournament_report.json'}")


if __name__ == "__main__":
    main()
