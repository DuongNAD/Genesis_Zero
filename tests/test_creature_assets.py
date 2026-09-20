"""
Genesis Zero — Automated Pytest Suite for 3D Creature Pipeline
Validates the biological taxonomy, turnaround concept sheets, 3D model deliverables,
glTF 2.0 rigging & 8 animations, headless Blender BMesh topology, and Web Viewer sync
across all 10 target species.

Test Classes Covering 6 Core Quality Dimensions:
1. TestCreatureTaxonomyAndMetadata (R1)
2. TestCreatureTurnaroundImages (R2)
3. TestCreatureThreeDDeliverables (R3)
4. TestCreatureGltfSkinningAnd8Animations (R4)
5. TestCreatureBlenderBMeshTopology (R5)
6. TestCreatureWebViewerIntegration (R6)
"""

import base64
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_CREATURES = PROJECT_ROOT / "assets" / "creatures"
DOCS_CREATURES = PROJECT_ROOT / "docs" / "creatures"
DOCS_IMAGES = DOCS_CREATURES / "images"
WEB_DIR = PROJECT_ROOT / "web"
WEB_IMAGES = WEB_DIR / "creature_images"

# 10 Target Species
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
    """Resolve file path with species name and aliases."""
    meta = SPECIES_METADATA.get(species, {})
    raw_aliases = meta.get("aliases")
    alias_list = raw_aliases if isinstance(raw_aliases, list) else []
    candidate_names = [species, *[a for a in alias_list if a != species]]
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
            return img.size
    except Exception:
        pass

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


# =============================================================================
# Dimension 1: Taxonomy & Biological Metadata Integrity
# =============================================================================
class TestCreatureTaxonomyAndMetadata:
    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_creature_metadata_and_traits(self, species):
        """R1: Validates that 10 species are recognized with correct domains and trait ranges."""
        meta = SPECIES_METADATA.get(species)
        assert meta is not None, f"Species {species} is not recognized in SPECIES_METADATA"

        domain = meta.get("domain")
        assert domain in {"CAN", "NUOC", "TROI"}, f"Invalid domain {domain} for {species}"

        traits = meta.get("traits", {})
        assert len(traits) == 6, f"Expected 6 traits for {species}, found {len(traits)}"
        assert set(traits.keys()) == {"brain", "attack", "armor", "speed", "sense", "stomach"}

        values = list(traits.values())
        assert all(isinstance(v, int) and v >= 0 for v in values), f"All traits must be non-negative integers: {values}"

        if meta["tier"].startswith("Founder"):
            assert sum(values) == 12, f"Founder species {species} trait sum must equal 12, got {sum(values)}"
            assert all(0 <= v <= 5 for v in values), f"Founder species {species} traits must be within [0, 5], got {values}"
        else:
            assert sum(values) == meta["trait_sum"], f"{species} trait sum must equal {meta['trait_sum']}, got {sum(values)}"
            assert all(0 <= v <= 7 for v in values), f"{species} traits must be within [0, 7], got {values}"

    def test_creature_catalog_readme_structure(self):
        """R1: Validates that docs/creatures/README.md documents all 10 target species."""
        readme_path = DOCS_CREATURES / "README.md"
        assert readme_path.exists(), f"docs/creatures/README.md missing at {readme_path}"

        content = readme_path.read_text(encoding="utf-8")
        missing_species = []
        for sp in TARGET_SPECIES:
            meta = SPECIES_METADATA[sp]
            if sp not in content and meta["code"] not in content and meta["name_vn"] not in content:
                missing_species.append(sp)

        assert len(missing_species) == 0, f"README.md missing documentation for: {missing_species}"


