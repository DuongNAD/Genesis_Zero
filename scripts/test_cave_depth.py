import math


def calculate_world_height(x: float, y: float) -> float:
    ny = (y + 210.0) / 420.0
    h_base = 12.0 + math.pow(ny, 2.4) * 98.0

    if y > 20.0:
        d_peak1 = math.hypot(x - (-45.0), y - 145.0)
        p1 = max(0.0, 1.0 - d_peak1 / 110.0)
        h_peak1 = math.pow(p1, 2.2) * 58.0

        d_peak2 = math.hypot(x - 65.0, y - 165.0)
        p2 = max(0.0, 1.0 - d_peak2 / 120.0)
        h_peak2 = math.pow(p2, 2.0) * 65.0

        d_ridge = math.hypot(x - 0.0, y - 130.0)
        p_ridge = max(0.0, 1.0 - d_ridge / 130.0)
        h_ridge = math.pow(p_ridge, 1.8) * 35.0
    else:
        h_peak1 = h_peak2 = h_ridge = 0.0

    d_tarn = math.hypot(x - (-70.0), y - 75.0)
    tarn_bowl = -math.pow(1.0 - d_tarn / 45.0, 1.6) * 24.0 if d_tarn < 45.0 else 0.0

    canyon_center_x = 8.0 * math.sin(y * 0.04)
    dist_canyon_axis = abs(x - canyon_center_x)
    canyon_trough = 0.0
    if 10.0 < y < 85.0 and dist_canyon_axis < 30.0:
        c_depth = (1.0 - dist_canyon_axis / 30.0) * math.sin((y - 10.0) / 75.0 * math.pi)
        canyon_trough = -c_depth * 18.0

    d_cliff = math.hypot(x - 10.0, y - 0.0)
    cliff_bulge = math.pow(1.0 - d_cliff / 55.0, 1.5) * 18.0 if d_cliff < 55.0 else 0.0

    d_lake = math.hypot(x - (-5.0), (y - (-95.0)) * 1.15)
    lake_trough = -math.pow(1.0 - d_lake / 85.0, 1.5) * 16.5 if d_lake < 85.0 else 0.0

    d_islet = math.hypot(x - 12.0, y - (-105.0))
    islet_bump = (1.0 - d_islet / 14.0) * 11.5 if d_islet < 14.0 else 0.0

    river_trough = 0.0
    if -65.0 < y < 0.0:
        river_rx = 18.0 * math.sin((y + 15.0) * 0.12)
        dist_r = abs(x - river_rx)
        if dist_r < 18.0:
            river_trough = -math.pow(1.0 - dist_r / 18.0, 1.8) * 6.5

    d_cave = math.hypot((x - (-10.0)) * 1.0, (y - (-15.0)) * 1.2)
    cave_carve = 0.0
    if d_cave < 15.0:
        cave_carve = -math.pow(math.cos(d_cave / 15.0 * math.pi * 0.5), 1.4) * 13.5

    n1 = math.sin(x * 0.032 + y * 0.024) * math.cos(y * 0.028 - x * 0.018) * 8.5
    n2 = math.sin(x * 0.085 - y * 0.075) * math.cos(x * 0.062 + y * 0.091) * 3.2
    n3 = math.sin(x * 0.220 + y * 0.180) * 1.1

    final_h = (h_base + h_peak1 + h_peak2 + h_ridge + tarn_bowl +
               canyon_trough + cliff_bulge + lake_trough + islet_bump +
               river_trough + cave_carve + n1 + n2 + n3)
    return max(-8.0, final_h)

print("--- Cave Hollow Profile ---")
for y in range(-28, -8, 2):
    h = calculate_world_height(-10.0, y)
    print(f"y={y:3d}: h={h:5.2f}m (Water at 14.2m -> Water Depth: {max(0.0, 14.2 - h):4.2f}m)")
