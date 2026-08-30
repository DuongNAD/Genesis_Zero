"""Kiểm thử WebSocket xem trực tiếp /v1/spectate và bảng xếp hạng (N-12).

Các bài kiểm bắt buộc:
1. Mở WS ở pha RUNNING, thu >= 50 khung: không rò rỉ luật/enum và LAW_FIRED có "law": "?".
2. Pha REVEAL: "law" trong LAW_FIRED KHÔNG còn là "?".
3. Khung có đủ các trường theo docs/05 §3.8.
4. GET /v1/leaderboard trả 200 và rows là list.
5. Quét web/watch.js: không có params_b hay model_name tham gia tính kích thước.
6. Quét web/watch.html + web/watch.js: không có http:// hay https://, không CDN.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from net import server, state
from net.match import MatchRunner, Phase

FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")


@pytest.fixture
def spectate_env(monkeypatch):
    r = MatchRunner(seed=1, ticks=200, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def test_1_spectate_running_no_law_leak(spectate_env):
    """1. Mở WS ở pha RUNNING, thu >= 50 khung: không rò rỉ luật và LAW_FIRED có law='?'."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    with c.websocket_connect("/v1/spectate") as ws:
        frames = []
        for _ in range(50):
            frame = ws.receive_json()
            frames.append(frame)

        assert len(frames) >= 50
        law_fired_count = 0

        for frame in frames:
            text = json.dumps(frame)
            m = FORBIDDEN_RUNNING_PATTERN.search(text)
            assert not m, f"Khung rò rỉ token cấm {m.group(0)!r}: {text}"

            for ev in frame.get("events", []):
                if ev.get("k") == "LAW_FIRED":
                    law_fired_count += 1
                    assert ev.get("law") == "?", f"LAW_FIRED phải có law='?', nhận {ev.get('law')!r}"

        assert law_fired_count > 0, "Phải có ít nhất 1 sự kiện LAW_FIRED trong 50 khung để khẳng định test có ý nghĩa"


def test_2_spectate_reveal_has_full_laws(monkeypatch):
    """2. Ở pha REVEAL thì law KHÔNG còn là '?' (điền luật đầy đủ từ laws_public())."""
    r = MatchRunner(seed=1, ticks=50, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)

    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(50):
        r.step()

    while r.phase is not Phase.REVEAL:
        r.advance_phase()

    with TestClient(server.app) as c, c.websocket_connect("/v1/spectate") as ws:
        law_fired_count = 0
        for _ in range(50):
            frame = ws.receive_json()
            for ev in frame.get("events", []):
                if ev.get("k") == "LAW_FIRED":
                    law_fired_count += 1
                    assert ev.get("law") != "?", "Ở pha REVEAL, law không được là '?'"
                    assert isinstance(ev.get("law"), str) and len(ev.get("law")) > 0

        assert law_fired_count > 0, "Phải có sự kiện LAW_FIRED ở pha REVEAL để kiểm tra"


def test_3_spectate_frame_schema(spectate_env):
    """3. Khung có đủ các trường mà 05 §3.8 quy định."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    with c.websocket_connect("/v1/spectate") as ws:
        frame = ws.receive_json()
        for key in ("t", "phase", "creatures", "plants", "corpses", "terrain_delta", "events"):
            assert key in frame, f"Thiếu trường {key} trong khung spectate"

        assert isinstance(frame["t"], int)
        assert frame["phase"] == "RUNNING"
        assert isinstance(frame["creatures"], list)
        assert isinstance(frame["plants"], list)
        assert isinstance(frame["corpses"], list)
        assert isinstance(frame["terrain_delta"], list)
        assert isinstance(frame["events"], list)

        if frame["creatures"]:
            cr = frame["creatures"][0]
            for ck in ("id", "x", "y", "hp", "e", "alive", "feral"):
                assert ck in cr, f"Thiếu trường creature.{ck}"


def test_4_leaderboard_endpoint(spectate_env):
    """4. GET /v1/leaderboard trả 200 và rows là list."""
    c, _ = spectate_env
    resp = c.get("/v1/leaderboard?season=2026s3")
    assert resp.status_code == 200
    data = resp.json()
    assert "season" in data and data["season"] == "2026s3"
    assert "rows" in data and isinstance(data["rows"], list)


def test_5_watch_js_no_model_size_dependence():
    """5. Quét web/watch.js: không có params_b hay model_name tham gia tính kích thước."""
    js_text = Path("web/watch.js").read_text(encoding="utf-8")
    for line in js_text.splitlines():
        line_lower = line.lower()
        if any(k in line_lower for k in ("size", "radius", "scale", "bodyw", "bodyh", "headr", "eyer")):
            assert "params_b" not in line, f"Dòng tính kích thước có chứa params_b: {line}"
            assert "model_name" not in line, f"Dòng tính kích thước có chứa model_name: {line}"

    assert "params_b" not in js_text
    assert "model_name" not in js_text


def test_6_no_cdn_or_external_urls():
    """6. Quét web/watch.html + web/watch.js: không có http:// hay https://, không CDN."""
    html_text = Path("web/watch.html").read_text(encoding="utf-8")
    js_text = Path("web/watch.js").read_text(encoding="utf-8")

    for file_name, text in (("web/watch.html", html_text), ("web/watch.js", js_text)):
        assert "http://" not in text, f"{file_name} chứa http://"
        assert "https://" not in text, f"{file_name} chứa https://"
        assert re.search(r"<script[^>]+src=[\"']//", text) is None, f"{file_name} chứa script trỏ //"


