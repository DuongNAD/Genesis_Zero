"""
Genesis Zero — Automated Pytest Suite for 3D Botanical Pipeline
Covers 5 core verification dimensions:
1. Botanical Taxonomy & Metadata Integrity (APG IV, POWO, WFO, GBIF, CoL, vncreatures)
2. Turnaround Concept Sheets (Existence, Dimensions, JPEG Format)
3. 3D Model Master Deliverables (.blend with zstd/BLENDER magic and size > 1KB)
4. glTF 2.0 Binary Container Conformance (Magic, JSON Chunk 0, BIN Chunk 1)
5. Web Viewer & Offline Base64 Binary Synchronization
6. Headless Blender BMesh Mesh Topology Remediation (0 loose verts, 0 ngons, 100% smooth)
"""

import base64
import glob
import json
import os
import re
import struct
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_FLORA = PROJECT_ROOT / "docs" / "flora"
DOCS_SPECIES = DOCS_FLORA / "species"
DOCS_IMAGES = DOCS_FLORA / "images"
ASSETS_FLORA = PROJECT_ROOT / "assets" / "flora"
WEB_DIR = PROJECT_ROOT / "web"
WEB_IMAGES = WEB_DIR / "flora_images"

CORE_SPECIES = [
    "canopy_ancient_oak",
    "canopy_giant_sequoia",
    "canopy_baobab",
    "understory_tree_fern",
    "aquatic_water_lily",
    "aquatic_sacred_lotus",
    "succulent_saguaro_cactus",
    "carnivorous_venus_flytrap",
    "carnivorous_pitcher_plant",
    "cave_bioluminescent_mushroom",
]

SUPPLEMENTARY_SPECIES = [
    "flower_oxeye_daisy",
    "endemic_paphiopedilum_vietnamense",
]

TARGET_SPECIES = CORE_SPECIES + SUPPLEMENTARY_SPECIES

ALL_16_SPECIES = [
    "canopy_ancient_oak",
    "canopy_alpine_pine",
    "canopy_weeping_willow",
    "canopy_giant_sequoia",
    "canopy_baobab",
    "understory_tree_fern",
    "understory_sword_fern",
    "grass_alpine_tussock",
    "aquatic_water_lily",
    "aquatic_sacred_lotus",
    "aquatic_broadleaf_cattail",
    "succulent_saguaro_cactus",
    "succulent_century_agave",
    "carnivorous_pitcher_plant",
    "carnivorous_venus_flytrap",
    "cave_bioluminescent_mushroom",
]