# =============================================================================
# Dimension 2: Turnaround Images (JPEG SOI/EOI, Size > 20KB, Dimensions >= 1024x1024)
# =============================================================================
class TestCreatureTurnaroundImages:
    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_creature_turnaround_images(self, species):
        """R2: Checks web and docs turnaround images for JPEG SOI/EOI, dimensions >= 1024x1024, file size > 20KB."""
        # 1. Web Image
        web_file = resolve_file(WEB_IMAGES, species, "_turnaround.jpg")
        assert web_file is not None and web_file.exists(), f"Missing web turnaround image for {species} in {WEB_IMAGES}"

        web_size = web_file.stat().st_size
        assert web_size > 20480, f"Web image for {species} must be > 20KB, found {web_size} bytes ({web_file})"

        with open(web_file, "rb") as f:
            soi = f.read(2)
            f.seek(-2, os.SEEK_END)
            eoi = f.read(2)
        assert soi == b"\xff\xd8", f"Web image for {species} missing JPEG SOI marker (0xFFD8)"
        assert eoi == b"\xff\xd9", f"Web image for {species} missing JPEG EOI marker (0xFFD9)"

        web_dims = get_jpeg_dimensions(web_file)
        assert web_dims is not None, f"Could not read JPEG dimensions for {web_file}"
        assert web_dims[0] >= 1024 and web_dims[1] >= 1024, f"Web image for {species} must be >= 1024x1024, found {web_dims}"

        # 2. Docs Image
        docs_file = resolve_file(DOCS_IMAGES, species, "_turnaround.jpg")
        assert docs_file is not None and docs_file.exists(), f"Missing docs turnaround image for {species} in {DOCS_IMAGES}"

        docs_size = docs_file.stat().st_size
        assert docs_size > 20480, f"Docs image for {species} must be > 20KB, found {docs_size} bytes ({docs_file})"

        with open(docs_file, "rb") as f:
            doc_soi = f.read(2)
            f.seek(-2, os.SEEK_END)
            doc_eoi = f.read(2)
        assert doc_soi == b"\xff\xd8", f"Docs image for {species} missing JPEG SOI marker"
        assert doc_eoi == b"\xff\xd9", f"Docs image for {species} missing JPEG EOI marker"

        docs_dims = get_jpeg_dimensions(docs_file)
        assert docs_dims is not None, f"Could not read JPEG dimensions for {docs_file}"
        assert docs_dims[0] >= 1024 and docs_dims[1] >= 1024, f"Docs image for {species} must be >= 1024x1024, found {docs_dims}"


# =============================================================================
# Dimension 3: 3D Model Deliverables (.blend & .glb container checks)
# =============================================================================
class TestCreatureThreeDDeliverables:
    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_creature_blend_and_glb_files(self, species):
        """R3: Checks assets/creatures/<species>.blend (magic BLEN or zstd) and assets/creatures/<species>.glb (magic glTF v2)."""
        blend_file = resolve_file(ASSETS_CREATURES, species, ".blend")
        assert blend_file is not None and blend_file.exists(), f"Missing .blend file for {species} in {ASSETS_CREATURES}"

        bsize = blend_file.stat().st_size
        assert bsize > 1024, f".blend file for {species} is unexpectedly small ({bsize} bytes)"

        with open(blend_file, "rb") as f:
            magic = f.read(4)
        assert (magic == b"BLEN") or (magic == b"\x28\xb5\x2f\xfd"), \
            f"{blend_file} invalid header magic: {magic} (expected b'BLEN' or zstandard b'\\x28\\xb5\\x2f\\xfd')"

        glb_file = resolve_file(ASSETS_CREATURES, species, ".glb")
        assert glb_file is not None and glb_file.exists(), f"Missing .glb file for {species} in {ASSETS_CREATURES}"

        gsize = glb_file.stat().st_size
        assert gsize > 1024, f".glb file for {species} is unexpectedly small ({gsize} bytes)"

        with open(glb_file, "rb") as f:
            magic, ver, total_len = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", f"{glb_file} invalid magic: {magic} (expected b'glTF')"
        assert ver == 2, f"{glb_file} invalid glTF version: {ver} (expected version 2)"
        assert total_len == gsize, f"{glb_file} header length {total_len} != disk size {gsize}"


