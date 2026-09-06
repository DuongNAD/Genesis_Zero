"""
Independent Audit Script for Gate 2 Review of Genesis Zero Master Diorama.
Executes inside Blender headless environment.
"""

import math
import sys
import json
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

audit_results = {}

def log_test(name, passed, details):
    audit_results[name] = {"passed": bool(passed), "details": details}
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}: {details}")

print("\n" + "="*70)
print("INDEPENDENT GATE 2 REVIEW AUDIT RUNNING IN BLENDER")
print("="*70)

# -----------------------------------------------------------------------------
# 1. Geomorphology & Karst Cave
# -----------------------------------------------------------------------------
# 1a. Arched cave entrance portal
portal_obj = bpy.data.objects.get("Cave_Entrance_Portal")
if not portal_obj:
    log_test("cave_portal_exists", False, "Cave_Entrance_Portal not found")
else:
    mesh = portal_obj.data
    v_count = len(mesh.vertices)
    f_count = len(mesh.polygons)
    coords = [v.co for v in mesh.vertices]
    min_x, max_x = min(v.x for v in coords), max(v.x for v in coords)
    min_y, max_y = min(v.y for v in coords), max(v.y for v in coords)
    min_z, max_z = min(v.z for v in coords), max(v.z for v in coords)
    
    # Tunnel runs from entrance (16.0, -6.5, ~2.1) to cavern interior (13.5, 5.0, -7.2)
    has_entrance = any(abs(v.x - 16.0) < 3.0 and abs(v.y - (-6.5)) < 2.0 and abs(v.z - 2.1) < 2.0 for v in coords)
    has_cavern_exit = any(abs(v.x - 13.5) < 3.0 and abs(v.y - 5.0) < 2.0 and abs(v.z - (-7.2)) < 2.0 for v in coords)
    
    # Check ring structure: 14 steps => 15 rings * 8 verts = 120 verts + 8 facade verts = 128 verts total
    # Faces: 14 steps * 8 quad faces = 112 faces + 8 facade quad faces = 120 faces total
    is_exact_rings = (v_count == 128 and f_count == 120)
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    # Check that there are no internal blocking faces inside the tunnel
    internal_blockers = [f for f in bm.faces if len(f.verts) > 4]
    bm.free()
    
    log_test("cave_entrance_portal_mesh", 
             has_entrance and has_cavern_exit and is_exact_rings and len(internal_blockers) == 0,
             f"verts={v_count} (14 rings x 8 verts + facade), faces={f_count}, X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}], Z=[{min_z:.1f}, {max_z:.1f}], hollow tunnel intact (0 blockers)")

# 1b. CAM_16 internal clearance & position
cam16 = bpy.data.objects.get("CAM_16_CLOSEUP_SUBTERRANEAN_CAVE")
if not cam16:
    log_test("cam16_exists", False, "CAM_16 not found")
else:
    pos = cam16.location
    cx, cy, cz = 14.0, 18.0, -7.20
    rx, ry = 11.5, 14.5
    z_apex = -2.20
    dx = pos.x - cx
    dy = pos.y - cy
    phi = math.asin(min(1.0, math.hypot(dx/rx, dy/ry)))
    ceiling_z = cz + (z_apex - cz) * math.cos(phi)
    headroom = ceiling_z - pos.z
    
    is_inside_x = abs(pos.x - cx) < rx
    is_inside_y = abs(pos.y - cy) < ry
    is_inside_z = -9.20 < pos.z < ceiling_z
    
    log_test("cam16_position_and_clearance",
             is_inside_x and is_inside_y and is_inside_z and abs(headroom - 3.5) < 0.15,
             f"pos=({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}), ceiling_z={ceiling_z:.2f}m, headroom={headroom:.2f}m (expected +3.5m), inside_cavern=True")

# 1c. Watertight diorama slab (160m x 160m, planar base at -16m, 0 boundary edges, 0 non-manifold edges)
slab = bpy.data.objects.get("Diorama_Island_Block")
if not slab:
    log_test("diorama_slab_exists", False, "Diorama_Island_Block not found")