ALL_103_SPECIES = [
    "aquatic_broadleaf_cattail",
    "aquatic_eelgrass",
    "aquatic_elodea",
    "aquatic_hornwort",
    "aquatic_mangrove",
    "aquatic_red_azolla",
    "aquatic_sacred_lotus",
    "aquatic_umbrella_papyrus",
    "aquatic_victoria_lily",
    "aquatic_water_hyacinth",
    "aquatic_water_lily",
    "aquatic_wetland_reed",
    "canopy_alpine_pine",
    "canopy_ancient_banyan",
    "canopy_ancient_ginkgo",
    "canopy_ancient_ironwood",
    "canopy_ancient_oak",
    "canopy_bald_cypress",
    "canopy_baobab",
    "canopy_cedar_lebanon",
    "canopy_giant_sequoia",
    "canopy_rainforest_dipterocarp",
    "canopy_sacred_bodhi",
    "canopy_sugar_pine",
    "canopy_weeping_willow",
    "carnivorous_bladderwort",
    "carnivorous_cobra_lily",
    "carnivorous_jungle_liana",
    "carnivorous_pitcher_plant",
    "carnivorous_sundew",
    "carnivorous_venus_flytrap",
    "carnivorous_wild_orchid",
    "cave_bioluminescent_mushroom",
    "cave_bracket_fungi",
    "cave_ghost_pipe",
    "cave_jack_o_lantern",
    "cave_luminescent_moss",
    "endemic_paphiopedilum_vietnamense",
    "flower_bluebell",
    "flower_corn_poppy",
    "flower_dandelion",
    "flower_lily_valley",
    "flower_morning_glory",
    "flower_oxeye_daisy",
    "flower_purple_coneflower",
    "flower_snowdrop",
    "flower_sweet_flag",
    "flower_wild_geranium",
    "flower_wild_lavender",
    "flower_wild_mint",
    "flower_wild_sunflower",
    "flower_wormwood",
    "grass_alpine_tussock",
    "grass_feather_grass",
    "grass_goosegrass",
    "grass_liverwort",
    "grass_needle_burr",
    "grass_red_fescue",
    "grass_sheeps_fescue",
    "grass_sphagnum_moss",
    "grass_switchgrass",
    "grass_velvet_moss",
    "grass_white_clover",
    "grass_woolly_moss",
    "shrub_alpine_rose",
    "shrub_bay_laurel",
    "shrub_birds_nest_fern",
    "shrub_creeping_juniper",
    "shrub_dogwood",
    "shrub_dwarf_bamboo",
    "shrub_elderberry",
    "shrub_stinging_nettle",
    "shrub_wild_berry",
    "shrub_wild_blackberry",
    "shrub_wild_briar_rose",
    "shrub_wild_hydrangea",
    "succulent_bottle_tree",
    "succulent_burros_tail",
    "succulent_cape_aloe",
    "succulent_century_agave",
    "succulent_desert_rose",
    "succulent_ghost_echeveria",
    "succulent_golden_barrel",
    "succulent_joshua_tree",
    "succulent_living_stones",
    "succulent_prickly_pear",
    "succulent_saguaro_cactus",
    "succulent_tumbleweed",
    "tree_blue_gum",
    "tree_chinese_hackberry",
    "tree_ginkgo",
    "tree_golden_larch",
    "tree_italian_cypress",
    "tree_jacaranda",
    "tree_jungle_palm",
    "tree_magnolia",
    "tree_mountain_cherry",
    "tree_oriental_arborvitae",
    "tree_red_maple",
    "tree_silver_birch",
    "tree_sweet_chestnut",
    "understory_sword_fern",
    "understory_tree_fern",
]

EXPECTED_DB_KEYS = {
    "MG01": {"powo": "296681-1", "wfo": "wfo-0000293123", "gbif": "2878688", "col": "4QVD4"},
    "MG03": {"powo": "263309-1", "wfo": "wfo-0000308871", "gbif": "2684031", "col": "4WS8F"},
    "MG04": {"powo": "558628-1", "wfo": "wfo-0000520448", "gbif": "3152222", "col": "9X2N"},
    "SH02": {"powo": "17068550-1", "wfo": "wfo-0001112442", "gbif": "7299946", "col": "32PRK"},
    "AQ01": {"powo": "605417-1", "wfo": "wfo-0000473523", "gbif": "2882443", "col": "486CP"},
    "AQ02": {"powo": "605335-1", "wfo": "wfo-0000473489", "gbif": "2888881", "col": "467R8"},
    "SC01": {"powo": "62495-2", "wfo": "wfo-0000587219", "gbif": "3084347", "col": "5X9TC"},
    "EX02": {"powo": "321332-1", "wfo": "wfo-0000650965", "gbif": "3190710", "col": "36CDQ"},
    "EX01": {"powo": "603798-1", "wfo": "wfo-0000418381", "gbif": "3702131", "col": "46XBL"},
    "EX05": {"gbif": "2527097", "col": "44TB3"},
    "FL01": {"powo": "230006-1", "wfo": "wfo-0000078028", "gbif": "3142270", "col": "3TB6F"},
    "ED01": {"powo": "1009139-1", "wfo": "wfo-0000262791", "gbif": "2818985", "col": "4CJG8"},
}


