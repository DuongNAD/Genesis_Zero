import bpy
import sys

print("=== GEOMETRY NODES INVESTIGATION ===")
node_groups = list(bpy.data.node_groups)
print(f"Total node groups: {len(node_groups)}")
for ng in node_groups:
    print(f"\nNode Group: {ng.name} (type: {ng.type})")
    nodes_summary = {}
    for n in ng.nodes:
        nodes_summary[n.type] = nodes_summary.get(n.type, 0) + 1
    print(f"  Node counts ({len(ng.nodes)} nodes total): {nodes_summary}")
    has_instance = any("INSTANCE" in n.type for n in ng.nodes)
    has_smooth = any("SHADE_SMOOTH" in n.type for n in ng.nodes)
    has_realize = any("REALIZE" in n.type for n in ng.nodes)
    print(f"  Contains Instance on Points: {has_instance}, Set Shade Smooth: {has_smooth}, Realize: {has_realize}")

print("\n=== OBJECTS WITH NODES MODIFIERS ===")
nodes_objs = [o for o in bpy.data.objects if any(m.type == "NODES" for m in o.modifiers)]
print(f"Objects with NODES modifiers: {[o.name for o in nodes_objs]}")
for o in nodes_objs:
    for m in o.modifiers:
        if m.type == "NODES":
            ng_name = m.node_group.name if m.node_group else "NONE"
            print(f"  Object {o.name}: Modifier {m.name}, NodeGroup: {ng_name}, show_viewport={m.show_viewport}, show_render={m.show_render}")

print("\n=== M_Terrain_PBR MATERIAL CHECK ===")
mat = bpy.data.materials.get("M_Terrain_PBR")
if mat:
    bm = getattr(mat, "blend_method", "N/A")
    sm = getattr(mat, "shadow_method", "N/A")
    print(f"M_Terrain_PBR found. blend_method: {bm}, shadow_method: {sm}")
    if mat.use_nodes:
        bsdf = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
        if bsdf:
            alpha_val = bsdf[0].inputs["Alpha"].default_value
            print(f"Principled BSDF Alpha: {alpha_val}")
        else:
            print("No Principled BSDF node found")
else:
    print("M_Terrain_PBR NOT FOUND")

print("\n=== CAVE_ENTRANCE CHECK ===")
cave_ent = bpy.data.objects.get("Cave_Entrance")
if cave_ent:
    print(f"Cave_Entrance found. Location: {cave_ent.location}, Vertices: {len(cave_ent.data.vertices)}, Polygons: {len(cave_ent.data.polygons)}")
    colls = [c.name for c in cave_ent.users_collection]
    print(f"  Collections: {colls}")
    cavern = bpy.data.objects.get("Cave_Cavern")
    if cavern:
        dist = (cave_ent.location - cavern.location).length
        print(f"  Cavern location: {cavern.location}, Distance: {dist:.2f}m")
else:
    print("Cave_Entrance NOT FOUND")

print("\n=== DIORAMA_CUTAWAY_BLOCK SHARP EDGES CHECK ===")
block = bpy.data.objects.get("Diorama_Cutaway_Block")
if block:
    sharp_edges = [e for e in block.data.edges if e.use_edge_sharp]
    print(f"Diorama_Cutaway_Block: total edges: {len(block.data.edges)}, sharp edges: {len(sharp_edges)}")
    print(f"  Modifiers on block: {[m.name for m in block.modifiers]}")
else:
    print("Diorama_Cutaway_Block NOT FOUND")

print("\n=== COLLECTIONS CHECK ===")
for c in bpy.data.collections:
    print(f"Collection '{c.name}': {len(c.objects)} objects: {[o.name for o in c.objects[:5]]}{'...' if len(c.objects)>5 else ''}")

print("\n=== FAUNA ARMATURES & ANIMATIONS CHECK ===")
armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
print(f"Total armatures: {len(armatures)}")
for arm in armatures:
    bones_count = len(arm.data.bones)
    nla_tracks = [t.name for t in arm.animation_data.nla_tracks] if arm.animation_data else []
    active_act = arm.animation_data.action.name if (arm.animation_data and arm.animation_data.action) else "None"
    print(f"  {arm.name}: {bones_count} bones, active action: {active_act}, NLA tracks: {nla_tracks}")

print("\n=== EVALUATED INSTANCES CHECK ===")
depsgraph = bpy.context.evaluated_depsgraph_get()
for o in nodes_objs:
    eval_obj = o.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    print(f"  Evaluated {o.name}: {len(mesh.vertices)} vertices, {len(mesh.polygons)} polygons")
    eval_obj.to_mesh_clear()
