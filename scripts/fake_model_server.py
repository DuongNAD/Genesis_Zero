#!/usr/bin/env python3
"""Một `llama-server` giả, đủ để chạy toàn bộ đường ống mà không cần model.

    python scripts/fake_model_server.py --port 8099 [--oracle-seed 9] [--cheat]

Nó **không** thay được model thật: nó không suy luận gì cả. Nó tồn tại để kiểm
đường ống — prompt đi ra, JSON đi vào, sổ tay, Sổ Luật, log, bảng điểm — mà không
phải chờ tải một file .gguf 4 GB. Mọi kết luận về *chất lượng* phải đến từ [S-02].

`--cheat` cho nó biết trước đáp án của một seed. Dùng để kiểm rằng bảng điểm
**bắt được** một lời giải đúng; nếu chế độ này mà điểm vẫn 0 thì lỗi ở bộ chấm,
không ở model. Đừng bao giờ báo cáo số đo từ chế độ này như số đo của model.
"""

from __future__ import annotations

import argparse
import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer

GOALS = ("FORAGE", "REST", "WANDER", "FLEE")


class Handler(BaseHTTPRequestHandler):
    cheat_law: dict | None = None
    rng = random.Random(0)

    def do_POST(self) -> None:  # noqa: N802 (tên do BaseHTTPRequestHandler quy định)
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        prompt = body.get("prompt", "")

        if "[CÂU HỎI]" in prompt:
            out = {"answers": []}
        elif "[GHI SỔ LUẬT]" in prompt:
            if self.cheat_law is None:
                out = {"op": "SET", "slot": 0, "conf": 2, "law": {
                    "trigger": {"kind": "DRINK"}, "conds": [],
                    "effect": {"kind": "HEAL", "mag": "SMALL", "dur": "INSTANT"}}}
            else:
                out = {"op": "SET", "slot": 0, "conf": 5, "law": self.cheat_law}
        else:
            out = {"goal": self.rng.choice(GOALS), "ttl": self.rng.randint(3, 8),
                   "want_codex": self.rng.random() < 0.25}

        payload = json.dumps(out, ensure_ascii=False)
        resp = json.dumps({
            "content": payload,
            "tokens_predicted": max(1, len(payload) // 4),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, *_a) -> None:
        pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--cheat-seed", type=int, default=None,
                    help="biết trước luật của seed này — CHỈ để kiểm bộ chấm")
    a = ap.parse_args(argv)

    if a.cheat_seed is not None:
        from genesis.lawgen import generate_cached
        from genesis.reveal import _law_to_surface_dict
        from genesis.tick import build_match
        world, _, _, _ = build_match(seed=a.cheat_seed)
        Handler.cheat_law = _law_to_surface_dict(
            generate_cached(a.cheat_seed)[0], world.surface_map
        )

    srv = HTTPServer(("127.0.0.1", a.port), Handler)
    print(f"model giả nghe ở http://127.0.0.1:{a.port}", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