class TestBotanicalMetadata:
    """Test Suite 1: APG IV Taxonomy and Database Cross-Referencing"""

    def test_master_catalog_readme_structure(self):
        readme_path = DOCS_FLORA / "README.md"
        assert readme_path.exists(), "docs/flora/README.md does not exist"
        content = readme_path.read_text(encoding="utf-8")
        assert "Bảng Tổng Hợp Đối Chiếu Danh Pháp APG IV" in content, "Missing APG IV master table header"

        for code, db_info in EXPECTED_DB_KEYS.items():
            assert f"**{code}**" in content, f"Code {code} missing in docs/flora/README.md table"
            for db_type, db_val in db_info.items():
                assert db_val in content, f"Expected {db_type} key {db_val} for {code} in README.md"

    @pytest.mark.parametrize("slug", ALL_103_SPECIES)
    def test_species_markdown_metadata_integrity(self, slug):
        spec_path = DOCS_SPECIES / f"{slug}.md"
        assert spec_path.exists(), f"Species specification missing: {spec_path}"
        content = spec_path.read_text(encoding="utf-8")

        assert "Mã Định Danh" in content, f"{slug}: Missing identifier"
        assert ("Hệ Thống Phân Loại" in content or "Phylogeny" in content), f"{slug}: Missing phylogeny"
        assert "Danh Pháp Khoa Học" in content, f"{slug}: Missing scientific name"
        assert "Mã Cơ Sở Dữ Liệu Đối Chiếu" in content, f"{slug}: Missing database IDs"
        assert ("Sinh Cảnh Genesis Zero" in content or "Sinh Cảnh Tự Nhiên" in content), f"{slug}: Missing habitat"

        assert "file:///" not in content, f"{slug}: contains non-portable file:/// absolute URI"

        rel_img = f"../images/{slug}_turnaround.jpg"
        assert rel_img in content, f"{slug}: Missing relative turnaround image link: {rel_img}"

        # Assert all relative links in this spec resolve to existing files on disk
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
            label, target = m.groups()
            if not target.startswith("http") and not target.startswith("#") and not target.startswith("mailto:"):
                fpart = target.split("#")[0]
                if fpart:
                    res = (spec_path.parent / fpart).resolve()
                    assert res.exists(), f"{slug}: Link '{target}' ({label}) does not resolve to existing file: {res}"

    def test_no_file_uri_in_all_flora_docs(self):
        """Verify 0 occurrences of file:/// in any .md file under docs/flora/."""
        md_files = sorted(glob.glob(str(DOCS_FLORA / "**/*.md"), recursive=True))
        assert len(md_files) > 0, "No markdown files found in docs/flora/"
        violating = []
        for p in md_files:
            content = Path(p).read_text(encoding="utf-8")
            if "file:///" in content:
                violating.append(Path(p).name)
        assert len(violating) == 0, f"Found non-portable file:/// URIs in: {violating}"

    def test_all_flora_markdown_links_resolve_to_filesystem(self):
        """Verify all markdown links across all 103 species resolve to existing files on disk."""
        species_files = sorted(glob.glob(str(DOCS_SPECIES / "*.md")))
        assert len(species_files) == 103, f"Expected 103 species markdown files, found {len(species_files)}"
        broken = []
        for sf in species_files:
            content = Path(sf).read_text(encoding="utf-8")
            for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
                label, target = m.groups()
                if not target.startswith("http") and not target.startswith("#") and not target.startswith("mailto:"):
                    fpart = target.split("#")[0]
                    if fpart:
                        res = (Path(sf).parent / fpart).resolve()
                        if not res.exists():
                            broken.append((Path(sf).name, label, target))
        assert len(broken) == 0, f"Found {len(broken)} broken links in docs/flora/species/: {broken[:5]}"


