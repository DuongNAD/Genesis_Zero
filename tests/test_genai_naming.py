"""Genesis Zero — tests/test_genai_naming.py: kiểm thử ma trận 27 Archetypes sinh thái và đặt tên sinh học."""

import pytest
from genesis.genai import ECOLOGICAL_ARCHETYPES_27, generate_ecological_name


def test_27_archetypes_matrix_completeness():
    """Ma trận 27 Archetypes phải phủ kín 3x3x3 tổ hợp (Domain x Diet x Strategy)."""
    assert len(ECOLOGICAL_ARCHETYPES_27) == 27

    domains = {"CAN", "NUOC", "TROI"}
    diets = {"HERBIVORE", "CARNIVORE", "OMNIVORE"}
    strategies = {"STRAT_R", "STRAT_K", "STRAT_SOCIAL"}

    count = 0
    for dom in domains:
        for dt in diets:
            for strat in strategies:
                key = (dom, dt, strat)
                assert key in ECOLOGICAL_ARCHETYPES_27, f"Thiếu tổ hợp {key}"
                item = ECOLOGICAL_ARCHETYPES_27[key]
                assert item["name"], f"Thiếu tên tiếng Việt cho {key}"
                assert item["scientific_name"], f"Thiếu tên khoa học cho {key}"
                assert len(item["scientific_name"].split()) >= 2
                assert item["niche_summary"], f"Thiếu tóm tắt sinh cảnh cho {key}"
                assert item["behavior_lore"], f"Thiếu tập tính cho {key}"
                tr = item["recommended_traits"]
                assert len(tr) == 6, f"Vector trait phải đủ 6 chỉ số: {tr}"
                assert sum(tr) == 12, f"Tổng quỹ điểm phải bằng 12: {tr}"
                assert all(0 <= x <= 5 for x in tr), f"Trait nằm ngoài khoảng [0, 5]: {tr}"
                count += 1
    assert count == 27


def test_generate_ecological_name_procedural_fallback(monkeypatch):
    """Khi không có API key nào trong router, hàm tự động trả về dữ liệu chuẩn từ ma trận 27 archetypes."""
    from genesis.genai import KEY_ROUTER
    monkeypatch.setattr(KEY_ROUTER, "get_rotated_keys", lambda custom_key=None: [])

    res = generate_ecological_name("CAN", "HERBIVORE", "STRAT_R")
    assert res["name"] == "Thỏ Đồng Cỏ"
    assert res["scientific_name"] == "Sylvilagus Campestris"
    assert res["source"] == "procedural"
    assert res["domain"] == "CAN"
    assert res["diet"] == "HERBIVORE"
    assert res["strategy"] == "STRAT_R"
    assert sum(res["recommended_traits"]) == 12

    res_nuoc = generate_ecological_name("NUOC", "CARNIVORE", "STRAT_K")
    assert res_nuoc["name"] == "Hải Quái Nanh Nhọn"
    assert res_nuoc["scientific_name"] == "Leviathan Monodon"
    assert res_nuoc["source"] == "procedural"

    res_troi = generate_ecological_name("TROI", "CARNIVORE", "STRAT_K")
    assert res_troi["name"] == "Kim Ưng Đỉnh Núi"
    assert res_troi["scientific_name"] == "Aquila Excelsa"
    assert res_troi["source"] == "procedural"


def test_generate_ecological_name_invalid_inputs():
    """Đầu vào không hợp lệ tự động chuẩn hoá an toàn mà không quăng exception."""
    res = generate_ecological_name("INVALID_DOM", "UNKNOWN_DIET", "STRAT_XYZ")
    assert res["name"] is not None
    assert res["scientific_name"] is not None
    assert res["domain"] == "CAN"
    assert res["diet"] == "HERBIVORE"
    assert res["strategy"] == "STRAT_R"
    assert sum(res["recommended_traits"]) == 12
