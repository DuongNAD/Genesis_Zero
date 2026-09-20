"""Kiểm thử visualizer đồ hoạ Pygame (X-07)."""

from __future__ import annotations

import ast
from pathlib import Path

# KHÔNG `importorskip` ở mức module. Đặt nó ở đây thì **cả file** bị bỏ qua khi
# máy không có pygame — kể cả những bài không hề cần nó, và chúng là phần lớn.
# Hậu quả thật: bài kiểm màu không bao giờ chạy, và một lỗi gõ trả `(r, g, g)`
# khiến mọi loài hue xanh lam hiện ra xám như nhau đã lọt qua.
#
# `scripts/x07_pygame.py` cố tình import pygame BÊN TRONG hàm, nên mọi thứ dưới
# đây — quét mã, tính màu, suy hình từ trait — chạy được mà không cần pygame.


def _get_x07_path() -> Path:
    return Path(__file__).resolve().parent.parent / "scripts" / "x07_pygame.py"


def test_khong_phu_thuoc_co_model_va_khong_chua_params_b():
    """Yêu cầu 2: quét file bằng AST/đọc mã nguồn.

    KHÔNG có "params_b"/"model_name" ở bất kỳ dòng nào tính kích thước
    (dòng chứa size, radius, scale, w=, h=, body_w, body_h, head_r, ...).
    """
    path = _get_x07_path()
    assert path.exists(), f"Không tìm thấy {path}"

    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    # Toàn bộ file không chứa params_b hoặc model_name
    assert "params_b" not in text, "CẤM KỴ: file scripts/x07_pygame.py không được chứa 'params_b'"
    assert "model_name" not in text, "CẤM KỴ: file scripts/x07_pygame.py không được chứa 'model_name'"

    # Kiểm tra cụ thể từng dòng chứa từ khoá kích thước
    size_keywords = ("size", "radius", "scale", "w=", "h=", "body_w", "body_h", "head_r", "eye_r", "fang_len")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if any(kw in line.lower() for kw in size_keywords):
            assert "params_b" not in line, f"Dòng {lineno} tính kích thước chứa 'params_b': {line}"
            assert "model_name" not in line, f"Dòng {lineno} tính kích thước chứa 'model_name': {line}"


def test_ve_sinh_vat_nhan_trait_tu_creature_khong_chep_cung():
    """Yêu cầu 3: hàm vẽ sinh vật nhận trait từ đối tượng creature, không tra bảng chép cứng.

    Khẳng định file KHÔNG chứa vector founder [4, 3, 1, 2, 1, 1] hay từ khoá FOUNDERS.
    """
    path = _get_x07_path()
    text = path.read_text(encoding="utf-8")

    assert "[4, 3, 1, 2, 1, 1]" not in text, "Không được chép cứng vector trait [4, 3, 1, 2, 1, 1]"
    assert "FOUNDERS" not in text, "Không được tra bảng cố định FOUNDERS"


def test_import_duoc_module_ma_khong_mo_cua_so():
    """Import được module mà KHÔNG cần pygame và không mở cửa sổ.

    Đây chính là bài kiểm cho quy ước "pygame nằm trong hàm": nếu ai đó đưa
    `import pygame` lên đầu file, bài này đỏ trên mọi máy không có pygame.
    """
    import importlib.util

    path = _get_x07_path()
    spec = importlib.util.spec_from_file_location("x07_pygame", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Thực hiện import module - không được nổ lỗi và không được mở display
    spec.loader.exec_module(mod)

    # Kiểm tra các hàm chức năng tồn tại
    assert hasattr(mod, "get_creature_visuals")
    assert hasattr(mod, "draw_creature")
    assert hasattr(mod, "run_gui")
    assert hasattr(mod, "main")


def test_mau_hsl_dung_ca_ba_kenh():
    """Bất biến "hue = hash(species_id)" tồn tại để phân biệt loài BẰNG MẮT.

    Bản đầu trả `(r, g, g)` — kênh lam lấy nhầm giá trị lục — nên mọi loài có
    hue ở nửa xanh lam hiện ra thành một đám xám như nhau. Không bài kiểm tĩnh
    nào bắt được; phải gọi hàm và nhìn số.
    """
    import sys

    sys.path.insert(0, str(_get_x07_path().parent))
    from scripts.x07_pygame import hash_species_hue, hsl_to_rgb

    assert hsl_to_rgb(0, 70, 50)[0] > 150, "hue 0 phải ĐỎ"
    assert hsl_to_rgb(120, 70, 50)[1] > 150, "hue 120 phải LỤC"
    assert hsl_to_rgb(240, 70, 50)[2] > 150, "hue 240 phải LAM"
    for h in (0, 60, 120, 180, 240, 300):
        r, g, b = hsl_to_rgb(h, 70, 50)
        assert len({r, g, b}) > 1, f"hue {h} ra màu xám: {(r, g, b)}"

    # và năm loài mặc định phải ra năm màu phân biệt được
    from genesis import config

    hues = [hash_species_hue(sp) for sp in config.POPULATION]
    rgbs = [hsl_to_rgb(h, 70, 50) for h in hues]
    assert len(set(rgbs)) == len(rgbs), f"hai loài cùng màu: {rgbs}"


def test_kich_thuoc_suy_tu_trait_hien_tai():
    """Hình suy từ trait — mà trait DỊCH giữa ván."""
    import sys

    sys.path.insert(0, str(_get_x07_path().parent))
    import dataclasses

    from genesis.tick import build_match
    from scripts.x07_pygame import get_creature_visuals

    _, creatures, _, _ = build_match(seed=9)
    c = creatures[0]
    before = get_creature_visuals(c, 30.0)
    c.traits = dataclasses.replace(
        c.traits, stomach=c.traits.stomach + 1, speed=c.traits.speed - 1
    )
    after = get_creature_visuals(c, 30.0)
    assert after["body_w"] != before["body_w"], "dịch trait mà hình không đổi"