class TestTurnaroundImages:
    """Test Suite 2: 4-Angle Concept Turnaround Sheets"""

    @pytest.mark.parametrize("slug", ALL_103_SPECIES)
    def test_turnaround_image_deliverables(self, slug):
        web_img = WEB_IMAGES / f"{slug}_turnaround.jpg"
        docs_img = DOCS_IMAGES / f"{slug}_turnaround.jpg"

        assert web_img.exists(), f"Missing turnaround image in web/flora_images: {web_img}"
        assert docs_img.exists(), f"Missing turnaround image in docs/flora/images: {docs_img}"

        # Assert valid non-empty JPEG (> 50KB)
        web_size = web_img.stat().st_size
        assert web_size > 50000, f"Web image unexpectedly small ({web_size} bytes): {web_img}"

        docs_size = docs_img.stat().st_size
        assert docs_size > 50000, f"Docs image unexpectedly small ({docs_size} bytes): {docs_img}"

        # Assert JPEG binary magic (SOI and EOI markers)
        with open(web_img, "rb") as f:
            soi = f.read(2)
            f.seek(-2, os.SEEK_END)
            eoi = f.read(2)
        assert soi == b"\xff\xd8", f"{web_img} missing JPEG SOI marker"
        assert eoi == b"\xff\xd9", f"{web_img} missing JPEG EOI marker"


class TestThreeDDeliverables:
    """Test Suite 3 & 4: 3D Model Deliverables (.blend, .glb, glTF 2.0 Conformance)"""

    def test_all_103_blend_and_glb_present(self):
        blend_files = glob.glob(str(ASSETS_FLORA / "**/*.blend"), recursive=True)
        glb_files = glob.glob(str(ASSETS_FLORA / "**/*.glb"), recursive=True)

        assert len(blend_files) == 103, f"Expected 103 .blend files, found {len(blend_files)}"
        assert len(glb_files) == 103, f"Expected 103 .glb files, found {len(glb_files)}"

    @pytest.mark.parametrize("slug", ALL_103_SPECIES)
    def test_blend_file_integrity(self, slug):
        matches = glob.glob(str(ASSETS_FLORA / f"**/{slug}.blend"), recursive=True)
        assert len(matches) == 1, f"Expected 1 .blend file for {slug}, found {len(matches)}"
        bf = matches[0]
        size = os.path.getsize(bf)
        assert size > 1000, f"{bf} is unexpectedly small ({size} bytes)"

        # Accept uncompressed 'BLEN' or zstandard compressed frame (0x28B52FFD)
        with open(bf, "rb") as f:
            magic = f.read(4)
        is_valid = (magic == b"BLEN") or (magic == b"\x28\xb5\x2f\xfd")
        assert is_valid, f"{bf} has invalid header magic: {magic}"

    @pytest.mark.parametrize("slug", ALL_103_SPECIES)
    def test_gltf2_binary_chunk_conformance(self, slug):
        matches = glob.glob(str(ASSETS_FLORA / f"**/{slug}.glb"), recursive=True)
        assert len(matches) == 1, f"Expected 1 .glb file for {slug}, found {len(matches)}"
        gf = matches[0]
        fsize = os.path.getsize(gf)
        assert fsize > 1000, f"{gf} is unexpectedly small ({fsize} bytes)"

        with open(gf, "rb") as f:
            # 12-byte header
            magic, ver, length = struct.unpack("<4sII", f.read(12))
            assert magic == b"glTF", f"{gf}: Invalid glTF magic"
            assert ver == 2, f"{gf}: Not glTF 2.0 (version={ver})"
            assert length == fsize, f"{gf}: Header length {length} != file size {fsize}"

            # Chunk 0: JSON metadata
            c0_len, c0_type = struct.unpack("<II", f.read(8))
            assert c0_type == 0x4E4F534A, f"{gf}: Chunk 0 is not JSON"
            meta = json.loads(f.read(c0_len).decode("utf-8"))

            assert meta.get("asset", {}).get("version") == "2.0", f"{gf}: asset.version is not 2.0"
            assert len(meta.get("meshes", [])) >= 1, f"{gf}: missing mesh primitives"
            assert len(meta.get("materials", [])) >= 1, f"{gf}: missing materials"

            # Chunk 1: BIN chunk
            c1_len, c1_type = struct.unpack("<II", f.read(8))
            assert c1_type == 0x004E4942, f"{gf}: Chunk 1 is not BIN"
            assert c1_len > 0, f"{gf}: BIN chunk length is 0"


