"""Genesis Zero — chạy vòng hỏi tiên đoán ở tick T−1 (B-09 bất biến 3).

Vì sao là một module riêng chứ không phải một method của `LlmStrategist`: hàm này
**biết luật thật**, còn tầng chiến lược thì tuyệt đối không được biết. Để chung
một lớp thì ranh giới ấy chỉ còn là kỷ luật của người sửa code tiếp theo, và
`docs/04 §7` nói rõ những ranh giới như thế phải do cấu trúc giữ, không do trí nhớ.

Tầng chấm thứ hai trả lời câu *nó hiểu, hay nó vừa may?* — Sổ Luật chấm cái agent
**phát biểu**, oracle chấm cái agent **tiên đoán** ở những tình huống nó chưa gặp.
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import Any

import httpx

from genesis import law_config
from genesis.creature import creature_sort_key
from genesis.lawdsl import Effect, EffectKind, Dur, Law, Mag
from genesis.llm_client import ask
from genesis.oracle import build_queries, score_answers
from genesis.situations import sample_situations
from genesis.strategist import _budget, schema_for
from genesis.world import visible

_ORACLE_TAIL = (
    "\n\n[CÂU HỎI]\nTrả lời từng câu: chuyện gì xảy ra? Nếu ngươi cho là không có "
    "gì xảy ra thì bỏ trống. Không ai chấm ngươi ngay, và không ai nói ngươi đúng "
    "hay sai.\n"
)


def _answer_to_effect(d: Any) -> Effect | None:
    """Đáp án của model -> Effect, hoặc None khi nó nói 'không có gì'.

    Mọi trường sai kiểu đều thành None chứ không thành một Effect nửa vời: một
    đáp án hỏng phải được chấm như 'không trả lời', không như 'trả lời sai một ít'.
    """
    if not isinstance(d, dict) or not d.get("kind"):
        return None
    try:
        return Effect(
            kind=EffectKind(d["kind"]),
            mag=Mag(d["mag"]) if d.get("mag") else None,
            dur=Dur(d["dur"]) if d.get("dur") else None,
            r=int(d["r"]) if isinstance(d.get("r"), int) else None,
            arg=d.get("arg") if isinstance(d.get("arg"), str) else None,
            dir=d.get("dir") if isinstance(d.get("dir"), str) else None,
        )
    except (ValueError, KeyError, TypeError):
        return None


async def run_oracle(
    strategist,
    creatures: list,
    world,
    laws: list[Law],
    tick_no: int,
    seed: int,
    log: Any = None,
) -> dict[str, float]:
    """Hỏi mỗi cá thể `ORACLE_QUERIES` câu về MỖI luật, một lần, ở tick T−1."""
    if not laws:
        return {}
    sm = world.surface_map
    n = law_config.ORACLE_QUERIES

    jobs = []
    for c in sorted(creatures, key=creature_sort_key):
        if c.id not in getattr(strategist, "slots", {}):
            continue
        for i, law in enumerate(laws):
            # Tất định theo (seed, luật): chấm lại được ở máy khác, năm sau.
            rng = random.Random(seed * 977 + i)
            sits = sample_situations(law, n, random.Random(seed * 977 + i))
            qs = build_queries(law, sm, n, rng)
            system, user = strategist.build_prompt(
                c, world, visible(c, world, creatures), tick_no
            )
            body = user + _ORACLE_TAIL + "\n".join(f"{k}. {q}" for k, q in enumerate(qs))
            jobs.append((c, i, law, sits, system, body))

    if not jobs:
        return {}

    # Đường thứ TƯ gọi model, và nó từng bỏ cả ba thứ mà `strategist.think` học
    # được sau ba lần hỏng:
    #
    #   1. `id_slot` thô 0..14 trong khi server chỉ có 8 chỗ -> mọi lời gọi từ
    #      chỗ 8 trở lên **hỏng** ("lỗi mạng ... slot 12/13/14"), và prefix cache
    #      của những con ấy không bao giờ chạy.
    #   2. không có cổng chặn -> cả đàn bay cùng lúc, phần thừa xếp hàng TRONG
    #      server và hạn chờ đếm cả lúc chờ.
    #   3. hạn chờ cứng -> đúng cái đã làm 20/41 lời gọi của Qwen-14B trượt.
    #
    # Dùng lại đúng cơ chế của `think`, không viết bản thứ hai.
    n = await strategist._ensure_slots_for(strategist.base_url, strategist.transport)
    waves = max(1, -(-len(jobs) // max(1, n)))
    timeout = max(strategist.timeout,
                  3.0 * (getattr(strategist, "_call_ms", None) or 0.0) / 1000.0) * waves
    gate = asyncio.Semaphore(n)

    async with httpx.AsyncClient(
        timeout=timeout, transport=strategist.transport
    ) as client:
        async def _one(c, system, body):
            async with gate:
                # `_budget`, không phải một biểu thức chép tay. Bản cũ viết
                # `CLAIM_BUDGET_BY_BRAIN * 2` ngay tại đây — đường thứ tư gọi
                # model, và nó bỏ bài học thứ TƯ của `think` sau khi đã bỏ ba
                # bài đầu (xem khối chú thích ngay trên).
                return await ask(
                    strategist.base_url, strategist.slots[c.id] % n, system, body,
                    _budget(c.traits, "oracle"),
                    schema_for(c.traits, "oracle", sm=world.surface_map), client=client)

        results = await asyncio.gather(*[
            _one(c, system, body) for c, _i, _law, _sits, system, body in jobs
        ])

    per_creature: dict[str, list[float]] = {}
    for (c, i, law, sits, _s, _b), r in zip(jobs, results):
        if r is None:
            continue
        answers: list[Effect | None] = [None] * len(sits)
        for a in (r["json"].get("answers") or []):
            q = a.get("q")
            if isinstance(q, int) and 0 <= q < len(sits):
                answers[q] = _answer_to_effect(a.get("effect"))
        acc = score_answers(answers, law, sits)
        per_creature.setdefault(c.id, []).append(acc)
        if log is not None:
            # `n_answered` tách được hai chuyện mà `pred_acc` gộp làm một: **trả
            # lời sai** và **không trả lời gì**. Thiếu cột này thì một lượt hỏi
            # bị cắt giữa chừng, hay một `{"answers": []}` nhả ra cho xong, đều
            # đọc thành `pred_acc = 0` — và ta kết luận về năng lực tiên đoán của
            # model từ một con số chỉ nói rằng nó đã im lặng.
            log.write(tick_no, "ORACLE", creature_id=c.id, species_id=c.species,
                      law_idx=i, pred_acc=round(acc, 4), n_q=len(sits),
                      n_answered=sum(1 for a in answers if a is not None))

    out = {cid: round(sum(v) / len(v), 4) for cid, v in per_creature.items() if v}
    if log is not None:
        for cid, acc in sorted(out.items()):
            log.write(tick_no, "ORACLE", creature_id=cid,
                      species_id=cid.rpartition(":")[0], law_idx=-1, pred_acc=acc,
                      n_q=len(laws) * n)
    return out
