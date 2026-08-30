"""Genesis Zero — score: một ván thành các con số (B-10).

Đây là mốc chứng minh cả bản v5 có sống được không: nếu không ai bao giờ đạt
`match >= 0.8` thì luật ẩn là câu đố không giải được, và mọi thứ phía trên vô nghĩa.

**Bất biến 1 — file này KHÔNG import `world.py`, `tick.py`, hay bất cứ gì thuộc
vòng chạy.** Nó đọc JSONL, chấm, xong. Ranh giới đó là thứ đảm bảo sim không bao
giờ chạm được vào bảng chấm — có `tests/test_score.py::test_khong_import_sim`
canh bằng AST, vì kỷ luật thì quên còn test thì không.

**Bất biến 2 — "còn tới cuối ván".** Trúng ở tick 30 rồi tick 40 xoá đi thì không
tính. Không có điều này thì chiến lược tối ưu là vét cạn: ghi bừa, ghi liên tục,
và một trong số đó sẽ trúng.

**Bất biến 3 — sàn 0.4.** Tìm ra ở tick 380 mà được ~0 thì tín hiệu ở phần đuôi
biến mất, đúng chỗ RL cần nó nhất lúc đầu.

**Bất biến 4 — mẫu nhỏ thì ghi `NA`.** `exploit_lag` đòi `n >= 4` lần xảy ra ở
mỗi cửa sổ. Không đủ thì `NA`, đừng ghi 0 và **đừng nới ngưỡng để có số đẹp**:
một cột toàn 0 trông như "agent không bao giờ khai thác", và đó là kết luận sai.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

from genesis import law_config
from genesis.lawdsl import Law, from_json
from genesis.situations import sample_situations
from genesis.verify import match

NA = "NA"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _situations_for(law: Law, seed: int, idx: int) -> list:
    """Tình huống chấm, tất định theo (seed, chỉ số luật).

    Không lấy từ log: bộ chấm phải chấm được lại y hệt từ một file truth và một
    file log, ở máy khác, năm sau.
    """
    return sample_situations(law, law_config.N_SITUATIONS, random.Random(seed * 1000 + idx))


def _codex_timeline(rows: list[dict]) -> dict[str, list[tuple[int, int, Law | None]]]:
    """(creature_id) -> [(tick, slot, law|None)] theo thứ tự thời gian, chỉ op THÀNH CÔNG.

    Op hỏng không đổi sổ, nên đưa nó vào dòng thời gian là chấm một cuốn sổ chưa
    bao giờ tồn tại.
    """
    out: dict[str, list[tuple[int, int, Law | None]]] = {}
    for r in rows:
        if r.get("kind") != "CODEX_OP" or not r.get("ok"):
            continue
        cid = r.get("creature_id")
        slot = r.get("slot")
        if cid is None or not isinstance(slot, int):
            continue
        op = r.get("op")
        law = None
        if op == "SET" and r.get("law"):
            law = from_json(r["law"])
        elif op == "CONF":
            continue        # đổi độ tự tin, không đổi nội dung ô
        out.setdefault(cid, []).append((int(r["t"]), slot, law))
    return out


def _final_codex(timeline: list[tuple[int, int, Law | None]]) -> dict[int, tuple[int, Law]]:
    """slot -> (tick ghi, law) ở cuối ván. Ô bị DROP hay ghi đè thì biến mất."""
    final: dict[int, tuple[int, Law]] = {}
    for t, slot, law in timeline:
        if law is None:
            final.pop(slot, None)
        else:
            final[slot] = (t, law)
    return final


def _exploit_lag(rows: list[dict], cid: str, law: Law, t_i: int | None, ticks: int):
    """Số tick từ lúc BIẾT tới lúc HÀNH XỬ KHÁC ĐI.

    Khoảng cách giữa tầng 1 (phát biểu được) và tầng 3 (làm theo) là phát hiện thú
    vị nhất môi trường này sinh ra được, và nó chỉ tồn tại vì §4.4 cấm reflex đọc
    codex. Đo bằng tần suất tự châm ngòi trigger, trước và sau `t_i`.
    """
    if t_i is None:
        return NA
    kind = law.trigger.kind.value
    marker = {"EAT": "EAT", "DRINK": "DRINK", "ATTACK": "ATTACK", "HIT_BY": "ATTACK"}.get(kind)
    if marker is None:
        return NA       # trigger không để lại dấu riêng trong log; đừng đoán

    w = law_config.EXPLOIT_WINDOW
    before = [r for r in rows
              if r.get("kind") == marker and r.get("creature_id") == cid
              and t_i - w <= r["t"] < t_i]
    after = [r for r in rows
             if r.get("kind") == marker and r.get("creature_id") == cid
             and t_i <= r["t"] < t_i + w]
    if len(before) < law_config.EXPLOIT_MIN_N or len(after) < law_config.EXPLOIT_MIN_N:
        return NA
    rate_before = len(before) / w
    rate_after = len(after) / w
    return round(rate_after - rate_before, 4)


def score_match(log: Path, truth: Path) -> list[dict]:
    """Một dòng cho mỗi (ván, cá thể, luật)."""
    rows = _read_jsonl(log)
    tr = json.loads(Path(truth).read_text(encoding="utf-8"))
    laws = [from_json(d) for d in tr["laws"]]
    seed = int(tr["seed"])
    match_id = next((r.get("match_id") for r in rows if r.get("match_id")), f"m_{seed}")

    start = next((r for r in rows if r.get("kind") == "RUN_START"), {})
    ticks = int(start.get("ticks") or max((r["t"] for r in rows), default=1))
    ticks = max(1, ticks)

    timelines = _codex_timeline(rows)
    sits = [_situations_for(law, seed, i) for i, law in enumerate(laws)]

    # tỉ lệ tick còn sống: mọi cá thể xuất hiện trong log, kể cả con không ghi sổ
    alive_deficit: dict[str, int] = {}
    dead_since: dict[str, int] = {}
    for r in rows:
        cid = r.get("creature_id")
        if r.get("kind") == "DEATH" and cid:
            dead_since[cid] = int(r["t"])
        elif r.get("kind") == "RESPAWN" and cid and cid in dead_since:
            alive_deficit[cid] = alive_deficit.get(cid, 0) + int(r["t"]) - dead_since.pop(cid)
    for cid, t in dead_since.items():
        alive_deficit[cid] = alive_deficit.get(cid, 0) + ticks - t

    creatures = sorted({
        r["creature_id"] for r in rows
        if r.get("creature_id") and r.get("kind") in
        ("CODEX_OP", "LLM_CALL", "EAT", "DRINK", "ATTACK", "DEATH", "RESPAWN")
    })

    oracle: dict[str, float] = {
        r["creature_id"]: float(r["pred_acc"])
        for r in rows if r.get("kind") == "ORACLE" and r.get("pred_acc") is not None
    }

    out: list[dict] = []
    for cid in creatures:
        timeline = timelines.get(cid, [])
        final = _final_codex(timeline)
        r_survive = max(0.0, 1.0 - alive_deficit.get(cid, 0) / ticks)

        for i, law in enumerate(laws):
            m_final = max(
                (match(entry_law, law, sits[i]) for _, entry_law in final.values()),
                default=0.0,
            )

            # Bất biến 2: chỉ tính mốc thời gian của những ô CÒN Ở LẠI tới cuối ván.
            t_i: int | None = None
            for slot, (t_written, entry_law) in final.items():
                if match(entry_law, law, sits[i]) >= law_config.MATCH_THETA:
                    # Ô này còn tới cuối ván; mốc là lần ghi ĐẦU TIÊN vào ô đó một
                    # luật đủ đúng, miễn là nó không bị ngắt quãng bởi lần ghi khác.
                    first = t_written
                    for t, sl, lw in timeline:
                        if sl != slot or lw is None or t > t_written:
                            continue
                        if match(lw, law, sits[i]) >= law_config.MATCH_THETA:
                            first = min(first, t)
                        else:
                            first = t_written   # bị ghi đè bằng luật sai -> mốc lùi lại
                    t_i = first if t_i is None else min(t_i, first)

            # ── CHẨN ĐOÁN, KHÔNG PHẢI ĐIỂM ────────────────────────────────
            # Đã có LÚC NÀO nói đúng luật này chưa, kể cả rồi xoá đi?
            #
            # Không dùng để tính `R_i` và không được dùng: bất biến 2 nói rõ ô
            # bị xoá thì không tính, và Sổ Luật **là** tờ đáp án. Nhưng hai
            # chuyện "chưa bao giờ tìm ra" và "tìm ra rồi đánh mất" là hai bài
            # toán khác hẳn nhau, mà cột `found` gộp chúng làm một.
            #
            # Ca thật: Qwen-14B, seed 55, `L5:1` ghi `WHEN DRINK THEN DAMAGE`
            # vào ô 0 ở tick 99 — **đúng nguyên văn luật thật** — rồi tick 148
            # ghi đè bằng một giả thuyết về quả. L5 là brain 0, nó có đúng MỘT
            # ô. `found = False` là đúng; nhưng đọc CSV thì nó trông y hệt một
            # model chưa bao giờ hiểu gì, và kết luận sẽ sai hoàn toàn.
            t_ever: int | None = None
            for t, _sl, lw in timeline:
                if lw is not None and match(lw, law, sits[i]) >= law_config.MATCH_THETA:
                    t_ever = t if t_ever is None else min(t_ever, t)

            speed = 0.0 if t_i is None else max(0.0, min(1.0, 1.0 - t_i / ticks))
            w_i = law_config.LAW_WEIGHT.get(law.tier(), 1.0)
            floor = law_config.SPEED_FLOOR
            r_i = w_i * m_final * (floor + (1.0 - floor) * speed)

            out.append({
                "match_id": match_id,
                "seed": seed,
                "creature_id": cid,
                "species_id": cid.rpartition(":")[0],
                "law_idx": i,
                "tier": law.tier(),
                "w": w_i,
                "match": round(m_final, 4),
                # `T+1` nếu không tìm ra (03 §9), để cột này không bao giờ trống
                # và các phép hồi quy ở §10 không phải đoán ý nghĩa của ô rỗng.
                "t_discover": ticks + 1 if t_i is None else t_i,
                # Nói THẲNG ra thay vì để người đọc suy từ `t_discover > T`:
                # `T` không có trong CSV, nên bên đọc sẽ phải đoán, và bản đầu
                # của `analyze.py` đã đoán bằng một chuỗi heuristic có hằng số
                # 400 viết cứng. Bên SINH ra dữ liệu là bên biết câu trả lời.
                "found": t_i is not None,
                # Chẩn đoán, KHÔNG vào điểm. Xem ghi chú ở trên.
                "ever_stated": t_ever is not None,
                "t_ever": ticks + 1 if t_ever is None else t_ever,
                "speed": round(speed, 4),
                "R_i": round(r_i, 4),
                "exploit_lag": _exploit_lag(rows, cid, law, t_i, ticks),
                "pred_acc": oracle.get(cid, NA),
                "R_survive": round(r_survive, 4),
            })
    return out


def total_reward(rows: list[dict]) -> dict[str, float]:
    """R = Σ R_i + 0.5·R_pred + 0.3·R_exploit + 0.3·R_social + 0.1·R_survive.

    R_social cần [B-11]/[B-12] (kênh nói, citation) nên hiện là 0.0 — đó là 0
    THẬT (chưa có kênh để chia sẻ), không phải NA vì thiếu mẫu.
    """
    w = law_config.R_WEIGHTS
    per: dict[str, float] = {}
    for r in rows:
        cid = r["creature_id"]
        if cid not in per:
            pred = r["pred_acc"]
            per[cid] = (
                w["pred"] * (0.0 if pred == NA else float(pred))
                + w["survive"] * float(r["R_survive"])
            )
        per[cid] += float(r["R_i"])
    return {k: round(v, 4) for k, v in sorted(per.items())}


FIELDS = [
    "match_id", "seed", "creature_id", "species_id", "law_idx", "tier", "w",
    "match", "found", "ever_stated", "t_ever", "t_discover", "speed", "R_i",
    "exploit_lag", "pred_acc",
    "R_survive",
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="genesis.score")
    ap.add_argument("log", type=Path)
    ap.add_argument("truth", type=Path)
    ap.add_argument("--no-header", action="store_true",
                    help="bỏ dòng tiêu đề khi nối nhiều ván vào một CSV")
    a = ap.parse_args(argv)

    rows = score_match(a.log, a.truth)
    wr = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
    if not a.no_header:
        wr.writeheader()
    wr.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
