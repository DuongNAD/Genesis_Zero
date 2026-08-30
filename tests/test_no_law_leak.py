"""★ Ca rò rỉ: luật thật không được rời server trước REVEAL (N-04 bất biến 5).

Đây là bất biến duy nhất trong track N mà một lỗi **không gây triệu chứng nào**:
ván vẫn chạy, client vẫn nhận việc, không ai báo gì, và cả thí nghiệm âm thầm vô
nghĩa vì agent đã được mớm đáp án. Nên nó phải được canh bằng test, không bằng
kỷ luật — và test phải quét **mọi phản hồi có mang prompt**, không chỉ những
phản hồi ta nhớ ra.

**Quét cái gì, và vì sao không quét nhiều hơn.** Bản đầu của file này cấm mọi tên
enum DSL ở mọi phản hồi. Nó bắt 35 "lỗi" trên `/match/brief` — tất cả đều là
**khối D**, tức là từ vựng agent BẮT BUỘC phải thấy để phát biểu được luật, cộng
với `json_schema` mà `/work` phải gửi kèm (05 §3.3 bất biến 2). Một bài test kêu
ở chỗ thiết kế cố tình đặt ở đó là bài test sẽ bị tắt đi. Ranh giới đúng:

* `law_id`, `FRUIT_[A-D]`, `match_seed` — cấm ở **mọi nơi**, mọi pha;
* nguyên văn `to_vietnamese(luật thật)` — cấm cho tới REVEAL;
* tên enum DSL trong **khối kể chuyện** — việc của `genesis.prompt._check_no_leak`,
  nó ném ngay lúc dựng nên tới đây không cần kiểm lại.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from genesis.lawdsl import to_vietnamese
from net import server, state
from net.match import MatchRunner, Phase

ALWAYS_FORBIDDEN = re.compile(r"law_id|FRUIT_[A-D]|match_seed")


@pytest.fixture
def env(monkeypatch):
    # Một chỗ duy nhất để thay: đó là điểm của net/state.py.
    r = MatchRunner(seed=1, ticks=50, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def _join(c) -> dict:
    resp = c.post("/v1/join", json={
        "display_name": "Kiến Lửa", "persona": "Sống theo đàn",
        "model_name": "fake-999B", "params_b": 999, "brain_tier": 5,
        "league": "LEAGUE_LLM", "pop_request": 2,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _all_responses(c, r, headers) -> dict[str, str]:
    out = {p: c.get(p).text for p in ("/v1/state", "/v1/match/result")}
    for p in ("/v1/match/brief", "/v1/work?hold_ms=50"):
        resp = c.get(p, headers=headers)
        out[p] = resp.text if resp.status_code == 200 else ""
    return out


def test_khong_ro_dinh_danh_noi_bo_o_moi_pha(env):
    c, r = env
    headers = {"Authorization": f"Bearer {_join(c)['token']}"}
    # REVEAL không nằm trong danh sách: từ đó trở đi `law_id` là ĐÚNG — nó là
    # định dạng công bố ở 05 §3.6. Bài `test_reveal_moi_cong_bo` kiểm chiều ngược lại.
    for target in (Phase.LOBBY, Phase.SEEDING, Phase.RUNNING):
        while r.phase is not target:
            r.advance_phase()
        for path, body in _all_responses(c, r, headers).items():
            m = ALWAYS_FORBIDDEN.search(body)
            assert not m, f"{target} {path} rò {m.group(0)!r}"


def test_khong_ro_noi_dung_luat_truoc_reveal(env):
    """Bài sắc nhất: nguyên văn luật thật, dịch sang tiếng Việt, ở mọi phản hồi."""
    c, r = env
    headers = {"Authorization": f"Bearer {_join(c)['token']}"}
    for target in (Phase.SEEDING, Phase.RUNNING):
        while r.phase is not target:
            r.advance_phase()
        assert r._laws, "ván phải CÓ luật thì bài này mới có nghĩa"
        vi = [to_vietnamese(l, r.world.surface_map) for l in r._laws]
        for path, body in _all_responses(c, r, headers).items():
            for text in vi:
                assert text not in body, f"{target} {path} rò nguyên văn luật"
            assert '"laws":[]' in body or "laws" not in body or path == "/v1/state", (
                f"{target} {path} có trường laws không rỗng"
            )


def test_reveal_moi_cong_bo(env):
    c, r = env
    while r.phase is not Phase.REVEAL:
        r.advance_phase()
    laws = c.get("/v1/match/result").json()["laws"]
    assert laws and all("vi" in l and "law_id" in l and "tier" in l for l in laws)
    # và tới đây thì nguyên văn PHẢI có mặt — nếu không thì REVEAL cũng hỏng
    body = c.get("/v1/match/result").text
    assert to_vietnamese(r._laws[0], r.world.surface_map) in body


def test_chi_mot_duong_ra(env):
    """`laws_public` phải là chỗ DUY NHẤT đọc `_laws` để gửi đi.

    Hai chỗ cùng quyết định một bất biến là hai chỗ sẽ lệch nhau.
    """
    import ast
    from pathlib import Path

    for f in ("net/server.py", "net/routes_join.py", "net/routes_work.py",
              "net/routes_decision.py"):
        assert "_laws" not in Path(f).read_text(encoding="utf-8"), (
            f"{f} đọc thẳng _laws thay vì qua laws_public()"
        )

    tree = ast.parse(Path("net/match.py").read_text(encoding="utf-8"))
    readers = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(n, ast.Attribute) and n.attr == "_laws" for n in ast.walk(node))
    }
    assert readers <= {"laws_public", "_seed_match", "step", "__init__", "_close_log"}, readers


def test_prompt_tu_chan_ro_ri_o_goc(env):
    """Tầng dưới đã ném khi rò, nên endpoint không phải kiểm lại — chứng minh điều đó."""
    from genesis.prompt import PromptLeak, system_block
    from genesis.surface import SurfaceMap

    c, r = env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    with pytest.raises(PromptLeak):
        system_block(r.creatures[0], "", SurfaceMap(cls_to_surface={"FRUIT_A": "FRUIT_A"}))
