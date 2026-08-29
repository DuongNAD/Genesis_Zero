"""Kiểm thử ba danh hiệu (W-14)."""

from __future__ import annotations

from genesis import law_config
from genesis.victory import TITLES, decide


def _row(cid, sp, idx, match, found, t_disc, survive):
    return {"creature_id": cid, "species_id": sp, "law_idx": idx,
            "match": match, "found": found, "t_discover": t_disc,
            "R_survive": survive, "R_i": match}


ROWS = [
    _row("L1:0", "L1", 0, 1.0, True, 40, 0.5),
    _row("L1:0", "L1", 1, 0.0, False, 401, 0.5),
    _row("L5:0", "L5", 0, 0.9, True, 120, 0.95),
    _row("L5:0", "L5", 1, 0.0, False, 401, 0.95),
    _row("L4:0", "L4", 0, 0.0, False, 401, 1.0),
    _row("L4:0", "L4", 1, 0.0, False, 401, 1.0),
]
TOTALS = {"L1:0": 1.05, "L5:0": 0.99, "L4:0": 0.10}


def test_ba_bang_rieng_khong_cong_lai():
    """Một trọng số duy nhất giữa "hiểu" và "sống" là một tuyên bố ta CHƯA biết
    đúng — đó chính là câu hỏi Q7 mà X-02 sinh ra để trả lời."""
    v = decide(ROWS, TOTALS, match_id="m", seed=9)
    assert set(v.boards) == set(TITLES)
    assert v.winner("NHA_KHOA_HOC").creature_id == "L1:0"
    assert v.winner("KE_SONG_SOT").creature_id == "L4:0"     # sống dai nhất
    assert v.winner("NGUOI_DAU_TIEN").creature_id == "L1:0"  # tìm ra sớm nhất
    # và ba bảng KHÁC nhau — nếu chúng luôn trùng thì tách ra vô nghĩa
    assert v.winner("NHA_KHOA_HOC").creature_id != v.winner("KE_SONG_SOT").creature_id


def test_nguoi_dau_tien_chi_tinh_ca_THAT_SU_tim_ra():
    """Cột `t_discover` toàn `T+1` sắp tăng dần sẽ đẻ ra một "người thắng" chưa
    hề tìm ra gì — bảng có số mà không có nghĩa."""
    rows = [_row("A:0", "A", 0, 0.0, False, 401, 1.0),
            _row("B:0", "B", 0, 0.0, False, 401, 0.5)]
    v = decide(rows, {"A:0": 0.1, "B:0": 0.05})
    assert v.boards["NGUOI_DAU_TIEN"] == []
    assert v.winner("NGUOI_DAU_TIEN") is None


def test_canh_bao_khi_khong_ai_tim_ra():
    rows = [_row("A:0", "A", 0, 0.0, False, 401, 1.0)]
    out = decide(rows, {"A:0": 0.1}).render()
    assert "KHÔNG AI tìm ra luật nào" in out
    assert "đừng" in out

    ok = decide(ROWS, TOTALS).render()
    assert "KHÔNG AI tìm ra" not in ok


def test_thu_hang_on_dinh_khi_bang_diem():
    """Hoà thì sắp theo id — hai lần chạy phải cho cùng một bảng."""
    rows = [_row("B:0", "B", 0, 0.0, False, 401, 0.5),
            _row("A:0", "A", 0, 0.0, False, 401, 0.5)]
    v = decide(rows, {"A:0": 0.5, "B:0": 0.5})
    assert [s.creature_id for s in v.boards["KE_SONG_SOT"]] == ["A:0", "B:0"]


def test_khong_import_vong_chay():
    """Cùng ranh giới với `score.py`: bộ chấm không được chạm vào sim."""
    import ast
    from pathlib import Path

    tree = ast.parse(Path("genesis/victory.py").read_text(encoding="utf-8"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
        elif isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
    for banned in ("genesis.world", "genesis.tick", "genesis.creature",
                   "genesis.strategist"):
        assert banned not in mods


def test_json_du_dung_cho_endpoint():
    d = decide(ROWS, TOTALS, match_id="m_1", seed=9).to_json()
    assert d["match_id"] == "m_1" and d["seed"] == 9
    for t in TITLES:
        for row in d["boards"][t]:
            assert set(row) == {"rank", "creature_id", "species_id", "value", "detail"}
    assert d["boards"]["NHA_KHOA_HOC"][0]["rank"] == 1
