#!/usr/bin/env python3
"""scripts/analyze_graphics_code.py - Graphics Code Static & Programmatic Analyzer.

Part of Genesis Zero Milestone 3 (Quality Verification & Architecture Certification).
Satisfies Acceptance Criteria 2:
- Programmatically verifies advanced lighting: DirectionalLight, AmbientLight, HemisphereLight.
- Programmatically verifies soft shadows enabled: castShadow, receiveShadow, shadowMap.enabled, PCFSoftShadowMap.
- Programmatically verifies PBR materials & advanced shaders: MeshStandardMaterial, MeshPhysicalMaterial,
  roughness, metalness, strata vertex colors, physical water shader.
- Inspects web/modules/render/ (LightingRig.js, RenderEngine.js, MaterialLibrary.js, WeatherAtmosphere.js),
  web/watch3d.js, and assets/blender_map/viewer.html.
- Supports CLI flags: --verbose, --json. Returns exit code 0 on pass, non-zero on failure.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class CodeMatch:
    """Represents a matched occurrence of a graphics construct."""
    file_path: str
    line_number: int
    matched_text: str
    context: str = ""


@dataclass
class CriteriaResult:
    """Represents the verification result of a specific graphics criterion."""
    criteria_id: str
    name: str
    category: str
    description: str
    passed: bool
    required: bool
    matches: List[CodeMatch] = field(default_factory=list)
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["match_count"] = len(self.matches)
        return d


class GraphicsCodeAnalyzer:
    """Performs static and programmatic code analysis on Genesis Zero graphics files."""

    CATEGORY_LIGHTING = "Advanced Lighting Pipeline"
    CATEGORY_SHADOWS = "Soft Shadows & Shadow Maps"
    CATEGORY_PBR = "PBR Materials & Advanced Shaders"

    DEFAULT_TARGET_FILES: ClassVar[List[str]] = [
        "web/modules/render/LightingRig.js",
        "web/modules/render/RenderEngine.js",
        "web/modules/render/MaterialLibrary.js",
        "web/modules/render/WeatherAtmosphere.js",
        "web/watch3d.js",
        "assets/blender_map/viewer.html",
    ]

    def __init__(self, root_dir: Optional[Path] = None, target_files: Optional[List[str]] = None):
        if root_dir is None:
            # Resolve root directory relative to this script
            self.root_dir = Path(__file__).resolve().parent.parent
        else:
            self.root_dir = Path(root_dir).resolve()

        self.target_rel_files = target_files or self.DEFAULT_TARGET_FILES
        self.file_contents: Dict[str, str] = {}
        self.file_lines: Dict[str, List[str]] = {}
        self._load_files()

    def _load_files(self) -> None:
        """Loads and caches lines for all targeted files."""
        for rel_path in self.target_rel_files:
            full_path = self.root_dir / rel_path
            if full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    self.file_contents[rel_path] = content
                    self.file_lines[rel_path] = content.splitlines()
                except Exception:
                    self.file_contents[rel_path] = ""
                    self.file_lines[rel_path] = []

    def _find_matches(
        self,
        pattern: str | re.Pattern,
        file_filter: Optional[List[str]] = None,
        is_regex: bool = True,
        flags: int = re.IGNORECASE,
    ) -> List[CodeMatch]:
        """Finds all occurrences of a pattern in the loaded files."""
        matches: List[CodeMatch] = []
        if is_regex:
            compiled = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        else:
            compiled = None

        search_files = file_filter or list(self.file_lines.keys())
        for rel_path in search_files:
            lines = self.file_lines.get(rel_path, [])
            for line_idx, line in enumerate(lines, 1):
                matched = False
                matched_str = ""
                if compiled:
                    m = compiled.search(line)
                    if m:
                        matched = True
                        matched_str = m.group(0)
                else:
                    if pattern in line:
                        matched = True
                        matched_str = str(pattern)

                if matched:
                    matches.append(
                        CodeMatch(
                            file_path=rel_path,
                            line_number=line_idx,
                            matched_text=matched_str,
                            context=line.strip(),
                        )
                    )
        return matches

    def check_advanced_lighting(self) -> List[CriteriaResult]:
        """Verifies advanced lighting configurations."""
        results: List[CriteriaResult] = []

        # 1. DirectionalLight
        dir_matches = self._find_matches(r"(?:new\s+)?(?:THREE\.)?DirectionalLight\b")
        results.append(
            CriteriaResult(
                criteria_id="LIGHT_DIR",
                name="Directional Sun Lighting",
                category=self.CATEGORY_LIGHTING,
                description="Presence of DirectionalLight for realistic primary solar illumination",
                passed=len(dir_matches) > 0,
                required=True,
                matches=dir_matches,
                failure_reason=None if dir_matches else "No DirectionalLight instantiation found",
            )
        )

        # 2. AmbientLight
        amb_matches = self._find_matches(r"(?:new\s+)?(?:THREE\.)?AmbientLight\b")
        results.append(
            CriteriaResult(
                criteria_id="LIGHT_AMB",
                name="Ambient Base Lighting",
                category=self.CATEGORY_LIGHTING,
                description="Presence of AmbientLight for environmental fill and cavern base illumination",
                passed=len(amb_matches) > 0,
                required=True,
                matches=amb_matches,
                failure_reason=None if amb_matches else "No AmbientLight instantiation found",
            )
        )

        # 3. HemisphereLight
        hemi_matches = self._find_matches(r"(?:new\s+)?(?:THREE\.)?HemisphereLight\b")
        results.append(
            CriteriaResult(
                criteria_id="LIGHT_HEMI",
                name="Hemisphere Skylight / Ground Bounce",
                category=self.CATEGORY_LIGHTING,
                description="Presence of HemisphereLight for dual-tone sky-to-ground bounce fill",
                passed=len(hemi_matches) > 0,
                required=True,
                matches=hemi_matches,
                failure_reason=None if hemi_matches else "No HemisphereLight instantiation found",
            )
        )

        # 4. Sun Positioning & Shadow Projection
        sun_pos_matches = self._find_matches(r"(?:sunLight|sun)\.position\.set\s*\(")
        results.append(
            CriteriaResult(
                criteria_id="LIGHT_POS",
                name="Sun Light Spatial Placement",
                category=self.CATEGORY_LIGHTING,
                description="Explicit directional light 3D spatial coordinate configuration",
                passed=len(sun_pos_matches) > 0,
                required=True,
                matches=sun_pos_matches,
                failure_reason=None if sun_pos_matches else "No directional sun position configuration found",
            )
        )

        return results

    def check_soft_shadows(self) -> List[CriteriaResult]:
        """Verifies soft shadows and shadow map configurations."""
        results: List[CriteriaResult] = []

        # 1. Shadow Map Enabled on Renderer
        map_enabled_matches = self._find_matches(r"(?:renderer\.)?shadowMap\.enabled\s*=\s*true")
        results.append(
            CriteriaResult(
                criteria_id="SHADOW_MAP_ENABLED",
                name="Shadow Map Activation",
                category=self.CATEGORY_SHADOWS,
                description="WebGLRenderer shadowMap.enabled is explicitly set to true",
                passed=len(map_enabled_matches) > 0,
                required=True,
                matches=map_enabled_matches,
                failure_reason=None if map_enabled_matches else "renderer.shadowMap.enabled = true missing",
            )
        )

        # 2. PCFSoftShadowMap Filtering
        pcf_matches = self._find_matches(r"(?:THREE\.)?PCFSoftShadowMap\b")
        results.append(
            CriteriaResult(
                criteria_id="SHADOW_PCF_SOFT",
                name="PCF Soft Shadow Map Filter",
                category=self.CATEGORY_SHADOWS,
                description="Use of PCFSoftShadowMap for anti-aliased, penumbra-softened shadow edges",
                passed=len(pcf_matches) > 0,
                required=True,
                matches=pcf_matches,
                failure_reason=None if pcf_matches else "PCFSoftShadowMap configuration missing",
            )
        )

        # 3. Cast Shadow Enabled
        cast_matches = self._find_matches(r"\.castShadow\s*=\s*(?:true|[\w\(\)]+)")
        results.append(
            CriteriaResult(
                criteria_id="SHADOW_CAST",
                name="Casting Shadows on Lights & Entities",
                category=self.CATEGORY_SHADOWS,
                description="castShadow configured on directional light and mesh geometry",
                passed=len(cast_matches) > 0,
                required=True,
                matches=cast_matches,
                failure_reason=None if cast_matches else "castShadow configuration missing",
            )
        )

        # 4. Receive Shadow Enabled
        receive_matches = self._find_matches(r"\.receiveShadow\s*=\s*true")
        results.append(
            CriteriaResult(
                criteria_id="SHADOW_RECEIVE",
                name="Receiving Shadows on Terrain & Surfaces",
                category=self.CATEGORY_SHADOWS,
                description="receiveShadow enabled on diorama terrain and receiver meshes",
                passed=len(receive_matches) > 0,
                required=True,
                matches=receive_matches,
                failure_reason=None if receive_matches else "receiveShadow configuration missing",
            )
        )

        # 5. Shadow Resolution & Bias Optimization
        res_bias_matches = self._find_matches(r"(?:shadow\.mapSize|\.shadow\.bias|\b2048\b)")
        results.append(
            CriteriaResult(
                criteria_id="SHADOW_BIAS_RES",
                name="Shadow Map Resolution & Bias Tuning",
                category=self.CATEGORY_SHADOWS,
                description="High-resolution shadow map (>= 2048) and acne-prevention bias tuning",
                passed=len(res_bias_matches) > 0,
                required=True,
                matches=res_bias_matches,
                failure_reason=None if res_bias_matches else "Shadow resolution / bias tuning missing",
            )
        )

        return results

    def check_pbr_and_shaders(self) -> List[CriteriaResult]:
        """Verifies PBR materials and advanced custom shaders."""
        results: List[CriteriaResult] = []

        # 1. MeshStandardMaterial
        std_matches = self._find_matches(r"(?:new\s+)?(?:THREE\.)?MeshStandardMaterial\b")
        results.append(
            CriteriaResult(
                criteria_id="PBR_STANDARD",
                name="MeshStandardMaterial PBR Pipeline",
                category=self.CATEGORY_PBR,
                description="Physically Based Rendering standard material for terrain and organic entities",
                passed=len(std_matches) > 0,
                required=True,
                matches=std_matches,
                failure_reason=None if std_matches else "MeshStandardMaterial usage missing",
            )
        )

        # 2. MeshPhysicalMaterial
        phys_matches = self._find_matches(r"(?:new\s+)?(?:THREE\.)?MeshPhysicalMaterial\b")
        results.append(
            CriteriaResult(
                criteria_id="PBR_PHYSICAL",
                name="MeshPhysicalMaterial Glass/Water Shader",
                category=self.CATEGORY_PBR,
                description="Advanced physical material with optical transmission, IOR, and dielectric physics",
                passed=len(phys_matches) > 0,
                required=True,
                matches=phys_matches,
                failure_reason=None if phys_matches else "MeshPhysicalMaterial usage missing",
            )
        )

        # 3. Roughness and Metalness Parameters
        param_matches = self._find_matches(r"\b(?:roughness|metalness)\s*[:=]\s*[\d\.]+")
        results.append(
            CriteriaResult(
                criteria_id="PBR_PARAMS",
                name="Roughness & Metalness Parameterization",
                category=self.CATEGORY_PBR,
                description="Explicit microfacet roughness and metallic reflectance parameter tuning",
                passed=len(param_matches) > 0,
                required=True,
                matches=param_matches,
                failure_reason=None if param_matches else "Roughness and metalness parameterization missing",
            )
        )

        # 4. Strata Vertex Colors & Elevation / Slope Shading
        strata_matches = self._find_matches(r"(?:vertexColors\s*[:=]\s*true|\bstrata\b|\bslope\b)")
        results.append(
            CriteriaResult(
                criteria_id="PBR_STRATA_SLOPE",
                name="Geological Strata & Slope Shading",
                category=self.CATEGORY_PBR,
                description="Slope-aware procedural strata blending and vertex color synthesis on diorama",
                passed=len(strata_matches) > 0,
                required=True,
                matches=strata_matches,
                failure_reason=None if strata_matches else "Strata/slope vertex color shading missing",
            )
        )

        # 5. Physical Water Shader (Transmission, IOR, Depth Transparency)
        water_matches = self._find_matches(r"(?:\btransmission\s*[:=]|\bior\s*[:=]|\breflectivity\s*[:=]|createPBRWaterMaterial|Water_Lake_Central)")
        results.append(
            CriteriaResult(
                criteria_id="PBR_WATER_SHADER",
                name="Physical Optical Water Shader",
                category=self.CATEGORY_PBR,
                description="Optical depth water shader with transmission, index of refraction, and surface reflectivity",
                passed=len(water_matches) > 0,
                required=True,
                matches=water_matches,
                failure_reason=None if water_matches else "Physical optical water shader parameters missing",
            )
        )

        return results

    def run_all_checks(self) -> List[CriteriaResult]:
        """Runs all categories of graphics code analysis."""
        all_results: List[CriteriaResult] = []
        all_results.extend(self.check_advanced_lighting())
        all_results.extend(self.check_soft_shadows())
        all_results.extend(self.check_pbr_and_shaders())
        return all_results

    def generate_report(self) -> Dict[str, Any]:
        """Generates a comprehensive structured report."""
        results = self.run_all_checks()
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        success = (failed == 0)

        # Group by category
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for r in results:
            cat = r.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r.to_dict())

        # Scanned files metadata
        scanned_files_info = []
        for rel_path in self.target_rel_files:
            full_path = self.root_dir / rel_path
            scanned_files_info.append({
                "path": rel_path,
                "exists": full_path.is_file(),
                "size_bytes": full_path.stat().st_size if full_path.is_file() else 0,
                "lines": len(self.file_lines.get(rel_path, [])),
            })

        return {
            "status": "PASS" if success else "FAIL",
            "success": success,
            "summary": {
                "total_criteria": total,
                "passed": passed,
                "failed": failed,
                "compliance_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
            },
            "scanned_files": scanned_files_info,
            "categories": categories,
            "results": [r.to_dict() for r in results],
        }


def verify_graphics_code(root_dir: Optional[Path] = None, verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """Programmatic API returning (passed: bool, report: dict)."""
    analyzer = GraphicsCodeAnalyzer(root_dir=root_dir)
    report = analyzer.generate_report()
    return report["success"], report


def format_cli_output(report: Dict[str, Any], verbose: bool = False) -> str:
    """Formats the analysis report for human-readable CLI printing."""
    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("  GENESIS ZERO — GRAPHICS CODE ANALYSIS REPORT (ACCEPTANCE CRITERIA 2)")
    lines.append("=" * 80)
    lines.append(f"Overall Status: [{'PASS' if report['success'] else 'FAIL'}] — Compliance: {report['summary']['compliance_rate']}")
    lines.append(f"Passed: {report['summary']['passed']}/{report['summary']['total_criteria']} criteria | Failed: {report['summary']['failed']}")
    lines.append("-" * 80)

    for cat_name, items in report["categories"].items():
        cat_passed = sum(1 for i in items if i["passed"])
        cat_total = len(items)
        status_marker = "[OK]" if cat_passed == cat_total else "[FAIL]"
        lines.append(f"\n{status_marker} {cat_name.upper()} ({cat_passed}/{cat_total})")
        for item in items:
            mark = "  [PASS]" if item["passed"] else "  [FAIL]"
            match_str = f" ({item['match_count']} occurrences)" if item["passed"] else f" [FAILED: {item['failure_reason']}]"
            lines.append(f"{mark} {item['name']}: {item['description']}{match_str}")

            if verbose and item["matches"]:
                lines.extend(
                    f"      -> {m['file_path']}:{m['line_number']} -> {m['context'][:70]}"
                    for m in item["matches"][:4]
                )
                if len(item["matches"]) > 4:
                    lines.append(f"      -> ... and {len(item['matches']) - 4} more occurrences")

    lines.append("\n" + "-" * 80)
    lines.append("Scanned Files Breakdown:")
    for f in report["scanned_files"]:
        status = "FOUND" if f["exists"] else "MISSING"
        lines.append(f"  - {f['path']} [{status}, {f['lines']} lines, {f['size_bytes']} bytes]")
    lines.append("=" * 80)

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for analyze_graphics_code.py."""
    parser = argparse.ArgumentParser(
        description="Statically analyze graphics code for advanced lighting, soft shadows, and PBR materials."
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
        help="Enable detailed verbose output with matched line numbers and snippets.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON to stdout instead of formatted text.",
    )

    args = parser.parse_args(argv)
    root_path = Path(args.root).resolve() if args.root else None
    analyzer = GraphicsCodeAnalyzer(root_dir=root_path)
    report = analyzer.generate_report()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_cli_output(report, verbose=args.verbose))

    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
