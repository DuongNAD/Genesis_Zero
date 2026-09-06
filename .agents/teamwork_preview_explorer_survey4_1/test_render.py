"""
test_render.py - Renders full 3/4 isometric diorama preview matching reference Image 3.
"""

import os
import sys
import math
import bpy
from mathutils import Vector, Euler

agent_dir = "/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1"
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

import prototype_survey
prototype_survey.build_prototype()

def look_at(obj, target):
    direction = Vector(target) - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

# 1. Setup Camera (3/4 Isometric Perspective)
cam_data = bpy.data.cameras.new("Diorama_Isometric_Camera")
cam_data.lens = 42.0
cam_data.clip_start = 1.0
cam_data.clip_end = 1500.0

cam_obj = bpy.data.objects.new("Diorama_Isometric_Camera", cam_data)
cam_obj.location = Vector((175.0, -175.0, 135.0))
look_at(cam_obj, (0.0, 5.0, 4.0))
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# 2. Atmospheric Lighting
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 4.5
sun_data.color = (1.0, 0.96, 0.90)
sun_data.angle = math.radians(2.0)
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = Euler((math.radians(50.0), math.radians(10.0), math.radians(40.0)))
bpy.context.scene.collection.objects.link(sun_obj)

# Ambient Fill Light
fill_data = bpy.data.lights.new("Fill", type='SUN')
fill_data.energy = 1.2
fill_data.color = (0.75, 0.85, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill_data)
fill_obj.rotation_euler = Euler((math.radians(-40.0), math.radians(-20.0), math.radians(-120.0)))
bpy.context.scene.collection.objects.link(fill_obj)

# 3. Materials
# Terrain Material reading COLOR_0
mat_terrain = bpy.data.materials.new("M_Terrain_Block")
mat_terrain.use_nodes = True
t_nodes = mat_terrain.node_tree.nodes
t_links = mat_terrain.node_tree.links
t_nodes.clear()
t_out = t_nodes.new("ShaderNodeOutputMaterial")
t_out.location = (400, 0)
t_bsdf = t_nodes.new("ShaderNodeBsdfPrincipled")
t_bsdf.location = (0, 0)
t_bsdf.inputs["Roughness"].default_value = 0.75
t_attr = t_nodes.new("ShaderNodeAttribute")
t_attr.location = (-300, 0)
t_attr.attribute_name = "COLOR_0"
t_links.new(t_attr.outputs["Color"], t_bsdf.inputs["Base Color"])
t_links.new(t_bsdf.outputs["BSDF"], t_out.inputs["Surface"])

obj_d = bpy.data.objects.get("Diorama_Block")
if obj_d:
    obj_d.data.materials.append(mat_terrain)

# Realistic Water Material with Volume Absorption
mat_water = bpy.data.materials.new("M_Water_PBR")
mat_water.use_nodes = True
w_nodes = mat_water.node_tree.nodes
w_links = mat_water.node_tree.links
w_nodes.clear()
w_out = w_nodes.new("ShaderNodeOutputMaterial")
w_out.location = (400, 0)
w_bsdf = w_nodes.new("ShaderNodeBsdfPrincipled")
w_bsdf.location = (0, 100)
w_bsdf.inputs["Base Color"].default_value = (0.05, 0.40, 0.45, 0.85)
w_bsdf.inputs["Roughness"].default_value = 0.04
w_bsdf.inputs["Transmission Weight"].default_value = 0.95
w_bsdf.inputs["IOR"].default_value = 1.333
w_links.new(w_bsdf.outputs["BSDF"], w_out.inputs["Surface"])

w_vol = w_nodes.new("ShaderNodeVolumeAbsorption")
w_vol.location = (0, -100)
w_vol.inputs["Color"].default_value = (0.08, 0.45, 0.75, 1.0)
w_vol.inputs["Density"].default_value = 0.20
w_links.new(w_vol.outputs["Volume"], w_out.inputs["Volume"])

mat_water.blend_method = 'BLEND'

for w_name in ["Water_Central_Lake", "Water_Coastal_Bay", "Water_River", "Cave_Pool"]:
    w_obj = bpy.data.objects.get(w_name)
    if w_obj:
        w_obj.data.materials.append(mat_water)

# Cave Rock & Speleothems
mat_speleo = bpy.data.materials.new("M_Speleo")
mat_speleo.use_nodes = True
mat_speleo.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.65, 0.60, 0.52, 1.0)
mat_speleo.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
obj_speleo = bpy.data.objects.get("Cave_Speleothems")
if obj_speleo:
    obj_speleo.data.materials.append(mat_speleo)

mat_cave = bpy.data.materials.new("M_Cave_Rock")
mat_cave.use_nodes = True
mat_cave.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.22, 0.20, 1.0)
obj_cave = bpy.data.objects.get("Cave_Cavern")
if obj_cave:
    obj_cave.data.materials.append(mat_cave)

# 4. Render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
preview_png = os.path.join(agent_dir, "test_render.png")
scene.render.filepath = preview_png

print(f"Rendering full diorama preview to {preview_png}...")
bpy.ops.render.render(write_still=True)
print("Preview render done!")
