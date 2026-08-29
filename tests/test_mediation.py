"""X-02 điều kiện (2): `t_discover` có phải trung gian không (kiểm phép hồi quy)."""

from __future__ import annotations

import numpy as np

from scripts.x02_mediation import mediation, ols

SPECIES_BRAIN = {"L1": 4, "L2": 3, "L3": 3, "L4": 1, "L5": 0}


def _rows(spec):
    """spec: [(creature_id, species, survival, t_discover|None)] -> dòng CSV."""
    out = []
    for cid, sp, surv, t in spec:
        out.append({"creature_id": cid, "species_id": sp, "R_survive": surv,
                    "found": "True" if t is not None else "False",
                    "t_discover": t if t is not None else 401, "match": 1.0 if t else 0.0})
    return out


def test_ols_khop_ca_da_biet():
    X = np.column_stack([np.ones(5), np.arange(5.0)])
    y = 2.0 + 3.0 * np.arange(5.0)
    b, _ = ols(X, y)
    assert abs(b[0] - 2.0) < 1e-9 and abs(b[1] - 3.0) < 1e-9


def test_gop_ve_MOT_dong_moi_ca_the():
    """Sinh tồn là của cá thể, không của từng luật. Đếm lặp thổi phồng cỡ mẫu và
    mọi sai số chuẩn thành sai."""
    rows = _rows([("L1:0", "L1", 0.9, 40)]) * 3      # ba luật, một cá thể
    assert mediation(rows)["n"] == 1


def test_it_ca_kham_pha_thi_noi_CHUA_DO_DUOC():
    """Trung gian không đo được khi gần như không ai khám phá — và câu trả lời
    lúc ấy KHÔNG phải là lấy thêm mẫu của cùng một model."""
    res = mediation(_rows([(f"L{i%5+1}:0", f"L{i%5+1}", 0.5, None) for i in range(15)]))
    assert res["n_found"] == 0
    assert "CHƯA ĐO ĐƯỢC" in res["verdict"]
    assert "KHÔNG phải một mẫu lớn hơn" in res["verdict"]
    assert "beta_brain_with_t" not in res


def test_bat_duoc_trung_gian_khi_no_CO_that():
    """Dựng dữ liệu mà sinh tồn PHỤ THUỘC t_discover, còn brain chỉ tác động
    QUA nó — hệ số brain phải tụt mạnh khi thêm t_discover."""
    spec = []
    for i in range(24):
        sp = ["L1", "L2", "L4", "L5"][i % 4]
        brain = SPECIES_BRAIN[sp]
        t = 200 - brain * 30 + (i % 3) * 5          # não to -> tìm ra sớm
        surv = 1.0 - t / 400 + (i % 5) * 0.004      # sống lâu <- tìm ra sớm
        spec.append((f"{sp}:{i}", sp, round(surv, 4), t))
    res = mediation(_rows(spec))
    assert res["n_found"] == 24
    assert res["shrink_pct"] > 40, res
    assert "TRUNG GIAN" in res["verdict"] and "KHÔNG TRUNG GIAN" not in res["verdict"]


def test_bat_duoc_khi_KHONG_trung_gian():
    """Sinh tồn phụ thuộc brain TRỰC TIẾP, `t_discover` chỉ là nhiễu — hệ số
    brain phải giữ nguyên, và kết luận phải là "đừng đổi model"."""
    spec = []
    for i in range(24):
        sp = ["L1", "L2", "L4", "L5"][i % 4]
        brain = SPECIES_BRAIN[sp]
        spec.append((f"{sp}:{i}", sp, round(0.4 + brain * 0.1, 4), 100 + (i * 37) % 150))
    res = mediation(_rows(spec))
    assert res["shrink_pct"] < 40, res
    assert "KHÔNG TRUNG GIAN" in res["verdict"]
    assert "ĐỪNG đổi model" in res["verdict"]


def test_khong_bia_t_discover_cho_ca_chua_tim_ra():
    """`T+1` là quy ước để cột không trống, KHÔNG phải một số đo. Đưa nó vào hồi
    quy là bịa một con số cho một thứ chưa xảy ra."""
    found = [(f"L1:{i}", "L1", 0.9 - i * 0.01, 40 + i) for i in range(10)]
    res_a = mediation(_rows(found))
    res_b = mediation(_rows(found + [(f"L5:{i}", "L5", 0.2, None) for i in range(10)]))
    # Thêm 10 ca KHÔNG tìm ra không được đổi hệ số của t_discover
    assert res_a["beta_t_discover"] == res_b["beta_t_discover"]
    assert res_b["n"] == 20 and res_b["n_found"] == 10
