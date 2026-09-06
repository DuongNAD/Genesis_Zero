"""
scratch/test_revamped_terrain.py
Interactive development & test script for realistic diorama geomorphology, PBR shaders,
water with foam and reflections, flora, and lighting.
"""
import math
import os
import sys
import bpy
import numpy as np
from mathutils import Vector, Euler

def compute_realistic_elevation(x_in, y_in):
    is_scalar = np.isscalar(x_in) and np.isscalar(y_in)
    if is_scalar:
        x = np.array([float(x_in)], dtype=np.float64)
        y = np.array([float(y_in)], dtype=np.float64)
    else:
        x = np.asarray(x_in, dtype=np.float64)
        y = np.asarray(y_in, dtype=np.float64)

    # 1. Base rolling meadow topography
    z = 5.2 + 2.5 * np.sin(x * 0.035 + 0.4) * np.cos(y * 0.038 - 0.2) \
            + 1.4 * np.sin(x * 0.075 + y * 0.065) \
            + 0.8 * np.cos(x * 0.12 - y * 0.09)

    # 2. Northern Alpine Mountain Massif (Y > 0)
    # Matterhorn-like sharp snowy peak at (-18, 52), Peak 2 at (28, 48), Peak 3 at (-48, 58)
    m_mask = np.clip((y - 2.0) / 65.0, 0.0, 1.0) ** 1.3
    p1 = 26.0 * np.exp(-((x + 18.0) ** 2 + (y - 52.0) ** 2) / (2.0 * 15.0 ** 2))
    p2 = 22.5 * np.exp(-((x - 28.0) ** 2 + (y - 48.0) ** 2) / (2.0 * 16.0 ** 2))
    p3 = 19.0 * np.exp(-((x + 48.0) ** 2 + (y - 58.0) ** 2) / (2.0 * 14.0 ** 2))
    # Mountain ridges and rock crags
    crags = 4.2 * np.abs(np.sin(x * 0.08 + y * 0.055)) + 2.5 * np.abs(np.cos(x * 0.11 - y * 0.07))
    z += m_mask * (p1 + p2 + p3 + crags)

    # 3. Organic Central Lake Basin around (-24, -10)
    lcx, lcy = -24.0, -10.0
    dx_l = x - lcx
    dy_l = y - lcy
    d_raw_lake = np.hypot(dx_l, dy_l)
    ang_l = np.arctan2(dy_l, dx_l)

    # Organic boundary modulation (not a circle! natural coves and peninsulas)
    r_organic_rim = 23.0 + 3.8 * np.cos(2.0 * ang_l + 0.6) + 2.5 * np.sin(3.0 * ang_l) + 1.8 * np.cos(5.0 * ang_l)
    r_organic_bed = r_organic_rim * 0.65

    # Small wooded islet at (-22, -9)
    d_islet = np.hypot(x - (-22.0), y - (-9.0))
    islet_mask = d_islet < 5.0

    mask_lake_deep = (d_raw_lake < r_organic_bed) & (~islet_mask)
    if np.any(mask_lake_deep):
        t = d_raw_lake[mask_lake_deep] / r_organic_bed[mask_lake_deep]
        z[mask_lake_deep] = 1.8 + 0.8 * (t ** 2)

    mask_lake_slope = (d_raw_lake >= r_organic_bed) & (d_raw_lake < r_organic_rim) & (~islet_mask)
    if np.any(mask_lake_slope):
        t = (d_raw_lake[mask_lake_slope] - r_organic_bed[mask_lake_slope]) / (r_organic_rim[mask_lake_slope] - r_organic_bed[mask_lake_slope])
        s = 3.0 * t**2 - 2.0 * t**3
        z[mask_lake_slope] = 2.6 + (4.75 - 2.6) * s

    # Retaining berm around lake
    r_berm = r_organic_rim + 5.5
    mask_berm = (d_raw_lake >= r_organic_rim) & (d_raw_lake < r_berm)
    if np.any(mask_berm):
        t = (d_raw_lake[mask_berm] - r_organic_rim[mask_berm]) / 5.5
        s = 3.0 * t**2 - 2.0 * t**3
        berm_h = 4.75 + 0.45 * np.sin(np.pi * t)
        z[mask_berm] = np.maximum(z[mask_berm], (1.0 - s) * berm_h + s * z[mask_berm])

    # Elevation on islet
    if np.any(islet_mask):
        t_isl = d_islet[islet_mask] / 5.0
        z[islet_mask] = 5.6 - 1.2 * (t_isl ** 2)

    # 4. Coastal Bay in South-East / South Quadrant
    # Natural crescent bay with sandy beach and rocky headland cliffs
    bcx, bcy = 44.0, -44.0
    dx_b = x - bcx
    dy_b = y - bcy
    d_bay = np.hypot(dx_b, dy_b)
    ang_b = np.arctan2(dy_b, dx_b)
    r_bay_rim = 46.0 + 3.0 * np.cos(2.0 * ang_b)
    r_bay_bed = 26.0

    mask_bay_slope = (d_bay < r_bay_rim) & (d_bay >= r_bay_bed)
    if np.any(mask_bay_slope):
        t = (d_bay[mask_bay_slope] - r_bay_bed) / (r_bay_rim[mask_bay_slope] - r_bay_bed)
        s = 3.0 * t**2 - 2.0 * t**3
        # Sea cliffs on north/east side of bay, gentle beach on west
        cliff_bias = np.clip((x[mask_bay_slope] - y[mask_bay_slope] - 20.0) / 40.0, 0.0, 1.0)
        target_z = (-4.2 + 4.2 * s) * (1.0 - cliff_bias * 0.4) + (10.5 * s) * (cliff_bias * 0.6)
        z[mask_bay_slope] = np.minimum(z[mask_bay_slope], target_z)

    mask_bay_bed = d_bay < r_bay_bed
    if np.any(mask_bay_bed):
        z[mask_bay_bed] = -4.5 + 0.6 * (d_bay[mask_bay_bed] / r_bay_bed)**2

    # 5. Continuous River Carving: Cascades -> Lake -> Waterfall Gorge -> Bay
    # Sample points along river
    t_steps = np.linspace(0.0, 1.0, 180)
    # River path:
    # 0.0 to 0.35: Alpine gully (-5, 45) -> (0, 32) -> (6, 20) -> (0, 10) -> Lake (-14, 2)
    # 0.35 to 0.65: Inside Lake
    # 0.65 to 1.0: Lake Outlet (-12, -22) -> Gorge (6, -28) -> Waterfall cliff (22, -36) -> Bay (34, -42)
    rx = np.where(t_steps < 0.35,
                  -5.0 + 35.0 * t_steps + 8.0 * np.sin(t_steps * 14.0),
                  np.where(t_steps < 0.65,
                           -22.0 + 15.0 * (t_steps - 0.35) / 0.30,
                           -12.0 + 46.0 * ((t_steps - 0.65) / 0.35)**1.1 + 4.0 * np.sin((t_steps - 0.65) * 12.0)))
    ry = np.where(t_steps < 0.35,
                  45.0 - 120.0 * t_steps,
                  np.where(t_steps < 0.65,
                           -6.0 - 16.0 * (t_steps - 0.35) / 0.30,
                           -22.0 - 20.0 * ((t_steps - 0.65) / 0.35)))
    rz = np.where(t_steps < 0.35,
                  18.0 - 38.0 * t_steps,
                  np.where(t_steps < 0.65,
                           4.5,
                           np.where(t_steps < 0.90,
                                    4.5 - 4.5 * ((t_steps - 0.65) / 0.25)**2,
                                    0.0)))
    rw = np.where(t_steps < 0.35, 3.2, np.where(t_steps < 0.65, 8.0, 5.0))

    # Carve river
    flat_x = x.ravel()
    flat_y = y.ravel()
    dx_all = flat_x[:, None] - rx[None, :]
    dy_all = flat_y[:, None] - ry[None, :]
    d_sq = dx_all * dx_all + dy_all * dy_all
    min_idx = np.argmin(d_sq, axis=-1)
    min_dist = np.sqrt(np.take_along_axis(d_sq, min_idx[:, None], axis=-1).squeeze(-1))

    rz_near = rz[min_idx].reshape(x.shape)
    rw_near = rw[min_idx].reshape(x.shape)
    min_dist = min_dist.reshape(x.shape)

    # Exclude lake bed and bay bed from river carving
    w_chan = rw_near * 0.5 + 2.2
    mask_riv = (min_dist < w_chan) & (d_raw_lake >= r_organic_bed) & (d_bay >= r_bay_bed)
    if np.any(mask_riv):
        t_b = min_dist[mask_riv] / w_chan[mask_riv]
        s_b = 3.0 * t_b**2 - 2.0 * t_b**3
        bed_cut = rz_near[mask_riv] - 0.9
        z[mask_riv] = (1.0 - s_b) * np.minimum(z[mask_riv], bed_cut) + s_b * z[mask_riv]

    z = np.maximum(z, -4.5)
    if is_scalar:
        return float(z[0])
    return z

print("Function compute_realistic_elevation defined successfully!")
EOF
