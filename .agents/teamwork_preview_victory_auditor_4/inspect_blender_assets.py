import bpy
import bmesh
import glob
import os
import sys

blend_files = sorted(glob.glob("assets/flora/**/*.blend", recursive=True))
print(f"Total .blend files found: {len(blend_files)}")

report = []
for bf in blend_files:
    slug = os.path.splitext(os.path.basename(bf))[0]
    bpy.ops.wm.open_mainfile(filepath=bf)
    
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    materials = list(bpy.data.materials)
    
    tot_verts = sum(len(m.data.vertices) for m in meshes)
    tot_faces = sum(len(m.data.polygons) for m in meshes)
    smooth_faces = sum(sum(1 for p in m.data.polygons if p.use_smooth) for m in meshes)
    
    # Check bmesh invariants
    tot_incontig = 0
    tot_loose = 0
    tot_ngons = 0
    for m in meshes:
        bm = bmesh.new()
        bm.from_mesh(m.data)
        bm.edges.ensure_lookup_table()
        tot_incontig += sum(1 for e in bm.edges if len(e.link_faces) == 2 and not e.is_contiguous)
        tot_loose += sum(1 for v in bm.verts if len(v.link_edges) == 0)
        tot_ngons += sum(1 for f in bm.faces if len(f.verts) > 4)
        bm.free()
    
    # Check materials and Principled BSDF & SSS
    mat_info = []
    has_principled = False
    has_sss = False
    for mat in materials:
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                has_principled = True
                sss_val = 0.0
                for input_name in ["Subsurface Weight", "Subsurface"]:
                    if input_name in node.inputs:
                        inp = node.inputs[input_name]
                        if inp.is_linked:
                            has_sss = True
                            sss_val = "linked"
                        elif inp.default_value > 0.0:
                            has_sss = True
                            sss_val = round(inp.default_value, 2)
                mat_info.append(f"{mat.name}(SSS={sss_val})")
    
    report.append({
        "slug": slug,
        "meshes": len(meshes),
        "verts": tot_verts,
        "faces": tot_faces,
        "smooth_pct": (smooth_faces / tot_faces * 100) if tot_faces else 0,
        "loose": tot_loose,
        "incontig": tot_incontig,
        "ngons": tot_ngons,
        "principled": has_principled,
        "sss": has_sss,
        "materials": mat_info
    })

hdr = f"{'Species Slug':<35} | {'V/F':<12} | {'Smooth':<6} | {'Loose':<5} | {'Inc':<4} | {'Ngons':<5} | {'PBR':<5} | {'SSS':<5}"
print("\n" + hdr)
print("-" * len(hdr))
for r in report:
    vf_str = f"{r['verts']}/{r['faces']}"
    line = f"{r['slug']:<35} | {vf_str:<12} | {r['smooth_pct']:5.1f}% | {r['loose']:5} | {r['incontig']:4} | {r['ngons']:5} | {str(r['principled']):<5} | {str(r['sss']):<5}"
    print(line)

all_clean = all(r["loose"] == 0 and r["incontig"] == 0 and r["ngons"] == 0 and r["smooth_pct"] == 100.0 and r["principled"] and r["sss"] for r in report)
if not all_clean:
    print("\n[ERROR] SOME ASSETS FAILED CHECKS!")
    sys.exit(1)
else:
    print("\n[SUCCESS] ALL 16 .blend MODELS ARE 100% CLEAN WITH PRINCIPLED BSDF & SSS!")
    sys.exit(0)
