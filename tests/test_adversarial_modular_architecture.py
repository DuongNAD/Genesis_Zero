"""tests/test_adversarial_modular_architecture.py - Adversarial Stress Tests for Modular Architecture & Zero-CDN.

Part of Genesis Zero Milestone 3 (Quality Verification & Architecture Certification).
Adversarial Challenger Suite:
1. Synthetic Negative Fixtures:
   - Circular dependency cycles (direct, 3-node, self-loop, complex graphs, real ES6 imports on disk)
   - Injected external CDN scripts/styles (cdnjs, jsdelivr, unpkg, googleapis, protocol-relative)
   - Injected remote HTTP/HTTPS network calls in JS runtime
   - Broken local script path references in HTML
   - Missing module directories (modules root, entities, render)
   - Missing required component files within module directories
   - Modular boundary violations (assets -> render, entities -> render loop, simulation -> mesh, audio -> render)
2. Genuine Codebase Invariant Audits:
   - 100% Zero-CDN scan across all .html, .js, .css files in web/ and assets/
   - Resolution verification for all local script tags in all HTML spectator/viewer files
3. CLI flags and return code contract validations.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

import pytest

from scripts.verify_modular_architecture import (
    ModularArchitectureVerifier,
)

ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. ADVERSARIAL CIRCULAR DEPENDENCY CYCLE DETECTION
# ==============================================================================

def test_adversarial_direct_cycle_2_nodes():
    """Verify detection of a direct 2-node cycle: A -> B -> A."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    graph: Dict[str, Set[str]] = {
        "web/modules/render/RenderEngine.js": {"web/modules/assets/AssetLoader.js"},
        "web/modules/assets/AssetLoader.js": {"web/modules/render/RenderEngine.js"},
    }
    passed, cycles, violations = verifier.detect_circular_dependencies(graph)
    assert passed is False
    assert len(cycles) >= 1
    assert len(violations) >= 1
    assert violations[0].rule_id == "CIRCULAR_DEPENDENCY"
    assert "web/modules/render/RenderEngine.js" in violations[0].detail
    assert "web/modules/assets/AssetLoader.js" in violations[0].detail


def test_adversarial_self_referential_cycle():
    """Verify detection of self-referential cycle: A -> A."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    graph: Dict[str, Set[str]] = {
        "web/modules/entities/CreatureController.js": {
            "web/modules/entities/CreatureController.js"
        },
    }
    passed, cycles, violations = verifier.detect_circular_dependencies(graph)
    assert passed is False
    assert len(cycles) == 1
    assert violations[0].rule_id == "CIRCULAR_DEPENDENCY"


def test_adversarial_complex_multi_branch_cycle():
    """Verify detection when cycle is buried in a multi-branch acyclic graph."""
    verifier = ModularArchitectureVerifier(root_dir=ROOT)
    # Graph:
    # A -> B -> C -> D -> E (acyclic line)
    # F -> G -> H -> F      (cyclic triangle)
    # D -> G                 (bridge to cycle)
    graph: Dict[str, Set[str]] = {
        "node_a.js": {"node_b.js"},
        "node_b.js": {"node_c.js"},
        "node_c.js": {"node_d.js"},
        "node_d.js": {"node_e.js", "node_g.js"},
        "node_e.js": set(),
        "node_f.js": {"node_g.js"},
        "node_g.js": {"node_h.js"},
        "node_h.js": {"node_f.js"},
    }
    passed, cycles, violations = verifier.detect_circular_dependencies(graph)
    assert passed is False
    assert len(cycles) >= 1
    flat_cycle = [item for c in cycles for item in c]
    assert "node_f.js" in flat_cycle
    assert "node_g.js" in flat_cycle
    assert "node_h.js" in flat_cycle
    # A and B must NOT be part of the cycle path
    assert "node_a.js" not in flat_cycle


def test_adversarial_real_filesystem_es6_import_cycle(tmp_path: Path):
    """Stress-test: create real files on disk with genuine ES6 cyclic imports and verify verifier."""
    fake_modules = tmp_path / "web" / "modules"
    (fake_modules / "assets").mkdir(parents=True)
    (fake_modules / "render").mkdir(parents=True)

    file_a = fake_modules / "assets" / "AssetLoader.js"
    file_b = fake_modules / "render" / "RenderEngine.js"

    file_a.write_text(
        "import { RenderEngine } from '../render/RenderEngine.js';\nexport class AssetLoader {}",
        encoding="utf-8"
    )
    file_b.write_text(
        "import { AssetLoader } from '../assets/AssetLoader.js';\nexport class RenderEngine {}",
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    graph = verifier.build_module_dependency_graph()

    # Graph must have resolved the relative paths accurately
    rel_a = "web/modules/assets/AssetLoader.js"
    rel_b = "web/modules/render/RenderEngine.js"
    assert rel_a in graph
    assert rel_b in graph
    assert rel_b in graph[rel_a]
    assert rel_a in graph[rel_b]

    passed, cycles, violations = verifier.detect_circular_dependencies(graph)
    assert passed is False
    assert len(cycles) >= 1
    assert any(v.rule_id == "CIRCULAR_DEPENDENCY" for v in violations)


# ==============================================================================
# 2. ADVERSARIAL ZERO-CDN INVARIANT TESTS
# ==============================================================================

@pytest.mark.parametrize("cdn_url", [
    "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js",
    "https://unpkg.com/three@0.128.0/build/three.js",
    "//cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js",
    "http://code.jquery.com/jquery-3.6.0.min.js",
    "https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js",
])
def test_adversarial_injected_cdn_scripts_in_html(tmp_path: Path, cdn_url: str):
    """Verify any forbidden external CDN in HTML script tags fails immediately."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    html_file = fake_web / "index.html"
    html_file.write_text(f'<html><head><script src="{cdn_url}"></script></head></html>', encoding="utf-8")

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "ZERO_CDN_HTML_SCRIPT" for v in violations)


