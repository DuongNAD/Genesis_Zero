# Survey Report — Flora Elevation Snapping & Terrain Invariant Verification

**Agent**: `teamwork_preview_explorer_iter2_3`  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_3`  
**Date**: 2026-09-04T00:10:00Z  
**Status**: Investigation Complete — Ready for Worker Implementation  

---

## 1. Executive Summary

Empirical investigation demonstrates that the observed 6-9.6cm float on 6 wetland reeds is caused by evaluating the continuous analytical mathematical function `compute_terrain_elevation(x, y)` rather than querying the discrete, tessellated polygon facets of `Terrain_Mesh` (160x160 resolution across 200m). Bilinear interpolation fails to eliminate float (leaving up to 6.96cm residual error due to non-planar quad diagonal triangulation in Blender), whereas BVH raycasting (`mathutils.bvhtree.BVHTree.FromBMesh`) eliminates ground offset completely down to **0.000 mm (0 float, 0 sink)** with an execution overhead of only **~5.9 ms**. Furthermore, empirical validation confirms that the combined hydrological remediations (lake rim levee and riverbank channel carving) strictly preserve the 200m x 200m horizontal span, a $\Delta Z$ of 33.10m ($\ge 15.0\text{m}$ mandate), the `COLOR_0` vertex color PBR shader contract, and a healthy $97.2\%$ slope diversity.

---

## 2. Root Cause Analysis: Flora Elevation Sampling

### 2.1 Current Implementation in `assets/blender_map/flora_generator.py`

In `generate_and_distribute_flora(context, collection_flora, terrain_data)`:
```python
height_func = terrain_data["height_func"]
...
# Lines 356 & 372 for Reeds:
pz = height_func(px, py)
obj.location = (px, py, pz)
```
`height_func` points directly to `compute_terrain_elevation` in `terrain_hydrology.py`. This evaluates an analytical polynomial/trigonometric function $z = f(x, y)$ in continuous $\mathbb{R}^2 \to \mathbb{R}$.

### 2.2 Discretization Discrepancy & Facet Sag

In Blender, `Terrain_Mesh` is generated as a regular quadrilateral grid:
- Resolution: $160 \times 160 = 25,600$ vertices, $25,281$ quad faces.
- Cell dimensions: $\Delta x = \Delta y = \frac{200.0}{159} \approx 1.25786\text{ m}$.
- In transitional zones—specifically riverbank levees and lake shoreline berms where cubic smoothstep functions $3t^2 - 2t^3$ introduce rapid second-derivative curvature—the discrete polygon facet chords deviate from the continuous curve.
- Where the ground is concave or the chord dips below the curve, $f(px, py)$ places the object origin higher than the actual polygon surface, causing visible air gaps.

### 2.3 Empirical Audit of Current Offsets

Running headless raycasting against `Terrain_Mesh` on the 50 current reed instances in `ecosystem_map.blend`:
- **Floating Reeds (> 2cm)**: 16 out of 50 reeds exhibit measurable vertical offset.
- **Worst-Case Floating Reeds (> 6cm)**:
  - `Flora_Reed_003` at $(57.59, 40.69, 9.688)$: ground = $9.592\text{m}$, diff = **$+0.0960\text{m}$ (+9.60cm)**
  - `Flora_Reed_005` at $(19.80, 34.97, 8.142)$: ground = $8.055\text{m}$, diff = **$+0.0871\text{m}$ (+8.71cm)**
  - `Flora_Reed_008` at $(36.83, 27.81, 6.104)$: ground = $6.019\text{m}$, diff = **$+0.0853\text{m}$ (+8.53cm)**
  - `Flora_Reed_019` at $(61.37, 47.34, 10.074)$: ground = $9.990\text{m}$, diff = **$+0.0840\text{m}$ (+8.40cm)**
  - `Flora_Reed_014` at $(12.92, 23.10, 7.062)$: ground = $6.997\text{m}$, diff = **$+0.0648\text{m}$ (+6.48cm)**
  - `Flora_Reed_006` at $(22.91, 25.32, 7.212)$: ground = $7.149\text{m}$, diff = **$+0.0635\text{m}$ (+6.35cm)**
- **Alpine Conifers**: Sunk into high-curvature ridges by up to **$-13.81\text{cm}$**.
- **Broadleaf Trees**: Offsets bounded within $[-0.77\text{cm}, +0.98\text{cm}]$.
- **Fauna (Stag)**: Hooves elevated at $+6.3\text{cm}$ above mesh at $(0.0, 15.0)$.

---

## 3. Surface-Snapping Comparative Analysis

We benchmarked two surface-snapping techniques against the actual geometry of `Terrain_Mesh` across all 50 reed positions:

| Metric | Analytical $f(x, y)$ (Current) | Bilinear Interpolation | BVHTree Raycasting (Recommended) |
| :--- | :--- | :--- | :--- |
| **Max Deviation from Mesh** | **9.60 cm** | **6.96 cm** | **0.000 mm (0.000000 m)** |
| **Mean Deviation** | 2.11 cm | 0.70 cm | **0.000 mm** |
| **Floating Instances (> 1mm)** | 16 / 50 (32%) | 12 / 50 (24%) | **0 / 50 (0.0%)** |
| **Computational Overhead** | 0.00 ms | ~0.04 ms | **~5.88 ms (BVH build) + 0.11 ms (queries)** |
| **Normal Vector Available?** | Analytical only | Approximate | **Exact surface normal at hit** |

### Why Bilinear Interpolation Fails to Eliminate Float
Bilinear interpolation evaluates:
$$Z_{\text{bili}}(u, v) = (1-\alpha)(1-\beta)z_{00} + \alpha(1-\beta)z_{10} + (1-\alpha)\beta z_{01} + \alpha\beta z_{11}$$
This produces a curved hyperbolic paraboloid (saddle surface). However, Blender (and glTF/GLB exporters) renders 3D quads by splitting non-planar 4-vertex polygons along a diagonal into **two flat planar triangles** ($Ax + By + Cz + D = 0$). Because the hyperbolic paraboloid deviates from the planar triangle facets by up to $6.96\text{cm}$, bilinear interpolation leaves significant residual float.

### Why `mathutils.bvhtree.BVHTree.FromBMesh` is Optimal
1. **Exact Precision**: Raycasting $(px, py, 60.0) \to (0, 0, -1)$ queries the exact tessellated triangular faces that Blender renders and exports to `.glb`. Setting `obj.location.z = hit.z` eliminates 100% of air gaps.
2. **Negligible Cost**: Building the BVH on 25,281 polygons takes $5.88\text{ ms}$, and 200 raycasts take $0.11\text{ ms}$. Total execution is under $6\text{ ms}$.
3. **Zero Risk**: If a coordinate falls outside the bounding box, a defensive fallback to `height_func(px, py)` guarantees zero crashes.

---

## 4. Verification of Combined Terrain Remediation Invariants

Challenger 1 mandated remediation of lake basin containment and riverbank levee containment in `terrain_hydrology.py`. We tested the combined remediated terrain against the core requirements:

### 4.1 Horizontal Span: 200m x 200m (Preserved)
- Grid axes: `xs = np.linspace(-100.0, 100.0, 160)` and `ys = np.linspace(-100.0, 100.0, 160)`.
- Span: $\Delta X = 200.000\text{m}$, $\Delta Y = 200.000\text{m}$.
- Result: **100% Preserved**.

### 4.2 Elevation Delta: $\Delta Z \ge 15.0\text{m}$ (Preserved)
- High point: $\max Z = 33.5541\text{m}$ on Northern alpine ridges ($y \in [70, 100], x \approx 40$).
- Low point: $\min Z = 0.4500\text{m}$ in the sedimentary lake bed.
- Net Delta: $\Delta Z = 33.1041\text{m} \ge 15.0\text{m}$ (excess margin: $+18.10\text{m}$).
- Result: **100% Preserved**. The lake and river remediations operate strictly in the low-to-mid elevation zones ($Z \in [0.45, 7.5]\text{m}$) and never suppress mountain peaks.

### 4.3 Color Attribute `COLOR_0` PBR Terrain Shader Mapping (Preserved)
- In `terrain_hydrology.py`, `COLOR_0` is computed dynamically from the final heightfield array $Z$ and its normal gradient $\nabla Z$:
  - $Z < 1.5\text{m}$: Shoreline/bed sand (`c_sand`: $[0.76, 0.70, 0.50, 1.0]$)
  - $1.5 \le Z < 3.0\text{m}$: Transition to alluvial soil (`c_soil`: $[0.30, 0.22, 0.14, 1.0]$)
  - $3.0 \le Z < 6.0\text{m}$: Transition to lush grass (`c_grass`: $[0.22, 0.44, 0.16, 1.0]$)
  - $6.0 \le Z < 18.0\text{m}$: Grass to rocky scree
  - $Z \ge 18.0\text{m}$: Subalpine rock to snow (`c_snow`: $[0.88, 0.90, 0.95, 1.0]$)
  - Steepness $> 0.25$: Dynamically exposes bare rock cliff face (`c_rock`)
- When the lake rim is raised to $Z \in [2.1, 2.6\text{m}]$, the rim naturally maps to wet sand and rich soil.
- When riverbank levees rise to $Z \in [rz + 0.15, rz + 0.45\text{m}]$, riverbanks naturally display fertile soil and lush grass.
- `M_Terrain_PBR` directly connects `ShaderNodeAttribute(attribute_name="COLOR_0")` to `Base Color`. Point domain color attributes are 100% glTF 2.0 compliant.
- Result: **100% Preserved and visually enhanced**.

### 4.4 Slope Diversity (Preserved)
- Slope evaluation across all 25,281 polygons:
  - $\min = 0.000^\circ$, $\max = 83.148^\circ$
  - Mean slope = $12.708^\circ$, Median slope = $9.986^\circ$
  - Active slope faces ($\ge 0.05^\circ$): **$97.20\%$** (24,573 / 25,281 faces)
  - Sedimentary flat lake bed: $2.80\%$ (708 faces)
- Result: **100% Preserved**.

---

## 5. Recommended Code Modifications for Worker

The Worker should apply the following targeted changes. (Do not modify source code from Explorer).

### Modification 1: Surface Snapping in `assets/blender_map/flora_generator.py`

In `assets/blender_map/flora_generator.py`:

1. **Add Imports**:
```python
import math
import random
import bpy
import bmesh
from mathutils import Vector, Euler
from mathutils.bvhtree import BVHTree
```

2. **Add BVH Snapping Helper in `generate_and_distribute_flora`**:
Immediately after extracting `terrain_data` (around line 301):
```python
    height_func = terrain_data["height_func"]
    river_dist_func = terrain_data.get("river_dist_func")
    lake_dist_func = terrain_data.get("lake_dist_func")

    # Construct spatial BVH tree from terrain mesh for exact polygon surface snapping
    terrain_obj = terrain_data.get("terrain_obj")
    terrain_bvh = None
    if terrain_obj and terrain_obj.data:
        bm = bmesh.new()
        bm.from_mesh(terrain_obj.data)
        terrain_bvh = BVHTree.FromBMesh(bm)
        bm.free()

    def get_snapped_z(px, py, fallback_z=None):
        """Raycasts down from Z=60 to snap origin to the exact polygon facet."""
        if terrain_bvh is not None:
            hit, _, _, _ = terrain_bvh.ray_cast(Vector((px, py, 60.0)), Vector((0.0, 0.0, -1.0)))
            if hit is not None:
                return hit.z
        if fallback_z is not None:
            return fallback_z
        return height_func(px, py)
