"""Genesis Zero — rollout: sinh dữ liệu huấn luyện từ ván chơi (R-01, R-02).

**R-01** chạy nhiều ván headless; **R-02** biến mỗi ván thành các bộ ba
`(prompt, response, reward)`.

Điểm mấu chốt của R-02: log **không chứa prompt** — nó chỉ chứa `prompt_hash`
(B-06 bất biến 1, để log khỏi phình gấp 20 lần). Nên prompt phải được **dựng
lại** đúng như lúc chạy, và đường dựng lại ấy đã có sẵn: nó chính là cơ chế
replay. Dùng lại nó nghĩa là mọi mẫu huấn luyện được **kiểm** bằng `prompt_hash`
— một mẫu mà prompt dựng lại không khớp thì bị loại chứ không lặng lẽ đi vào tập
train. Sai một chỗ đó thì model học trên một prompt chưa từng tồn tại.

Ngân sách R-01 (03 §11): 15–25 s cho một ván 150 tick. Đo trên máy này:

* môi trường thuần: **0,07 s/ván** — nhanh hơn ngân sách ~200×, Python không
  phải nút cổ chai;
* nhưng với model thật, 4 lời gọi song song mất **2,3×** thời gian một lời gọi
  (llama.cpp trên Metal gần như tuần tự hoá phần decode). Nên thông lượng bị
  chặn bởi **tổng số lời gọi**, không bởi số tiến trình. Song song hoá **giữa
  các ván** không cứu được điều đó trên một máy một GPU; nó chỉ có nghĩa khi có
  nhiều máy — mà đó đúng là hình dạng chế độ mở ở [04](../docs/04-THE-GIOI-MO.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from genesis.lawdsl import to_json
from genesis.lawgen import generate_cached
from genesis.logio import LogWriter, read_log
from genesis.prompt import prompt_hash
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick
from genesis.world import visible


@dataclass
class Sample:
    """Một bộ ba huấn luyện."""

    match_id: str
    seed: int
    t: int
    creature_id: str
    kind: str                    # decide | codex | shift
    system: str
    user: str
    response: str
    tokens: int
    reward: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


def rollout(
    seed: int,
    ticks: int,
    llm_ids: list[str],
    url: str,
    out_dir: Path,
    arm: str = "STANDARD",
    prior_arm: str = "PRIOR_FREE",
    transport: Any = None,
) -> tuple[Path, Path]:
    """Chạy MỘT ván headless, ghi log + truth. Trả (log, truth)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    laws = generate_cached(seed, arm=arm)
    world, creatures, state, rng = build_match(seed, prior_arm=prior_arm, laws=laws)

    match_id = f"r_{seed:05d}"
    log_p = out_dir / f"{match_id}.jsonl"
    truth_p = out_dir / f"{match_id}.truth.json"
    with LogWriter(log_p, match_id) as log:
        log.write(0, "RUN_START", seed=seed, ticks=ticks, arm=arm, n_laws=len(laws))
        strat = LlmStrategist(url, llm_ids, log=log, transport=transport)
        for t in range(ticks):
            tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=strat)
        log.write(ticks, "RUN_END", ticks=ticks)

    truth_p.write_text(json.dumps({
        "seed": seed, "arm": arm, "prior_arm": prior_arm,
        "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }, ensure_ascii=False), encoding="utf-8")
    return log_p, truth_p


def samples_from(
    log_p: Path,
    truth_p: Path,
    url: str = "http://unused",
    transport: Any = None,
) -> list[Sample]:
    """R-02: log + truth -> danh sách `Sample` đã gắn reward.

    Prompt được **dựng lại** rồi **đối chiếu `prompt_hash`**. Mẫu nào lệch thì bị
    loại và đếm vào `meta`, không đi vào tập train: học trên một prompt chưa từng
    tồn tại là cách âm thầm nhất để hỏng một lần huấn luyện.
    """
    from genesis.score import score_match

    rows = read_log(log_p)
    truth = json.loads(Path(truth_p).read_text(encoding="utf-8"))
    seed = int(truth["seed"])
    laws = generate_cached(seed, arm=truth.get("arm", "STANDARD"))

    start = next((r for r in rows if r.get("kind") == "RUN_START"), {})
    ticks = int(start.get("ticks") or max((r["t"] for r in rows), default=1))

    # Phần thưởng cuối ván, chia theo cá thể. Mọi quyết định của một cá thể nhận
    # cùng một reward: đây là RLVR ở mức VÁN, không phải mức bước — và đó là chủ
    # ý, vì tín hiệu duy nhất kiểm chứng được nằm ở cuối ván (03 §0).
    #
    # Dùng `total_reward`, KHÔNG chỉ `ΣR_i`. Công thức đủ ở 03 §5.5 là
    # `R = ΣR_i + 0.5·R_pred + 0.3·R_exploit + 0.3·R_social + 0.1·R_survive`, và
    # cái đuôi 0.1·R_survive chính là **dây neo**: khi chưa con nào tìm ra luật
    # thì `ΣR_i = 0` cho tất cả, mọi lợi thế trong nhóm bằng 0, và GRPO không có
    # một gradient nào. Bỏ dây neo đi thì giai đoạn đầu huấn luyện — đúng lúc cần
    # tín hiệu nhất — hoàn toàn câm.
    from genesis.score import total_reward

    per_creature = total_reward(score_match(log_p, truth_p))

    world, creatures, state, rng = build_match(
        seed, prior_arm=truth.get("prior_arm", "PRIOR_FREE"), laws=laws
    )
    by_tick: dict[int, list[dict]] = {}
    for r in rows:
        if r.get("kind") == "LLM_CALL":
            by_tick.setdefault(int(r["t"]), []).append(r)

    llm_ids = sorted({r["creature_id"] for rs in by_tick.values() for r in rs})
    mind = LlmStrategist(url, llm_ids, transport=transport)
    from genesis.replay import ReplayStrategist

    rep = ReplayStrategist(log_p, mind=mind)
    out: list[Sample] = []
    mismatched = 0
    for t in range(ticks):
        # `build_prompt` tự đặt `world.phase = phase_at(t)` từ khi bẫy này bị
        # bịt ở gốc, nên ở đây không cần gán nữa. Giữ lại lời kể vì nó là một
        # bài học đắt: vá ở CHỖ GỌI thì bẫy còn nguyên cho mọi chỗ gọi sau.
        for rec in by_tick.get(t, ()):
            c = next((x for x in creatures if x.id == rec["creature_id"]), None)
            if c is None:
                continue
            system, user = mind.build_prompt(c, world, visible(c, world, creatures), t)
            if prompt_hash(system, user) != rec.get("prompt_hash"):
                mismatched += 1
                continue
            out.append(Sample(
                match_id=rec.get("match_id", ""), seed=seed, t=t,
                creature_id=c.id, kind=rec.get("kind_asked") or "decide",
                system=system, user=user, response=rec.get("raw", ""),
                tokens=int(rec.get("tokens_used", 0)),
                reward=round(per_creature.get(c.id, 0.0), 4),
            ))
        tick(world, creatures, t, rng, state, laws=laws, strategist=rep)

    for s in out:
        s.meta["n_mismatched_in_match"] = mismatched
    return out


def write_jsonl(samples: list[Sample], out: Path) -> Path:
    """Xuất tập train dạng JSONL. Một dòng một mẫu, prompt đã ghép sẵn."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for s in samples:
            fh.write(json.dumps({
                "prompt": s.system + s.user,
                "response": s.response,
                "reward": s.reward,
                "kind": s.kind,
                "seed": s.seed, "t": s.t, "creature_id": s.creature_id,
                "tokens": s.tokens,
            }, ensure_ascii=False) + "\n")
    return out


def split_by_law_structure(
    seeds: list[int], arm: str = "STANDARD", holdout: int = 4
) -> dict[str, Any]:
    """R-04: tách train/test theo **cấu trúc luật**, không theo seed.

    Chia ngẫu nhiên theo seed là tự lừa mình: "test" khi đó chỉ đo khả năng chạy
    lại, không đo khả năng khái quát.

    Nhưng khoá ở mức **bộ luật** cũng vô dụng, và điều đó đo được: một ván có 3
    luật, mỗi luật chọn từ 11 trigger × 15 effect, nên hai seed gần như **không
    bao giờ** trùng bộ. Đo thật: 400 seed cho 400 bộ khác nhau, và 24 seed cho
    24 bộ khác nhau kể cả với khoá thô nhất. Chia theo "bộ" là chia theo seed
    dưới một cái tên khác.

    Nên khoá ở mức **từng luật**: giữ lại một phần các cặp `(trigger, effect)`,
    và seed nào dùng tới một cặp bị giữ thì vào test. Câu hỏi mà tập test trả
    lời khi đó là câu đáng hỏi: *model có suy ra được một kiểu nhân quả nó chưa
    từng thấy không?*
    """
    pairs_of: dict[int, set[tuple[str, str]]] = {}
    for s in seeds:
        pairs_of[s] = {
            (l.trigger.kind.value, l.effect.kind.value)
            for l in generate_cached(s, arm=arm)
        }
    all_pairs = sorted({p for ps in pairs_of.values() for p in ps})
    held = {p for i, p in enumerate(all_pairs) if i % holdout == holdout - 1}

    train = sorted(s for s in seeds if not (pairs_of[s] & held))
    test = sorted(s for s in seeds if pairs_of[s] & held)
    return {
        "train": train, "test": test,
        "n_pairs": len(all_pairs), "n_pairs_held": len(held),
        "held_pairs": sorted(held),
    }
