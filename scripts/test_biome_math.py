import math


def get_soil_factor(x, y, z, slope):
    # Forest Grove Centers
    groves = [
        (-45.0, 25.0, 32.0),   # Pine forest west
        (45.0, 15.0, 30.0),    # Oak woods east
        (-35.0, -35.0, 26.0),  # Birch grove southwest
        (35.0, -25.0, 28.0),   # Mixed woodland southeast
        (-15.0, -5.0, 20.0),   # Cavern cliff woods
    ]
    max_forest = 0.0
    for gx, gy, gr in groves:
        d = math.hypot(x - gx, y - gy)
        if d < gr:
            factor = math.pow(1.0 - d / gr, 1.4)
            if factor > max_forest:
                max_forest = factor

    # Slope erosion
    is_scree = (0.24 < slope < 0.55 and z > 16.0)

    # Riverbank proximity
    river_rx = 18.0 * math.sin((y + 15.0) * 0.12)
    dist_river = abs(x - river_rx) if -65.0 < y < 5.0 else 999.0
    is_riverbank = (dist_river < 12.0 and z < 18.0)

    # Lake beach proximity
    dist_lake = math.hypot(x - (-5.0), (y - (-95.0)) * 1.15)
    is_lake_shore = (dist_lake < 82.0 and z < 13.5)

    return {
        "forest_loam": max_forest,
        "is_scree": is_scree,
        "is_riverbank": is_riverbank,
        "is_lake_shore": is_lake_shore
    }

print("Tested Biome Math successfully.")
