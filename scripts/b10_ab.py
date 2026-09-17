"""Paired B-10 experiment. --plan records the protocol without model calls."""
import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SEEDS = (7, 9, 42, 55, 101)


def summarize(rows):
    if not rows:
        raise ValueError("Scorer produced no rows")
    values = [float(r["match"]) for r in rows]
    return {"mean_match": statistics.mean(values), "best_match": max(values),
            "found_fraction": statistics.mean(float(r["found"]) for r in rows)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--thinking-tokens", type=int, default=2048)
    ap.add_argument("--timeout", type=float, default=7200)
    ap.add_argument("--plan", action="store_true")
    a = ap.parse_args(argv)
    from urllib.parse import urlsplit
    url = urlsplit(a.url)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query:
        ap.error("Endpoint must be HTTP(S), without credentials or query parameters")
    if a.ticks <= 0 or a.timeout <= 0 or a.thinking_tokens < 0:
        ap.error("ticks/timeout must be positive; thinking-tokens non-negative")
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    protocol = {"schema_version": "1.0", "seeds": SEEDS, "ticks": a.ticks,
                "arm": "STANDARD", "hunch": False, "model": a.model, "url": a.url,
                "thinking_tokens": a.thinking_tokens,
                "primary": "paired per-seed mean_match delta; exploratory n=5",
                "order": [("frontier", "reflex") if i % 2 == 0 else ("reflex", "frontier") for i in range(5)],
                "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                  ("genesis/prompt.py", "genesis/llm_client.py", "genesis/score.py",
                                   "genesis/strategist.py", "genesis/run.py")}}
    (a.out / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    if a.plan:
        print("Protocol written. No model calls or measured results.")
        return 0
    from genesis.score import score_match
    results, valid = [], True
    for i, seed in enumerate(SEEDS):
        pair, truths = {}, []
        for controller in protocol["order"][i]:
            stem = a.out / f"{seed}-{controller}"
            log, truth = stem.with_suffix(".jsonl"), stem.with_suffix(".truth.json")
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                       GENESIS_LLM_BACKEND="frontier" if controller == "frontier" else "reflex",
                       GENESIS_LLM_MODEL=a.model, GENESIS_THINKING_TOKENS=str(a.thinking_tokens))
            cmd = [sys.executable, "-X", "utf8", "-m", "genesis.run", "--seed", str(seed),
                   "--ticks", str(a.ticks), "--no-render", "--out", str(log), "--truth", str(truth)]
            cmd += (["--llm", "all", "--llm-url", a.url] if controller == "frontier"
                    else ["--controller", "reflex"])
            with stem.with_suffix(".stderr.log").open("w", encoding="utf-8") as errors:
                subprocess.run(cmd, cwd=ROOT, env=env, check=True, timeout=a.timeout,
                               stdout=subprocess.DEVNULL, stderr=errors)
            truths.append(json.loads(truth.read_text(encoding="utf-8")))
            rows = score_match(log, truth)
            metrics = summarize(rows)
            with stem.with_suffix(".csv").open("w", encoding="utf-8", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
            misses = sum(e.get("kind") == "LLM_MISS" for e in events)
            calls = sum(e.get("kind") == "LLM_CALL" for e in events)
            pair[controller] = {**metrics, "llm_calls": calls, "llm_misses": misses}
            if controller == "frontier" and (misses or not calls):
                valid = False
        if truths[0] != truths[1]:
            raise RuntimeError(f"Seed {seed}: paired truth mismatch")
        results.append({"seed": seed, **pair,
                        "delta": pair["frontier"]["mean_match"] - pair["reflex"]["mean_match"]})
        (a.out / "pairs.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    report = {"status": "complete" if valid else "degraded_model_calls",
              "mean_paired_delta": statistics.mean(r["delta"] for r in results), "pairs": results}
    (a.out / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