```

3. **Snap Conifers (Line 315)**:
```python
        if z >= 12.0 and d_lake > 28.0:
            snap_z = get_snapped_z(x, y, z)
            obj = bpy.data.objects.new(f"Flora_Conifer_{c_count:03d}", m_conifer)
            obj.location = (x, y, snap_z)
```

4. **Snap Broadleaf Trees (Line 338)**:
```python
        if 3.5 <= z <= 13.0 and d_lake > 34.0 and d_river > 6.0:
            snap_z = get_snapped_z(x, y, z)
            obj = bpy.data.objects.new(f"Flora_Broadleaf_{b_count:03d}", m_broad)
            obj.location = (x, y, snap_z)
```

5. **Snap Reeds along River Corridor (Line 357)**:
```python
        px, py = rx + offset, ry - offset
        pz = height_func(px, py)
        snap_z = get_snapped_z(px, py, pz)
        obj = bpy.data.objects.new(f"Flora_Reed_{r_count:03d}", m_reed)
        obj.location = (px, py, snap_z)
```

6. **Snap Reeds along Lake Shoreline (Line 373)**:
```python
        px = -40.0 + rad * math.cos(ang)
        py = -40.0 + rad * math.sin(ang)
        pz = height_func(px, py)
        snap_z = get_snapped_z(px, py, pz)
        obj = bpy.data.objects.new(f"Flora_Reed_{r_count:03d}", m_reed)
        obj.location = (px, py, snap_z)
