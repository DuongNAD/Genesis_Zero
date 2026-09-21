"""tests/test_analyze_graphics_code.py - Automated tests for scripts/analyze_graphics_code.py.

Part of Genesis Zero Milestone 3 (Quality Verification & Architecture Certification).
Verifies:
1. Programmatic API and criteria evaluations across actual project files.
2. CLI execution, return codes, JSON serialization, and verbose flag.
3. Genuine detection logic on synthetic fixtures (verifying that missing lighting, shadows,
   or PBR materials correctly cause failures, proving no hardcoded/dummy bypass).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.analyze_graphics_code import (
    GraphicsCodeAnalyzer,
    format_cli_output,
    verify_graphics_code,
)

ROOT = Path(__file__).resolve().parent.parent


def test_programmatic_verification_passes_on_project():
    """Verify that verify_graphics_code returns True and PASS on the actual Genesis Zero codebase."""
    success, report = verify_graphics_code(root_dir=ROOT)
    assert success is True
    assert report["status"] == "PASS"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["passed"] >= 14
    assert report["summary"]["total_criteria"] >= 14


def test_analyzer_advanced_lighting_pipeline():
    """Verify analyzer identifies all advanced lighting components."""
    analyzer = GraphicsCodeAnalyzer(root_dir=ROOT)
    results = analyzer.check_advanced_lighting()

    res_by_id = {r.criteria_id: r for r in results}
    assert "LIGHT_DIR" in res_by_id
    assert "LIGHT_AMB" in res_by_id
    assert "LIGHT_HEMI" in res_by_id
    assert "LIGHT_POS" in res_by_id

    for r in results:
        assert r.passed is True, f"Lighting check {r.criteria_id} failed: {r.failure_reason}"
        assert len(r.matches) > 0, f"Lighting check {r.criteria_id} had 0 matches"


def test_analyzer_soft_shadows_pipeline():
    """Verify analyzer identifies soft shadow configurations."""
    analyzer = GraphicsCodeAnalyzer(root_dir=ROOT)
    results = analyzer.check_soft_shadows()

    res_by_id = {r.criteria_id: r for r in results}
    assert "SHADOW_MAP_ENABLED" in res_by_id
    assert "SHADOW_PCF_SOFT" in res_by_id
    assert "SHADOW_CAST" in res_by_id
    assert "SHADOW_RECEIVE" in res_by_id
    assert "SHADOW_BIAS_RES" in res_by_id

    for r in results:
        assert r.passed is True, f"Shadow check {r.criteria_id} failed: {r.failure_reason}"
        assert len(r.matches) > 0, f"Shadow check {r.criteria_id} had 0 matches"


def test_analyzer_pbr_materials_and_shaders():
    """Verify analyzer identifies PBR materials and optical depth water shaders."""
    analyzer = GraphicsCodeAnalyzer(root_dir=ROOT)
    results = analyzer.check_pbr_and_shaders()

    res_by_id = {r.criteria_id: r for r in results}
    assert "PBR_STANDARD" in res_by_id
    assert "PBR_PHYSICAL" in res_by_id
    assert "PBR_PARAMS" in res_by_id
    assert "PBR_STRATA_SLOPE" in res_by_id
    assert "PBR_WATER_SHADER" in res_by_id

    for r in results:
        assert r.passed is True, f"PBR check {r.criteria_id} failed: {r.failure_reason}"
        assert len(r.matches) > 0, f"PBR check {r.criteria_id} had 0 matches"


def test_cli_execution_returns_zero():
    """Verify CLI execution via subprocess returns exit code 0."""
    script_path = ROOT / "scripts" / "analyze_graphics_code.py"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path), "--root", str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    assert "Overall Status: [PASS]" in proc.stdout
    assert "ADVANCED LIGHTING PIPELINE" in proc.stdout
    assert "SOFT SHADOWS & SHADOW MAPS" in proc.stdout
    assert "PBR MATERIALS & ADVANCED SHADERS" in proc.stdout


def test_cli_json_output():
    """Verify CLI with --json produces valid parseable JSON."""
    script_path = ROOT / "scripts" / "analyze_graphics_code.py"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path), "--root", str(ROOT), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["status"] == "PASS"
    assert data["success"] is True
    assert "summary" in data
    assert "categories" in data
    assert data["summary"]["failed"] == 0


def test_cli_verbose_output():
    """Verify CLI with --verbose prints match details and file snippets."""
    script_path = ROOT / "scripts" / "analyze_graphics_code.py"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path), "--root", str(ROOT), "--verbose"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    assert "->" in proc.stdout


def test_synthetic_detection_detects_missing_lighting(tmp_path: Path):
    """Adversarial test: prove analyzer genuinely detects missing DirectionalLight."""
    fake_render_dir = tmp_path / "web" / "modules" / "render"
    fake_render_dir.mkdir(parents=True)
    fake_lighting = fake_render_dir / "LightingRig.js"
    # File without DirectionalLight
    fake_lighting.write_text("export class LightingRig { constructor() { this.ambient = 1; } }", encoding="utf-8")

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/LightingRig.js"])
    results = analyzer.check_advanced_lighting()
    dir_res = next(r for r in results if r.criteria_id == "LIGHT_DIR")
    assert dir_res.passed is False
    assert "No DirectionalLight instantiation found" in str(dir_res.failure_reason)


def test_synthetic_detection_detects_missing_shadows(tmp_path: Path):
    """Adversarial test: prove analyzer genuinely detects disabled/missing shadow maps."""
    fake_render_dir = tmp_path / "web" / "modules" / "render"
    fake_render_dir.mkdir(parents=True)
    fake_engine = fake_render_dir / "RenderEngine.js"
    # File without shadowMap.enabled = true
    fake_engine.write_text("export class RenderEngine { constructor() { this.shadows = false; } }", encoding="utf-8")

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/RenderEngine.js"])
    results = analyzer.check_soft_shadows()
    map_res = next(r for r in results if r.criteria_id == "SHADOW_MAP_ENABLED")
    assert map_res.passed is False


def test_synthetic_detection_detects_missing_pbr(tmp_path: Path):
    """Adversarial test: prove analyzer genuinely detects missing MeshPhysicalMaterial."""
    fake_render_dir = tmp_path / "web" / "modules" / "render"
    fake_render_dir.mkdir(parents=True)
    fake_mat = fake_render_dir / "MaterialLibrary.js"
    # File without MeshPhysicalMaterial
    fake_mat.write_text("export class MaterialLibrary { static create() { return new THREE.MeshBasicMaterial(); } }", encoding="utf-8")

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/MaterialLibrary.js"])
    results = analyzer.check_pbr_and_shaders()
    phys_res = next(r for r in results if r.criteria_id == "PBR_PHYSICAL")
    assert phys_res.passed is False


def test_format_cli_output_contains_expected_headers():
    """Verify format_cli_output renders proper report structure."""
    analyzer = GraphicsCodeAnalyzer(root_dir=ROOT)
    report = analyzer.generate_report()
    out = format_cli_output(report, verbose=True)
    assert "GRAPHICS CODE ANALYSIS REPORT" in out
    assert "Compliance: 100.0%" in out
