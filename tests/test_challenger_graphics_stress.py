"""tests/test_challenger_graphics_stress.py - Empirical Adversarial Stress Suite for Graphics Code Analyzer.

Authored by Challenger M3-1 (Role: Graphics Analysis & Shaders Challenger).
Part of Genesis Zero Milestone 3 Verification Gate.

Adversarial stress-testing suite for scripts/analyze_graphics_code.py:
1. Synthetic negative fixtures:
   - Disabled shadows (shadowMap.enabled = false)
   - Omitted castShadow & semantic evaluation of castShadow = false
   - Degraded/replaced PBR materials (MeshBasicMaterial, MeshLambertMaterial)
   - Missing directional, ambient, and hemisphere lighting
   - Missing sun position configuration
   - Empty workspace directory
2. Genuine codebase compliance:
   - Programmatic verification API (verify_graphics_code)
   - Full 14-criteria compliance
   - Non-comment active code density verification
3. CLI & JSON contract verification:
   - CLI exit code 0 on genuine project
   - CLI exit code 1 on failed fixtures
   - JSON output schema adherence and external tool parseability
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.analyze_graphics_code import (
    GraphicsCodeAnalyzer,
    verify_graphics_code,
)

ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. Synthetic Negative Fixtures & Sensitivity Tests
# ==============================================================================

def test_adversarial_synthetic_disabled_shadow_map(tmp_path: Path):
    """Adversarial Test: When shadowMap.enabled is false or omitted, SHADOW_MAP_ENABLED must fail."""
    render_dir = tmp_path / "web" / "modules" / "render"
    render_dir.mkdir(parents=True)
    engine_file = render_dir / "RenderEngine.js"
    engine_file.write_text(
        """
        export class RenderEngine {
            constructor() {
                this.renderer = {
                    shadowMap: { enabled: false, type: 1 },
                    toneMapping: 3
                };
            }
        }
        """,
        encoding="utf-8",
    )

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/RenderEngine.js"])
    results = analyzer.check_soft_shadows()
    map_res = next(r for r in results if r.criteria_id == "SHADOW_MAP_ENABLED")

    assert map_res.passed is False
    assert "renderer.shadowMap.enabled = true missing" in str(map_res.failure_reason)

    # Full report check
    report = analyzer.generate_report()
    assert report["success"] is False
    assert report["status"] == "FAIL"


def test_adversarial_synthetic_omitted_cast_shadow(tmp_path: Path):
    """Adversarial Test: When castShadow is entirely omitted, SHADOW_CAST must fail with exit code 1."""
    render_dir = tmp_path / "web" / "modules" / "render"
    render_dir.mkdir(parents=True)
    light_file = render_dir / "LightingRig.js"
    light_file.write_text(
        """
        export class LightingRig {
            setupLighting() {
                this.sunLight = new THREE.DirectionalLight(0xfff7ed, 1.0);
                this.sunLight.position.set(10, 20, 10);
                // No castShadow configured anywhere
            }
        }
        """,
        encoding="utf-8",
    )

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/LightingRig.js"])
    results = analyzer.check_soft_shadows()
    cast_res = next(r for r in results if r.criteria_id == "SHADOW_CAST")

    assert cast_res.passed is False
    assert "castShadow configuration missing" in str(cast_res.failure_reason)


def test_adversarial_synthetic_cast_shadow_false_regex_blindspot(tmp_path: Path):
    """Adversarial Finding: Document and assert the sensitivity of regex r'\\.castShadow\\s*=\\s*(?:true|[\\w\\(\\)]+)'

    When a codebase explicitly writes `castShadow = false`, the regex [\\w\\(\\)]+
    blindly matches the word 'false'. This test documents this empirical behavior.
    """
    render_dir = tmp_path / "web" / "modules" / "render"
    render_dir.mkdir(parents=True)
    light_file = render_dir / "LightingRig.js"
    light_file.write_text(
        """
        export class LightingRig {
            setupLighting() {
                this.sunLight = new THREE.DirectionalLight(0xfff7ed, 1.0);
                this.sunLight.castShadow = false; // Explicitly disabled
            }
        }
        """,
        encoding="utf-8",
    )

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/LightingRig.js"])
    results = analyzer.check_soft_shadows()
    cast_res = next(r for r in results if r.criteria_id == "SHADOW_CAST")

    # Empirical finding: Analyzer matches 'this.sunLight.castShadow = false' as True
    # because [\\w\\(\\)]+ matches word characters 'false'.
    assert len(cast_res.matches) > 0
    assert "castShadow = false" in cast_res.matches[0].context


def test_adversarial_synthetic_pbr_replaced_with_basic_materials(tmp_path: Path):
    """Adversarial Test: When PBR materials are replaced with MeshBasicMaterial / MeshLambertMaterial,
    all 5 PBR and shader criteria must fail with pinpointed failure reasons.
    """
    render_dir = tmp_path / "web" / "modules" / "render"
    render_dir.mkdir(parents=True)
    mat_file = render_dir / "MaterialLibrary.js"
    mat_file.write_text(
        """
        export class MaterialLibrary {
            static createTerrainMaterial() {
                return new THREE.MeshBasicMaterial({ color: 0x228b22 });
            }
            static createCreatureMaterial() {
                return new THREE.MeshLambertMaterial({ color: 0xff0000 });
            }
            static createWaterMaterial() {
                return new THREE.MeshBasicMaterial({ color: 0x0000ff, opacity: 0.5 });
            }
        }
        """,
        encoding="utf-8",
    )

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/MaterialLibrary.js"])
    results = analyzer.check_pbr_and_shaders()
    res_map = {r.criteria_id: r for r in results}

    assert res_map["PBR_STANDARD"].passed is False
    assert "MeshStandardMaterial usage missing" in str(res_map["PBR_STANDARD"].failure_reason)

    assert res_map["PBR_PHYSICAL"].passed is False
    assert "MeshPhysicalMaterial usage missing" in str(res_map["PBR_PHYSICAL"].failure_reason)

    assert res_map["PBR_PARAMS"].passed is False
    assert "Roughness and metalness parameterization missing" in str(res_map["PBR_PARAMS"].failure_reason)

    assert res_map["PBR_STRATA_SLOPE"].passed is False
    assert "Strata/slope vertex color shading missing" in str(res_map["PBR_STRATA_SLOPE"].failure_reason)

    assert res_map["PBR_WATER_SHADER"].passed is False
    assert "Physical optical water shader parameters missing" in str(res_map["PBR_WATER_SHADER"].failure_reason)


def test_adversarial_synthetic_missing_lighting_components(tmp_path: Path):
    """Adversarial Test: When directional, ambient, or hemisphere lights are missing,
    each respective criteria fails with an exact descriptive failure reason.
    """
    render_dir = tmp_path / "web" / "modules" / "render"
    render_dir.mkdir(parents=True)
    light_file = render_dir / "LightingRig.js"
    # Only PointLight present, no DirectionalLight, AmbientLight, or HemisphereLight
    light_file.write_text(
        """
        export class LightingRig {
            setupLighting() {
                this.pointLight = new THREE.PointLight(0xffffff, 1.0, 100);
            }
        }
        """,
        encoding="utf-8",
    )

    analyzer = GraphicsCodeAnalyzer(root_dir=tmp_path, target_files=["web/modules/render/LightingRig.js"])
    results = analyzer.check_advanced_lighting()
    res_map = {r.criteria_id: r for r in results}

    assert res_map["LIGHT_DIR"].passed is False
    assert "No DirectionalLight instantiation found" in str(res_map["LIGHT_DIR"].failure_reason)

    assert res_map["LIGHT_AMB"].passed is False
    assert "No AmbientLight instantiation found" in str(res_map["LIGHT_AMB"].failure_reason)

    assert res_map["LIGHT_HEMI"].passed is False
    assert "No HemisphereLight instantiation found" in str(res_map["LIGHT_HEMI"].failure_reason)

    assert res_map["LIGHT_POS"].passed is False
    assert "No directional sun position configuration found" in str(res_map["LIGHT_POS"].failure_reason)


def test_adversarial_synthetic_empty_workspace_fails_with_exit_code_1(tmp_path: Path):
    """Adversarial Test: An empty workspace must yield exit code 1 and 0% compliance."""
    script_path = ROOT / "scripts" / "analyze_graphics_code.py"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path), "--root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["status"] == "FAIL"
    assert data["success"] is False
    assert data["summary"]["passed"] == 0
    assert data["summary"]["failed"] == 14
    assert data["summary"]["compliance_rate"] == "0.0%"


# ==============================================================================
# 2. Genuine Codebase Verification & Active Code Density
# ==============================================================================

def test_genuine_codebase_full_14_criteria_pass():
    """Verify that the real Genesis Zero codebase passes 100% of all 14 criteria."""
    success, report = verify_graphics_code(root_dir=ROOT)
    assert success is True
    assert report["status"] == "PASS"
    assert report["summary"]["total_criteria"] == 14
    assert report["summary"]["passed"] == 14
    assert report["summary"]["failed"] == 0
    assert report["summary"]["compliance_rate"] == "100.0%"


def test_genuine_codebase_all_criteria_have_active_code_matches():
    """Adversarial Verification: Ensure matches in the real codebase are not merely comments."""
    analyzer = GraphicsCodeAnalyzer(root_dir=ROOT)
    report = analyzer.generate_report()

    for item in report["results"]:
        cid = item["criteria_id"]
        matches = item["matches"]
        assert len(matches) > 0, f"Criterion {cid} has 0 matches in genuine codebase"

        # Count lines that do not start with comment tokens
        active = [
            m for m in matches
            if not m["context"].strip().startswith(("//", "/*", "*", "<!--"))
        ]
        assert len(active) > 0, f"Criterion {cid} has only comment matches, zero active code!"


def test_genuine_codebase_cast_shadow_assignments_are_active():
    """Verify that all SHADOW_CAST matches in the genuine codebase are positive assignments."""
    analyzer = GraphicsCodeAnalyzer(root_dir=ROOT)
    report = analyzer.generate_report()
    shadow_cast = next(r for r in report["results"] if r["criteria_id"] == "SHADOW_CAST")

    # In genuine codebase, every match must enable shadows (= true or positive expression)
    for m in shadow_cast["matches"]:
        ctx = m["context"]
        assert "castShadow = false" not in ctx, f"Found negative castShadow in {m['file_path']}:{m['line_number']}"
        assert "castShadow" in ctx


# ==============================================================================
# 3. CLI & JSON External Parseability Tests
# ==============================================================================

def test_cli_execution_genuine_codebase():
    """Verify CLI exit code is 0 and stdout contains formatted report."""
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
    assert "Compliance: 100.0%" in proc.stdout
    assert "Passed: 14/14 criteria" in proc.stdout


def test_cli_json_mode_external_tool_parseability():
    """Verify CLI --json outputs clean, valid JSON with exact schema expected by external tooling."""
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

    # Top-level contract
    assert isinstance(data, dict)
    for key in ["status", "success", "summary", "scanned_files", "categories", "results"]:
        assert key in data, f"Missing top-level key: {key}"

    # Summary contract
    summary = data["summary"]
    assert summary["total_criteria"] == 14
    assert summary["passed"] == 14
    assert summary["failed"] == 0
    assert summary["compliance_rate"] == "100.0%"

    # Results contract
    for res in data["results"]:
        for field in ["criteria_id", "name", "category", "description", "passed", "required", "matches", "match_count"]:
            assert field in res, f"Missing field {field} in result {res.get('criteria_id')}"
        assert res["passed"] is True
        assert res["match_count"] > 0
        assert res["failure_reason"] is None

    # Scanned files contract
    assert len(data["scanned_files"]) == 6
    for sf in data["scanned_files"]:
        assert sf["exists"] is True
        assert sf["size_bytes"] > 0
        assert sf["lines"] > 0
