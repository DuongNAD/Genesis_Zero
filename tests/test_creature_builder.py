"""Genesis Zero — tests cho creature_builder và build_creatures."""

from __future__ import annotations

import pytest
from genesis import config
from genesis.creature_builder import build_creature_blender_code
from genesis.domain import Domain
from genesis.traits import Traits
from genesis.features import roll_for_species


def test_build_creature_code_syntax():
    """Đảm bảo chuỗi mã sinh ra có đầy đủ các cấu trúc giải phẫu và hợp lệ."""
    code = build_creature_blender_code(
        species_id="L1",
        seed=1,
        out_glb="/tmp/test_L1.glb",
        out_blend="/tmp/test_L1.blend",
    )
    assert "Genesis_L1_s1" in code
    assert "Armature_L1_s1" in code
    assert "Body_L1_s1" in code
    assert "Eyes_L1_s1" in code
    assert "Creature_L1_s1_Idle" in code
    assert "Subsurf" in code
    assert "/tmp/test_L1.glb" in code


def test_all_domains_generate_valid_code():
    """Kiểm tra cả 3 tầng CAN, NUOC, TROI đều sinh mã tương thích."""
    for sp in ["L1", "W1", "A1"]:
        code = build_creature_blender_code(species_id=sp, seed=1)
        assert f"Genesis_{sp}_s1" in code
        assert "export_scene.gltf" not in code  # out_glb None thì không xuất


def test_traits_scale_affects_anatomy():
    """Kiểm tra sự thay đổi của trait và feature tác động trực tiếp vào thông số."""
    tr_high_brain = Traits(brain=5, attack=2, armor=1, speed=2, sense=1, stomach=1)
    code_high_brain = build_creature_blender_code(
        species_id="L1", seed=1, traits=tr_high_brain, domain=Domain.CAN
    )
    # 0.80 + 0.12 * 5 = 1.40
    assert "1.40" in code_high_brain
