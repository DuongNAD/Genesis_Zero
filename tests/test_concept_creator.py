"""Kiểm thử cho quy trình tạo Concept Art và Dựng 3D Blender (Động vật, Thực vật, Nấm)."""

from fastapi.testclient import TestClient

from genesis.concept_creator import (
    build_master_concept_prompt,
)
from net.server import app


def test_build_master_concept_prompt_fauna() -> None:
    prompt = build_master_concept_prompt(
        name="Thỏ Đồng Cỏ",
        latin="Sylvilagus Campestris",
        domain="CAN",
        diet="HERBIVORE",
        strategy="STRAT_R",
        traits=[1, 0, 1, 4, 3, 3],
        features=["CAMOUFLAGE"],
        description="Thỏ rừng nhỏ gọn, lông xám tro ngụy trang",
        kingdom="FAUNA",
    )
    assert "Thỏ Đồng Cỏ" in prompt
    assert "Sylvilagus Campestris" in prompt
    assert "Động vật" in prompt
    assert "Thỏ rừng nhỏ gọn" in prompt
    assert "Phong cách 3D" in prompt


def test_build_master_concept_prompt_flora() -> None:
    prompt = build_master_concept_prompt(
        name="Cây Ăn Thịt Rễ Bước",
        latin="Nepenthes Ambulans",
        domain="CAN",
        diet="CARNIVORE",
        strategy="STRAT_K",
        traits=[2, 4, 3, 3, 4, 4], # 20 điểm
        features=["GAI_DOC"],
        description="Cây ăn thịt rễ bước đài hoa bẫy kẹp",
        kingdom="FLORA",
    )
    assert "Cây Ăn Thịt Rễ Bước" in prompt
    assert "Thực vật" in prompt
    assert "Snap-trap" in prompt or "bẫy kẹp" in prompt


def test_generate_creature_concept_and_3d_api(monkeypatch, tmp_path) -> None:
    from genesis import concept_creator
    monkeypatch.setattr(concept_creator, "_find_blender", lambda: None)
    monkeypatch.setattr(concept_creator, "CONCEPTS_DIR", tmp_path / "concepts")
    monkeypatch.setattr(concept_creator, "CREATURES_DIR", tmp_path / "creatures")
    client = TestClient(app)
    res = client.post(
        "/v1/spectate/generate_concept",
        json={
            "name": "Nấm Phát Quang",
            "latin": "Mycena Phosphorea",
            "domain": "CAN",
            "diet": "HERBIVORE",
            "strategy": "STRAT_R",
            "traits": [1, 1, 2, 4, 4, 4], # 16 điểm
            "features": ["CAMOUFLAGE"],
            "description": "Nấm phát quang lơ lửng bọng bào tử acid",
            "kingdom": "FUNGI",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is False
    assert data["status"] == "concept_only"
    assert data["error"] == "BLENDER_UNAVAILABLE"
    assert "concept" in data["image_url"]
    assert data["glb_url"] is None
    assert data["blend_url"] is None
    assert list((tmp_path / "concepts").glob("*.svg"))
