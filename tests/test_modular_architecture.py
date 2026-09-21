"""Tests for Genesis Zero 3D Modular Architecture & Graphics Pipeline (Milestone 1).

Verifies:
1. Physical directory separation: assets/, render/, entities/, simulation/, audio/.
2. Presence of all 18 modular components specified in PROJECT.md.
3. 100% Zero-CDN and offline compliance (no external URLs).
4. Boundary decoupling (no cross-domain leaks between assets and entity state machines).
5. Presence of advanced lighting, PCFSoftShadowMap, and PBR materials across rendering modules.
6. Integration of Master Diorama (ecosystem_map.glb) and Rigged 8-Animation Creature models.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT / "web" / "modules"

EXPECTED_MODULE_FILES = [
    # Assets Module
    MODULES_DIR / "assets" / "AssetManifest.js",
    MODULES_DIR / "assets" / "AssetLoader.js",
    MODULES_DIR / "assets" / "AssetCache.js",
    MODULES_DIR / "assets" / "FallbackFactory.js",
    # Render Module
    MODULES_DIR / "render" / "RenderEngine.js",
    MODULES_DIR / "render" / "SceneManager.js",
    MODULES_DIR / "render" / "LightingRig.js",
    MODULES_DIR / "render" / "MaterialLibrary.js",
    MODULES_DIR / "render" / "WeatherAtmosphere.js",
    # Entities Module
    MODULES_DIR / "entities" / "CreatureController.js",
    MODULES_DIR / "entities" / "CreatureStateMachine.js",
    MODULES_DIR / "entities" / "AnimationDispatcher.js",
    MODULES_DIR / "entities" / "SpatialSynchronizer.js",
    MODULES_DIR / "entities" / "CreatureOverlay.js",
    # Simulation Module
    MODULES_DIR / "simulation" / "TelemetryClient.js",
    MODULES_DIR / "simulation" / "ReplayBuffer.js",
    MODULES_DIR / "simulation" / "EventBus.js",
    # Audio Module
    MODULES_DIR / "audio" / "AudioSynthesizer.js",
]


def test_physical_file_separation_all_components_exist():
    """Verify all 18 modular JavaScript files exist on disk."""
    for file_path in EXPECTED_MODULE_FILES:
        assert file_path.exists(), f"Missing modular component: {file_path.relative_to(ROOT)}"
        content = file_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 50, f"Module file appears empty or incomplete: {file_path.name}"


def test_zero_cdn_across_all_modules():
    """Verify 100% offline zero-CDN invariant across all modular JavaScript files."""
    for file_path in EXPECTED_MODULE_FILES:
        content = file_path.read_text(encoding="utf-8")
        assert "http://" not in content, f"{file_path.name} contains forbidden http://"
        assert "https://" not in content, f"{file_path.name} contains forbidden https://"
        assert not re.search(r"src=[\"']//", content), f"{file_path.name} contains protocol-relative URL"


def test_asset_manifest_catalogs_master_diorama_and_10_rigged_creatures():
    """Verify AssetManifest.js catalogs all 10 core creature GLBs and the master diorama."""
    manifest_js = (MODULES_DIR / "assets" / "AssetManifest.js").read_text(encoding="utf-8")

    # Master diorama
    assert "ecosystem_map.glb" in manifest_js, "AssetManifest.js must catalog ecosystem_map.glb"
    assert "master_diorama" in manifest_js, "AssetManifest.js must define master_diorama entry"

    # 10 core species
    required_species = [
        "sand_skink",
        "snow_ferret",
        "alpine_ibex",
        "meadow_hare",
        "marsh_croc",
        "abyssal_hunter",
        "storm_eagle",
        "armored_sentinel",
        "giant_tarantula",
        "carnivore_apex",
    ]
    for sp in required_species:
        assert sp in manifest_js, f"AssetManifest.js missing species: {sp}"


def test_render_modules_pbr_and_lighting_pipeline():
    """Verify LightingRig, MaterialLibrary, and RenderEngine implement PBR and soft shadows."""
    lighting_js = (MODULES_DIR / "render" / "LightingRig.js").read_text(encoding="utf-8")
    render_js = (MODULES_DIR / "render" / "RenderEngine.js").read_text(encoding="utf-8")
    material_js = (MODULES_DIR / "render" / "MaterialLibrary.js").read_text(encoding="utf-8")

    # LightingRig assertions
    assert "DirectionalLight" in lighting_js, "LightingRig must implement DirectionalLight"
    assert "HemisphereLight" in lighting_js, "LightingRig must implement HemisphereLight"
    assert "AmbientLight" in lighting_js or "PointLight" in lighting_js, "LightingRig must implement ambient/point fill"
    assert "2048" in lighting_js, "LightingRig must configure 2048x2048 shadow map"
    assert "-0.0003" in lighting_js or "-0.0004" in lighting_js, "LightingRig must configure shadow bias"

    # RenderEngine assertions
    assert "PCFSoftShadowMap" in render_js, "RenderEngine must configure PCFSoftShadowMap"
    assert "ACESFilmicToneMapping" in render_js, "RenderEngine must configure ACESFilmicToneMapping"

    # MaterialLibrary assertions
    assert "MeshStandardMaterial" in material_js, "MaterialLibrary must use MeshStandardMaterial"
    assert "MeshPhysicalMaterial" in material_js, "MaterialLibrary must use MeshPhysicalMaterial"
    assert "transmission" in material_js, "MaterialLibrary water shader must use transmission"
    assert "roughness" in material_js and "metalness" in material_js, "MaterialLibrary must parameterize roughness & metalness"


def test_entity_state_machine_and_animation_dispatcher():
    """Verify CreatureStateMachine maps simulation events to 8 canonical action clips."""
    state_js = (MODULES_DIR / "entities" / "CreatureStateMachine.js").read_text(encoding="utf-8")
    dispatcher_js = (MODULES_DIR / "entities" / "AnimationDispatcher.js").read_text(encoding="utf-8")

    # 8 canonical animation clips
    expected_clips = [
        "Idle_Normal",
        "Idle_Alert",
        "Walk",
        "Run",
        "Attack",
        "Hurt_Defend",
        "Eat",
        "Death",
    ]
    for clip in expected_clips:
        assert clip in state_js, f"CreatureStateMachine missing action clip: {clip}"
        assert clip in dispatcher_js, f"AnimationDispatcher missing action clip: {clip}"

    # Cross-fading support
    assert "crossFadeTo" in dispatcher_js, "AnimationDispatcher must implement crossFadeTo"
    assert "AnimationMixer" in dispatcher_js, "AnimationDispatcher must use THREE.AnimationMixer"


def test_module_boundary_decoupling():
    """Verify strict separation of concerns between assets, rendering, and simulation."""
    assets_js = (MODULES_DIR / "assets" / "AssetLoader.js").read_text(encoding="utf-8")
    assert "CreatureStateMachine" not in assets_js, "AssetLoader must not couple to CreatureStateMachine"
    assert "syncBodies" not in assets_js, "AssetLoader must not couple to spectator syncBodies"

    lighting_js = (MODULES_DIR / "render" / "LightingRig.js").read_text(encoding="utf-8")
    assert "TR.stomach" not in lighting_js, "LightingRig must not reference creature traits"
    assert "TR.speed" not in lighting_js, "LightingRig must not reference creature traits"


def test_watch3d_js_facade_integration():
    """Verify watch3d.js integrates master diorama and rigged creature pipeline."""
    watch_js = (ROOT / "web" / "watch3d.js").read_text(encoding="utf-8")

    # Master diorama integration
    assert "ecosystem_map.glb" in watch_js, "watch3d.js must reference ecosystem_map.glb"
    assert "applyPrimordialShaders" in watch_js, "watch3d.js must implement applyPrimordialShaders"

    # Rigged creature pipeline
    assert "createRiggedOrProceduralBody" in watch_js, "watch3d.js must implement createRiggedOrProceduralBody"
    assert "crossFadeCreatureAction" in watch_js, "watch3d.js must implement crossFadeCreatureAction"
    assert "SkeletonUtils" in watch_js, "watch3d.js must reference SkeletonUtils for skinned mesh cloning"

    # Shadows and PBR
    assert "PCFSoftShadowMap" in watch_js, "watch3d.js must configure PCFSoftShadowMap"
    assert "2048" in watch_js, "watch3d.js must configure 2048x2048 shadow maps"
