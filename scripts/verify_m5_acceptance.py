"""
Milestone 5 Physical Acceptance Deliverables Verification Script
Genesis_Zero Primordial Abiotic 3D Map
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

from PIL import Image, ImageStat

GENESIS_ZERO = Path(r"e:/Project/01_AI_Agents/Genesis_Zero")
ASSETS_DIR = GENESIS_ZERO / "assets"
BLENDER_MAP_DIR = ASSETS_DIR / "blender_map"


def verify_world_artifact():
    print("=== 1. VERIFYING assets/world_256.anmw ===")
    anmw_path = ASSETS_DIR / "world_256.anmw"
    assert anmw_path.exists(), f"File missing: {anmw_path}"
    anmw_bytes = anmw_path.read_bytes()
    anmw_size = len(anmw_bytes)
    print(f"File size: {anmw_size:,} bytes")
    assert anmw_size == 1_114_148, f"Expected 1,114,148 bytes, got {anmw_size}"

    HEADER_STRUCT = struct.Struct("<4sIIIfIIfI")
    magic, ver, width, height, sea_level, seed, gen_ver, world_scale, stored_csum = HEADER_STRUCT.unpack_from(anmw_bytes, 0)
    print(f"Header: magic={magic}, version={ver}, width={width}, height={height}, sea_level={sea_level}, seed={seed}, gen_ver={gen_ver}, world_scale={world_scale}, stored_checksum=0x{stored_csum:08x}")
    assert magic == b"ANMW", f"Invalid magic: {magic}"
    assert ver == 2, f"Invalid version: {ver}"
    assert width == 256 and height == 256, f"Invalid dimensions: {width}x{height}"
    assert world_scale == 200.0, f"Invalid scale: {world_scale}"
    assert sea_level == 0.0, f"Invalid sea level: {sea_level}"

    def fnv1a_32(data: bytes) -> int:
        h = 0x811C9DC5
        for b in data:
            h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
        return h

    computed_csum = fnv1a_32(anmw_bytes[36:])
    print(f"Computed FNV-1a checksum: 0x{computed_csum:08x}")
    assert computed_csum == 0x861B9B50, f"Expected checksum 0x861b9b50, got 0x{computed_csum:08x}"
    assert stored_csum == 0x861B9B50, f"Header checksum mismatch: 0x{stored_csum:08x}"
    print(">>> world_256.anmw PASSED: Exact 1,114,148 bytes and FNV-1a 0x861b9b50 confirmed.")


def verify_manifest_and_glb():
    print("\n=== 2. VERIFYING map_manifest.json and ecosystem_map.glb ===")
    manifest_path = ASSETS_DIR / "map_manifest.json"
    glb_path = BLENDER_MAP_DIR / "ecosystem_map.glb"

    assert manifest_path.exists(), "map_manifest.json missing"
    assert glb_path.exists(), "ecosystem_map.glb missing"

    glb_bytes = glb_path.read_bytes()
    glb_size = len(glb_bytes)
    glb_sha256 = f"sha256:{hashlib.sha256(glb_bytes).hexdigest()}"

    print(f"ecosystem_map.glb size: {glb_size:,} bytes")
    print(f"ecosystem_map.glb SHA-256: {glb_sha256}")

    expected_glb_size = 8_773_452
    expected_glb_sha256 = "sha256:4967e070538763135507dcabe30c341b3b27ed6b00544c42f585d3b887ef8caa"

    assert glb_size == expected_glb_size, f"Expected size {expected_glb_size}, got {glb_size}"
    assert glb_sha256 == expected_glb_sha256, f"Expected hash {expected_glb_sha256}, got {glb_sha256}"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_asset = manifest.get("modelAsset", {})
    manifest_bytes = model_asset.get("bytes")
    manifest_checksum = model_asset.get("checksum")

    print(f"Manifest modelAsset bytes: {manifest_bytes:,}")
    print(f"Manifest modelAsset checksum: {manifest_checksum}")

    assert manifest_bytes == glb_size, f"Manifest bytes mismatch: {manifest_bytes} != {glb_size}"
    assert manifest_checksum == glb_sha256, f"Manifest checksum mismatch: {manifest_checksum} != {glb_sha256}"
    print(">>> map_manifest.json and ecosystem_map.glb PASSED: Exact SHA-256 and byte length parity confirmed.")


def verify_blender_map_directory():
    print("\n=== 3. VERIFYING assets/blender_map/ DIRECTORY CONTENTS ===")
    entries = sorted(list(BLENDER_MAP_DIR.iterdir()))
    files = [e for e in entries if e.is_file()]
    dirs = [e for e in entries if e.is_dir()]

    print(f"Total entries: {len(entries)}")
    print(f"Subdirectories ({len(dirs)}): {[d.name for d in dirs]}")
    print(f"Files ({len(files)}): {[f.name for f in files]}")

    dir_names = {d.name for d in dirs}
    expected_dirs = {"vendor", "renders"}
    assert dir_names == expected_dirs, f"Expected subdirectories {expected_dirs}, got: {dir_names}"

    expected_files = {
        "ecosystem_map.blend",
        "ecosystem_map.glb",
        "render_closeup_water_cavern.png",
        "render_iso_overview.png",
        "render_ne_angle.png",
        "render_top_down.png",
        "simulation_heightmap.json",
        "viewer.html",
    }
    actual_files = {f.name for f in files}
    assert actual_files == expected_files, f"File set mismatch: {actual_files ^ expected_files}"
    assert len(files) == 8, f"Expected exactly 8 files, found {len(files)}"

    vendor_files = sorted([f.name for f in (BLENDER_MAP_DIR / "vendor").iterdir() if f.is_file()])
    print(f"vendor/ files: {vendor_files}")
    assert "three.min.js" in vendor_files and "GLTFLoader.js" in vendor_files, "Missing vendor libraries"

    renders_files = sorted([f.name for f in (BLENDER_MAP_DIR / "renders").iterdir() if f.is_file()])
    print(f"renders/ files: {renders_files}")
    expected_renders_subdir = {"closeup_water_cavern.png", "northeast_angle.png", "overview.png", "topdown.png"}
    assert expected_renders_subdir.issubset(set(renders_files)), f"Missing required renders: {expected_renders_subdir - set(renders_files)}"
    print(">>> assets/blender_map/ directory audit PASSED: Strictly 8 abiotic files, vendor/, and renders/ directories.")


def verify_visual_acceptance_renders():
    print("\n=== 4. VERIFYING 4 VISUAL ACCEPTANCE RENDERS ===")
    renders = [
        "render_iso_overview.png",
        "render_ne_angle.png",
        "render_top_down.png",
        "render_closeup_water_cavern.png",
    ]
    for r_name in renders:
        r_path = BLENDER_MAP_DIR / r_name
        assert r_path.exists(), f"Render missing: {r_name}"
        r_size = r_path.stat().st_size
        img = Image.open(r_path)
        w, h = img.size
        stat = ImageStat.Stat(img.convert("L"))
        mean_lum = stat.mean[0]

        print(f"  {r_name}: {w}x{h}, size={r_size:,} bytes, mean_luminance={mean_lum:.2f}")
        assert (w, h) == (1280, 720), f"Invalid dimensions {(w, h)} for {r_name}, expected (1280, 720)"
        assert r_size > 1_100_000, f"File size too small ({r_size} <= 1.1MB) for {r_name}"
        assert mean_lum > 50.0, f"Mean luminance too low ({mean_lum:.2f} <= 50) for {r_name} (black image regression)"
    print(">>> Visual acceptance renders PASSED: 4 renders at 1280x720, non-black, > 1.1MB each.")


def verify_viewer_html():
    print("\n=== 5. VERIFYING viewer.html OFFLINE INTEGRITY ===")
    viewer_path = BLENDER_MAP_DIR / "viewer.html"
    assert viewer_path.exists(), "viewer.html missing"
    content = viewer_path.read_text(encoding="utf-8")

    urls = re.findall(r"https?://[^\s\"\'<>]+", content)
    print(f"External URLs in viewer.html: {urls}")
    assert len(urls) == 0, f"External network URLs found in viewer.html: {urls}"

    assert "vendor/three.min.js" in content, "Missing vendor/three.min.js link in viewer.html"
    assert "vendor/GLTFLoader.js" in content, "Missing vendor/GLTFLoader.js link in viewer.html"
    assert 'id="canvas-container"' in content, "Canvas container missing from viewer.html"
    assert "setCamera" in content, "Missing setCamera function in viewer.html"
    assert "toggleLighting" in content, "Missing toggleLighting function in viewer.html"
    print(">>> viewer.html PASSED: Strictly 0 external network requests, clean local vendor sourcing.")


def verify_pure_abiotic_invariant():
    print("\n=== 6. VERIFYING PURE ABIOTIC INVARIANT (0% FLORA, 0% FAUNA) ===")
    glb_path = BLENDER_MAP_DIR / "ecosystem_map.glb"
    glb_bytes = glb_path.read_bytes()

    magic, version, total_len = struct.unpack("<4sII", glb_bytes[:12])
    assert magic == b"glTF" and version == 2, "Invalid glTF header"

    json_chunk_len, json_chunk_type = struct.unpack("<II", glb_bytes[12:20])
    assert json_chunk_type == 0x4E4F534A, "First chunk is not JSON"
    gltf_json = json.loads(glb_bytes[20:20 + json_chunk_len].decode("utf-8"))

    biological_tokens = [
        "tree", "pine", "broadleaf", "oak", "bush", "shrub", "grass", "plant",
        "flower", "reed", "flora", "moss", "leaf", "leaves", "animal", "fauna",
        "creature", "deer", "stag", "goat", "ibex", "eagle", "fish", "frog",
        "bat", "bird", "ferret", "skink", "hare", "croc", "tarantula", "hunter", "sentinel"
    ]

    mesh_names = [m.get("name", "") for m in gltf_json.get("meshes", [])]
    node_names = [n.get("name", "") for n in gltf_json.get("nodes", [])]
    material_names = [mat.get("name", "") for mat in gltf_json.get("materials", [])]

    print(f"Total Meshes in GLB: {len(mesh_names)}")
    print(f"Total Nodes in GLB: {len(node_names)}")
    print(f"Total Materials in GLB: {len(material_names)}")

    for category, names in [("Mesh", mesh_names), ("Node", node_names), ("Material", material_names)]:
        for name in names:
            lower = name.lower()
            for token in biological_tokens:
                assert token not in lower, f"Violation: Biological token '{token}' in {category} name '{name}'"

    animations = gltf_json.get("animations", [])
    print(f"Total Animations in GLB: {len(animations)}")
    assert len(animations) == 0, f"Expected 0 animations, got {len(animations)}"

    preset_path = Path(r"E:/tool/mcp/terra_forge/terra_forge/schema/presets/genesis_primordial_abiotic.json")
    assert preset_path.exists(), "Preset missing"
    preset = json.loads(preset_path.read_text(encoding="utf-8"))
    biomes = preset.get("biomes", None)
    print(f"Preset biomes list: {biomes}")
    assert biomes == [], f"Preset biomes must be strictly empty [], got: {biomes}"

    manifest_path = ASSETS_DIR / "map_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "vegetation" not in manifest or len(manifest["vegetation"]) == 0
    assert "flora" not in manifest or len(manifest["flora"]) == 0
    assert "fauna" not in manifest or len(manifest["fauna"]) == 0
    assert "creatures" not in manifest or len(manifest["creatures"]) == 0
    print("Manifest pure abiotic check: strictly 0 flora/fauna/vegetation/creatures fields.")

    print(">>> Pure abiotic invariant PASSED: Strictly 0% flora and 0% fauna verified across GLB, preset, and manifest.")


if __name__ == "__main__":
    verify_world_artifact()
    verify_manifest_and_glb()
    verify_blender_map_directory()
    verify_visual_acceptance_renders()
    verify_viewer_html()
    verify_pure_abiotic_invariant()
    print("\n========================================================")
    print("ALL 6 PHYSICAL ACCEPTANCE DELIVERABLES 100% VERIFIED!")
    print("========================================================")