# =============================================================================
# Dimension 4: glTF 2.0 Skinning & 8-Animation Verification
# =============================================================================
class TestCreatureGltfSkinningAnd8Animations:
    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_creature_gltf_skinning_and_8_animations(self, species):
        """R4: Parses JSON chunk of .glb, verifies skins array > 0, armature nodes exist, and 8 canonical animation clips exist."""
        glb_file = resolve_file(ASSETS_CREATURES, species, ".glb")
        assert glb_file is not None and glb_file.exists(), f"Missing .glb file for {species} in {ASSETS_CREATURES}"

        with open(glb_file, "rb") as f:
            magic, ver, fsize = struct.unpack("<4sII", f.read(12))
            assert magic == b"glTF" and ver == 2, f"{glb_file} is not a valid glTF 2.0 container"

            c0_len, c0_type = struct.unpack("<II", f.read(8))
            assert c0_type == 0x4E4F534A, f"{glb_file} Chunk 0 is not JSON ({hex(c0_type)})"
            meta = json.loads(f.read(c0_len).decode("utf-8"))

        # 1. Skinning & Armature verification
        skins = meta.get("skins", [])
        nodes = meta.get("nodes", [])
        assert len(skins) > 0, f"{glb_file} must have skins array > 0 (hierarchical armature skinning)"
        joints = skins[0].get("joints", [])
        assert len(joints) > 0, f"{glb_file} skins[0] has no joints defined"
        assert len(nodes) > 0, f"{glb_file} has no nodes defined"
        for joint_idx in joints:
            assert 0 <= joint_idx < len(nodes), f"{glb_file} joint index {joint_idx} out of range (nodes: {len(nodes)})"

        # 2. Animations verification
        animations = meta.get("animations", [])
        assert len(animations) >= 8, f"{glb_file} expected at least 8 animation tracks, found {len(animations)}"

        found_canonicals = set()
        for clip in animations:
            name = clip.get("name", "")
            samplers = clip.get("samplers", [])
            channels = clip.get("channels", [])

            assert len(samplers) > 0, f"{glb_file} animation clip '{name}' has 0 samplers"
            assert len(channels) > 0, f"{glb_file} animation clip '{name}' has 0 channels"

            for ch in channels:
                target = ch.get("target", {})
                target_node = target.get("node")
                assert target_node is not None, f"{glb_file} clip '{name}' channel missing target node"
                assert 0 <= target_node < len(nodes), f"{glb_file} clip '{name}' target node {target_node} out of range"
                assert target.get("path") in {"translation", "rotation", "scale", "weights"}, \
                    f"{glb_file} clip '{name}' invalid target path: {target.get('path')}"

            lower = name.lower()
            for canon in CANONICAL_ANIMATIONS:
                c_low = canon.lower()
                if c_low == lower or f"_{c_low}" in lower or f"{c_low}_" in lower:
                    found_canonicals.add(canon)
                elif canon == "Hurt_Defend" and ("hurt" in lower or "defend" in lower):
                    found_canonicals.add("Hurt_Defend")
                elif canon == "Idle_Normal" and ("idle_normal" in lower or (lower.endswith("idle") and "alert" not in lower)):
                    found_canonicals.add("Idle_Normal")
                elif canon == "Idle_Alert" and "alert" in lower:
                    found_canonicals.add("Idle_Alert")

        missing = set(CANONICAL_ANIMATIONS) - found_canonicals
        assert len(missing) == 0, f"{glb_file} missing canonical animation clips: {missing}. Present: {[a.get('name') for a in animations]}"


