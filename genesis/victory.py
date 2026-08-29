"""Genesis Zero — victory: ba danh hiệu, ba bảng riêng (W-14).

**Vì sao ba chứ không một.** Bản v5 cố ý bỏ "sống lâu" làm mục tiêu duy nhất
(03 §0.1): sinh tồn không có đáp án, nên không chấm được, nên không train được.
Nhưng bỏ hẳn nó thì mất phần **vui** — người xem cần một câu chuyện, và "con nào
sống tới cuối" là câu chuyện dễ kể nhất trên đời.

Nên: ba danh hiệu, **ba bảng riêng**, không cộng vào nhau.

| Danh hiệu | Thắng bằng | Vì sao có mặt |
|---|---|---|
| `NHA_KHOA_HOC` | `R` cao nhất (03 §5.5) | đây là thứ dự án **đo**, và là thứ RL học |
| `KE_SONG_SOT` | tỉ lệ tick còn sống cao nhất | phần vui, phần kể chuyện |
| `NGUOI_DAU_TIEN` | ghi được luật đạt `match ≥ θ` **sớm nhất** và giữ tới cuối | khoảnh khắc kịch tính nhất của một ván |

Cộng chúng thành một điểm tổng là hỏng: một trọng số duy nhất giữa "hiểu" và
"sống" là một tuyên bố về việc cái nào quan trọng hơn, và **ta không biết** — đó
chính là câu hỏi Q7 mà thí nghiệm [X-02] sinh ra để trả lời. Để ba bảng riêng thì
khoảng cách giữa chúng **là dữ liệu**: một loài đứng đầu bảng khoa học mà cuối
bảng sinh tồn nói lên nhiều hơn bất kỳ điểm tổng nào.

File này **không import vòng chạy**, cùng lý do với `score.py`: nó đọc log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from genesis import law_config

TITLES = ("NHA_KHOA_HOC", "KE_SONG_SOT", "NGUOI_DAU_TIEN")

TITLE_VN = {
    "NHA_KHOA_HOC": "Nhà khoa học",
    "KE_SONG_SOT": "Kẻ sống sót",
    "NGUOI_DAU_TIEN": "Người đầu tiên",
}


@dataclass(frozen=True)
class Standing:
    title: str
    creature_id: str
    species_id: str
    value: float
    detail: str = ""


@dataclass
class Victory:
    match_id: str
    seed: int
    ticks: int
    boards: dict[str, list[Standing]] = field(default_factory=dict)

    def winner(self, title: str) -> Standing | None:
        rows = self.boards.get(title) or []
        return rows[0] if rows else None

    def to_json(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id, "seed": self.seed, "ticks": self.ticks,
            "boards": {
                t: [
                    {"rank": i + 1, "creature_id": s.creature_id,
                     "species_id": s.species_id, "value": s.value, "detail": s.detail}
                    for i, s in enumerate(rows)
                ]
                for t, rows in self.boards.items()
            },
        }

    def render(self) -> str:
        lines = [f"═══ KẾT QUẢ · {self.match_id} (seed {self.seed}) ═══"]
        if not (self.boards.get("NGUOI_DAU_TIEN") or []):
            # Nói thẳng, đừng để người đọc tự suy: khi không ai tìm ra luật thì
            # `R = 0.1·R_survive` cho tất cả, và bảng "Nhà khoa học" **chỉ là
            # bảng sinh tồn thu nhỏ**. Không ghi câu này thì có người sẽ đọc thứ
            # hạng đó như một kết luận về năng lực quy nạp.
            lines.append("  ⚠ KHÔNG AI tìm ra luật nào trong ván này. Bảng \"Nhà")
            lines.append("    khoa học\" khi đó chỉ còn phần 0.1·sinh tồn — đừng")
            lines.append("    đọc nó như một xếp hạng về quy nạp.")
        for t in TITLES:
            rows = self.boards.get(t) or []
            lines.append(f"\n[{TITLE_VN[t]}]")
            if not rows:
                lines.append("  không ai đạt")
                continue
            for i, s in enumerate(rows[:5], 1):
                mark = "★" if i == 1 else " "
                lines.append(f"  {mark} {i}. {s.creature_id:<14} {s.value:>7.3f}  {s.detail}")
        return "\n".join(lines)


def decide(score_rows: list[dict], totals: dict[str, float],
           match_id: str = "", seed: int = 0, ticks: int = 400) -> Victory:
    """Ba bảng, từ `score.score_match` + `score.total_reward`.

    Không tự tính lại điểm: bộ chấm đã làm, và tính lại ở đây là một chỗ nữa để
    hai con số lệch nhau.
    """
    sp = {r["creature_id"]: r["species_id"] for r in score_rows}
    v = Victory(match_id=match_id, seed=seed, ticks=ticks)

    v.boards["NHA_KHOA_HOC"] = [
        Standing("NHA_KHOA_HOC", cid, sp.get(cid, "?"), round(r, 4),
                 f"{_n_found(score_rows, cid)}/{_n_laws(score_rows)} luật")
        for cid, r in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    alive = {r["creature_id"]: float(r["R_survive"]) for r in score_rows}
    v.boards["KE_SONG_SOT"] = [
        Standing("KE_SONG_SOT", cid, sp.get(cid, "?"), round(a, 4),
                 f"{a * 100:.0f}% số lượt còn sống")
        for cid, a in sorted(alive.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    # "Người đầu tiên": chỉ tính ca THẬT SỰ tìm ra. Một cột toàn `T+1` sắp tăng
    # dần sẽ cho ra một "người thắng" chưa hề tìm ra gì — đúng kiểu bảng xếp
    # hạng có số mà không có nghĩa.
    firsts: dict[str, int] = {}
    for r in score_rows:
        if not _found(r):
            continue
        t = int(r["t_discover"])
        cid = r["creature_id"]
        if cid not in firsts or t < firsts[cid]:
            firsts[cid] = t
    v.boards["NGUOI_DAU_TIEN"] = [
        Standing("NGUOI_DAU_TIEN", cid, sp.get(cid, "?"), float(t),
                 f"lượt {t}")
        for cid, t in sorted(firsts.items(), key=lambda kv: (kv[1], kv[0]))
    ]
    return v


def _found(row: dict) -> bool:
    f = row.get("found")
    if isinstance(f, bool):
        return f
    if isinstance(f, str):
        return f.strip().lower() in ("true", "1", "yes")
    return float(row.get("match", 0)) >= law_config.MATCH_THETA


def _n_found(rows: list[dict], cid: str) -> int:
    return sum(1 for r in rows if r["creature_id"] == cid and _found(r))


def _n_laws(rows: list[dict]) -> int:
    return len({r["law_idx"] for r in rows}) or 1


def from_files(log: Path, truth: Path) -> Victory:
    from genesis.score import score_match, total_reward

    rows = score_match(log, truth)
    t = json.loads(Path(truth).read_text(encoding="utf-8"))
    ticks = max((int(r["t_discover"]) for r in rows), default=400) - 1
    return decide(rows, total_reward(rows),
                  match_id=rows[0]["match_id"] if rows else "",
                  seed=int(t["seed"]), ticks=ticks)
