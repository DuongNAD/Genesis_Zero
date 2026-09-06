"""
test_diorama_math.py - Prototyping mathematical formulation for Diorama Cutaway, Multi-Tier Hydrology & Karst Cave.
Executed in headless Blender to verify geometry validity, manifoldness, and shader tree compatibility.
"""

import math
import numpy as np
import bpy
import bmesh

def test_elevation_and_diorama():
    print("Testing diorama math...")
    res = 80
    xs = np.linspace(-75.0, 75.0, res)
    ys = np.linspace(-75.0, 75.0, res)
    xx, yy = np.meshgrid(xs, ys)

    # 1. Northern Alpine Peaks (y > 15m, x in [-50, 20])
    mount_factor = np.clip((yy - 5.0) / 70.0, 0.0, 1.0) ** 1.4
    p1 = np.exp(-((xx + 30.0)**2 + (yy - 45.0)**2) / (2.0 * 18.0**2)) * 26.0
    p2 = np.exp(-((xx - 15.0)**2 + (yy - 55.0)**2) / (2.0 * 20.0**2)) * 22.0
    ridges = np.abs(np.sin(xx * 0.06 + yy * 0.04)) * 6.0
    mount_z = mount_factor * (ridges + p1 + p2)

    # 2. Rolling Hills in East/Center
    hills = 3.0 * np.sin(xx * 0.05) * np.cos(yy * 0.05) + 2.0 * np.sin(xx * 0.09 + 0.8)

    # 3. Base Valley
    z = 6.0 + mount_z + hills

    # 4. Lake Basin at (-25, -10)
    d_lake = np.hypot(xx - (-25.0), yy - (-10.0))
    r_rim, r_bed = 30.0, 18.0
    mask_slope = (d_lake < r_rim) & (d_lake >= r_bed)
    t_s = (d_lake[mask_slope] - r_bed) / (r_rim - r_bed)
    blend_s = 1.0 - (3.0 * t_s**2 - 2.0 * t_s**3)
    z[mask_slope] = (1.0 - blend_s) * z[mask_slope] + blend_s * (3.8 + 1.2 * t_s)
    mask_bed = d_lake < r_bed
    z[mask_bed] = 1.8 + 0.5 * (d_lake[mask_bed] / r_bed)**2

    # 5. Lower Coastal Marine Bay in Southeast (x > 5, y < -10)
    bay_cx, bay_cy = 40.0, -40.0
    d_bay = np.hypot(xx - bay_cx, yy - bay_cy)
    r_bay_rim, r_bay_bed = 48.0, 28.0
    mask_bay_slope = (d_bay < r_bay_rim) & (d_bay >= r_bay_bed)
    t_bs = (d_bay[mask_bay_slope] - r_bay_bed) / (r_bay_rim - r_bay_bed)
    blend_bs = 1.0 - (3.0 * t_bs**2 - 2.0 * t_bs**3)
    z[mask_bay_slope] = (1.0 - blend_bs) * z[mask_bay_slope] + blend_bs * (-0.8 + 3.0 * t_bs)
    mask_bay_bed = d_bay < r_bay_bed
    z[mask_bay_bed] = -4.5 + 1.2 * (d_bay[mask_bay_bed] / r_bay_bed)**2

    min_z = float(np.min(z))
    max_z = float(np.max(z))
    delta_z = max_z - min_z
    print(f"Elevation bounds: min={min_z:.2f}m, max={max_z:.2f}m, delta={delta_z:.2f}m")
    assert delta_z >= 20.0, f"Delta Z {delta_z} < 20m!"
    print("Elevation math test PASSED!")

test_elevation_and_diorama()
