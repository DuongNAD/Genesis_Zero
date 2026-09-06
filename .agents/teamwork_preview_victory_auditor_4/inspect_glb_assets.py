import glob
import json
import os
import struct
import sys
from pathlib import Path

glb_files = sorted(glob.glob("assets/flora/**/*.glb", recursive=True))
print(f"Total .glb files: {len(glb_files)}")

report = []
for gf in glb_files:
    slug = Path(gf).stem
    size = os.path.getsize(gf)
    with open(gf, "rb") as f:
        magic, ver, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", f"Bad magic {magic}"
        assert ver == 2, f"Bad ver {ver}"
        assert length == size, f"Header length {length} != file size {size}"

        c0_len, c0_type = struct.unpack("<II", f.read(8))
        assert c0_type == 0x4E4F534A
        meta = json.loads(f.read(c0_len).decode("utf-8"))

        c1_len, c1_type = struct.unpack("<II", f.read(8))
        assert c1_type == 0x004E4942
        bin_data = f.read(c1_len)

    # Check accessors for positions to get bounds
    meshes = meta.get("meshes", [])
    materials = meta.get("materials", [])
    accessors = meta.get("accessors", [])

    tot_primitives = sum(len(m.get("primitives", [])) for m in meshes)

    # Check position min/max bounds across primitives
    pos_bounds = []
    for m in meshes:
        for prim in m.get("primitives", []):
            pos_acc_idx = prim.get("attributes", {}).get("POSITION")
            if pos_acc_idx is not None and pos_acc_idx < len(accessors):
                acc = accessors[pos_acc_idx]
                pos_bounds.append((acc.get("min"), acc.get("max"), acc.get("count")))

    # Check bounding box extents
    has_valid_extent = False
    counts = 0
    for bmin, bmax, cnt in pos_bounds:
        counts += cnt
        if bmin and bmax:
            dx = bmax[0] - bmin[0]
            dy = bmax[1] - bmin[1]
            dz = bmax[2] - bmin[2]
            if dx > 0.001 or dy > 0.001 or dz > 0.001:
                has_valid_extent = True

    report.append({
        "slug": slug,
        "size_kb": size / 1024,
        "meshes": len(meshes),
        "prims": tot_primitives,
        "mats": len(materials),
        "vert_count": counts,
        "valid_extent": has_valid_extent
    })

hdr = f"{'GLB Asset':<32} | {'Size':<9} | {'Meshes':<6} | {'Prims':<5} | {'Mats':<4} | {'Verts':<7} | {'Valid Extent':<12}"
print("\n" + hdr)
print("-" * len(hdr))
for r in report:
    line = f"{r['slug']:<32} | {r['size_kb']:6.1f} KB | {r['meshes']:<6} | {r['prims']:<5} | {r['mats']:<4} | {r['vert_count']:<7} | {str(r['valid_extent']):<12}"
    print(line)

all_valid = all(r["valid_extent"] and r["vert_count"] > 0 and r["mats"] > 0 for r in report)
if all_valid:
    print("\n[SUCCESS] 100% OF GLB ASSETS HAVE VALID GEOMETRY, MATERIALS, AND 3D EXTENTS!")
    sys.exit(0)
else:
    print("\n[ERROR] SOME GLB ASSETS FAILED EXTENT/GEOMETRY CHECKS!")
    sys.exit(1)