class TestWebViewerSynchronization:
    """Test Suite 5: Web Viewer and Base64 Offline Storage Sync"""

    def test_web_viewer_html_catalog_entries(self):
        html_file = WEB_DIR / "flora_viewer.html"
        assert html_file.exists(), "web/flora_viewer.html missing"
        html = html_file.read_text(encoding="utf-8")

        assert "badge-turnaround" in html, "Badge markup missing in HTML"
        assert "4 Góc 📷" in html, "Badge text missing in HTML"
        assert "turnaround-modal" in html, "Turnaround modal missing in HTML"
        assert "openTurnaroundModal" in html, "Modal handler missing in HTML"

        for slug in ALL_103_SPECIES:
            assert f'id: "{slug}"' in html, f"Species {slug} not defined in FLORA_DATABASE"
            assert f'turnaroundImg: "flora_images/{slug}_turnaround.jpg"' in html, \
                f"turnaroundImg missing for species {slug}"

    def test_offline_base64_exact_byte_sync(self):
        js_file = WEB_DIR / "flora_models_data.js"
        assert js_file.exists(), "web/flora_models_data.js missing"
        js_text = js_file.read_text(encoding="utf-8")

        glb_files = glob.glob(str(ASSETS_FLORA / "**/*.glb"), recursive=True)
        assert len(glb_files) == 103, f"Expected 103 .glb files, found {len(glb_files)}"

        for gf in glb_files:
            slug = Path(gf).stem
            disk_bytes = Path(gf).read_bytes()

            disk_b64 = base64.b64encode(disk_bytes).decode("ascii")

            m = re.search(r"\"" + slug + r"\":\s*\"([^\"]+)\"", js_text)
            assert m is not None, f"{slug} not found in FLORA_MODELS_BASE64 in flora_models_data.js"
            js_b64 = m.group(1)

            assert js_b64 == disk_b64, f"Base64 mismatch for {slug}: disk length {len(disk_b64)} vs JS {len(js_b64)}"


class TestBlenderMeshTopologyRemediation:
    """Test Suite 6: Headless Blender BMesh Mesh Topology Verification"""

    def test_all_103_blend_files_clean_bmesh_topology(self):
        import shutil

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

        cmd = [
            blender_bin,
            "--background",
            "--python-expr",
            """
import bpy, bmesh, glob, os, sys

blend_files = sorted(glob.glob("assets/flora/**/*.blend", recursive=True))
assert len(blend_files) == 103, f"Expected 103 .blend files, found {len(blend_files)}"

defects = []
for bf in blend_files:
    bpy.ops.wm.open_mainfile(filepath=bf)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for m in meshes:
        bm = bmesh.new()
        bm.from_mesh(m.data)
        bm.edges.ensure_lookup_table()
        incontiguous_edges = sum(1 for e in bm.edges if len(e.link_faces) == 2 and not e.is_contiguous)
        loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)
        multi_face_edges = sum(1 for e in bm.edges if len(e.link_faces) > 2)
        wire_edges = sum(1 for e in bm.edges if len(e.link_faces) == 0)
        ngons = sum(1 for p in bm.faces if len(p.verts) > 4)
        non_smooth = sum(1 for p in m.data.polygons if not p.use_smooth)
        bm.free()

        if incontiguous_edges > 0 or loose_verts > 0 or multi_face_edges > 0 or wire_edges > 0 or ngons > 0 or non_smooth > 0:
            defects.append({
                "file": os.path.basename(bf),
                "mesh": m.name,
                "incontiguous_edges": incontiguous_edges,
                "loose_verts": loose_verts,
                "multi_face_edges": multi_face_edges,
                "wire_edges": wire_edges,
                "ngons": ngons,
                "non_smooth": non_smooth
            })

if defects:
    print("DEFECTS FOUND:", defects)
    sys.exit(1)
else:
    print(f"ALL {len(blend_files)} MODELS 100% CLEAN: 0 incontiguous edges, 0 loose verts, 0 ngons, 0 multi-face edges, 0 wire edges, 100% smooth")
    sys.exit(0)
"""
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Blender BMesh verification failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        assert "MODELS 100% CLEAN" in result.stdout
