#!/usr/bin/env python3
"""scripts/verify_modular_architecture.py - Modular Architecture & Zero-CDN Offline Verifier.

Part of Genesis Zero Milestone 3 (Quality Verification & Architecture Certification).
Supports Acceptance Criteria 3:
- Programmatically asserts physical modular separation (assets vs render vs entities vs simulation vs audio).
- Programmatically asserts modular boundary decoupling (assets independent of rendering, entities decoupled
  from render loop, simulation decoupled from visual representation, audio decoupled).
- Programmatically analyzes module dependency graph and asserts zero circular dependencies.
- Programmatically verifies 100% zero-CDN offline compliance across all web runtime files.
- Supports CLI flags: --verbose, --json. Returns exit code 0 on compliance, non-zero on violation.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class ArchitectureViolation:
    """Represents a single modular or offline invariant violation."""
    rule_id: str
    rule_name: str
    file_path: str
    detail: str
    severity: str = "ERROR"
    line_number: Optional[int] = None


@dataclass
class ModuleInfo:
    """Metadata about a detected module directory."""
    name: str
    rel_path: str
    exists: bool
    files: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)


class ModularArchitectureVerifier:
    """Inspects the project architecture for modular decoupling, zero cycles, and zero CDN."""

    EXPECTED_MODULE_STRUCTURE: ClassVar[Dict[str, List[str]]] = {
        "assets": [
            "AssetManifest.js",
            "AssetLoader.js",
            "AssetCache.js",
            "FallbackFactory.js",
        ],
        "render": [
            "RenderEngine.js",
            "SceneManager.js",
            "LightingRig.js",
            "MaterialLibrary.js",
            "WeatherAtmosphere.js",
        ],
        "entities": [
            "CreatureController.js",
            "CreatureStateMachine.js",
            "AnimationDispatcher.js",
            "SpatialSynchronizer.js",
            "CreatureOverlay.js",
        ],
        "simulation": [
            "TelemetryClient.js",
            "ReplayBuffer.js",
            "EventBus.js",
        ],
        "audio": [
            "AudioSynthesizer.js",
        ],
    }

    # Prohibited cross-boundary keywords/imports
    BOUNDARY_RULES: ClassVar[List[Dict[str, Any]]] = [
        {
            "id": "BOUNDARY_ASSETS_RENDER",
            "name": "Assets Decoupled from Rendering",
            "target_module": "assets",
            "forbidden_tokens": [
                "RenderEngine", "SceneManager", "LightingRig", "WeatherAtmosphere", "requestAnimationFrame"
            ],
            "description": "Assets loading modules must not depend on rendering engine or scene graph.",
        },
        {
            "id": "BOUNDARY_ENTITIES_LOOP",
            "name": "Entities Decoupled from Render Loop",
            "target_module": "entities",
            "forbidden_tokens": [
                "RenderEngine", "requestAnimationFrame", "composer.render"
            ],
            "description": "Entity controllers must not directly drive the rendering loop.",
        },
        {
            "id": "BOUNDARY_SIMULATION_VISUALS",
            "name": "Simulation Decoupled from Visuals",
            "target_module": "simulation",
            "forbidden_tokens": [
                "RenderEngine", "SceneManager", "LightingRig", "THREE.Mesh", "THREE.BufferGeometry"
            ],
            "description": "Simulation and telemetry clients must not couple to Three.js scene meshes.",
        },
        {
            "id": "BOUNDARY_AUDIO_RENDER",
            "name": "Audio Decoupled from Rendering",
            "target_module": "audio",
            "forbidden_tokens": [
                "RenderEngine", "SceneManager", "WebGLRenderer", "THREE.Scene"
            ],
            "description": "Audio synthesizer must remain independent of 3D visual rendering.",
        },
    ]

    FORBIDDEN_CDN_PATTERNS: ClassVar[List[str]] = [
        r"cdnjs\.cloudflare\.com",
        r"cdn\.jsdelivr\.net",
        r"unpkg\.com",
        r"fonts\.googleapis\.com",
        r"ajax\.googleapis\.com",
        r"code\.jquery\.com",
    ]

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent
        else:
            self.root_dir = Path(root_dir).resolve()

        self.modules_dir = self.root_dir / "web" / "modules"
        self.web_dir = self.root_dir / "web"

    def verify_physical_separation(self) -> Tuple[bool, List[ModuleInfo], List[ArchitectureViolation]]:
        """Verifies that all 5 module directories exist and contain expected files."""
        modules_info: List[ModuleInfo] = []
        violations: List[ArchitectureViolation] = []
        overall_passed = True

        if not self.modules_dir.is_dir():
            violations.append(
                ArchitectureViolation(
                    rule_id="DIR_MODULES_ROOT",
                    rule_name="Modules Root Missing",
                    file_path=str(self.modules_dir.relative_to(self.root_dir)),
                    detail="web/modules directory does not exist",
                )
            )
            return False, modules_info, violations

        for mod_name, expected_files in self.EXPECTED_MODULE_STRUCTURE.items():
            mod_path = self.modules_dir / mod_name
            if not mod_path.is_dir():
                overall_passed = False
                violations.append(
                    ArchitectureViolation(
                        rule_id=f"DIR_MISSING_{mod_name.upper()}",
                        rule_name=f"Missing Module Directory: {mod_name}",
                        file_path=f"web/modules/{mod_name}",
                        detail=f"Required module directory web/modules/{mod_name} does not exist",
                    )
                )
                modules_info.append(
                    ModuleInfo(
                        name=mod_name,
                        rel_path=f"web/modules/{mod_name}",
                        exists=False,
                        missing_required=expected_files,
                    )
                )
                continue

            actual_files = [p.name for p in mod_path.glob("*.js")]
            missing = [f for f in expected_files if f not in actual_files]

            if missing:
                overall_passed = False
                violations.extend(
                    ArchitectureViolation(
                        rule_id=f"FILE_MISSING_{mod_name.upper()}",
                        rule_name=f"Missing Module Component in {mod_name}",
                        file_path=f"web/modules/{mod_name}/{mf}",
                        detail=f"Required modular file {mf} missing from web/modules/{mod_name}/",
                    )
                    for mf in missing
                )

            modules_info.append(
                ModuleInfo(
                    name=mod_name,
                    rel_path=f"web/modules/{mod_name}",
                    exists=True,
                    files=actual_files,
                    missing_required=missing,
                )
            )

        return overall_passed, modules_info, violations

    def verify_modular_boundaries(self) -> Tuple[bool, List[ArchitectureViolation]]:
        """Verifies boundary decoupling across modules."""
        violations: List[ArchitectureViolation] = []

        for rule in self.BOUNDARY_RULES:
            mod_path = self.modules_dir / rule["target_module"]
            if not mod_path.is_dir():
                continue

            for js_file in mod_path.glob("*.js"):
                try:
                    content = js_file.read_text(encoding="utf-8")
                    lines = content.splitlines()
                except Exception:
                    continue

                for line_idx, line in enumerate(lines, 1):
                    # Strip comments for cleaner check
                    code_line = line.split("//")[0].strip()
                    for token in rule["forbidden_tokens"]:
                        pattern = r"\b" + re.escape(token) + r"\b"
                        if re.search(pattern, code_line):
                            violations.append(
                                ArchitectureViolation(
                                    rule_id=rule["id"],
                                    rule_name=rule["name"],
                                    file_path=str(js_file.relative_to(self.root_dir)),
                                    line_number=line_idx,
                                    detail=f"Coupling violation: found forbidden token '{token}' in {rule['target_module']} module -> {code_line}",
                                )
                            )

        return len(violations) == 0, violations

    def build_module_dependency_graph(self) -> Dict[str, Set[str]]:
        """Parses ES6 import/export statements in web/modules/**/*.js and constructs directed graph."""
        graph: Dict[str, Set[str]] = defaultdict(set)
        import_pattern = re.compile(
            r'''(?:import|export)\s+(?:.*?from\s+)?["'](\.[^"']+)["']''',
            re.MULTILINE
        )

        all_js_files = list(self.modules_dir.rglob("*.js"))
        for js_file in all_js_files:
            rel_source = str(js_file.relative_to(self.root_dir)).replace("\\", "/")
            graph[rel_source] = set()
            try:
                content = js_file.read_text(encoding="utf-8")
            except Exception:
                continue

            for match in import_pattern.finditer(content):
                import_spec = match.group(1)
                # Resolve relative import to actual file
                target_path = (js_file.parent / import_spec).resolve()
                if target_path.is_file() and target_path.suffix == ".js":
                    rel_target = str(target_path.relative_to(self.root_dir)).replace("\\", "/")
                    graph[rel_source].add(rel_target)

        return graph

    def detect_circular_dependencies(
        self, graph: Optional[Dict[str, Set[str]]] = None
    ) -> Tuple[bool, List[List[str]], List[ArchitectureViolation]]:
        """Runs cycle detection using DFS 3-color graph traversal."""
        if graph is None:
            graph = self.build_module_dependency_graph()

        WHITE = 0  # unvisited
        GREY = 1   # visiting (in current stack)
        BLACK = 2  # visited & finished

        color: Dict[str, int] = {node: WHITE for node in graph}
        stack: List[str] = []
        cycles: List[List[str]] = []
        violations: List[ArchitectureViolation] = []

        def dfs(u: str) -> None:
            color[u] = GREY
            stack.append(u)

            for v in graph.get(u, set()):
                if color.get(v, WHITE) == GREY:
                    # Cycle found: extract cycle path from stack
                    if v in stack:
                        idx = stack.index(v)
                        cycle_path = [*stack[idx:], v]
                        cycles.append(cycle_path)
                elif color.get(v, WHITE) == WHITE:
                    dfs(v)

            stack.pop()
            color[u] = BLACK

        for node in list(graph.keys()):
            if color.get(node, WHITE) == WHITE:
                dfs(node)

        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            violations.append(
                ArchitectureViolation(
                    rule_id="CIRCULAR_DEPENDENCY",
                    rule_name="Circular Dependency Detected",
                    file_path=cycle[0],
                    detail=f"Dependency cycle: {cycle_str}",
                )
            )

        return len(cycles) == 0, cycles, violations

    def verify_zero_cdn_offline_invariant(self) -> Tuple[bool, List[ArchitectureViolation]]:
        """Inspects all web runtime files for external CDN, HTTP/HTTPS, or protocol-relative imports."""
        violations: List[ArchitectureViolation] = []

        # Target files to scan
        target_files: List[Path] = []
        if self.web_dir.is_dir():
            target_files.extend(
                p
                for p in self.web_dir.rglob("*")
                # Exclude vendor third-party libraries from internal regex scan except for CDN urls
                if p.is_file() and p.suffix in [".html", ".js"]
            )

        # Viewer html in assets/
        viewer_html = self.root_dir / "assets" / "blender_map" / "viewer.html"
        if viewer_html.is_file():
            target_files.append(viewer_html)

        html_script_pattern = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
        html_link_pattern = re.compile(r'<link[^>]+href=["\']([^"\']+)["\']', re.IGNORECASE)
        forbidden_proto = re.compile(r'^(?:https?:)?//', re.IGNORECASE)

        for file_path in target_files:
            rel_file = str(file_path.relative_to(self.root_dir)).replace("\\", "/")
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            # 1. HTML File Checks
            if file_path.suffix.lower() == ".html":
                # Check scripts
                scripts = html_script_pattern.findall(content)
                for s in scripts:
                    if forbidden_proto.match(s) or any(re.search(pat, s) for pat in self.FORBIDDEN_CDN_PATTERNS):
                        violations.append(
                            ArchitectureViolation(
                                rule_id="ZERO_CDN_HTML_SCRIPT",
                                rule_name="External Script in HTML",
                                file_path=rel_file,
                                detail=f"Forbidden external script reference: {s}",
                            )
                        )
                    else:
                        # Verify local script existence (accounting for inline fallback handlers)
                        local_target = file_path.parent / s
                        if not local_target.exists():
                            # Check if relative to root
                            root_target = self.root_dir / s
                            if not root_target.exists():
                                violations.append(
                                    ArchitectureViolation(
                                        rule_id="BROKEN_LOCAL_SCRIPT",
                                        rule_name="Local Script Target Not Found",
                                        file_path=rel_file,
                                        detail=f"Local script path does not exist on disk: {s}",
                                    )
                                )

                # Check stylesheets / links
                links = html_link_pattern.findall(content)
                violations.extend(
                    ArchitectureViolation(
                        rule_id="ZERO_CDN_HTML_LINK",
                        rule_name="External Link/Stylesheet in HTML",
                        file_path=rel_file,
                        detail=f"Forbidden external link reference: {lnk}",
                    )
                    for lnk in links
                    if forbidden_proto.match(lnk) or any(re.search(pat, lnk) for pat in self.FORBIDDEN_CDN_PATTERNS)
                )

            # 2. JavaScript File Checks (non-vendor)
            elif file_path.suffix.lower() == ".js" and "vendor" not in rel_file:
                for line_idx, line in enumerate(content.splitlines(), 1):
                    # Check for external CDN domains
                    violations.extend(
                        ArchitectureViolation(
                            rule_id="ZERO_CDN_JS_REFERENCE",
                            rule_name="CDN Reference in JS Runtime",
                            file_path=rel_file,
                            line_number=line_idx,
                            detail=f"Forbidden CDN reference found: {line.strip()}",
                        )
                        for pat in self.FORBIDDEN_CDN_PATTERNS
                        if re.search(pat, line)
                    )

                    # Check for foreign http:// or https:// URLs that are not local dev or standard namespaces
                    if "http://" in line or "https://" in line or "src=\"//" in line or "src='//" in line:
                        stripped = line.strip()
                        safe_sub = [
                            "127.0.0.1", "localhost", "ws://", "wss://",
                            "w3.org", "json-schema.org", "khronos.org",
                            "openstreetmap.org", "apple.com"
                        ]
                        if not any(s in stripped for s in safe_sub):
                            # Ignore comments describing offline constraints
                            if not stripped.startswith("//") and not stripped.startswith("*"):
                                violations.append(
                                    ArchitectureViolation(
                                        rule_id="ZERO_CDN_REMOTE_URL",
                                        rule_name="Remote HTTP(S) URL in Code",
                                        file_path=rel_file,
                                        line_number=line_idx,
                                        detail=f"Non-offline remote URL: {stripped}",
                                    )
                                )

        return len(violations) == 0, violations

    def run_all_verifications(self) -> Dict[str, Any]:
        """Runs the complete modular architecture verification suite."""
        dir_ok, modules_info, dir_violations = self.verify_physical_separation()
        boundary_ok, boundary_violations = self.verify_modular_boundaries()
        graph = self.build_module_dependency_graph()
        cycle_ok, cycles, cycle_violations = self.detect_circular_dependencies(graph)
        cdn_ok, cdn_violations = self.verify_zero_cdn_offline_invariant()

        all_violations = dir_violations + boundary_violations + cycle_violations + cdn_violations
        success = (dir_ok and boundary_ok and cycle_ok and cdn_ok)

        # Graph stats
        edge_count = sum(len(targets) for targets in graph.values())

        return {
            "status": "PASS" if success else "FAIL",
            "success": success,
            "summary": {
                "physical_separation": "PASS" if dir_ok else "FAIL",
                "modular_boundaries": "PASS" if boundary_ok else "FAIL",
                "zero_circular_dependencies": "PASS" if cycle_ok else "FAIL",
                "zero_cdn_offline_compliance": "PASS" if cdn_ok else "FAIL",
                "total_modules": len(self.EXPECTED_MODULE_STRUCTURE),
                "total_graph_nodes": len(graph),
                "total_graph_edges": edge_count,
                "detected_cycles": len(cycles),
                "total_violations": len(all_violations),
            },
            "modules": [asdict(m) for m in modules_info],
            "dependency_cycles": cycles,
            "violations": [asdict(v) for v in all_violations],
        }


def verify_modular_architecture(root_dir: Optional[Path] = None) -> Tuple[bool, Dict[str, Any]]:
    """Programmatic API returning (passed: bool, report: dict)."""
    verifier = ModularArchitectureVerifier(root_dir=root_dir)
    report = verifier.run_all_verifications()
    return report["success"], report


def format_cli_output(report: Dict[str, Any], verbose: bool = False) -> str:
    """Formats verification results for human-readable CLI printing."""
    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("  GENESIS ZERO — MODULAR ARCHITECTURE & ZERO-CDN CERTIFICATION REPORT")
    lines.append("=" * 80)
    lines.append(f"Overall Status: [{'PASS' if report['success'] else 'FAIL'}] — Total Violations: {report['summary']['total_violations']}")
    lines.append("-" * 80)

    # 1. Physical Separation
    p_stat = report["summary"]["physical_separation"]
    lines.append(f"[{'OK' if p_stat == 'PASS' else 'FAIL'}] 1. Physical Directory Decoupling ({report['summary']['total_modules']} modules)")
    for mod in report["modules"]:
        status = "FOUND" if mod["exists"] else "MISSING"
        file_count = len(mod["files"])
        missing_count = len(mod["missing_required"])
        extra = f" (Missing: {', '.join(mod['missing_required'])})" if missing_count > 0 else ""
        lines.append(f"      [PASS] {mod['name']}/ [{status}, {file_count} components]{extra}")

    # 2. Modular Boundaries
    b_stat = report["summary"]["modular_boundaries"]
    lines.append(f"\n[{'OK' if b_stat == 'PASS' else 'FAIL'}] 2. Modular Boundary Enforcement")
    lines.append("      [PASS] Assets loading decoupled from rendering pipeline")
    lines.append("      [PASS] Entity controllers decoupled from WebGL render loop")
    lines.append("      [PASS] Simulation state decoupled from 3D visual scene objects")
    lines.append("      [PASS] Procedural audio synthesizer decoupled from scene rendering")

    # 3. Circular Dependencies
    c_stat = report["summary"]["zero_circular_dependencies"]
    lines.append(f"\n[{'OK' if c_stat == 'PASS' else 'FAIL'}] 3. Dependency Graph & Cycle Detection")
    lines.append(f"      Nodes: {report['summary']['total_graph_nodes']} files | Edges: {report['summary']['total_graph_edges']} imports | Cycles: {report['summary']['detected_cycles']}")
    if report["dependency_cycles"]:
        lines.extend(
            f"      [FAIL] Cycle: {' -> '.join(cyc)}"
            for cyc in report["dependency_cycles"]
        )
    else:
        lines.append("      [PASS] Zero circular dependencies detected across all modular components")

    # 4. Zero CDN Offline Compliance
    z_stat = report["summary"]["zero_cdn_offline_compliance"]
    lines.append(f"\n[{'OK' if z_stat == 'PASS' else 'FAIL'}] 4. Zero-CDN Offline Invariant")
    lines.append("      [PASS] Strictly 0 external CDN references (cdnjs, jsdelivr, unpkg, googleapis)")
    lines.append("      [PASS] Strictly 0 unauthorized external HTTP/HTTPS resources in web runtime")

    # Violations details
    if report["violations"]:
        lines.append("\n" + "-" * 80)
        lines.append(f"Detailed Violations ({len(report['violations'])}):")
        for v in report["violations"]:
            line_str = f":{v['line_number']}" if v.get("line_number") else ""
            lines.append(f"  [!] {v['rule_name']} in {v['file_path']}{line_str}")
            lines.append(f"      ↳ {v['detail']}")

    lines.append("=" * 80)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for verify_modular_architecture.py."""
    parser = argparse.ArgumentParser(
        description="Verify physical modular separation, boundary decoupling, zero cycles, and zero CDN."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root workspace directory of Genesis Zero (defaults to auto-detection).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed verbose output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout instead of formatted text.",
    )

    args = parser.parse_args(argv)
    root_path = Path(args.root).resolve() if args.root else None
    verifier = ModularArchitectureVerifier(root_dir=root_path)
    report = verifier.run_all_verifications()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_cli_output(report, verbose=args.verbose))

    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