@pytest.mark.parametrize("link_url", [
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    "//cdn.jsdelivr.net/npm/normalize.css@8.0.1/normalize.css",
])
def test_adversarial_injected_cdn_links_in_html(tmp_path: Path, link_url: str):
    """Verify any forbidden external stylesheet / font CDN link fails immediately."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    html_file = fake_web / "index.html"
    html_file.write_text(f'<html><head><link rel="stylesheet" href="{link_url}"></head></html>', encoding="utf-8")

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "ZERO_CDN_HTML_LINK" for v in violations)


def test_adversarial_injected_cdn_in_javascript(tmp_path: Path):
    """Verify forbidden CDN domains referenced in runtime JS fail immediately."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    js_file = fake_web / "telemetry_addon.js"
    js_file.write_text(
        'const THREE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";',
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "ZERO_CDN_JS_REFERENCE" for v in violations)


def test_adversarial_injected_remote_http_url_in_javascript(tmp_path: Path):
    """Verify unauthorized external HTTP/HTTPS network calls in JS runtime fail."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    js_file = fake_web / "analytics.js"
    js_file.write_text(
        'fetch("https://external-telemetry-collector.io/api/v1/ping");',
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "ZERO_CDN_REMOTE_URL" for v in violations)


def test_adversarial_broken_local_script_reference(tmp_path: Path):
    """Verify non-existent local script target in HTML generates BROKEN_LOCAL_SCRIPT."""
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    html_file = fake_web / "spectate.html"
    html_file.write_text('<script src="modules/missing_controller.js"></script>', encoding="utf-8")

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_zero_cdn_offline_invariant()
    assert passed is False
    assert any(v.rule_id == "BROKEN_LOCAL_SCRIPT" for v in violations)


# ==============================================================================
# 3. ADVERSARIAL STRUCTURAL & MODULAR VIOLATIONS
# ==============================================================================

def test_adversarial_missing_modules_root(tmp_path: Path):
    """Verify missing web/modules directory triggers DIR_MODULES_ROOT."""
    (tmp_path / "web").mkdir(parents=True)
    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, modules_info, violations = verifier.verify_physical_separation()
    assert passed is False
    assert any(v.rule_id == "DIR_MODULES_ROOT" for v in violations)


def test_adversarial_missing_module_folder(tmp_path: Path):
    """Verify missing one required module directory (e.g. entities/) triggers failure."""
    fake_modules = tmp_path / "web" / "modules"
    for mod in ["assets", "render", "simulation", "audio"]:
        (fake_modules / mod).mkdir(parents=True)
        # Create dummy expected files
        for f in ModularArchitectureVerifier.EXPECTED_MODULE_STRUCTURE[mod]:
            (fake_modules / mod / f).write_text("// stub", encoding="utf-8")
    # 'entities' is intentionally omitted

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, modules_info, violations = verifier.verify_physical_separation()
    assert passed is False
    assert any(v.rule_id == "DIR_MISSING_ENTITIES" for v in violations)


def test_adversarial_missing_component_in_existing_module(tmp_path: Path):
    """Verify missing a required file inside an existing module directory triggers failure."""
    fake_modules = tmp_path / "web" / "modules"
    for mod, files in ModularArchitectureVerifier.EXPECTED_MODULE_STRUCTURE.items():
        (fake_modules / mod).mkdir(parents=True)
        for f in files:
            (fake_modules / mod / f).write_text("// stub", encoding="utf-8")

    # Delete RenderEngine.js from render/
    (fake_modules / "render" / "RenderEngine.js").unlink()

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, modules_info, violations = verifier.verify_physical_separation()
    assert passed is False
    assert any(v.rule_id == "FILE_MISSING_RENDER" for v in violations)
    assert any("RenderEngine.js" in v.file_path for v in violations)


# ==============================================================================
# 4. ADVERSARIAL BOUNDARY DECOUPLING VIOLATIONS
# ==============================================================================

def test_adversarial_boundary_assets_calling_render_engine(tmp_path: Path):
    """Verify Assets module referencing RenderEngine triggers BOUNDARY_ASSETS_RENDER."""
    fake_modules = tmp_path / "web" / "modules" / "assets"
    fake_modules.mkdir(parents=True)
    loader_file = fake_modules / "AssetLoader.js"
    loader_file.write_text(
        "class AssetLoader {\n  hook(re) { RenderEngine.instance.sync(); }\n}",
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_modular_boundaries()
    assert passed is False
    assert any(v.rule_id == "BOUNDARY_ASSETS_RENDER" for v in violations)
    assert any(v.line_number == 2 for v in violations)


def test_adversarial_boundary_entities_calling_render_loop(tmp_path: Path):
    """Verify Entities module driving render loop triggers BOUNDARY_ENTITIES_LOOP."""
    fake_modules = tmp_path / "web" / "modules" / "entities"
    fake_modules.mkdir(parents=True)
    ctrl_file = fake_modules / "CreatureController.js"
    ctrl_file.write_text(
        "class CreatureController {\n  loop() { requestAnimationFrame(this.loop); }\n}",
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_modular_boundaries()
    assert passed is False
    assert any(v.rule_id == "BOUNDARY_ENTITIES_LOOP" for v in violations)


def test_adversarial_boundary_simulation_coupling_mesh(tmp_path: Path):
    """Verify Simulation module coupling to Three.js Mesh triggers BOUNDARY_SIMULATION_VISUALS."""
    fake_modules = tmp_path / "web" / "modules" / "simulation"
    fake_modules.mkdir(parents=True)
    telemetry_file = fake_modules / "TelemetryClient.js"
    telemetry_file.write_text(
        "class TelemetryClient {\n  make() { const m = new THREE.Mesh(); }\n}",
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_modular_boundaries()
    assert passed is False
    assert any(v.rule_id == "BOUNDARY_SIMULATION_VISUALS" for v in violations)


def test_adversarial_boundary_audio_coupling_webgl(tmp_path: Path):
    """Verify Audio module coupling to WebGLRenderer triggers BOUNDARY_AUDIO_RENDER."""
    fake_modules = tmp_path / "web" / "modules" / "audio"
    fake_modules.mkdir(parents=True)
    audio_file = fake_modules / "AudioSynthesizer.js"
    audio_file.write_text(
        "class AudioSynthesizer {\n  bind(gl) { WebGLRenderer.attach(); }\n}",
        encoding="utf-8"
    )

    verifier = ModularArchitectureVerifier(root_dir=tmp_path)
    passed, violations = verifier.verify_modular_boundaries()
    assert passed is False
    assert any(v.rule_id == "BOUNDARY_AUDIO_RENDER" for v in violations)


# ==============================================================================
# 5. GENUINE CODEBASE EXHAUSTIVE ZERO-CDN & LOCAL ASSET RESOLUTION AUDIT
# ==============================================================================

def test_genuine_codebase_exhaustive_zero_cdn_scan():
    """Independent empirical challenger scan: 100% Zero-CDN across all html, js, css in web/ & assets/."""
    cdn_patterns = [
        re.compile(r"cdnjs\.cloudflare\.com", re.I),
        re.compile(r"cdn\.jsdelivr\.net", re.I),
        re.compile(r"unpkg\.com", re.I),
        re.compile(r"fonts\.googleapis\.com", re.I),
        re.compile(r"ajax\.googleapis\.com", re.I),
        re.compile(r"code\.jquery\.com", re.I),
    ]

    target_extensions = {".html", ".js", ".css"}
    all_files: List[Path] = []
    for base in ["web", "assets"]:
        base_path = ROOT / base
        if base_path.is_dir():
            all_files.extend(
                f
                for f in base_path.rglob("*")
                if f.is_file() and f.suffix.lower() in target_extensions
            )

    assert len(all_files) >= 35, f"Expected >= 35 web/asset runtime files, found {len(all_files)}"

    violations = []
    for f in all_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        rel = f.relative_to(ROOT).as_posix()

        # 1. Assert zero forbidden CDN matches anywhere
        violations.extend(
            f"Forbidden CDN domain pattern '{pat.pattern}' found in {rel}"
            for pat in cdn_patterns
            if pat.search(content)
        )

        # 2. HTML script/link tags must NOT have remote protocols
        if f.suffix.lower() == ".html":
            script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content, re.I)
            for s in script_srcs:
                if s.startswith(("http://", "https://", "//")):
                    violations.append(f"Remote script src in {rel}: {s}")
                else:
                    # Verify target exists locally
                    p1 = f.parent / s
                    p2 = ROOT / s.lstrip("/")
                    p3 = ROOT / "web" / s.lstrip("/")
                    if not (p1.exists() or p2.exists() or p3.exists()):
                        violations.append(f"Unresolvable local script in {rel}: {s}")

            link_hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content, re.I)
            violations.extend(
                f"Remote link href in {rel}: {h}"
                for h in link_hrefs
                if h.startswith(("http://", "https://", "//"))
            )

        # 3. Non-vendor JS must NOT contain unauthorized remote HTTP(S) calls
        if f.suffix.lower() == ".js" and "vendor" not in rel:
            for line_idx, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith(("//", "/*", "*")):
                    continue
                safe_allowlist = [
                    "127.0.0.1", "localhost", "ws://", "wss://",
                    "w3.org", "json-schema.org", "khronos.org",
                    "openstreetmap.org", "apple.com"
                ]
                if any(allow in stripped for allow in safe_allowlist):
                    continue
                if re.search(r"https?://", stripped):
                    violations.append(f"Unauthorized remote URL in {rel}:{line_idx} -> {stripped}")

    assert len(violations) == 0, "Zero-CDN invariant violations detected:\n" + "\n".join(violations)


def test_cli_execution_adversarial_failure(tmp_path: Path):
    """Verify CLI returns exit code 1 when architectural violations exist."""
    # Create invalid workspace with missing modules and CDN injection
    fake_web = tmp_path / "web"
    fake_web.mkdir(parents=True)
    fake_html = fake_web / "index.html"
    fake_html.write_text(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>',
        encoding="utf-8"
    )

    script_path = ROOT / "scripts" / "verify_modular_architecture.py"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(script_path), "--root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 1, f"Expected returncode 1, got {proc.returncode}"
    data = json.loads(proc.stdout)
    assert data["status"] == "FAIL"
    assert data["success"] is False
    assert data["summary"]["total_violations"] >= 2
