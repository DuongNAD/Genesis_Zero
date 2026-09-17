"""Bài canh quan trọng nhất của kho, gói thành một lệnh chạy được ở cả CI lẫn máy.

    python scripts/ci_smoke.py

Chạy MỘT ván qua HTTP với model giả **biết trước đáp án**, rồi đòi bộ chấm cho
`match = 1.000`.

Vì sao đây là bài canh quan trọng nhất: cả dự án đo đúng một thứ — model có quy
nạp ra được luật ẩn không — và câu trả lời hiện tại là `match = 0.000`. Một số 0
có **hai** cách giải thích, và chúng dẫn tới hai việc hoàn toàn khác nhau:

    · model không quy nạp được   -> đi sửa prompt, sửa trí nhớ, đổi model
    · bộ chấm không chấm được    -> mọi kết luận phía trên đều vô nghĩa

Bài này loại khả năng thứ hai. Không có nó thì mỗi lần ai đó chạm vào `verify`,
`score`, hay `lawdsl`, toàn bộ kết luận của dự án lặng lẽ mất chỗ dựa.

Nó cố ý KHÔNG cần model thật, không cần GPU, không cần mạng ra ngoài — nên nó
chạy được ở mọi nơi và không có cớ để bỏ qua.
"""

from __future__ import annotations

import csv
import io
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PORT = 8099
SEED = 9
TICKS = 120


def main() -> int:
    from genesis.run import configure_console_encoding
    configure_console_encoding()
    tmp = Path(tempfile.mkdtemp())
    print(f"Smoke artifacts: {tmp}", flush=True)
    log, truth = tmp / "ci.jsonl", tmp / "ci.truth.json"

    server = subprocess.Popen(
        [sys.executable, "-X", "utf8", "-u", "-m", "scripts.fake_model_server",
         "--port", str(PORT), "--cheat-seed", str(SEED)],
        cwd=ROOT, stdout=subprocess.DEVNULL,
    )
    try:
        # Chờ CỔNG MỞ thay vì ngủ một khoảng đoán chừng: `sleep 4` là thứ sẽ đỏ
        # ngẫu nhiên trên máy CI chậm, và đỏ ngẫu nhiên tệ hơn đỏ hẳn.
        #
        # Kiểm bằng socket, không bằng HTTP: model giả chỉ có `do_POST`, nên một
        # GET `/props` trả 501 và `urlopen` ném — vòng chờ sẽ quay cho tới hết
        # lượt rồi báo "server không lên được" trong khi server đã lên từ lâu.
        # Bản đầu của chính file này mắc đúng lỗi ấy.
        import socket
        for _ in range(240):
            if server.poll() is not None:
                print(f"model exited: {server.returncode}", file=sys.stderr)
                return 1
            with socket.socket() as sk:
                sk.settimeout(0.5)
                if sk.connect_ex(("127.0.0.1", PORT)) == 0:
                    break
            time.sleep(0.5)
        else:
            print("model giả không lên được", file=sys.stderr)
            return 1

        subprocess.run(
            [sys.executable, "-m", "genesis.run", "--seed", str(SEED),
             "--ticks", str(TICKS), "--llm", "all",
             "--llm-url", f"http://127.0.0.1:{PORT}", "--no-render",
             "--out", str(log), "--truth", str(truth)],
            cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
        )
        out = subprocess.run(
            [sys.executable, "-m", "genesis.score", str(log), str(truth)],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout
    finally:
        server.terminate()
        server.wait(timeout=10)

    rows = list(csv.DictReader(io.StringIO(out)))
    if not rows:
        print("bộ chấm không ra dòng nào", file=sys.stderr)
        return 1
    best = max(float(r["match"]) for r in rows)
    print(f"match cao nhất {best:.3f} trên {len(rows)} dòng")
    if best != 1.0:
        print("BỘ CHẤM KHÔNG BẮT ĐƯỢC LỜI GIẢI ĐÚNG.\n"
              "Model giả biết trước đáp án mà vẫn không ăn điểm — lỗi nằm ở bộ\n"
              "chấm, không ở model. Mọi kết luận về năng lực quy nạp đang treo\n"
              "trên một phép đo hỏng.", file=sys.stderr)
        return 1
    print("bộ chấm bắt được lời giải đúng ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