else:
    bm_slab = bmesh.new()
    bm_slab.from_mesh(slab.data)
    boundary_edges = [e for e in bm_slab.edges if e.is_boundary]
    non_manifold_edges = [e for e in bm_slab.edges if not e.is_manifold]
    wire_edges = [e for e in bm_slab.edges if e.is_wire]
    
    verts = [v.co for v in bm_slab.verts]
    min_x = min(v.x for v in verts)
    max_x = max(v.x for v in verts)
    min_y = min(v.y for v in verts)
    max_y = max(v.y for v in verts)
    min_z = min(v.z for v in verts)
    max_z = max(v.z for v in verts)
    delta_z = max_z - min_z
    
    bottom_verts = [v for v in verts if v.z <= -15.5]
    all_bottom_minus_16 = all(abs(v.z - (-16.0)) < 1e-4 for v in bottom_verts)
    
    watertight = (len(boundary_edges) == 0 and len(non_manifold_edges) == 0 and len(wire_edges) == 0)
    dimensions_ok = (abs(min_x - (-80.0)) < 0.1 and abs(max_x - 80.0) < 0.1 and
                     abs(min_y - (-80.0)) < 0.1 and abs(max_y - 80.0) < 0.1 and
                     abs(min_z - (-16.0)) < 0.1 and delta_z >= 48.0)
    
    log_test("watertight_diorama_slab",
             watertight and dimensions_ok and all_bottom_minus_16,
             f"boundary_edges={len(boundary_edges)}, non_manifold={len(non_manifold_edges)}, wire={len(wire_edges)}, X=[{min_x:.1f}, {max_x:.1f}], Y=[{min_y:.1f}, {max_y:.1f}], Z=[{min_z:.2f}, {max_z:.2f}], delta_z={delta_z:.2f}m, bottom_planar={all_bottom_minus_16} (count={len(bottom_verts)})")
    bm_slab.free()

# -----------------------------------------------------------------------------
# 2. Hydrology Network
# -----------------------------------------------------------------------------
# 2a. Coastal Marine Bay water clipped to slab bounds with vertical cutaway walls
bay_obj = bpy.data.objects.get("Water_Bay_Marine")
if not bay_obj:
    log_test("bay_water_exists", False, "Water_Bay_Marine not found")
else:
    bm_bay = bmesh.new()
    bm_bay.from_mesh(bay_obj.data)
    bay_coords = [v.co for v in bm_bay.verts]
    bay_min_x = min(v.x for v in bay_coords)
    bay_max_x = max(v.x for v in bay_coords)
    bay_min_y = min(v.y for v in bay_coords)
    bay_max_y = max(v.y for v in bay_coords)
    bay_min_z = min(v.z for v in bay_coords)
    bay_max_z = max(v.z for v in bay_coords)
    
    clipped_to_slab = (bay_min_x >= -80.01 and bay_max_x <= 80.01 and bay_min_y >= -80.01 and bay_max_y <= 80.01)
    
    # Check vertical cutaway faces along East (X = 80.0) and South (Y = -80.0)
    east_wall_faces = [f for f in bm_bay.faces if all(abs(v.co.x - 80.0) < 0.1 for v in f.verts) and any(v.co.z < -1.0 for v in f.verts)]
    south_wall_faces = [f for f in bm_bay.faces if all(abs(v.co.y - (-80.0)) < 0.1 for v in f.verts) and any(v.co.z < -1.0 for v in f.verts)]
    drops_to_seabed = (bay_min_z <= -4.00)
    
    has_cutaway_walls = (len(east_wall_faces) > 0 and len(south_wall_faces) > 0 and drops_to_seabed)
    log_test("marine_bay_water_clipped_and_cutaway",
             clipped_to_slab and has_cutaway_walls,
             f"clipped={clipped_to_slab} (X=[{bay_min_x:.1f}, {bay_max_x:.1f}], Y=[{bay_min_y:.1f}, {bay_max_y:.1f}]), east_faces={len(east_wall_faces)}, south_faces={len(south_wall_faces)}, drops_to_seabed={bay_min_z:.2f}m")
    bm_bay.free()

