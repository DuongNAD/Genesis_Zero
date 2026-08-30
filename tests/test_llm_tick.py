"""Kiểm thử ghép LLM vào vòng tick (B-05) và replay đầu-cuối (B-06).

Toàn bộ chạy trên `httpx.MockTransport`: không model, không cổng, không mạng.
Cái được kiểm ở đây là **kiến trúc**, không phải chất lượng model — và kiến trúc
kiểm được mà không cần model là chủ ý, không phải chỗ tạm bợ.
"""

from __future__ import annotations

import json
import random

import httpx
import pytest

from genesis import config
from genesis.creature import creature_sort_key
from genesis.logio import LogWriter, read_log
from genesis.reflex import Goal
from genesis.replay import ReplayMismatch, ReplayStrategist
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick


class FakeModel:
    """Model giả tất định: chọn goal theo hash của prompt, đếm số lời gọi."""

    def __init__(self, fail: bool = False, tokens: int = 40) -> None:
        self.fail = fail
        self.tokens = tokens
        self.n = 0
        self.slots: dict[int, int] = {}
        self.prompts: list[str] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.n += 1
            body = json.loads(request.content)
            self.slots[body["id_slot"]] = self.slots.get(body["id_slot"], 0) + 1
            self.prompts.append(body["prompt"])
            if self.fail:
                return httpx.Response(503, text="model chưa lên")
            goal = ("FORAGE", "REST", "WANDER")[len(body["prompt"]) % 3]
            return httpx.Response(200, json={
                "content": json.dumps({"goal": goal, "ttl": 4}),
                "tokens_predicted": self.tokens,
            })
        return httpx.MockTransport(handler)


def _run(seed: int, ticks: int, model: FakeModel, ids: list[str] | None = None,
         out=None, laws=None, on_tick=None):
    world, creatures, state, rng = build_match(seed=seed)
    if ids is None:
        ids = [c.id for c in creatures if c.species == "L1"]
    log = LogWriter(out, f"m_{seed}") if out is not None else None
    strat = LlmStrategist("http://model", ids, log=log, transport=model.transport())
    for t in range(ticks):
        tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=strat)
        if on_tick is not None:
            on_tick(t, strat)
    if log is not None:
        log.close()
    return world, creatures, strat


def test_chi_goi_cho_con_duoc_chon_va_dung_nhip(tmp_path):
    """Bất biến 2: t % think_interval == offset, và offset rải đều trong loài."""
    out = tmp_path / "b05.jsonl"
    model = FakeModel()
    _run(44, 200, model, ids=["L1:0"], out=out)

    calls = [r for r in read_log(out) if r["kind"] == "LLM_CALL"]
    assert calls, "không có lời gọi nào"
    assert all(r["creature_id"] == "L1:0" for r in calls)
    for r in calls:
        assert r["t"] % r["think_interval"] == r["offset"], r


def test_offset_rai_deu_trong_loai():
    """Không rải thì cả đàn cùng nghĩ một tick: cùng tải, gấp mấy lần độ trễ đuôi."""
    world, creatures, _, _ = build_match(seed=44)
    # Loài đông nhất trong POPULATION hiện tại; offset phải trải chứ không dồn.
    by_sp: dict[str, list] = {}
    for c in creatures:
        by_sp.setdefault(c.species, []).append(c)
    sp, members = max(by_sp.items(), key=lambda kv: len(kv[1]))
    assert len(members) >= 2, "POPULATION quá nhỏ để test được việc rải pha"
    offsets = {LlmStrategist.offset_of(c) for c in members}
    assert len(offsets) == min(len(members), members[0].traits.think_interval), (
        f"loài {sp}: {len(members)} con nhưng chỉ {len(offsets)} pha khác nhau"
    )


def test_cost_think_theo_token_thuc_sinh(tmp_path):
    """Bất biến 3: tính theo max_tokens thì ngân sách token theo brain vô nghĩa."""
    out = tmp_path / "b05.jsonl"
    _run(44, 120, FakeModel(tokens=37), ids=["L1:0", "L5:0"], out=out)
    calls = [r for r in read_log(out) if r["kind"] == "LLM_CALL"]
    for r in calls:
        assert r["tokens_used"] == 37
        assert r["cost_think"] == round(37 / config.TOKENS_PER_ENERGY, 4)
    # và ngân sách max_tokens KHÁC nhau giữa hai loài, nên nếu tính theo
    # max_tokens thì cost sẽ khác nhau — nó không khác, đúng như phải thế.
    assert len({r["cost_think"] for r in calls}) == 1


def test_llm_khong_goi_moi_tick_cho_moi_con(tmp_path):
    """Bất biến 1: thấy mình gọi LLM mỗi tick cho mỗi con là hiểu sai kiến trúc."""
    out = tmp_path / "b05.jsonl"
    model = FakeModel()
    world, creatures, _ = _run(44, 100, model, out=out)
    n_l1 = len([c for c in creatures if c.species == "L1"])
    assert model.n < 100 * n_l1 / 2, f"{model.n} lời gọi cho {n_l1} con trong 100 tick"


