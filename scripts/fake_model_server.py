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
import hashlib
import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer

GOALS = ("FORAGE", "REST", "WANDER", "FLEE")


class Handler(BaseHTTPRequestHandler):
    cheat_law: dict | None = None
    # Tần suất xin nêu linh cảm. `0.0` cho một NHÁNH ĐỐI CHỨNG thật: bật
    # `--hunch` mà không con nào xin, nên khối E6 luôn rỗng và hai nhánh
    # phải ra hai ván GIỐNG HỆT. Nhánh ấy là cách duy nhất tách được
    # "linh cảm làm đổi kết quả" khỏi "hai ván vốn đã khác nhau".
    hunch_rate: float = 0.35

    def do_POST(self) -> None:
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        prompt = body.get("prompt", "")

        # RNG suy từ CHÍNH PROMPT, không phải một dòng ngẫu nhiên dùng chung.
        #
        # Bản cũ giữ một `random.Random(0)` ở cấp lớp và tiêu nó theo thứ tự yêu
        # cầu tới. Hậu quả chỉ lộ ra khi có ai đó so hai NHÁNH: đổi bất cứ thứ gì
        # làm lệch thứ tự lời gọi — thêm một loại việc, thêm một khối prompt — là
        # cả hai nhánh nhận hai dòng ngẫu nhiên khác nhau và trôi thành hai thế
        # giới khác hẳn. Lúc ấy mọi chênh lệch đo được đều là nhiễu đội lốt kết
        # quả. Đã suýt đọc nhầm một lần: `x09` cho thấy ghi sổ tụt 11 -> 2 khi
        # bật linh cảm, trông y như linh cảm đang cướp lượt nghĩ, trong khi hai
        # ván ấy đơn giản là hai ván khác nhau.
        #
        # Suy từ prompt thì cùng một câu hỏi luôn nhận cùng một câu trả lời, nên
        # hai nhánh chỉ tách ra ở đúng chỗ cơ chế thật sự khác nhau.
        rng = random.Random(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16])

        if "[CÂU HỎI]" in prompt:
            # KHÔNG có chế độ gian lận cho oracle, và lý do đáng ghi lại.
            #
            # Đã thử: biết `cheat_law` rồi trả lời cùng một hệ quả cho MỌI câu.
            # Nó ra `pred_acc = 0.000` — và đó là **đúng**, không phải hỏng.
            # `score_answers` chuẩn hoá theo đường cơ sở null y như `match()`,
            # mà chỉ ~3-4/8 tình huống là luật thật NỔ; trả lời "có hệ quả" ở cả
            # 8 câu thì ăn đúng bằng đường cơ sở, nên điểm chuẩn hoá về 0.
            #
            # Muốn gian lận thật thì phải biết TỪNG tình huống có nổ hay không,
            # mà model giả chỉ nhìn thấy chuỗi câu hỏi — nó không có `Situation`
            # để `evaluate`. Nên phép kiểm ấy thuộc về bài test, không thuộc về
            # server giả: xem `tests/test_oracle.py::test_dap_an_hoan_hao_an_1`.
            out = {"answers": []}
        elif "[GHI SỔ LUẬT]" in prompt:
            if self.cheat_law is None:
                out = {"op": "SET", "slot": 0, "conf": 2, "law": {
                    "trigger": {"kind": "DRINK"}, "conds": [],
                    "effect": {"kind": "HEAL", "mag": "SMALL", "dur": "INSTANT"}}}
            else:
                out = {"op": "SET", "slot": 0, "conf": 5, "law": self.cheat_law}
        elif "[LINH CẢM]" in prompt:
            # Linh cảm (B-14). Model giả nghi về DRINK — cố ý KHÁC chỗ nó ghi Sổ
            # Luật, để một ván giả cũng phơi ra được đường đi của bảng đếm.
            out = {"op": "SET", "slot": 0, "law": {
                "trigger": {"kind": "DRINK"}, "conds": [],
                "effect": {"kind": "DAMAGE", "mag": "MED", "dur": "SHORT"}}}
        elif "[DỊCH CƠ THỂ]" in prompt:
            out = {"from": "speed", "to": "brain", "why": "cần nhớ nhiều hơn"}
        else:
            out = {"goal": rng.choice(GOALS), "ttl": rng.randint(3, 8),
                   "want_codex": rng.random() < 0.25,
                   "want_hunch": rng.random() < Handler.hunch_rate}

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
    ap.add_argument("--hunch-rate", type=float, default=0.35,
                    help="xác suất model giả xin nêu linh cảm; 0.0 = nhánh đối chứng")
    ap.add_argument("--cheat-seed", type=int, default=None,
                    help="biết trước luật của seed này — CHỈ để kiểm bộ chấm")
    a = ap.parse_args(argv)

    Handler.hunch_rate = a.hunch_rate

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
