"""Genesis Zero — tests cho mesh_prompts (N-13 mở rộng)."""

from __future__ import annotations

import itertools

import pytest

from genesis import config, law_config
from genesis.maps import MAPS
from genesis.mesh_prompts import (
    all_static_prompts,
    creature_prompt,
    creature_visual,
    fruit_prompt,
    map_prompt,
    meshy_payload,
    terrain_prompt,
)
from genesis.traits import Traits, founder_traits
from genesis.world import Terrain


def _all_trait_vectors():
    names = ("brain", "attack", "armor", "speed", "sense", "stomach")
    for combo in itertools.product(range(config.TRAIT_MIN, config.TRAIT_MAX + 1),
                                   repeat=len(names)):
        if sum(combo) == config.TRAIT_SUM:
            yield Traits(**dict(zip(names, combo)))


def test_hinh_la_ham_thuan_cua_trait():
    """Bất biến 1 của N-13: cùng vector trait -> cùng một câu, không đổi.

    Nếu prompt lấy thêm bất cứ thứ gì ngoài sáu con số (giờ, ngẫu nhiên, tên
    loài) thì hình và số rời nhau, và đó đúng là thứ N-13 sinh ra để chặn.
    """
    for tr in itertools.islice(_all_trait_vectors(), 60):
        assert creature_prompt(tr) == creature_prompt(tr)
    a = Traits(brain=5, attack=3, armor=2, speed=1, sense=1, stomach=0)
    b = Traits(brain=5, attack=3, armor=2, speed=1, sense=1, stomach=0)
    assert creature_prompt(a) == creature_prompt(b)


def test_moi_trait_deu_doi_duoc_hinh():
    """Mỗi trong sáu trait phải TỰ MÌNH đổi được câu mô tả.

    Bảng tra thiếu một mục thì trait ấy thành trang trí: người chơi đổi
    `armor` mà con vật trông y hệt.

    Tổng sáu trait luôn bằng `config.TRAIT_SUM`, nên không dựng được vector chỉ
    đổi một ô — phải bù vào một ô khác. Ta bù vào `stomach` và kiểm `stomach`
    bằng cách bù ngược lại, để không trait nào được kiểm bằng chính nó.
    """
    names = ("brain", "attack", "armor", "speed", "sense", "stomach")
    for name in names:
        pad = "brain" if name == "stomach" else "stomach"
        low = {n: 2 for n in names}
        low[name], low[pad] = 0, 2 + 2          # bù đúng 2 điểm vừa lấy đi
        high = {n: 2 for n in names}
        high[name], high[pad] = 4, 2 - 2
        assert sum(low.values()) == sum(high.values()) == config.TRAIT_SUM
        assert creature_visual(Traits(**low)) != creature_visual(Traits(**high)), (
            f"{name} không đổi hình"
        )


def test_moi_gia_tri_0_den_5_deu_co_mo_ta():
    """Không giá trị trait nào rơi vào chuỗi rỗng hay trùng chuỗi của giá trị khác.

    Kiểm thẳng trên bảng tra: `Traits` bắt tổng phải bằng 12 nên không dựng
    được vector quét một trait qua cả sáu giá trị.
    """
    from genesis.mesh_prompts import _TABLES

    for name, table in _TABLES:
        assert len(table) == config.TRAIT_MAX - config.TRAIT_MIN + 1, (
            f"bảng {name} không phủ hết [{config.TRAIT_MIN}, {config.TRAIT_MAX}]"
        )
        assert all(s.strip() for s in table), f"bảng {name} có mục rỗng"
        assert len(set(table)) == len(table), f"bảng {name} có mục trùng"


def test_khong_lo_dinh_danh_noi_bo():
    """Mesh gửi ra dịch vụ NGOÀI. Không lớp quả, không tên enum DSL.

    Sinh mesh theo LỚP thì hình quả đổi màu giữa hai ván, và người xem đọc
    được luật ẩn qua… hình 3D.
    """
    texts = [r["prompt"] for r in all_static_prompts()]
    texts += [creature_prompt(tr) for tr in itertools.islice(_all_trait_vectors(), 40)]
    for t in texts:
        assert "FRUIT_" not in t
        assert "law_id" not in t and "match_seed" not in t
        for cls in ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D"):
            assert cls not in t


def test_khong_mang_thu_do_client_viet():
    """Không có chỗ nào nhận display_name/persona: chữ ký hàm là bằng chứng."""
    import inspect

    for fn in (creature_prompt, creature_visual):
        params = set(inspect.signature(fn).parameters)
        assert params == {"tr"}, f"{fn.__name__} nhận thêm {params - {'tr'}}"


def test_phu_kin_dia_hinh_qua_ban_do():
    ids = {r["id"] for r in all_static_prompts()}
    for t in Terrain:
        assert f"terrain_{t.name.lower()}" in ids
        assert terrain_prompt(t).strip()
    for name in MAPS:
        assert f"map_{name.lower()}" in ids
    assert len([r for r in all_static_prompts() if r["nhom"] == "vat_the"]) == (
        law_config.FRUIT_KINDS + 1     # 4 quả + xác
    )


def test_mo_ta_ban_do_bam_theo_can_bang_that():
    """Tỉ lệ địa hình trong câu lấy thẳng từ `MapSpec.seeds`.

    Gõ tay thì đổi cân bằng bản đồ xong mô tả 3D vẫn nói con số cũ.
    """
    hoang_mac = map_prompt(MAPS["HOANG_MAC"])
    assert "rock 12" in hoang_mac
    rung_ram = map_prompt(MAPS["RUNG_RAM"])
    assert "bush 11" in rung_ram
    # Rừng rậm nhiều bụi hơn hoang mạc — câu chữ phải phản ánh đúng thứ tự.
    assert rung_ram.index("bush") < rung_ram.index("water")


def test_qua_khoa_theo_be_mat_khong_theo_lop():
    """Bốn quả dùng được cho MỌI ván, vì bề mặt bị hoán vị lại mỗi ván."""
    seen = set()
    for color, shape in law_config.FRUIT_SURFACES:
        p = fruit_prompt(color, shape)
        assert p not in seen
        seen.add(p)
    assert len(seen) == law_config.FRUIT_KINDS


def test_payload_gui_duoc_ngay():
    p = meshy_payload(creature_prompt(founder_traits("L1")))
    assert p["prompt"] and p["negative_prompt"]
    assert p["mode"] == "preview"
    import json

    json.dumps(p)   # phải serialize được, không có kiểu lạ


def test_fruit_prompt_bao_loi_voi_be_mat_la():
    with pytest.raises(KeyError):
        fruit_prompt("hồng", "tròn")
