"""Genesis Zero — net/routes_decision: nhận và validate quyết định (N-07)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

import net_config
from genesis import law_config, speech
from genesis.lawdsl import to_json
from genesis.reveal import law_from_surface_dict
from genesis.strategist import payload_to_goal
from genesis.validate import (
    Verdict,
    validate_codex,
    validate_decide,
    validate_hunch,
    validate_shift,
)
from genesis.world import visible
from net import state
from net.match import Phase
from net.routes_work import (
    _issued_works,
    get_bearer_token,
    get_creature_codex,
    get_registration,
    set_creature_notepad,
    set_creature_want_codex,
)

router = APIRouter(prefix="/v1", tags=["decision"])


def _log_codex(runner, creature, payload, verdict, law) -> None:
    """Ván ở chế độ mở phải sinh ra log chấm được y như ván Lab.

    Luật ghi bằng LỚP, không bằng bề mặt: bộ chấm so với luật thật, mà luật thật
    viết bằng lớp; ghi bề mặt thì mỗi ván một cách viết khác và không so được.
    """
    runner._write(
        "CODEX_OP",
        creature_id=creature.id, species_id=creature.species,
        ok=verdict.ok, reason=verdict.reason,
        op=payload.get("op"), slot=payload.get("slot"), conf=payload.get("conf"),
        law=to_json(law) if law is not None else None,
    )


@router.post("/decision")
async def decision(
    request: Request,
    authorization: str | None = Header(None),
) -> JSONResponse:
    """Nhận và xác thực quyết định cho một work item."""
    raw_body = await request.body()
    if len(raw_body) > net_config.BODY_MAX_BYTES:
        raise HTTPException(status_code=413, detail="TOO_LARGE")

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="INVALID_PAYLOAD") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="INVALID_PAYLOAD")

    token = get_bearer_token(authorization)
    reg = get_registration(token)

    # 1. Kiểm tra pha ván đấu
    if state.runner.phase in (Phase.LOBBY, Phase.SEEDING, Phase.COOLDOWN):
        raise HTTPException(status_code=409, detail="WRONG_PHASE")
    if state.runner.phase is Phase.REVEAL:
        raise HTTPException(status_code=410, detail="WORK_EXPIRED")
    if state.runner.phase != Phase.RUNNING:
        raise HTTPException(status_code=409, detail="WRONG_PHASE")

    # 2. Kiểm tra work_id
    work_id = data.get("work_id")
    if not work_id or not isinstance(work_id, str):
        raise HTTPException(status_code=422, detail="INVALID_PAYLOAD")

    work_record = _issued_works.get(work_id)
    if work_record is None:
        raise HTTPException(status_code=404, detail="UNKNOWN_WORK")

    # 3. Kiểm tra quyền sở hữu sinh vật
    if work_record.client_id != reg.client_id:
        raise HTTPException(status_code=403, detail="NOT_YOUR_CREATURE")

    # 4. Thời hạn: hỏi runner, đừng tự tính lại.
    # Hai chỗ cùng trả lời "muộn hay chưa" là hai chỗ sẽ lệch nhau — và ở đây
    # chúng ĐÃ lệch: route cho `2*LATE_TOLERANCE`, `on_decision` cho một lần.
    # Quan trọng hơn: đường của route không ghi độ trễ vào `runner.latencies`,
    # nên nhịp thích ứng của N-08 không bao giờ có dữ liệu để điều chỉnh — một
    # tính năng chết lặng lẽ.
    current_tick = state.runner.tick_no
    if current_tick - work_record.issued_tick > 2 * net_config.LATE_TOLERANCE:
        state.runner.on_decision(work_record.issued_tick, work_id, lambda: None)
        raise HTTPException(status_code=410, detail="WORK_EXPIRED")

    # 5. Bất biến theo work_id (idempotent)
    if work_record.processed:
        if work_record.cached_response is not None:
            return JSONResponse(status_code=200, content=work_record.cached_response)
        return JSONResponse(
            status_code=200,
            content={
                "accepted": True,
                "applied_at_tick": work_record.applied_at_tick,
                "latency_ticks": work_record.latency_ticks,
            },
        )

    # 6. Kiểm tra payload
    payload = data.get("payload")
    if payload is None or not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="INVALID_PAYLOAD")

    world = state.runner.world
    if world is None:
        raise HTTPException(status_code=400, detail="MATCH_NOT_ACTIVE")

    creature = next(
        (c for c in state.runner.creatures if c.id == work_record.creature_id),
        None,
    )
    if creature is None or not creature.alive:
        resp: dict[str, Any] = {"accepted": False, "reason": "CREATURE_DEAD"}
        work_record.processed = True
        work_record.cached_response = resp
        return JSONResponse(status_code=200, content=resp)

    # 7. Xử lý theo từng loại công việc
    if work_record.kind == "decide":
        seen = visible(creature, world, state.runner.creatures)
        verdict = validate_decide(payload, creature, world, seen)
        if not verdict.ok:
            resp = {"accepted": False, "reason": verdict.reason}
            work_record.processed = True
            work_record.cached_response = resp
            return JSONResponse(status_code=200, content=resp)

        goal = payload_to_goal(payload)
        if goal is not None:
            state.runner.decisions[creature.id] = goal

        note = payload.get("note")
        if isinstance(note, str) and note.strip():
            # `sanitize_free_text`, không `.strip()[:N]`. Đường cục bộ đã học
            # bài này bằng một ván gãy ở lượt 87: ghi chú do model viết đi thẳng
            # vào khối E ở lượt sau, nên chỉ cần nó viết đúng chữ "HP" là
            # `_check_no_leak` ném `PromptLeak` và **ván chết**. Ở chế độ mở thì
            # tệ hơn hẳn — chuỗi ấy đến từ một người lạ, nên đây không còn là
            # một tai nạn mà là một nút bấm để giết ván của mọi người.
            set_creature_notepad(
                creature.id,
                speech.sanitize_free_text(note, law_config.NOTEPAD_MAX_CHARS),
            )

        if payload.get("want_codex"):
            set_creature_want_codex(creature.id, True)

        if payload.get("want_hunch"):
            state.runner.minds.want_hunch.add(creature.id)

        # Nói và DẠY (B-11, B-12). Trước N-16 trường `say` có trong schema mà
        # `/decision` không đọc: client qua mạng gửi lên rồi rơi vào hư không,
        # nên ở chế độ mở **không ai nói được câu nào**. Cả câu hỏi Q2 của dự án
        # ("giao tiếp đáng giá bao nhiêu?") không đo được ở đúng chế độ sinh ra
        # để hỏi nó, và bản đồ RUNG_RAM được thiết kế riêng cho nó thì vô nghĩa.
        say = speech.Say.parse(payload.get("say"))
        if say is not None:
            state.runner.strategist.pending_say[creature.id] = say

        latency = current_tick - work_record.issued_tick
        state.runner.on_decision(work_record.issued_tick, work_id, lambda: None)
        resp = {
            "accepted": True,
            "applied_at_tick": current_tick,
            "latency_ticks": latency,
        }
        work_record.processed = True
        work_record.applied_at_tick = current_tick
        work_record.latency_ticks = latency
        work_record.cached_response = resp
        return JSONResponse(status_code=200, content=resp)

    elif work_record.kind == "codex":
        cx = get_creature_codex(creature)
        verdict = validate_codex(
            payload,
            creature,
            world.surface_map,
            current_tick,
            cx.last_claim,
        )
        law = None
        if verdict.ok and payload.get("law") is not None:
            try:
                law = law_from_surface_dict(
                    payload["law"],
                    world.surface_map,
                )
            except (KeyError, ValueError, TypeError) as exc:
                verdict = Verdict(
                    ok=False,
                    reason=f"CODEX_MALFORMED_LAW:{type(exc).__name__}",
                )

        if verdict.ok:
            verdict = cx.apply(
                payload.get("op", "SET"),
                int(payload.get("slot", 0)),
                law,
                int(payload.get("conf", 3)),
                current_tick,
            )

        # Ghi CODEX_OP dù ok hay không: `score.py` chỉ tính op THÀNH CÔNG, nhưng
        # tỉ lệ op hỏng theo lý do là chỉ số chẩn đoán chính của B-08.
        _log_codex(state.runner, creature, payload, verdict, law)

        if not verdict.ok:
            resp = {"accepted": False, "reason": verdict.reason}
            work_record.processed = True
            work_record.cached_response = resp
            return JSONResponse(status_code=200, content=resp)

        latency = current_tick - work_record.issued_tick
        state.runner.on_decision(work_record.issued_tick, work_id, lambda: None)
        resp = {
            "accepted": True,
            "applied_at_tick": current_tick,
            "latency_ticks": latency,
        }
        work_record.processed = True
        work_record.applied_at_tick = current_tick
        work_record.latency_ticks = latency
        work_record.cached_response = resp
        return JSONResponse(status_code=200, content=resp)

    elif work_record.kind == "hunch":
        # B-14 ở chế độ mở. KHÔNG ghi `CODEX_OP` và không đụng `Ledger`: linh
        # cảm không được chấm, và một dòng log sai tên là đủ để nó chảy vào bộ
        # chấm — bất biến 1 của B-14 vỡ bằng đúng một chữ.
        hb = state.runner.minds.hunch_of(creature)
        verdict = validate_hunch(
            payload, creature, world.surface_map, current_tick, hb.last_write,
        )
        law = None
        if verdict.ok and payload.get("law") is not None:
            try:
                law = law_from_surface_dict(
                    payload["law"], world.surface_map,
                )
            except (KeyError, ValueError, TypeError) as exc:
                verdict = Verdict(
                    ok=False, reason=f"HUNCH_MALFORMED_LAW:{type(exc).__name__}",
                )
        if verdict.ok:
            verdict = hb.apply(
                payload.get("op", "SET"), int(payload.get("slot", 0)), law, current_tick,
            )

        state.runner._write(
            "HUNCH_OP",
            creature_id=creature.id, species_id=creature.species,
            ok=verdict.ok, reason=verdict.reason,
            op=payload.get("op"), slot=payload.get("slot"),
            law=to_json(law) if law is not None else None,
        )

        if not verdict.ok:
            resp = {"accepted": False, "reason": verdict.reason}
            work_record.processed = True
            work_record.cached_response = resp
            return JSONResponse(status_code=200, content=resp)

        latency = current_tick - work_record.issued_tick
        state.runner.on_decision(work_record.issued_tick, work_id, lambda: None)
        resp = {
            "accepted": True,
            "applied_at_tick": current_tick,
            "latency_ticks": latency,
        }
        work_record.processed = True
        work_record.applied_at_tick = current_tick
        work_record.latency_ticks = latency
        work_record.cached_response = resp
        return JSONResponse(status_code=200, content=resp)

    elif work_record.kind == "shift":
        # B-13 ở chế độ mở. Sai thì **bỏ lượt, KHÔNG thử lại** — `take_shift`
        # nhớ mức `adapt_points` đã hỏi, nên con trả lời sai không được hỏi lại
        # ở cùng mức điểm. Thử lại là một ưu đãi vô hình cho con hay sai: mọi
        # lượt nghĩ của nó đổ vào một câu hỏi nó liên tục trả lời hỏng.
        verdict = validate_shift(payload, creature)
        state.runner._write(
            "SHIFT_OP",
            creature_id=creature.id, species_id=creature.species,
            ok=verdict.ok, reason=verdict.reason,
            frm=payload.get("from"), to=payload.get("to"),
        )
        if not verdict.ok:
            resp = {"accepted": False, "reason": verdict.reason}
            work_record.processed = True
            work_record.cached_response = resp
            return JSONResponse(status_code=200, content=resp)

        why = payload.get("why")
        state.runner.strategist.shift_choice[creature.id] = (
            payload["from"], payload["to"],
        )
        state.runner.strategist.shift_why[creature.id] = (
            str(why)[:80] if isinstance(why, str) else None
        )

        latency = current_tick - work_record.issued_tick
        state.runner.on_decision(work_record.issued_tick, work_id, lambda: None)
        resp = {
            "accepted": True,
            "applied_at_tick": current_tick,
            "latency_ticks": latency,
        }
        work_record.processed = True
        work_record.applied_at_tick = current_tick
        work_record.latency_ticks = latency
        work_record.cached_response = resp
        return JSONResponse(status_code=200, content=resp)

    elif work_record.kind == "oracle":
        latency = current_tick - work_record.issued_tick
        state.runner.on_decision(work_record.issued_tick, work_id, lambda: None)
        resp = {
            "accepted": True,
            "applied_at_tick": current_tick,
            "latency_ticks": latency,
        }
        work_record.processed = True
        work_record.applied_at_tick = current_tick
        work_record.latency_ticks = latency
        work_record.cached_response = resp
        return JSONResponse(status_code=200, content=resp)

    raise HTTPException(status_code=422, detail="INVALID_PAYLOAD")
