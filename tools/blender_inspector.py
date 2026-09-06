"""
Blender 3D Multi-Angle Inspector Tool
Allows AI and developers to rotate Blender's viewport/cameras across preset angles,
capture snapshots, and build a unified 2x2 vision grid for visual inspection.
"""

import math
from typing import Dict, Any

# Standard 4-angle inspection presets
PRESET_ANGLES: Dict[str, Dict[str, Any]] = {
    "topdown": {
        "label": "1. Top-Down (Bird's Eye)",
        "pitch_deg": 0.0,
        "yaw_deg": 0.0,
        "location": (0.0, 0.0, 0.0),
        "distance": 220.0,
    },
    "iso_sw": {
        "label": "2. Southwest (Valley -> Peak)",
        "pitch_deg": 55.0,
        "yaw_deg": -45.0,
        "location": (10.0, 10.0, 5.0),
        "distance": 160.0,
    },
    "iso_ne": {
        "label": "3. Northeast (Ridge -> Lake)",
        "pitch_deg": 60.0,
        "yaw_deg": 135.0,
        "location": (0.0, 20.0, 5.0),
        "distance": 180.0,
    },
    "closeup_lake": {
        "label": "4. Close-Up (Lake Shore)",
        "pitch_deg": 75.0,
        "yaw_deg": -30.0,
        "location": (-20.0, -30.0, 2.0),
        "distance": 70.0,
    },
}


def get_blender_rotation_code(preset_name: str, hide_overlays: bool = True) -> str:
    """Generate Blender Python snippet to orient the 3D viewport."""
    cfg = PRESET_ANGLES[preset_name]
    pitch = math.radians(cfg["pitch_deg"])
    yaw = math.radians(cfg["yaw_deg"])
    loc = cfg["location"]
    dist = cfg["distance"]

    return f"""import bpy
import mathutils

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        r3d = area.spaces.active.region_3d
        r3d.view_rotation = mathutils.Euler(({pitch}, 0.0, {yaw}), 'XYZ').to_quaternion()
        r3d.view_location = mathutils.Vector({loc})
        r3d.view_distance = {dist}
        area.spaces.active.overlay.show_overlays = {not hide_overlays}
        area.tag_redraw()
"""
