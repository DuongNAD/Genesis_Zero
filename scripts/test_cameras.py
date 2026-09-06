from mathutils import Vector
import math

WILDERNESS_CAMERAS = [
    {
        "name": "CAM_01_WATER_CAVE",
        "loc": Vector((-10.0, -27.0, 15.5)),
        "target": Vector((-10.0, -14.0, 16.5)),
        "focal": 26.0,
    },
    {
        "name": "CAM_02_ALPINE_TARN",
        "loc": Vector((-70.0, 24.0, 52.0)),
        "target": Vector((-70.0, 85.0, 46.0)),
        "focal": 28.0,
    },
    {
        "name": "CAM_03_VALLEY_RIVER",
        "loc": Vector((30.0, -38.0, 24.0)),
        "target": Vector((-5.0, -30.0, 14.0)),
        "focal": 30.0,
    },
    {
        "name": "CAM_04_WATERFALL_CANYON",
        "loc": Vector((18.0, 5.0, 40.0)),
        "target": Vector((-25.0, 42.0, 42.0)),
        "focal": 28.0,
    },
    {
        "name": "CAM_05_LAKE_SOLITUDE",
        "loc": Vector((-8.0, -68.0, 16.5)),
        "target": Vector((10.0, -102.0, 12.5)),
        "focal": 30.0,
    },
    {
        "name": "CAM_OVERVIEW_WILDERNESS",
        "loc": Vector((165.0, -165.0, 135.0)),
        "target": Vector((-10.0, 0.0, 25.0)),
        "focal": 28.0,
    }
]

print("Validated 6 camera parameters:")
for cam in WILDERNESS_CAMERAS:
    dist = (cam["target"] - cam["loc"]).length
    print(f"  {cam['name']}: loc={cam['loc']}, target={cam['target']}, dist={dist:.1f}m, focal={cam['focal']}mm")
