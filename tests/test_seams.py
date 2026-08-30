"""Genesis Zero — kiểm thử cho 3 đường may mở rộng (N-01, N-02, N-03)."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

from genesis import config
from genesis.creature import Creature
from genesis.logio import COMMON_FIELDS, EVENT_KINDS, LogWriter
from genesis.reflex import ActiveGoal, Goal
from genesis.strategist import (
    LlmStrategist,
    ReflexStrategist,
    RemoteClientStrategist,
    Strategist,
)
from genesis.tick import build_match, tick


def test_strategist_protocol_and_classes() -> None:
    """N-01: Các lớp hiện thực đều thoả Strategist Protocol."""
    assert isinstance(ReflexStrategist(), Strategist)
    assert isinstance(RemoteClientStrategist({}), Strategist)
    assert isinstance(LlmStrategist("http://x", []), Strategist)


def test_remote_client_strategist_queue() -> None:
    """N-01: RemoteClientStrategist trả None khi rỗng, trả Goal khi có trong hàng đợi."""
    w, cs, st, rng = build_match(seed=1)
    strat = RemoteClientStrategist({})
    assert strat.decide(cs[0], w, []) is None

    goal = ActiveGoal(goal=Goal.FORAGE, target=None, ttl=5)
    strat_with_goal = RemoteClientStrategist({cs[0].id: goal})
    decided = strat_with_goal.decide(cs[0], w, [])
    assert decided == goal
    # Gọi lần 2: hàng đợi đã lấy ra nên trả None
    assert strat_with_goal.decide(cs[0], w, []) is None


def test_llm_strategist_roi_ve_phan_xa() -> None:
    """N-01/B-05: chưa có câu trả lời nào của model thì vẫn phải ra được ý đồ.

    Đây là hình dạng cuối của cái stub cũ: đường may thứ nhất không còn chỗ nào
    `NotImplementedError`, và tầng phản xạ đỡ dưới đúng như bất biến 1 của B-05.
    """
    w, cs, _, _ = build_match(seed=1)
    llama = LlmStrategist("http://khong-ton-tai", [c.id for c in cs])
    g = llama.decide(cs[0], w, [], random.Random(0))
    assert g is not None


def test_tick_without_mode_branch() -> None:
    """B1: tick() không có nhánh theo chế độ và không isinstance Strategist."""
    src = Path("genesis/tick.py").read_text(encoding="utf-8")
    assert "isinstance(" not in src or "Strategist" not in src.split("isinstance(")[1][:60]
    assert 'mode ==' not in src
    assert "mode ==" not in src


def test_them_ca_the_giua_van() -> None:
    """W-11 bất biến 3: thêm sinh vật giữa ván thì vòng tick chạy tiếp bình thường.

    Đây là phần CÒN GIÁ TRỊ của ba bài kiểm `SpeciesRegistry` cũ. Bản thân
    `SpeciesRegistry` đã bị xoá (xem [N-02 §5]) vì nó là cấu trúc thứ hai cho
    một khái niệm mà `net.match.Registration` mới là bản chạy thật; nhưng bất
    biến nó dùng để minh hoạ thì không phụ thuộc vào nó, và bất biến ấy là thứ
    cả chế độ mở đứng lên trên — người lạ `/join` giữa ván là chuyện thường.
    """
    w, cs, st, rng = build_match(seed=3)
    for t in range(30):
        tick(w, cs, t, rng, st)

    tr = cs[0].traits
    new_ids = ["zz_new:0", "zz_new:1"]
    for cid in new_ids:
        cs.append(
            Creature(
                id=cid,
                species="zz_new",
                traits=tr,
                pos=(0, 0),
                hp=float(config.HP_MAX),
                energy=tr.energy_max,
            )
        )

    for t in range(30, 60):
        tick(w, cs, t, rng, st)

    assert any(c.id.startswith("zz_new:") for c in cs)


def test_tick_with_remote_strategist() -> None:
    """Vòng tick chạy với RemoteClientStrategist và giữ goal khi trả None."""
    w, cs, st, rng = build_match(seed=5)
    custom_goal = ActiveGoal(goal=Goal.REST, target=None, ttl=10)
    queue_dict = {cs[0].id: custom_goal}
    strat = RemoteClientStrategist(queue_dict)

    # Tick 0: nhận custom_goal
    tick(w, cs, 0, rng, st, strategist=strat)
    assert st.active_goals[cs[0].id].goal == Goal.REST

    # Tick 1: queue_dict đã rỗng -> strat trả None -> giữ goal cũ
    tick(w, cs, 1, rng, st, strategist=strat)
    assert st.active_goals[cs[0].id].goal == Goal.REST


def test_log_fields_and_event_kinds(tmp_path: Path) -> None:
    """N-03: Kiểm tra COMMON_FIELDS và các EVENT_KINDS bắt buộc."""
    for kind in ("LAW_FIRED", "TRAIT_SHIFT", "DRINK", "PHASE_CHANGE"):
        assert kind in EVENT_KINDS, f"{kind} thiếu trong EVENT_KINDS"

    log_path = tmp_path / "test_log.jsonl"
    with LogWriter(log_path, "match_test") as log:
        log.write(0, "RUN_START", seed=1)
        log.write(1, "DRINK", creature_id="L1:0", species_id="L1", pos=[1, 2])
        log.write(2, "PHASE_CHANGE", phase="DAWN")
        log.write(3, "TRAIT_SHIFT", creature_id="L1:0", frm="speed", to="sense", traits=[4, 3, 1, 1, 2, 1])
        log.write(4, "LAW_FIRED", creature_id="L1:0", law_id="L0", effect="test")

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        row = json.loads(line)
        for field in COMMON_FIELDS:
            assert field in row, f"Trường {field} thiếu trong dòng log: {row}"


def test_moi_ten_su_kien_duoc_GHI_deu_co_trong_EVENT_KINDS() -> None:
    """`LogWriter.write` NÉM với `kind` lạ — nên một tên chưa khai là ván gãy.

    Và nó gãy đúng ở chỗ khó thấy nhất: bộ test chạy với `log_dir=None`, nên
    `MatchRunner._write` không làm gì cả và mọi bài đều xanh. Lỗi chỉ nổ trên
    server thật, ở lượt đầu tiên có người gửi đúng loại quyết định ấy.

    Đã xảy ra thật: `SHIFT_OP` (N-16) được ghi ở `net/routes_decision.py` suốt
    một lượt sửa mà không có trong `EVENT_KINDS`, và 564 bài test không bài nào
    đỏ. Bài này quét nguồn thay vì chờ một ván thật đi qua nhánh đó.
    """
    root = Path(__file__).resolve().parent.parent
    pat = re.compile(r'_write\(\s*(?:tick_no\s*,\s*)?"([A-Z][A-Z0-9_]*)"')
    seen = 0
    for path in sorted(list((root / "genesis").glob("*.py"))
                       + list((root / "net").glob("*.py"))):
        for name in pat.findall(path.read_text(encoding="utf-8")):
            seen += 1
            assert name in EVENT_KINDS, (
                f"{path.name} ghi {name!r} mà EVENT_KINDS chưa có — "
                f"LogWriter sẽ NÉM ở ván thật")
    assert seen > 5, "regex không bắt được gì, bài kiểm này đang tự lừa mình"
