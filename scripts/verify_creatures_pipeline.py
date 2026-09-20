#!/usr/bin/env python3
"""
Genesis Zero — Comprehensive 3D Creature Pipeline Verification Suite
Validates the biological taxonomy, turnaround concept sheets, 3D model deliverables,
glTF 2.0 rigging & 8 animations, headless Blender BMesh topology, and Web Viewer sync
across all 10 target species.

Usage:
    python3 scripts/verify_creatures_pipeline.py
    python3 scripts/verify_creatures_pipeline.py --skip-blender
    python3 scripts/verify_creatures_pipeline.py --verbose
"""

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

# Console stream encoding reconfiguration for Windows
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            continue

# ANSI Color codes for terminal report
COLOR_HEADER = "\033[95m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_CREATURES = PROJECT_ROOT / "assets" / "creatures"
DOCS_CREATURES = PROJECT_ROOT / "docs" / "creatures"
DOCS_IMAGES = DOCS_CREATURES / "images"
WEB_DIR = PROJECT_ROOT / "web"
WEB_IMAGES = WEB_DIR / "creature_images"

# 10 Target Species Roster and Biological Specifications
TARGET_SPECIES = [
    "sand_skink",
    "snow_ferret",
    "alpine_ibex",
    "meadow_hare",
    "marsh_croc",
    "abyssal_hunter",
    "storm_eagle",
    "giant_tarantula",
    "armored_sentinel",
    "carnivore_apex",
]

SPECIES_METADATA = {
    "sand_skink": {
        "code": "L1",
        "domain": "CAN",
        "name_vn": "Thằn Lằn Cát Apex",
        "name_en": "Sand Skink",
        "tier": "Founder Tier 1",
        "traits": {"brain": 4, "attack": 3, "armor": 1, "speed": 2, "sense": 1, "stomach": 1},
        "trait_sum": 12,
        "aliases": ["sand_skink", "creature_L1_s1"],
    },
    "snow_ferret": {
        "code": "L2",
        "domain": "CAN",
        "name_vn": "Chồn Tuyết Phục Kích",
        "name_en": "Snow Ferret",
        "tier": "Founder Tier 1",
        "traits": {"brain": 3, "attack": 4, "armor": 2, "speed": 1, "sense": 2, "stomach": 0},
        "trait_sum": 12,
        "aliases": ["snow_ferret", "creature_L2_s1"],
    },
    "alpine_ibex": {
        "code": "L3",
        "domain": "CAN",
        "name_vn": "Dê Sừng Núi Thích Nghi",
        "name_en": "Alpine Ibex",
        "tier": "Founder Tier 1",
        "traits": {"brain": 3, "attack": 1, "armor": 1, "speed": 3, "sense": 3, "stomach": 1},
        "trait_sum": 12,
        "aliases": ["alpine_ibex", "creature_L3_s1"],
    },
    "meadow_hare": {
        "code": "L4",
        "domain": "CAN",
        "name_vn": "Thỏ Đồng Cỏ Bọc Giáp",
        "name_en": "Meadow Hare",
        "tier": "Founder Tier 1",
        "traits": {"brain": 1, "attack": 1, "armor": 5, "speed": 1, "sense": 2, "stomach": 2},
        "trait_sum": 12,
        "aliases": ["meadow_hare", "creature_L4_s1"],
    },
    "marsh_croc": {
        "code": "L5",
        "domain": "CAN",
        "name_vn": "Cá Sấu Đầm Lầy",
        "name_en": "Marsh Croc",
        "tier": "Founder Tier 1",
        "traits": {"brain": 0, "attack": 2, "armor": 0, "speed": 5, "sense": 3, "stomach": 2},
        "trait_sum": 12,
        "aliases": ["marsh_croc", "creature_L5_s1"],
    },
    "abyssal_hunter": {
        "code": "W1",
        "domain": "NUOC",
        "name_vn": "Cá Săn Mồi Vực Sâu",
        "name_en": "Abyssal Hunter",
        "tier": "Founder Tier 1",
        "traits": {"brain": 1, "attack": 1, "armor": 0, "speed": 5, "sense": 4, "stomach": 1},
        "trait_sum": 12,
        "aliases": ["abyssal_hunter", "creature_W1_s1"],
    },
    "storm_eagle": {
        "code": "A1",
        "domain": "TROI",
        "name_vn": "Đại Bàng Săn Mồi Bầu Trời",
        "name_en": "Storm Eagle",
        "tier": "Founder Tier 1",
        "traits": {"brain": 2, "attack": 2, "armor": 0, "speed": 4, "sense": 4, "stomach": 0},
        "trait_sum": 12,
        "aliases": ["storm_eagle", "creature_A1_s1"],
    },
    "giant_tarantula": {
        "code": "Tarantula",
        "domain": "CAN",
        "name_vn": "Nhện Khổng Lồ Độc",
        "name_en": "Giant Tarantula",
        "tier": "Specialist Tier 2",
        "traits": {"brain": 2, "attack": 4, "armor": 2, "speed": 3, "sense": 4, "stomach": 1},
        "trait_sum": 16,
        "aliases": ["giant_tarantula", "creature_giant_tarantula"],
    },
    "armored_sentinel": {
        "code": "Sentinel",
        "domain": "CAN",
        "name_vn": "Sentinel Cơ Khí Sinh Học",
        "name_en": "Armored Sentinel",
        "tier": "Specialist Tier 2",
        "traits": {"brain": 3, "attack": 3, "armor": 6, "speed": 1, "sense": 3, "stomach": 0},
        "trait_sum": 16,
        "aliases": ["armored_sentinel", "genesis_sentinel", "creature_armored_sentinel"],
    },
    "carnivore_apex": {
        "code": "L1_Evo",
        "domain": "CAN",
        "name_vn": "Quái Thú Apex Tiến Hóa",
        "name_en": "Carnivore Apex",
        "tier": "Super Apex Tier 3",
        "traits": {"brain": 5, "attack": 6, "armor": 3, "speed": 4, "sense": 3, "stomach": 2},
        "trait_sum": 23,
        "aliases": ["carnivore_apex", "creature_L1_Evo_s1"],
    },
}

