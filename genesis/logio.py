"""Genesis Zero — ghi và đọc log JSONL.

Log là **giao diện duy nhất** giữa sim và bộ chấm: `verify.py` và `score.py`
không import gì từ vòng tick, chúng chỉ đọc file này (docs/03-LUAT-AN-V5.md §5).
Nên định dạng log là một API, và nó phải đúng từ đầu — thêm trường sau nghĩa là
ván cũ không so được với ván mới (docs/04-THE-GIOI-MO.md §5, đường may 5).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Luôn có mặt trong MỌI bản ghi, null cũng phải có mặt.
COMMON_FIELDS: tuple[str, ...] = (
    "t",
    "kind",
    "match_id",
    "creature_id",
    "species_id",
    "client_id",
    "model_name",
)

EVENT_KINDS: frozenset[str] = frozenset({
    # thế giới
    "RUN_START", "RUN_END", "TICK", "PHASE_CHANGE",
    # sinh vật
    "MOVE", "EAT", "DRINK", "ATTACK", "DEATH", "RESPAWN", "TRAIT_SHIFT",
    "REPRODUCE", "EXTINCTION",
    # giao tiếp
    "SPEAK", "TEACH",
    # tầng LLM
    "LLM_CALL", "LLM_MISS", "LLM_SEMANTIC_FAIL", "PREFIX_INVALIDATED",
    # luật ẩn
    "LAW_FIRED", "CODEX_OP", "ORACLE",
    # linh cảm (B-14) — TÊN RIÊNG, không dùng lại "CODEX_OP": `score.py` gom
    # theo `kind`, nên trộn tên là để linh cảm chảy thẳng vào bộ chấm và phá
    # bất biến 1 của B-14 bằng đúng một chữ.
    "HUNCH_OP",
    # dịch trait qua mạng (B-13 ở chế độ mở, N-16)
    "SHIFT_OP",
    # đề bài trùng ván gần đây nên bốc lại seed (N-04). Xuất hiện đều = không
    # gian luật của bản đồ ấy hẹp hơn `LAW_NOVELTY_WINDOW`.
    "LAW_REPEAT",
    # mạng
    "NODE_DOWN", "DECISION_LATE", "THINK_LATENCY", "TICK_RATE",
    # gỡ lỗi
    "DEBUG_RNG",
})

FLOAT_NDIGITS = 4


def _round(value: Any) -> Any:
    """Làm tròn mọi float để hai lần chạy cùng seed cho file giống hệt nhau."""
    if isinstance(value, float):
        return round(value, FLOAT_NDIGITS)
    if isinstance(value, list):
        return [_round(v) for v in value]
    if isinstance(value, tuple):
        return [_round(v) for v in value]
    if isinstance(value, dict):
        return {k: _round(v) for k, v in value.items()}
    return value


class LogWriter:
    """Một dòng JSON một sự kiện. Ghi tuần tự, flush theo lô."""

    def __init__(self, path: str | Path, match_id: str, flush_every: int = 64) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.match_id = match_id
        self.flush_every = flush_every
        self._fh = self.path.open("w", encoding="utf-8")
        self._n = 0

    def write(self, t: int, kind: str, **fields: Any) -> None:
        if kind not in EVENT_KINDS:
            raise ValueError(f"kind lạ: {kind!r} — thêm vào EVENT_KINDS trước đã")
        row: dict[str, Any] = {
            "t": t,
            "kind": kind,
            "match_id": self.match_id,
            "creature_id": None,
            "species_id": None,
            "client_id": None,
            "model_name": None,
        }
        row.update(_round(fields))
        # sort_keys là bắt buộc: thứ tự chèn khác nhau ở hai chỗ dựng dict sẽ
        # làm hai lần chạy cùng seed cho hai file khác nhau.
        self._fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self._n += 1
        if self._n % self.flush_every == 0:
            self._fh.flush()

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.flush()
            self._fh.close()

    def __enter__(self) -> LogWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def read_log(path: str | Path) -> list[dict[str, Any]]:
    """Đọc toàn bộ file JSONL. Dùng ở score.py, analyze.py, replay."""
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