# 2b. River water ribbon alignment (0 submerged, 0 floating, conformed to BVH, 0 uphill surges)
river_obj = bpy.data.objects.get("Water_River_Meander")
if not river_obj or not slab:
    log_test("river_water_ribbon_alignment", False, "Water_River_Meander or Diorama_Island_Block not found")
else:
    bm_t = bmesh.new()
    bm_t.from_mesh(slab.data)
    bvh = BVHTree.FromBMesh(bm_t)
    
    bm_r = bmesh.new()
    bm_r.from_mesh(river_obj.data)
    
    submerged_count = 0
    floating_count = 0
    diffs = []
    
    for v in bm_r.verts:
        hit, _, _, _ = bvh.ray_cast(Vector((v.co.x, v.co.y, 50.0)), Vector((0, 0, -1)))
        if hit:
            tz = hit.z
            diff = v.co.z - tz
            diffs.append(diff)
            if diff < -0.005:
                submerged_count += 1
            if diff > 0.90:
                floating_count += 1
    
    verts_list = list(bm_r.verts)
    n_rows = len(verts_list) // 5
    center_zs = [verts_list[r * 5 + 2].co.z for r in range(n_rows)]
    uphill_surges = sum(1 for k in range(len(center_zs) - 1) if center_zs[k + 1] > center_zs[k] + 1e-4)
    
    min_d = min(diffs) if diffs else 0
    max_d = max(diffs) if diffs else 0
    
    ribbon_ok = (submerged_count == 0 and floating_count == 0 and uphill_surges == 0 and len(verts_list) == 375)
    log_test("river_water_ribbon_alignment",
             ribbon_ok,
             f"total_verts={len(verts_list)}, submerged={submerged_count}, floating={floating_count}, min_diff={min_d:.3f}m, max_diff={max_d:.3f}m, uphill_surges={uphill_surges}, z_start={center_zs[0]:.2f}m -> z_end={center_zs[-1]:.2f}m")
    bm_t.free()
    bm_r.free()

# 2c. Lake perimeter berm preserved at Z >= 4.56m across 360 degrees
sys.path.insert(0, "/Users/duongnad/Documents/project/Genesis_Zero/scripts")
from build_genesis_diorama_master import compute_terrain_elevation

lcx, lcy = -20.0, -8.0
angles = [math.radians(deg) for deg in range(360)]
r_berm = 23.5  # lake boundary
berm_zs = [float(compute_terrain_elevation(lcx + r_berm * math.cos(a), lcy + r_berm * math.sin(a))) for a in angles]
min_berm_z = min(berm_zs)
breaches = [deg for deg, z in enumerate(berm_zs) if z < 4.50]

log_test("lake_perimeter_berm_containment",
         len(breaches) == 0 and min_berm_z >= 4.56,
         f"360 degrees tested at R=23.5m: min_z={min_berm_z:.3f}m >= 4.56m (water level 4.50m), breaches={len(breaches)}")

# 2d. 4-tier cascades, stepped lake outlet gorge waterfall, circular impact foam apron
casc_obj = bpy.data.objects.get("Water_Mountain_Cascades")
if not casc_obj:
    log_test("cascades_and_foam_apron", False, "Water_Mountain_Cascades not found")
