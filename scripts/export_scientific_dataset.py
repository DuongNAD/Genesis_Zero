"""Genesis Zero — scripts/export_scientific_dataset.py
Công cụ xuất dữ liệu nghiên cứu khoa học mở (Open Science Scientific Dataset Exporter)
đóng gói quỹ đạo tư duy đa tác nhân sang định dạng chuẩn nghiên cứu quốc tế.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Export Genesis Zero matches to Open Science Dataset format")
    ap.add_argument("--log", type=Path, required=True, help="Đường dẫn file match JSONL")
    ap.add_argument("--truth", type=Path, default=None, help="Đường dẫn file truth JSON (tùy chọn)")
    ap.add_argument("--out", type=Path, required=True, help="Đường dẫn file dataset xuất ra (.jsonl)")
    ap.add_argument("--split", choices=["train", "val", "test"], default="test", help="Nhãn phân chia dataset")
    return ap


def parse_and_export_trajectories(log_path: Path, truth_path: Path | None, out_path: Path, split: str = "test") -> dict[str, Any]:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with log_path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    truth_laws = []
    if truth_path and truth_path.exists():
        t_data = json.loads(truth_path.read_text(encoding="utf-8"))
        truth_laws = t_data.get("laws", [])

    match_id = log_path.stem
    dataset_rows = []

    # Nhóm các sự kiện theo (creature_id, tick)
    for r in records:
        kind = r.get("kind")
        cid = r.get("creature_id")
        t = r.get("t", 0)
        if not cid or kind not in ("STEP", "DECIDE", "CODEX_OP", "HUNCH_OP", "LLM_CALL"):
            continue

        entry = {
            "dataset_version": "2.2.0",
            "split": split,
            "match_id": match_id,
            "tick": t,
            "creature_id": cid,
            "event_kind": kind,
            "species": r.get("species", "unknown"),
            "pos": r.get("pos"),
            "hp": r.get("hp"),
            "energy": r.get("energy"),
            "goal": r.get("goal"),
            "action": r.get("action") or r.get("op"),
            "raw_reasoning": r.get("raw"),
            "law_claim": r.get("law"),
            "ground_truth_laws_count": len(truth_laws),
        }
        dataset_rows.append(entry)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out_f:
        for row in dataset_rows:
            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")

    metadata = {
        "source_match": str(log_path),
        "exported_records": len(dataset_rows),
        "split": split,
        "out_file": str(out_path),
    }
    return metadata


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()
    meta = parse_and_export_trajectories(args.log, args.truth, args.out, args.split)
    print(f"Exported {meta['exported_records']} scientific trajectory rows to {args.out}")


if __name__ == "__main__":
    main()
