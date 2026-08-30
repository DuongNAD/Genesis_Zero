"""Genesis Zero v5 — reveal: Công bố luật thật và chấm điểm cuối ván (L-07)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.table import Table

from genesis.lawdsl import (
    Cond,
    Dur,
    Effect,
    Law,
    Mag,
    Trigger,
    from_json,
    to_vietnamese,
)
from genesis.surface import SurfaceMap

if TYPE_CHECKING:
    from rich.console import RenderableType


def _trigger_to_surface_dict(t: Trigger, sm: SurfaceMap) -> dict[str, Any]:
    d: dict[str, Any] = {"kind": t.kind.value}
    if t.arg is not None:
        if t.arg.startswith("FRUIT_"):
            d["arg"] = sm.surface_of(t.arg)
        else:
            d["arg"] = t.arg
    if t.k is not None:
        d["k"] = t.k
    if t.n is not None:
        d["n"] = t.n
    if t.r is not None:
        d["r"] = t.r
    return d


def _cond_to_surface_dict(c: Cond, sm: SurfaceMap) -> dict[str, Any]:
    d: dict[str, Any] = {"kind": c.kind.value}
    if c.arg is not None:
        if c.arg.startswith("FRUIT_"):
            d["arg"] = sm.surface_of(c.arg)
        else:
            d["arg"] = c.arg
    if c.k is not None:
        d["k"] = c.k
    if c.op is not None:
        d["op"] = c.op
    if c.n is not None:
        d["n"] = c.n
    if c.r is not None:
        d["r"] = c.r
    return d


def _effect_to_surface_dict(e: Effect, sm: SurfaceMap) -> dict[str, Any]:
    d: dict[str, Any] = {"kind": e.kind.value}
    if e.mag is not None:
        d["mag"] = e.mag.value if isinstance(e.mag, Mag) else str(e.mag)
    if e.dur is not None:
        d["dur"] = e.dur.value if isinstance(e.dur, Dur) else str(e.dur)
    if e.r is not None:
        d["r"] = e.r
    if e.arg is not None:
        if e.arg.startswith("FRUIT_"):
            d["arg"] = sm.surface_of(e.arg)
        else:
            d["arg"] = e.arg
    if e.dir is not None:
        d["dir"] = e.dir
    return d


def _law_to_surface_dict(law: Law, sm: SurfaceMap) -> dict[str, Any]:
    return {
        "trigger": _trigger_to_surface_dict(law.trigger, sm),
        "conds": [_cond_to_surface_dict(c, sm) for c in law.conds],
        "effect": _effect_to_surface_dict(law.effect, sm),
    }


def law_from_surface_dict(d: dict[str, Any], sm: SurfaceMap) -> Law:
    """Nghịch đảo của `_law_to_surface_dict`: bề mặt -> lớp.

    Agent chỉ biết bề mặt ("quả đỏ tròn") vì lớp là thứ ta giấu. Nhưng bộ chấm so
    với luật thật, mà luật thật viết bằng lớp. Chỗ đổi chiều là ĐÂY, một chỗ duy
    nhất, ngay cạnh hàm đi chiều ngược lại — hai hàm nghịch đảo nằm xa nhau là hai
    hàm sẽ lệch nhau.

    Bề mặt không có trong bảng thì giữ nguyên chuỗi: `validate_codex` đã bắt ca đó
    bằng `CODEX_UNKNOWN_SURFACE` trước khi tới đây, và im lặng đổi nó thành một lớp
    nào đó là bịa ra một câu trả lời hộ agent.
    """
    def unmap(arg: Any) -> Any:
        if not isinstance(arg, str):
            return arg
        return sm.class_of(arg) or arg

    out: dict[str, Any] = {"trigger": dict(d.get("trigger") or {}), "conds": [], "effect": dict(d.get("effect") or {})}
    for part in (out["trigger"], out["effect"]):
        if "arg" in part:
            part["arg"] = unmap(part["arg"])
    for c in d.get("conds") or ():
        cc = dict(c)
        if "arg" in cc:
            cc["arg"] = unmap(cc["arg"])
        out["conds"].append(cc)
    return from_json(out)


def build_reveal(
    laws: list[Law],
    codices: dict[str, Any] | None,
    sm: SurfaceMap,
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    """Tạo payload kết quả REVEAL theo đúng đặc tả docs/05-GIAO-THUC.md §3.6."""
    if log_path is not None:
        p = Path(log_path)
        name = p.name
        for suffix in (".truth.json", ".reveal.json", ".jsonl", ".json", ".log"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        match_id = name
    else:
        match_id = "m_00000"

    laws_payload: list[dict[str, Any]] = []
    for i, law in enumerate(laws):
        laws_payload.append({
            "law_id": f"L{i}",
            "tier": law.tier(),
            "dsl": _law_to_surface_dict(law, sm),
            "vi": to_vietnamese(law, sm),
            "fired_count": 0,
        })

    scores_payload: list[dict[str, Any]] = []
    if codices:
        for cid in sorted(codices.keys()):
            per_law = []
            for i, _ in enumerate(laws):
                per_law.append({
                    "law_id": f"L{i}",
                    "match": 0.0,
                    "t_discover": None,
                    "exploited": False,
                    "exploit_lag": None,
                })
            scores_payload.append({
                "creature_id": cid,
                "per_law": per_law,
                "pred_acc": 0.0,
                "brier": 0.0,
                "R_discovery": 0.0,
                "R_social": 0.0,
                "R_total": 0.0,
            })

    return {
        "match_id": match_id,
        "laws": laws_payload,
        "scores": scores_payload,
        "citations": [],
        "deception": [],
    }


def render_reveal(payload: dict[str, Any]) -> RenderableType:
    """Render bảng terminal rich cho kết quả REVEAL."""
    table = Table(
        title=f"REVEAL — KẾT QUẢ VÁN ĐẤU ({payload.get('match_id', '')})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Hạng", style="green", width=6)
    table.add_column("Diễn giải (Tiếng Việt)", style="white")
    table.add_column("Kích hoạt", justify="right", style="yellow")
    table.add_column("Ai đoán đúng", style="cyan")
    table.add_column("Tick", justify="right", style="green")

    discoveries: dict[str, list[tuple[str, int]]] = {}
    for score in payload.get("scores", []):
        cid = score.get("creature_id", "")
        for pl in score.get("per_law", []):
            lid = pl.get("law_id", "")
            t_disc = pl.get("t_discover")
            match_val = pl.get("match", 0.0)
            if t_disc is not None and match_val >= 0.8:
                discoveries.setdefault(lid, []).append((cid, t_disc))

    for lid in discoveries:
        discoveries[lid].sort(key=lambda x: x[1])

    for law in payload.get("laws", []):
        lid = law.get("law_id", "")
        tier = law.get("tier", "")
        vi = law.get("vi", "")
        fired = str(law.get("fired_count", 0))

        disc_list = discoveries.get(lid, [])
        if disc_list:
            who = ", ".join(d[0] for d in disc_list)
            ticks = ", ".join(str(d[1]) for d in disc_list)
        else:
            who = "-"
            ticks = "-"

        table.add_row(lid, tier, vi, fired, who, ticks)

    return table