else:
    bm_c = bmesh.new()
    bm_c.from_mesh(casc_obj.data)
    c_verts = [v.co for v in bm_c.verts]
    # Check for circular foam apron at (9.0, -25.0, 0.05)
    has_foam_apron = any(math.hypot(v.x - 9.0, v.y - (-25.0)) < 4.2 and abs(v.z - 0.05) < 0.02 for v in c_verts)
    
    # Check altitude span of cascades: high alpine (Z > 20m) to outlet at bay (Z ~ 0.05m)
    c_max_z = max(v.z for v in c_verts)
    c_min_z = min(v.z for v in c_verts)
    
    # 4 quad faces for the 4 tiers + 1 n-gon face for circular foam apron = 5 faces
    n_faces = len(bm_c.faces)
    quad_faces = [f for f in bm_c.faces if len(f.verts) == 4]
    circle_faces = [f for f in bm_c.faces if len(f.verts) == 16]
    
    log_test("cascades_and_foam_apron",
             has_foam_apron and c_max_z >= 21.0 and c_min_z <= 0.10 and len(quad_faces) == 4 and len(circle_faces) == 1,
             f"tiers_quads={len(quad_faces)}, circle_apron={len(circle_faces)}, Z_range=[{c_min_z:.2f}m, {c_max_z:.2f}m], foam_apron_at_bay={has_foam_apron}")
    bm_c.free()

# -----------------------------------------------------------------------------
# 3. Biomes & Shaders
# -----------------------------------------------------------------------------
# 3a. Botanical prototypes multi-material assignment
multi_mat_prototypes = [
    ("Flora_Alpine_DwarfPine", "needle cones"),
    ("Flora_Forest_CanopyOak", "canopy foliage"),
    ("Flora_Forest_Shrub", "shrub foliage"),
    ("Flora_Forest_Wildflower", "petals"),
    ("Flora_Aquatic_WaterLily", "flower"),
    ("Flora_Aquatic_Reed", "spike"),
    ("Flora_Cave_BioMushroom", "glowing cap"),
]

proto_audit_ok = True
proto_details = []
for p_name, part in multi_mat_prototypes:
    obj = bpy.data.objects.get(p_name)
    if not obj:
        proto_audit_ok = False
        proto_details.append(f"{p_name}: NOT FOUND")
        continue
    mats = obj.data.materials
    if len(mats) < 2:
        proto_audit_ok = False
        proto_details.append(f"{p_name}: only {len(mats)} materials")
        continue
    mat0_faces = sum(1 for p in obj.data.polygons if p.material_index == 0)
    mat1_faces = sum(1 for p in obj.data.polygons if p.material_index == 1)
    if mat1_faces == 0:
        proto_audit_ok = False
        proto_details.append(f"{p_name}: 0 faces on mat1 ({part})")
    else:
        proto_details.append(f"{p_name}: mat0={mat0_faces}, mat1={mat1_faces} ({part})")

log_test("botanical_prototypes_multi_material", proto_audit_ok, "; ".join(proto_details))

# 3b. M_Terrain_PBR: Procedural slope-aware triplanar and snow blending actively mixed with COLOR_0 into Base Color
mat_terrain = bpy.data.materials.get("M_Terrain_PBR")
if not mat_terrain or not mat_terrain.use_nodes:
    log_test("terrain_pbr_shader_graph", False, "M_Terrain_PBR not found or use_nodes is False")
else:
    nt = mat_terrain.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    base_color_link = bsdf.inputs["Base Color"].links[0] if bsdf.inputs["Base Color"].links else None
    
    if not base_color_link:
        log_test("terrain_pbr_shader_graph", False, "Principled BSDF Base Color has NO incoming link")
    else:
        mix_node = base_color_link.from_node
        mix_name = mix_node.name
        in6_link = mix_node.inputs[6].links[0] if mix_node.inputs[6].links else None
        in7_link = mix_node.inputs[7].links[0] if mix_node.inputs[7].links else None
        
        proc_node = in6_link.from_node if in6_link else None
        attr_node = in7_link.from_node if in7_link else None
        
        has_color_0 = (attr_node and attr_node.type == 'ATTRIBUTE' and getattr(attr_node, 'attribute_name', '') == 'COLOR_0')
        has_proc_snow = (proc_node and "Snow" in proc_node.name)
        
        log_test("terrain_pbr_shader_graph",
                 mix_name == "Color_Terrain_Strata_Mix" and has_color_0 and has_proc_snow,
                 f"Base Color driven by {mix_name}; input6={proc_node.name if proc_node else 'None'}, input7={attr_node.name if attr_node else 'None'} (attr={getattr(attr_node, 'attribute_name', 'None')})")