def test_7_xem_khong_cham_vao_sim(monkeypatch):
    """Trình bày KHÔNG được chạm vào mô phỏng.

    Bản đầu vá đè `runner.step` và `runner.advance_phase` bằng closure ngay
    trong handler WebSocket, và bọc luôn `runner.log`. Hậu quả: hành vi của sim
    phụ thuộc vào việc **có ai đang xem hay không** — thứ hỏng mà không ai để ý
    cho tới lúc một ván có người xem cho kết quả khác một ván không có.
    """
    import ast

    src = Path("net/routes_spectate.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute) and tgt.attr in (
                    "step", "advance_phase", "log", "world", "creatures", "_laws"
                ):
                    raise AssertionError(f"routes_spectate gán đè runner.{tgt.attr}")
    assert "_laws" not in src

    # và kiểm bằng hành vi: ván chạy giống hệt dù có hay không có người xem
    def run(watch: bool) -> list:
        r = MatchRunner(seed=7, ticks=30, tick_ms=1, log_dir=None)
        monkeypatch.setattr(state, "runner", r)
        while r.phase is not Phase.RUNNING:
            r.advance_phase()
        if watch:
            # `stopped=True` để `runner.loop()` của lifespan thoát ngay: nếu không
            # thì nó chạy tick song song với vòng `r.step()` bên dưới và ta đo
            # nhầm hai độ dài ván khác nhau chứ không đo ảnh hưởng của người xem.
            r.stopped = True
            with TestClient(server.app) as c, c.websocket_connect("/v1/spectate"):
                for _ in range(30):
                    r.step()
        else:
            for _ in range(30):
                r.step()
        return [(x.id, x.pos, round(x.hp, 4), round(x.energy, 4)) for x in r.creatures]

    assert run(watch=True) == run(watch=False)


def test_8_do_thi_nghe_den_tu_server(spectate_env):
    """Ai nghe được ai phụ thuộc `sense` của NGƯỜI NGHE và vị trí lúc đó — chỉ
    server biết. Bản đầu gửi trường rỗng rồi để JS tự tính từ bảng trait chép
    cứng, nên nó sai ngay lần dịch trait đầu tiên."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    ev = {"kind": "SPEAK", "creature_id": "L1:0", "signal": "ALARM",
          "hear_full": ["L1:1"], "hear_signal": ["L2:0", "L3:0"]}
    out = r.frame(0, [ev])["events"][0]
    assert out["k"] == "SPEAK" and out["sig"] == "ALARM"
    assert out["hear"] == ["L1:1", "L2:0", "L3:0"]


def test_9_khung_mang_trait_hien_tai(spectate_env):
    """Hình suy từ trait (bất biến 4) — mà trait DỊCH giữa ván."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    cr = r.creatures[0]
    f = r.frame(0, [])
    row = next(x for x in f["creatures"] if x["id"] == cr.id)
    assert row["tr"] == list(__import__("dataclasses").astuple(cr.traits))
    assert row["e_max"] == round(cr.traits.energy_max, 1)
    assert f["w"] == r.world.w and f["h"] == r.world.h


def test_10_js_khong_chep_cung_bang_trait():
    """Một bản sao của bảng trait trong JS là một bản sao sẽ lệch."""
    js = Path("web/watch.js").read_text(encoding="utf-8")
    assert "FOUNDERS" not in js
    assert "GRID_SIZE" not in js, "cỡ lưới phải đến từ khung"
    for vec in ("[4, 3, 1, 2, 1, 1]", "[0, 2, 0, 5, 3, 2]"):
        assert vec not in js


def test_11_khung_mang_dia_hinh_va_ten_ban_do(spectate_env):
    """Trang 3D dựng địa hình TỪ KHUNG. Chép cứng trong JS là bảng sẽ lệch ngay
    khi có bản đồ mới — mà giờ đã có năm cái (W-15)."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    f0 = r.frame(0, [])
    assert f0["map"] == r.world.map_name
    rows = f0["terrain"]
    assert len(rows) == r.world.h and all(len(x) == r.world.w for x in rows)
    # D = nước sâu, T = cây (W-18). Mã lấy từ `world.TERRAIN_CODE`, một bảng.
    assert set("".join(rows)) <= set("PWBRFDTC")
    # Địa hình chỉ đi kèm tick 0: 24×24 mỗi tick sẽ chiếm gần hết băng thông.
    assert r.frame(5, [])["terrain"] is None


def test_12_nguoi_xem_vao_giua_van_van_co_dia_hinh(spectate_env):
    """Khung tick 0 có thể đã trôi khỏi backlog — không nhét bù thì trang 3D
    hiện ra một khoảng trống và không có gì báo lỗi."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    for _ in range(6):
        r.step()
    r.frames = r.frames[3:]          # giả lập backlog đã trôi mất tick đầu
    r._frame_raw = r._frame_raw[3:]
    with c.websocket_connect("/v1/spectate") as ws:
        assert ws.receive_json().get("terrain"), "người xem vào muộn không nhận được địa hình"


def test_13_trang_3D_khong_chep_cung_bang_gi():
    """Cùng luật với trang 2D: mọi thứ đến từ khung, không từ một bảng trong JS."""
    from pathlib import Path

    js = Path("web/watch3d.js").read_text(encoding="utf-8")
    assert "FOUNDERS" not in js
    for vec in ("[4, 3, 1, 2, 1, 1]", "[0, 2, 0, 5, 3, 2]"):
        assert vec not in js
    for banned in ("params_b", "model_name"):
        assert banned not in js, f"kích thước KHÔNG được phụ thuộc {banned}"
    # không CDN
    assert "http://" not in js and "https://" not in js
    html = Path("web/watch3d.html").read_text(encoding="utf-8")
    assert "http://" not in html and "https://" not in html
    assert 'src="vendor/three.min.js"' in html, "three.js phải nằm trong repo"
    assert Path("web/vendor/three.min.js").exists()
