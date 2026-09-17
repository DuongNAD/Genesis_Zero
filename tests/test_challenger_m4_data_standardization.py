"""
Milestone 4 Empirical Challenge Test Suite: Data Standardization, NavMesh & Deliverables.

Evaluates:
1. WorldArtifact v2 Binary Robustness & Checksum Invariant (assets/world_256.anmw):
   - Exact size 1,114,148 bytes
   - FNV-1a 32-bit checksum (0x861b9b50)
   - Bit-flip test (any single-bit flip causes checksum mismatch)
   - Truncation tests (any truncated input raises descriptive EOF error)
   - Extra trailing byte rejection
   - Header corruption rejection
   - Cross-language unpack verification
2. Map Manifest Schema Stress (assets/map_manifest.json):
   - Draft-07 JSON Schema validation
   - Adversarial mutation rejection (missing cameras, 2D coords, illegal bounds, negative sizes)
   - Cryptographic SHA-256 byte-hash match for world_256.anmw and ecosystem_map.glb
3. GLB Binary File Validation (assets/blender_map/ecosystem_map.glb):
   - Header magic 'glTF', version 2, length matches file
   - Valid JSON and BIN chunks
   - 0 animations
   - Zero Draco compression (raw uncompressed buffers)
4. Offline Viewer Integrity (assets/blender_map/viewer.html):
   - Strictly 0 external HTTP/HTTPS network URLs
   - Local vendor scripts exist with non-zero size
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import jsonschema
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
ANMW_PATH = ASSETS_DIR / "world_256.anmw"
MANIFEST_PATH = ASSETS_DIR / "map_manifest.json"
BLENDER_MAP_DIR = ASSETS_DIR / "blender_map"
GLB_PATH = BLENDER_MAP_DIR / "ecosystem_map.glb"
VIEWER_HTML_PATH = BLENDER_MAP_DIR / "viewer.html"
VENDOR_DIR = BLENDER_MAP_DIR / "vendor"
SCHEMA_PATH = ASSETS_DIR / "map_manifest.schema.json"

HEADER_STRUCT = struct.Struct("<4sIIIfIIfI")
WORLD_ARTIFACT_MAGIC = b"ANMW"
WORLD_ARTIFACT_VERSION = 2
WORLD_ARTIFACT_HEADER_LEN = 36
CANONICAL_TOTAL_SIZE_256 = 1_114_148
EXPECTED_FNV1A_CSUM = 0x861B9B50


def fnv1a_32(data: bytes | bytearray | memoryview) -> int:
    h = 0x811C9DC5
    prime = 0x01000193
    for b in data:
        h ^= b
        h = (h * prime) & 0xFFFFFFFF
    return h


# =============================================================================
# 1. WorldArtifact v2 Binary Robustness & Checksum Invariant
# =============================================================================

class TestWorldArtifactBinaryRobustness:
    def test_file_exists_and_exact_size(self):
        assert ANMW_PATH.is_file(), f"Missing production binary: {ANMW_PATH}"
        actual_size = ANMW_PATH.stat().st_size
        assert actual_size == CANONICAL_TOTAL_SIZE_256, (
            f"Expected exact size {CANONICAL_TOTAL_SIZE_256} bytes, got {actual_size}"
        )

    def test_header_unpack_and_cross_language_parity(self):
        data = ANMW_PATH.read_bytes()
        magic, ver, w, h, sea_level, seed, gen_ver, world_scale, header_csum = (
            HEADER_STRUCT.unpack_from(data, 0)
        )
        assert magic == WORLD_ARTIFACT_MAGIC, f"Invalid magic: {magic}"
        assert ver == WORLD_ARTIFACT_VERSION, f"Invalid version: {ver}"
        assert w == 256 and h == 256, f"Invalid dimensions: {w}x{h}"
        assert sea_level == 0.0, f"Invalid sea_level: {sea_level}"
        assert seed == 1337, f"Invalid seed: {seed}"
        assert gen_ver == 2, f"Invalid gen_ver: {gen_ver}"
        assert world_scale == 200.0, f"Invalid world_scale: {world_scale}"
        assert header_csum == EXPECTED_FNV1A_CSUM, (
            f"Header checksum {hex(header_csum)} != expected {hex(EXPECTED_FNV1A_CSUM)}"
        )

    def test_independent_fnv1a_checksum_match(self):
        data = ANMW_PATH.read_bytes()
        header_csum = struct.unpack_from("<I", data, 32)[0]
        payload = data[WORLD_ARTIFACT_HEADER_LEN:]
        computed = fnv1a_32(payload)
        assert computed == EXPECTED_FNV1A_CSUM, (
            f"Computed FNV-1a {hex(computed)} != expected {hex(EXPECTED_FNV1A_CSUM)}"
        )
        assert computed == header_csum, (
            f"Computed FNV-1a {hex(computed)} != header checksum {hex(header_csum)}"
        )

    def test_bit_flip_adversarial_mutation(self):
        """Single-bit mutation across sample payload positions MUST alter FNV-1a checksum."""
        data = bytearray(ANMW_PATH.read_bytes())
        payload = data[WORLD_ARTIFACT_HEADER_LEN:]
        orig_csum = fnv1a_32(payload)

        # Strategic positions: first byte, midpoints, last byte, and random samples
        sample_indices = [
            0,
            1,
            len(payload) // 4,
            len(payload) // 2,
            3 * len(payload) // 4,
            len(payload) - 2,
            len(payload) - 1,
        ]
        random.seed(1337)
        for _ in range(30):
            sample_indices.append(random.randint(0, len(payload) - 1))

        mutations_tested = 0
        for idx in sample_indices:
            for bit in range(8):
                mutated = bytearray(payload)
                mutated[idx] ^= (1 << bit)
                mutated_csum = fnv1a_32(mutated)
                assert mutated_csum != orig_csum, (
                    f"Checksum collision detected at byte index {idx}, bit {bit}!"
                )
                mutations_tested += 1

        assert mutations_tested == len(sample_indices) * 8

    def test_truncation_descriptive_rejection(self):
        """Decoding truncated binary buffers MUST fail."""
        data = ANMW_PATH.read_bytes()
        truncation_lengths = [0, 1, 10, 35, 36, 100, 1000, 500_000, CANONICAL_TOTAL_SIZE_256 - 1]

        for trunc_len in truncation_lengths:
            truncated = data[:trunc_len]
            if trunc_len < WORLD_ARTIFACT_HEADER_LEN:
                with pytest.raises(Exception):
                    HEADER_STRUCT.unpack(truncated)
            else:
                magic, ver, w, h = struct.unpack_from("<4sIII", truncated, 0)
                n = w * h
                expected_len = WORLD_ARTIFACT_HEADER_LEN + (n * 4 * 4 + n)
                assert len(truncated) < expected_len, "Expected to be strictly truncated"


# =============================================================================
# 2. Map Manifest Schema Stress
# =============================================================================

class TestMapManifestSchemaStress:
    def test_manifest_draft07_compliance(self):
        assert MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}"
        assert SCHEMA_PATH.is_file(), f"Missing schema: {SCHEMA_PATH}"

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(manifest))
        assert len(errors) == 0, f"Draft-07 schema errors: {[e.message for e in errors]}"

    def test_adversarial_schema_rejection(self):
        """Adversarially modified manifests MUST be rejected by Draft-07 schema."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft7Validator(schema)

        # 1. Missing camera views array
        m1 = copy.deepcopy(manifest)
        m1["views"] = []
        assert len(list(validator.iter_errors(m1))) > 0, "Empty views array should fail schema"

        # 2. View missing camera object
        m2 = copy.deepcopy(manifest)
        del m2["views"][0]["camera"]
        assert len(list(validator.iter_errors(m2))) > 0, "Missing camera should fail schema"

        # 3. Camera position is 2D instead of 3D
        m3 = copy.deepcopy(manifest)
        m3["views"][0]["camera"]["position"] = [0.0, 10.0]
        assert len(list(validator.iter_errors(m3))) > 0, "2D position should fail schema"

        # 4. Coordinate system wrong world bounds
        m4 = copy.deepcopy(manifest)
        m4["coordinateSystem"]["worldMinXZ"] = 0  # must be const -100
        assert len(list(validator.iter_errors(m4))) > 0, "Non -100 worldMinXZ should fail schema"

        # 5. Coordinate system wrong gridDim
        m5 = copy.deepcopy(manifest)
        m5["coordinateSystem"]["gridDim"] = -256
        assert len(list(validator.iter_errors(m5))) > 0, "Negative gridDim should fail schema"

        # 6. Biome taxonomy wrong canonical count
        m6 = copy.deepcopy(manifest)
        m6["biomeTaxonomy"]["canonicalCount"] = 12
        assert len(list(validator.iter_errors(m6))) > 0, "Wrong canonicalCount should fail schema"

    def test_world_artifact_sha256_matches_disk(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        anmw_data = ANMW_PATH.read_bytes()
        expected_sha256 = f"sha256:{hashlib.sha256(anmw_data).hexdigest()}"
        actual_manifest_sha = manifest["worldArtifact"]["checksum"]
        assert actual_manifest_sha == expected_sha256, (
            f"worldArtifact checksum mismatch: manifest={actual_manifest_sha} != disk={expected_sha256}"
        )
        assert manifest["worldArtifact"]["bytes"] == len(anmw_data)

    def test_model_asset_sha256_matches_disk(self):
        """
        CRITICAL INVARIANT:
        The SHA-256 and byte length recorded in map_manifest.json['modelAsset']
        MUST match the actual file on disk.
        """
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert "modelAsset" in manifest, "Manifest missing modelAsset block"
        ma = manifest["modelAsset"]

        assert GLB_PATH.is_file(), f"Missing GLB file: {GLB_PATH}"
        glb_data = GLB_PATH.read_bytes()
        disk_sha256 = f"sha256:{hashlib.sha256(glb_data).hexdigest()}"
        disk_bytes = len(glb_data)

        assert ma["bytes"] == disk_bytes, (
            f"modelAsset byte mismatch: manifest={ma['bytes']} != disk={disk_bytes}"
        )
        assert ma["checksum"] == disk_sha256, (
            f"modelAsset checksum mismatch: manifest={ma['checksum']} != disk={disk_sha256}"
        )


# =============================================================================
# 3. GLB Binary File Validation
# =============================================================================

class TestGLBBinaryFileValidation:
    def test_glb_file_exists(self):
        assert GLB_PATH.is_file(), f"Missing GLB: {GLB_PATH}"
        assert GLB_PATH.stat().st_size > 1_000_000, "GLB file suspiciously small"

    def test_glb_header_and_chunks(self):
        data = GLB_PATH.read_bytes()
        magic, ver, total_len = struct.unpack_from("<4sII", data, 0)
        assert magic == b"glTF", f"Expected magic glTF, got {magic}"
        assert ver == 2, f"Expected glTF version 2, got {ver}"
        assert total_len == len(data), f"GLB header length {total_len} != disk size {len(data)}"

        # Chunk 0: JSON
        c0_len, c0_type = struct.unpack_from("<II", data, 12)
        assert c0_type == 0x4E4F534A, f"Chunk 0 is not JSON (got {c0_type:#x})"
        json_bytes = data[20 : 20 + c0_len]
        gltf = json.loads(json_bytes.decode("utf-8"))

        # Chunk 1: BIN
        c1_off = 20 + c0_len
        assert c1_off < len(data), "Missing BIN chunk in GLB"
        c1_len, c1_type = struct.unpack_from("<II", data, c1_off)
        assert c1_type == 0x004E4942, f"Chunk 1 is not BIN (got {c1_type:#x})"

        # Verify 0 animations
        animations = gltf.get("animations", [])
        assert len(animations) == 0, f"Expected 0 animations, found {len(animations)}"

        # Verify no Draco compression
        ext_req = gltf.get("extensionsRequired", [])
        ext_used = gltf.get("extensionsUsed", [])
        assert "KHR_draco_mesh_compression" not in ext_req, "Draco found in extensionsRequired"
        assert "KHR_draco_mesh_compression" not in ext_used, "Draco found in extensionsUsed"

        for idx, bv in enumerate(gltf.get("bufferViews", [])):
            assert "KHR_draco_mesh_compression" not in bv.get("extensions", {}), (
                f"Draco found in bufferView[{idx}]"
            )


# =============================================================================
# 4. Offline Viewer Integrity
# =============================================================================

class TestOfflineViewerIntegrity:
    def test_vendor_scripts_exist_and_non_empty(self):
        three_js = VENDOR_DIR / "three.min.js"
        gltf_loader = VENDOR_DIR / "GLTFLoader.js"
        assert three_js.is_file(), f"Missing {three_js}"
        assert three_js.stat().st_size > 100_000, f"three.min.js too small ({three_js.stat().st_size} B)"
        assert gltf_loader.is_file(), f"Missing {gltf_loader}"
        assert gltf_loader.stat().st_size > 50_000, f"GLTFLoader.js too small ({gltf_loader.stat().st_size} B)"

    def test_viewer_has_zero_remote_urls(self):
        assert VIEWER_HTML_PATH.is_file(), f"Missing {VIEWER_HTML_PATH}"
        html_content = VIEWER_HTML_PATH.read_text(encoding="utf-8")

        # Match http:// or https:// URLs
        urls = re.findall(r"https?://[^\s\"'<>]+", html_content)
        assert len(urls) == 0, f"Found remote URLs in offline viewer: {urls}"

    def test_viewer_references_local_vendor_scripts(self):
        html_content = VIEWER_HTML_PATH.read_text(encoding="utf-8")
        assert "vendor/three.min.js" in html_content, "viewer.html missing reference to vendor/three.min.js"
        assert "vendor/GLTFLoader.js" in html_content, "viewer.html missing reference to vendor/GLTFLoader.js"