# =============================================================================
# Dimension 5: Headless Blender BMesh Manifold Verification
# =============================================================================
class TestCreatureBlenderBMeshTopology:
    def test_creature_bmesh_manifold_topology(self):
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
            pytest.skip("Blender binary not available in standard paths or PATH")

        blend_files = []
        for sp in TARGET_SPECIES:
            bf = resolve_file(ASSETS_CREATURES, sp, ".blend")
            assert bf is not None and bf.exists(), f"Cannot run topology verification: missing .blend file for {sp}"
            blend_files.append(str(bf))

        assert len(blend_files) == 10, f"Expected 10 .blend files for BMesh verification, found {len(blend_files)}"

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
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0, f"Headless Blender BMesh manifold topology check failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        assert "BMESH_TOPOLOGY_100_PERCENT_CLEAN" in res.stdout


# =============================================================================
# Dimension 6: Web Viewer & Zero-CORS Synchronization
# =============================================================================
class TestCreatureWebViewerIntegration:
    def test_creature_web_viewer_html_elements(self):
        """R6: Checks that web/creature_viewer.html references all 10 species and contains all required UI controls."""
        viewer_html = WEB_DIR / "creature_viewer.html"
        assert viewer_html.exists(), f"Missing web/creature_viewer.html at {viewer_html}"

        html_text = viewer_html.read_text(encoding="utf-8")

        # 1. References all 10 species
        for sp in TARGET_SPECIES:
            meta = SPECIES_METADATA[sp]
            referenced = (sp in html_text) or (meta["code"] in html_text) or (meta["name_vn"] in html_text)
            assert referenced, f"Species {sp} ({meta['name_vn']}) is not referenced in web/creature_viewer.html"

        # 2. References 8 animation clips
        for canon in CANONICAL_ANIMATIONS:
            assert canon in html_text, f"Canonical animation '{canon}' not referenced in web/creature_viewer.html controls"

        # 3. Armature skeleton overlay toggle
        has_skeleton = ("SkeletonHelper" in html_text) or ("toggleSkeleton" in html_text) or ("btn-toggle-skeleton" in html_text)
        assert has_skeleton, "web/creature_viewer.html must contain SkeletonHelper armature visualization controls"

        # 4. Turnaround modal dialog
        has_modal = ("turnaround-modal" in html_text) or ("openTurnaroundModal" in html_text)
        assert has_modal, "web/creature_viewer.html must contain turnaround modal inspection dialog"

    def test_creature_offline_base64_sha256_sync(self):
        """R6: Checks that web/creature_models_data.js contains base64 payloads matching .glb sha256."""
        models_data_js = WEB_DIR / "creature_models_data.js"
        assert models_data_js.exists(), f"Missing web/creature_models_data.js at {models_data_js}"

        js_text = models_data_js.read_text(encoding="utf-8")

        for sp in TARGET_SPECIES:
            glb_file = resolve_file(ASSETS_CREATURES, sp, ".glb")
            assert glb_file is not None and glb_file.exists(), f"Cannot test base64 sync: missing .glb file for {sp}"

            disk_bytes = glb_file.read_bytes()
            disk_sha256 = hashlib.sha256(disk_bytes).hexdigest()

            candidates = [sp, *[a for a in SPECIES_METADATA[sp].get("aliases", []) if a != sp]]
            found = False
            for cname in candidates:
                pattern = r"[\"']" + re.escape(cname) + r"[\"']\s*:\s*[\"']([A-Za-z0-9+/=\s]+?)[\"']"
                m = re.search(pattern, js_text)
                if m:
                    b64_str = re.sub(r"\s+", "", m.group(1))
                    decoded_bytes = base64.b64decode(b64_str)
                    js_sha256 = hashlib.sha256(decoded_bytes).hexdigest()
                    assert js_sha256 == disk_sha256, \
                        f"SHA256 mismatch for {sp}: disk={disk_sha256} vs JS base64={js_sha256}"
                    found = True
                    break

            assert found, f"Species {sp} payload not found in web/creature_models_data.js"