```

*(Note: `Flora_Lily` instances sit on the water surface at $Z = 2.02\text{m}$ and do not snap to terrain).*

---

### Modification 2: Ground Snapping in `assets/blender_map/fauna_generator.py`

In `assets/blender_map/fauna_generator.py`, in `generate_fauna(context, collection_fauna, terrain_data)`:
```python
    height_func = terrain_data["height_func"]
    stag_x, stag_y = 0.0, 15.0
    stag_z = height_func(stag_x, stag_y)

    terrain_obj = terrain_data.get("terrain_obj")
    if terrain_obj and terrain_obj.data:
        bm = bmesh.new()
        bm.from_mesh(terrain_obj.data)
        bvh = BVHTree.FromBMesh(bm)
        bm.free()
        hit, _, _, _ = bvh.ray_cast(Vector((stag_x, stag_y, 60.0)), Vector((0.0, 0.0, -1.0)))
        if hit is not None:
            stag_z = hit.z

    stag_arm, stag_mesh = build_stag(collection_fauna, offset=(stag_x, stag_y, stag_z))
```

---

### Modification 3: Export `snap_func` in `assets/blender_map/terrain_hydrology.py`

In `generate_terrain_and_hydrology`:
```python
    bm = bmesh.new()
    bm.from_mesh(mesh_terrain)
    terrain_bvh = BVHTree.FromBMesh(bm)
    bm.free()

    def snap_to_terrain(px, py, fallback_z=None):
        hit, _, _, _ = terrain_bvh.ray_cast(mathutils.Vector((px, py, 60.0)), mathutils.Vector((0.0, 0.0, -1.0)))
        if hit is not None:
            return hit.z
        return fallback_z if fallback_z is not None else compute_terrain_elevation(px, py)

    return {
        "terrain_obj": terrain_obj,
        "river_obj": river_obj,
        "lake_obj": lake_obj,
        "height_func": compute_terrain_elevation,
        "snap_func": snap_to_terrain,
        "river_dist_func": compute_river_distance,
        "lake_dist_func": compute_lake_distance,
    }