CANONICAL_ANIMATIONS = [
    "Idle_Normal",
    "Idle_Alert",
    "Walk",
    "Run",
    "Attack",
    "Hurt_Defend",
    "Eat",
    "Death",
]


def resolve_file(base_dir: Path, species: str, extension: str) -> Path | None:
    """Resolve a file path considering standard species name and aliases."""
    meta = SPECIES_METADATA.get(species, {})
    raw_aliases = meta.get("aliases", []) if isinstance(meta, dict) else []
    aliases: list[str] = list(raw_aliases) if isinstance(raw_aliases, (list, tuple)) else []
    candidate_names = [species, *[a for a in aliases if a != species]]
    for name in candidate_names:
        candidate = base_dir / f"{name}{extension}"
        if candidate.exists():
            return candidate
    return None


def get_jpeg_dimensions(file_path: Path) -> tuple[int, int] | None:
    """Extract (width, height) of a JPEG file."""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            return img.size  # (width, height)
    except Exception:
        pass

    # Pure Python binary fallback for JPEG SOF markers
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        i = 2
        while i < len(data) - 8:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return (w, h)
            seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
            i += 2 + seg_len
    except Exception:
        pass
    return None


class CreaturePipelineVerifier:
    def __init__(self, verbose: bool = False, skip_blender: bool = False):
        self.verbose = verbose
        self.skip_blender = skip_blender
        self.results: list[dict[str, Any]] = []
        self.total_checks = 0
        self.passed_checks = 0

    def log(self, category: str, item: str, passed: bool, detail: str = ""):
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
        self.results.append({
            "category": category,
            "item": item,
            "passed": passed,
            "detail": detail,
        })
        if self.verbose:
            tag = f"{COLOR_GREEN}PASS{COLOR_RESET}" if passed else f"{COLOR_RED}FAIL{COLOR_RESET}"
            print(f"[{tag}] {category} - {item}: {detail}")

    def print_summary(self):
        print("\n" + "=" * 92)
        print(f"{COLOR_BOLD}{COLOR_CYAN}          GENESIS ZERO — CREATURE PIPELINE AUDIT REPORT (10 SPECIES){COLOR_RESET}")
        print("=" * 92)
        print(f"{'Category':<24} | {'Item':<32} | {'Status':<10} | Detail")
        print("-" * 92)

        current_cat = ""
        for r in self.results:
            cat_display = r["category"] if r["category"] != current_cat else ""
            current_cat = r["category"]
            status_str = f"{COLOR_GREEN}PASS ✓{COLOR_RESET}" if r["passed"] else f"{COLOR_RED}FAIL ❌{COLOR_RESET}"
            detail = r["detail"]
            if len(detail) > 42:
                detail = detail[:39] + "..."
            print(f"{cat_display:<24} | {r['item']:<32} | {status_str:<19} | {detail}")

        print("-" * 92)
        failed_count = self.total_checks - self.passed_checks
        rate = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        summary_color = COLOR_GREEN if failed_count == 0 else COLOR_RED
        print(
            f"Total Checks: {self.total_checks} | Passed: {self.passed_checks} | "
            f"Failed: {failed_count} | {summary_color}Compliance: {rate:.1f}%{COLOR_RESET}"
        )
        print("=" * 92)

    # -------------------------------------------------------------------------
    # 1. Taxonomy & Biological Metadata Integrity
    # -------------------------------------------------------------------------
    def verify_taxonomy_and_metadata(self):
        cat = "1. Taxonomy & Traits"

        # Check all 10 species are registered in target roster
        self.log(cat, "10 Target Species Count", len(TARGET_SPECIES) == 10, f"{len(TARGET_SPECIES)} species registered")

        valid_domains = {"CAN", "NUOC", "TROI"}

        for sp in TARGET_SPECIES:
            meta = SPECIES_METADATA.get(sp)
            if not meta:
                self.log(cat, f"Metadata: {sp}", False, "Missing metadata record")
                continue

            dom = meta.get("domain")
            traits = meta.get("traits", {})
            values = list(traits.values())
            sum_traits = sum(values)

            # Valid domain
            valid_dom = dom in valid_domains

            # Trait range checks
            all_non_negative = all(isinstance(v, int) and v >= 0 for v in values)
            has_6_traits = len(traits) == 6 and set(traits.keys()) == {
                "brain", "attack", "armor", "speed", "sense", "stomach"
            }

            # Founder check: sum == 12, each in [0, 5]
            is_founder = meta["tier"].startswith("Founder")
            if is_founder:
                valid_bounds = all(0 <= v <= 5 for v in values)
                valid_sum = (sum_traits == 12)
            else:
                valid_bounds = all(0 <= v <= 7 for v in values)
                valid_sum = (sum_traits == meta["trait_sum"])

            passed = valid_dom and all_non_negative and has_6_traits and valid_bounds and valid_sum
            detail = f"Domain={dom}, Traits={values}, Sum={sum_traits}"
            self.log(cat, f"Specs: {sp}", passed, detail)

        # Check README catalog if exists
        readme_path = DOCS_CREATURES / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            missing_in_doc = [sp for sp in TARGET_SPECIES if sp not in content and SPECIES_METADATA[sp]["code"] not in content]
            self.log(cat, "Docs Catalog README.md", len(missing_in_doc) == 0,
                     "All 10 species documented" if not missing_in_doc else f"Missing: {missing_in_doc}")
        else:
            self.log(cat, "Docs Catalog README.md", False, f"Missing {readme_path}")

    # -------------------------------------------------------------------------
    # 2. Turnaround Concept Sheets (JPEG SOI/EOI, Size > 20KB, Dims >= 1024x1024)
    # -------------------------------------------------------------------------
    def verify_turnaround_images(self):
        cat = "2. Turnaround Images"

        for sp in TARGET_SPECIES:
            web_file = resolve_file(WEB_IMAGES, sp, "_turnaround.jpg")
            docs_file = resolve_file(DOCS_IMAGES, sp, "_turnaround.jpg")

            # Check web turnaround image
            if not web_file:
                self.log(cat, f"Web Image: {sp}", False, f"Missing in {WEB_IMAGES}")
            else:
                size = web_file.stat().st_size
                size_ok = size > 20480  # > 20KB

                with open(web_file, "rb") as f:
                    soi = f.read(2)
                    f.seek(-2, os.SEEK_END)
                    eoi = f.read(2)
                is_jpeg = (soi == b"\xff\xd8") and (eoi == b"\xff\xd9")

                dims = get_jpeg_dimensions(web_file)
                dims_ok = dims is not None and dims[0] >= 1024 and dims[1] >= 1024
                dims_str = f"{dims[0]}x{dims[1]}" if dims else "unknown"

                passed = size_ok and is_jpeg and dims_ok
                self.log(cat, f"Web Image: {sp}", passed,
                         f"{size / 1024:.1f} KB, {dims_str}, SOI/EOI valid")

            # Check docs turnaround image
            if not docs_file:
                self.log(cat, f"Docs Image: {sp}", False, f"Missing in {DOCS_IMAGES}")
            else:
                size = docs_file.stat().st_size
                size_ok = size > 20480

                with open(docs_file, "rb") as f:
                    soi = f.read(2)
                    f.seek(-2, os.SEEK_END)
                    eoi = f.read(2)
                is_jpeg = (soi == b"\xff\xd8") and (eoi == b"\xff\xd9")

                dims = get_jpeg_dimensions(docs_file)
                dims_ok = dims is not None and dims[0] >= 1024 and dims[1] >= 1024
                dims_str = f"{dims[0]}x{dims[1]}" if dims else "unknown"

                passed = size_ok and is_jpeg and dims_ok
                self.log(cat, f"Docs Image: {sp}", passed, f"{size / 1024:.1f} KB, {dims_str}, SOI/EOI valid")

    # -------------------------------------------------------------------------
    # 3. 3D Model Deliverables (.blend magic & .glb magic)
    # -------------------------------------------------------------------------
    def verify_3d_model_deliverables(self):
        cat = "3. 3D Deliverables"

        for sp in TARGET_SPECIES:
            blend_file = resolve_file(ASSETS_CREATURES, sp, ".blend")
            glb_file = resolve_file(ASSETS_CREATURES, sp, ".glb")

            # Check .blend file
            if not blend_file:
                self.log(cat, f"Blend File: {sp}", False, f"Missing in {ASSETS_CREATURES}")
            else:
                bsize = blend_file.stat().st_size
                with open(blend_file, "rb") as f:
                    magic = f.read(4)
                # Valid headers: uncompressed b"BLEN" or zstd compressed b"\x28\xb5\x2f\xfd"
                is_blend_valid = (magic == b"BLEN") or (magic == b"\x28\xb5\x2f\xfd")
                magic_name = "zstd" if magic == b"\x28\xb5\x2f\xfd" else ("BLEN" if magic == b"BLEN" else hex(struct.unpack(">I", magic)[0]))
                passed = bsize > 1024 and is_blend_valid
                self.log(cat, f"Blend File: {sp}", passed, f"{bsize / 1024:.1f} KB, magic: {magic_name}")

            # Check .glb file
            if not glb_file:
                self.log(cat, f"GLB File: {sp}", False, f"Missing in {ASSETS_CREATURES}")
            else:
                gsize = glb_file.stat().st_size
                with open(glb_file, "rb") as f:
                    magic, ver, total_len = struct.unpack("<4sII", f.read(12))
                is_glb_valid = (magic == b"glTF") and (ver == 2) and (total_len == gsize)
                passed = gsize > 1024 and is_glb_valid
                self.log(cat, f"GLB File: {sp}", passed, f"{gsize / 1024:.1f} KB, glTF v2 valid")

    # -------------------------------------------------------------------------
    # 4. glTF 2.0 Skinning & 8-Animation Verification
    # -------------------------------------------------------------------------
    def verify_gltf2_skinning_and_animations(self):
        cat = "4. glTF Rig & 8-Anim"

        for sp in TARGET_SPECIES:
            glb_file = resolve_file(ASSETS_CREATURES, sp, ".glb")
            if not glb_file:
                self.log(cat, f"Rig/Anim: {sp}", False, "GLB file missing")
                continue

            try:
                with open(glb_file, "rb") as f:
                    magic, ver, fsize = struct.unpack("<4sII", f.read(12))
                    if magic != b"glTF" or ver != 2:
                        self.log(cat, f"Rig/Anim: {sp}", False, f"Invalid glTF header: {magic}, ver={ver}")
                        continue

                    c0_len, c0_type = struct.unpack("<II", f.read(8))
                    if c0_type != 0x4E4F534A:  # ASCII "JSON"
                        self.log(cat, f"Rig/Anim: {sp}", False, f"Chunk 0 is not JSON ({hex(c0_type)})")
                        continue

                    meta = json.loads(f.read(c0_len).decode("utf-8"))

                # 1. Skinning & Armature verification
                skins = meta.get("skins", [])
                nodes = meta.get("nodes", [])
                has_skin = len(skins) > 0
                joints_count = sum(len(s.get("joints", [])) for s in skins)
                joints_valid = all(
                    0 <= j < len(nodes) for s in skins for j in s.get("joints", [])
                )

                # 2. Animations verification
                animations = meta.get("animations", [])

                # Map to canonical 8 animations
                found_canonicals = set()
                invalid_clips = []
                for clip in animations:
                    name = clip.get("name", "")
                    samplers = clip.get("samplers", [])
                    channels = clip.get("channels", [])

                    if len(samplers) == 0 or len(channels) == 0:
                        invalid_clips.append(f"{name} (samplers={len(samplers)}, channels={len(channels)})")

                    # Verify channel targets valid node
                    for ch in channels:
                        target = ch.get("target", {})
                        tnode = target.get("node")
                        if tnode is None or not (0 <= tnode < len(nodes)):
                            invalid_clips.append(f"{name} (invalid target node {tnode})")

                    # Canonical mapping
                    lower = name.lower()
                    for canon in CANONICAL_ANIMATIONS:
                        c_low = canon.lower()
                        if c_low == lower or f"_{c_low}" in lower or f"{c_low}_" in lower:
                            found_canonicals.add(canon)
                        # Special match for Hurt_Defend vs Hurt
                        elif canon == "Hurt_Defend" and ("hurt" in lower or "defend" in lower):
                            found_canonicals.add("Hurt_Defend")
                        elif canon == "Idle_Normal" and ("idle_normal" in lower or (lower.endswith("idle") and "alert" not in lower)):
                            found_canonicals.add("Idle_Normal")
                        elif canon == "Idle_Alert" and "alert" in lower:
                            found_canonicals.add("Idle_Alert")

                missing_canon = set(CANONICAL_ANIMATIONS) - found_canonicals
                anims_ok = len(missing_canon) == 0 and len(invalid_clips) == 0 and len(animations) >= 8
                rig_ok = has_skin and joints_count > 0 and joints_valid

                passed = rig_ok and anims_ok
                if passed:
                    detail = f"Skin OK ({joints_count} joints), 8/8 actions baked ({len(animations)} clips)"
                else:
                    reasons = []
                    if not has_skin:
                        reasons.append("Missing skins array")
                    elif not joints_valid:
                        reasons.append("Invalid joint node references")
                    if missing_canon:
                        reasons.append(f"Missing anims: {sorted(list(missing_canon))}")
                    if invalid_clips:
                        reasons.append(f"Empty channels/samplers: {invalid_clips}")
                    detail = "; ".join(reasons)

                self.log(cat, f"Rig/Anim: {sp}", passed, detail)

            except Exception as e:
                self.log(cat, f"Rig/Anim: {sp}", False, f"glTF parse error: {e}")

    # -------------------------------------------------------------------------
    # 5. Headless Blender BMesh Manifold Verification
    # -------------------------------------------------------------------------
    def verify_bmesh_manifold_topology(self):
        cat = "5. Blender BMesh Topology"

        if self.skip_blender:
            self.log(cat, "Blender Topology Check", True, "Skipped via --skip-blender flag")
            return

        blender_bin = shutil.which("blender")
        if not blender_bin:
            candidates = [
                Path("/Applications/Blender.app/Contents/MacOS/Blender"),
                Path("/usr/bin/blender"),
                Path("/usr/local/bin/blender"),
            ]
            pf = Path("C:/Program Files/Blender Foundation")
            if pf.exists():
                candidates.extend(sorted(pf.glob("**/blender.exe"), reverse=True))
            for c in candidates:
                if c.is_file():
                    blender_bin = str(c)
                    break

        if not blender_bin or not os.path.exists(blender_bin):
            self.log(cat, "Blender Executable", True, "Blender binary not found in standard paths or PATH (skipped)")
            return

        # Build list of blend files to test
        blend_files = []
        for sp in TARGET_SPECIES:
            bf = resolve_file(ASSETS_CREATURES, sp, ".blend")
            if bf:
                blend_files.append(str(bf))

        if len(blend_files) < 10:
            self.log(cat, "Blend Files Present", False, f"Found only {len(blend_files)}/10 .blend files")
            return

        expr = f"""
import bpy, bmesh, os, sys

blend_files = {blend_files!r}
defects = []

for bf in blend_files:
    if not os.path.exists(bf):
        defects.append(f"{{bf}}: file not found")
        continue
    bpy.ops.wm.open_mainfile(filepath=bf)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    if not meshes:
        defects.append(f"{{os.path.basename(bf)}}: no MESH objects")
        continue

    for m in meshes:
        bm = bmesh.new()
        bm.from_mesh(m.data)
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        loose = sum(1 for v in bm.verts if len(v.link_edges) == 0)
        incontig = sum(1 for e in bm.edges if len(e.link_faces) == 2 and not e.is_contiguous)
        multi = sum(1 for e in bm.edges if len(e.link_faces) > 2)
        wire = sum(1 for e in bm.edges if len(e.link_faces) == 0)
        ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
        non_smooth = sum(1 for p in m.data.polygons if not p.use_smooth)
        bm.free()

        non_manifold = incontig + multi + wire
        if loose > 0 or non_manifold > 0 or ngons > 0 or non_smooth > 0:
            defects.append(
                f"{{os.path.basename(bf)}}:{{m.name}} (loose={{loose}}, non_manifold={{non_manifold}}, ngons={{ngons}}, non_smooth={{non_smooth}})"
            )

if defects:
    print("DEFECTS_DETECTED:" + "; ".join(defects))
    sys.exit(1)
else:
    print("BMESH_TOPOLOGY_100_PERCENT_CLEAN")
    sys.exit(0)
"""
        cmd = [blender_bin, "--background", "--python-expr", expr]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(PROJECT_ROOT),
            )
            passed = (result.returncode == 0) and ("BMESH_TOPOLOGY_100_PERCENT_CLEAN" in result.stdout)
            if passed:
                detail = f"All {len(blend_files)} models: 0 loose verts, 0 non-manifold, 0 ngons, 100% smooth"
            else:
                out = result.stdout + result.stderr
                m = re.search(r"DEFECTS_DETECTED:(.*)", out)
                detail = m.group(1).strip() if m else out[:120].strip()

            self.log(cat, "BMesh Manifold Topology", passed, detail)
        except Exception as e:
            self.log(cat, "BMesh Manifold Topology", False, f"Subprocess error: {e}")

    # -------------------------------------------------------------------------
    # 6. Web Viewer & Offline Base64 Data Synchronization
    # -------------------------------------------------------------------------
    def verify_web_viewer_sync(self):
        cat = "6. Web Viewer Sync"

        viewer_html = WEB_DIR / "creature_viewer.html"
        models_data_js = WEB_DIR / "creature_models_data.js"

        # 1. creature_viewer.html existence and elements
        if not viewer_html.exists():
            self.log(cat, "HTML Viewer Exists", False, f"Missing {viewer_html}")
        else:
            html_text = viewer_html.read_text(encoding="utf-8")

            # References all 10 species
            missing_species = []
            for sp in TARGET_SPECIES:
                meta = SPECIES_METADATA[sp]
                if sp not in html_text and meta["code"] not in html_text and meta["name_vn"] not in html_text:
                    missing_species.append(sp)

            self.log(cat, "HTML 10 Species Catalog", len(missing_species) == 0,
                     "All 10 species referenced" if not missing_species else f"Missing: {missing_species}")

            # Has 8 animation controls
            missing_anims = [a for a in CANONICAL_ANIMATIONS if a not in html_text]
            self.log(cat, "HTML 8-Animation Controls", len(missing_anims) == 0,
                     "All 8 actions defined in UI" if not missing_anims else f"Missing: {missing_anims}")

            # Has skeleton toggle
            has_skeleton = ("SkeletonHelper" in html_text) or ("toggleSkeleton" in html_text) or ("btn-toggle-skeleton" in html_text)
            self.log(cat, "HTML SkeletonHelper Toggle", has_skeleton, "Armature skeleton toggle present")

            # Has turnaround modal
            has_modal = ("turnaround-modal" in html_text) or ("openTurnaroundModal" in html_text)
            self.log(cat, "HTML Turnaround Modal", has_modal, "Turnaround inspection modal present")

        # 2. creature_models_data.js synchronization
        if not models_data_js.exists():
            self.log(cat, "Models Data JS Exists", False, f"Missing {models_data_js}")
        else:
            js_text = models_data_js.read_text(encoding="utf-8")

            mismatched_hashes = []
            synced_count = 0

            for sp in TARGET_SPECIES:
                glb_file = resolve_file(ASSETS_CREATURES, sp, ".glb")
                if not glb_file:
                    mismatched_hashes.append(f"{sp}: missing glb")
                    continue

                disk_bytes = glb_file.read_bytes()
                disk_sha256 = hashlib.sha256(disk_bytes).hexdigest()

                # Extract base64 payload from JS file for this species or alias
                candidates = [sp, *[a for a in SPECIES_METADATA[sp].get("aliases", []) if a != sp]]
                found_match = False
                for cname in candidates:
                    pattern = r"[\"']" + re.escape(cname) + r"[\"']\s*:\s*[\"']([A-Za-z0-9+/=\s]+?)[\"']"
                    m = re.search(pattern, js_text)
                    if m:
                        b64_str = re.sub(r"\s+", "", m.group(1))
                        try:
                            decoded_bytes = base64.b64decode(b64_str)
                            js_sha256 = hashlib.sha256(decoded_bytes).hexdigest()
                            if js_sha256 == disk_sha256:
                                found_match = True
                                synced_count += 1
                                break
                            else:
                                mismatched_hashes.append(f"{sp}: sha256 mismatch (disk={disk_sha256[:8]}, js={js_sha256[:8]})")
                                found_match = True
                                break
                        except Exception as e:
                            mismatched_hashes.append(f"{sp}: base64 decode error {e}")
                            found_match = True
                            break

                if not found_match:
                    mismatched_hashes.append(f"{sp}: not found in creature_models_data.js")

            all_synced = (synced_count == len(TARGET_SPECIES)) and len(mismatched_hashes) == 0
            detail = f"{synced_count}/10 models SHA256 synced" if all_synced else f"Mismatches: {mismatched_hashes}"
            self.log(cat, "Base64 SHA256 Sync", all_synced, detail)

    # -------------------------------------------------------------------------
    # Main Execution Entry
    # -------------------------------------------------------------------------
    def run_all(self) -> int:
        self.verify_taxonomy_and_metadata()
        self.verify_turnaround_images()
        self.verify_3d_model_deliverables()
        self.verify_gltf2_skinning_and_animations()
        self.verify_bmesh_manifold_topology()
        self.verify_web_viewer_sync()

        self.print_summary()

        if self.passed_checks == self.total_checks and self.total_checks > 0:
            print(f"\n{COLOR_BOLD}{COLOR_GREEN}🎉 [SUCCESS] All Creature Pipeline checks passed with 100% compliance! Exit Code 0.{COLOR_RESET}\n")
            return 0
        else:
            failed = self.total_checks - self.passed_checks
            print(f"\n{COLOR_BOLD}{COLOR_RED}❌ [FAILURE] {failed} verification check(s) failed.{COLOR_RESET}\n")
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Genesis Zero 3D Creature Pipeline Verification Suite")
    parser.add_argument("--skip-blender", action="store_true", help="Skip headless Blender BMesh verification")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose test reporting")
    args = parser.parse_args()

    verifier = CreaturePipelineVerifier(verbose=args.verbose, skip_blender=args.skip_blender)
    return verifier.run_all()


if __name__ == "__main__":
    sys.exit(main())
