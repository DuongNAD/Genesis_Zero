"""tests/test_verify_modular_architecture.py - Automated tests for scripts/verify_modular_architecture.py.

Part of Genesis Zero Milestone 3 (Quality Verification & Architecture Certification).
Verifies:
1. Programmatic API and architecture compliance on actual project files.
2. Physical modular separation (assets vs render vs entities vs simulation vs audio).
3. Modular boundary decoupling rules.
4. Dependency graph cycle detection (verifying 0 cycles on project + genuine cycle detection on synthetic cycles).
5. Zero-CDN offline compliance (verifying 0 CDN references on project + genuine detection on synthetic CDN references).
6. CLI execution, return codes, JSON serialization, and verbose flag.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.verify_modular_architecture import (
    ModularArchitectureVerifier,
    format_cli_output,
    verify_modular_architecture,
)

ROOT = Path(__file__).resolve().parent.parent


def test_programmatic_verification_passes_on_project():
    """Verify that verify_modular_architecture returns True and PASS on Genesis Zero."""
    success, report = verify_modular_architecture(root_dir=ROOT)
    assert success is True
    assert report["status"] == "PASS"
    assert report["summary"]["total_violations"] == 0
    assert report["summary"]["detected_cycles"] == 0
    assert report["summary"]["physical_separation"] == "PASS"
    assert report["summary"]["modular_boundaries"] == "PASS"
    assert report["summary"]["zero_circular_dependencies"] == "PASS"
    assert report["summary"]["zero_cdn_offline_compliance"] == "PASS"


def test_physical_separation_modules_and_components():
    """Verify all 5 module directories and their components are properly indexed."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    passed, modules_info, violations = verifier.verify_physical_separation()
    assert passed is True
    assert len(violations) == 0

    mod_names = {m.name for m in modules_info}
    assert mod_names == {"assets", "render", "entities", "simulation", "audio"}
    for m in modules_info:
        assert m.exists is True
        assert len(m.missing_required) == 0
        assert len(m.files) >= 1


def test_modular_boundaries_enforced():
    """Verify boundary decoupling: no cross-layer leakage across modules."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    passed, violations = verifier.verify_modular_boundaries()
    assert passed is True
    assert len(violations) == 0


def test_zero_circular_dependencies_on_project():
    """Verify that the module dependency graph is strictly acyclic (DAG)."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    graph = verifier.build_module_dependency_graph()
    assert len(graph) >= 18
    passed, cycles, violations = verifier.detect_circular_dependencies(graph)
    assert passed is True
    assert len(cycles) == 0
    assert len(violations) == 0


def test_synthetic_cycle_detection():
    """Adversarial test: prove cycle detector genuinely detects cycles."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    # Synthetic cyclic graph: A -> B -> C -> A
    cyclic_graph = {
        "moduleA.js": {"moduleB.js"},
        "moduleB.js": {"moduleC.js"},
        "moduleC.js": {"moduleA.js"},
        "moduleD.js": set(),
    }
    passed, cycles, violations = verifier.detect_circular_dependencies(cyclic_graph)
    assert passed is False
    assert len(cycles) >= 1
    assert len(violations) >= 1
    # Check that cycle contains A, B, C
    flat_cycle = [item for sublist in cycles for item in sublist]
    assert "moduleA.js" in flat_cycle
    assert "moduleB.js" in flat_cycle
    assert "moduleC.js" in flat_cycle


def test_zero_cdn_offline_compliance_on_project():
    """Verify that all web runtime files are 100% offline and free of external CDNs."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is True
    assert len(violations) == 0


def test_synthetic_cdn_detection_html(tmp_path: Path):
    """Adversarial test: prove zero-CDN scanner genuinely detects forbidden CDN scripts."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    fake_html = fake_web / "test.html"
    fake_html.write_text(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>',
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "ZERO_CDN_HTML_SCRIPT" for v in violations)
    assert any("cdnjs.cloudflare.com" in v.detail for v in violations)


def test_synthetic_cdn_detection_js(tmp_path: Path):
    """Adversarial test: prove zero-CDN scanner genuinely detects forbidden CDN references in JS."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    fake_js = fake_web / "app.js"
    fake_js.write_text(
        'const cdn = "https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js";',
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "ZERO_CDN_JS_REFERENCE" for v in violations)


def test_synthetic_broken_script_detection(tmp_path: Path):
    """Adversarial test: prove zero-CDN scanner detects missing local script targets."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    fake_html = fake_web / "index.html"
    fake_html.write_text(
        '<script src="non_existent_local_lib.js"></script>',
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "BROKEN_LOCAL_SCRIPT" for v in violations)


def test_cli_execution_returns_zero():
    """Verify CLI execution via subprocess returns exit code 0."""
    script_path = ROOT / "scripts" / "verify_modular_architecture.py"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path), "--root", str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    assert "Overall Status: [PASS]" in proc.stdout
    assert "Physical Directory Decoupling" in proc.stdout
    assert "Modular Boundary Enforcement" in proc.stdout
    assert "Zero circular dependencies detected" in proc.stdout
    assert "Zero-CDN Offline Invariant" in proc.stdout


def test_cli_json_output():
    """Verify CLI with --json produces valid parseable JSON."""
    script_path = ROOT / "scripts" / "verify_modular_architecture.py"
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
    assert data["summary"]["total_violations"] == 0
    assert data["summary"]["detected_cycles"] == 0


def test_format_cli_output_contains_expected_headers():
    """Verify format_cli_output produces correct human-readable report."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    report = verifier.run_all_verifications()
    out = format_cli_output(report, verbose=True)
    assert "MODULAR ARCHITECTURE & ZERO-CDN CERTIFICATION REPORT" in out
    assert "Physical Directory Decoupling (5 modules)" in out