```

---

## 6. Verification Method

Once the Worker applies the modifications, verify with the following headless commands:

### Command 1: Verify Zero Floating Flora
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background assets/blender_map/ecosystem_map.blend --python-expr "
import bpy, bmesh, mathutils
from mathutils.bvhtree import BVHTree

t = bpy.data.objects['Terrain_Mesh']
bm = bmesh.new()
bm.from_mesh(t.data)
bvh = BVHTree.FromBMesh(bm)

floating = 0
for o in bpy.data.collections['Flora'].objects:
    if any(sp in o.name.lower() for sp in ['conifer', 'broadleaf', 'reed']):
        loc = o.location
        rc, _, _, _ = bvh.ray_cast(mathutils.Vector((loc.x, loc.y, 60.0)), mathutils.Vector((0, 0, -1)))
        if rc and abs(loc.z - rc.z) > 0.001:  # 1mm tolerance
            floating += 1
            print(f'Floating: {o.name} diff={loc.z - rc.z:+.5f}m')

print(f'Total Floating Terrestrial Flora Instances (> 1mm): {floating} / 160')
assert floating == 0, f'{floating} flora instances float above terrain facets!'
"
```
*Expected Result*: `Total Floating Terrestrial Flora Instances (> 1mm): 0 / 160`.

### Command 2: Verify Scene Tests & Deliverables
```bash
pytest tests/test_ecosystem_map.py
```
*Expected Result*: 30 passed in < 6 seconds.