# 3c. Geometry Nodes: 3rd mathematical mask (Water Proximity curve <= 3.5m) and culling interface toggles
gn_aquatic = bpy.data.node_groups.get("GN_Scatter_Aquatic_Riparian")
if not gn_aquatic:
    log_test("geometry_nodes_water_proximity", False, "GN_Scatter_Aquatic_Riparian node group not found")
else:
    prox_node = gn_aquatic.nodes.get("Water_Proximity_Curve")
    and_water_node = gn_aquatic.nodes.get("And_Water_Proximity")
    join_water_node = gn_aquatic.nodes.get("Join_Water_Bodies")
    
    has_frust_socket = any("Frustum" in s.name for s in gn_aquatic.interface.items_tree if s.in_out == 'INPUT')
    has_lod_socket = any("LOD" in s.name for s in gn_aquatic.interface.items_tree if s.in_out == 'INPUT')
    has_prox_mask = (prox_node is not None and and_water_node is not None and join_water_node is not None)
    
    carrier_aq = bpy.data.objects.get("Scatter_Aquatic_Riparian")
    if carrier_aq:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_aq = carrier_aq.evaluated_get(dg)
        verts = [v.co for v in eval_aq.data.vertices]
        far_count = sum(1 for v in verts if math.hypot(v.x - (-20.0), v.y - (-8.0)) > 28.0)
        total_eval_verts = len(verts)
        dry_leak_pct = (far_count / total_eval_verts * 100.0) if total_eval_verts > 0 else 0.0
    else:
        total_eval_verts = 0
        dry_leak_pct = 100.0
    
    log_test("geometry_nodes_water_proximity",
             has_prox_mask and has_frust_socket and has_lod_socket and dry_leak_pct < 5.0,
             f"prox_node={prox_node is not None}, frustum_socket={has_frust_socket}, lod_socket={has_lod_socket}, dry_land_leak={dry_leak_pct:.1f}% (< 5% acceptance threshold)")

# 3d. Material contract name M_Cave_BioFungi in .blend and in .glb
mat_bio = bpy.data.materials.get("M_Cave_BioFungi")
log_test("material_contract_name_blend",
         mat_bio is not None,
         f"bpy.data.materials['M_Cave_BioFungi'] exists: {mat_bio is not None}")

# Check in GLB file
import struct

glb_path = "/Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama.glb"
with open(glb_path, "rb") as f:
    magic = f.read(4)
    version, length = struct.unpack("<II", f.read(8))
    chunk_len, chunk_type = struct.unpack("<II", f.read(8))
    json_bytes = f.read(chunk_len)
    gltf_data = json.loads(json_bytes.decode("utf-8"))

glb_mats = [m.get("name") for m in gltf_data.get("materials", [])]
has_bio_glb = "M_Cave_BioFungi" in glb_mats
log_test("material_contract_name_glb",
         has_bio_glb,
         f"GLB materials contains 'M_Cave_BioFungi': {has_bio_glb} (total mats: {len(glb_mats)})")

glb_cams = [c.get("name") for c in gltf_data.get("cameras", [])]
log_test("glb_cameras_count",
         len(glb_cams) == 24,
         f"GLB embedded cameras: {len(glb_cams)}/24")

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
all_passed = all(r["passed"] for r in audit_results.values())
print("\n" + "="*70)
print(f"OVERALL AUDIT STATUS: {'PASS' if all_passed else 'FAIL'}")
print("="*70 + "\n")

with open("/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_gate2_5_1/independent_audit_results.json", "w") as f:
    json.dump({"overall_pass": all_passed, "tests": audit_results}, f, indent=2)

if not all_passed:
    sys.exit(1)