def test_slot_ghim_suot_van(tmp_path):
    """B-03 bất biến 2: một creature_id giữ nguyên một slot, nếu không cache mất trắng."""
    model = FakeModel()
    _run(44, 150, model, ids=["L1:0", "L1:1", "L2:0"])
    assert set(model.slots) == {0, 1, 2}


def test_model_chet_thi_ngat_mach_va_van_van_chay(tmp_path):
    """Bất biến 3 của B-03: rơi về phản xạ, ván không gãy, và không gọi mãi."""
    out = tmp_path / "b05.jsonl"
    model = FakeModel(fail=True)
    world, creatures, strat = _run(44, 200, model, ids=["L1:0"], out=out)
    rows = read_log(out)
    assert not [r for r in rows if r["kind"] == "LLM_CALL"]
    assert [r for r in rows if r["kind"] == "LLM_MISS"]
    assert strat.stats["skipped_open"] > 0, "ngắt mạch không bao giờ đóng"
    assert model.n < 20, f"vẫn gọi {model.n} lần sau khi model chết"
    assert any(c.alive for c in creatures), "ván phải sống tiếp bằng phản xạ"


def test_hoan_vi_thu_tu_khong_doi_ket_qua():
    """W-11: thêm tầng LLM KHÔNG được phá bất biến đồng thời."""
    def run(perm_seed: int) -> list[tuple]:
        world, creatures, state, rng = build_match(seed=44)
        random.Random(perm_seed).shuffle(creatures)
        strat = LlmStrategist(
            "http://model", [c.id for c in creatures if c.species == "L1"],
            transport=FakeModel().transport(),
        )
        for t in range(60):
            tick(world, creatures, t, rng, state, strategist=strat)
        return [
            (c.id, c.pos, round(c.hp, 4), round(c.energy, 4), c.alive)
            for c in sorted(creatures, key=creature_sort_key)
        ]

    base = run(1)
    for p in (2, 3, 4):
        assert run(p) == base, f"hoán vị {p} cho kết quả khác"


def test_so_tay_duoc_nap_tu_su_kien_that():
    """Sổ tay rỗng thì agent không có gì để quy nạp, và cả v5 vô nghĩa."""
    from genesis.lawgen import generate_cached
    laws = generate_cached(44, arm="STANDARD")

    # Chụp sổ tay TRONG lúc chạy, không đọc ở đúng tick cuối.
    #
    # Bản cũ đọc `strat.notes[...]` sau vòng lặp, và nó đứng trên một sự trùng
    # hợp: sổ tay CHẾT THEO ĐỜI (W-17), nên nếu con vật tình cờ chết ở vài tick
    # cuối thì sổ rỗng và bài kiểm đỏ vì một lý do chẳng liên quan gì tới điều nó
    # muốn khẳng định. Đã xảy ra thật khi W-18 xê dịch thế giới đi một chút —
    # đo lại thì đời sống của quần thể **không đổi** (chết/ván 53 trước và sau),
    # chỉ là con `L1:0` của seed 44 rơi sang bên kia lằn ranh.
    #
    # Điều bài này thật sự muốn nói là *"sổ tay CÓ được nạp từ sự kiện thật"*,
    # và câu ấy phải đúng ở mọi tick, không riêng tick cuối.
    seen: list[str] = []

    def snap(t, strat):
        n = strat.notes.get("L1:0")
        if n is not None:
            txt = n.render(20)
            if txt:
                seen.append(txt)

    _, _, strat = _run(44, 150, FakeModel(), ids=["L1:0"], laws=laws, on_tick=snap)
    assert seen, "sổ tay chưa bao giờ được nạp trong 150 tick"
    txt = max(seen, key=len)
    # Tên hệ quả là đáp án. Sổ tay ghi CẢM GIÁC, không ghi tên.
    from genesis.lawdsl import EffectKind
    for e in EffectKind:
        assert e.value not in txt
    assert "FRUIT_" not in txt


def test_replay_khop_ban_ghi_va_bat_lech(tmp_path):
    """B-06: replay phải dựng lại đúng, và phải NÉM khi prompt đã rẽ nhánh."""
    out = tmp_path / "live.jsonl"
    _run(44, 90, FakeModel(), ids=["L1:0"], out=out)
    calls = [r for r in read_log(out) if r["kind"] == "LLM_CALL"]
    assert calls

    world, creatures, state, rng = build_match(seed=44)
    mind = LlmStrategist("http://model", ["L1:0"], transport=FakeModel().transport())
    rep = ReplayStrategist(out, mind=mind)
    assert rep.verifying
    for t in range(90):
        tick(world, creatures, t, rng, state, strategist=rep)
    assert rep.n_replayed == len(calls), (
        f"phát lại {rep.n_replayed}/{len(calls)} lời gọi"
    )

    # Lệch: đổi persona -> prompt khác -> hash khác -> phải dừng, không chạy tiếp.
    world, creatures, state, rng = build_match(seed=44)
    mind2 = LlmStrategist("http://model", ["L1:0"], personas={"L1": "KHÁC HẲN"})
    rep2 = ReplayStrategist(out, mind=mind2)
    with pytest.raises(ReplayMismatch):
        for t in range(90):
            tick(world, creatures, t, rng, state, strategist=rep2)
