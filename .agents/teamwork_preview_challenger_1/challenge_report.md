# Empirical Challenge Report — 3D Ecological Environment Map Deliverables

**Agent**: `teamwork_preview_challenger_1`  
**Date**: 2026-09-03T17:03:00Z  
**Target Environment**: macOS Apple Silicon Metal, Blender 5.2.1 LTS  
**Target Deliverables**:
- `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.blend`
- `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.glb`
- `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/render_preview.png`
- `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/terrain_hydrology.py`
- `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/flora_generator.py`
- `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/fauna_generator.py`

---

## 1. Challenge Summary

- **Overall Risk Assessment**: **HIGH**
- **Explicit Verdict**: **`REQUEST_CHANGES`**

While the work product successfully satisfies general mesh structure, 4-tier unit test coverage (30/30 passing in `test_ecosystem_map.py`), asset packaging, PBR materials, and skeletal animation, adversarial stress-testing revealed **two critical hydrological containment failures** that directly violate the core mission requirements:
1. **The lake basin does NOT strictly contain the water surface**: 22 of the 36 perimeter vertices of `Water_Lake` float in mid-air up to **+0.861m** above the terrain. The northern rim of the lake is uncontained where the terrain dips down to 0.45m.
2. **The river water ribbon edges float up to +1.383m above the terrain**: Across 34 of the 80 river cross-sections (sections 46 to 79), the river channel banks do not contain the water ribbon, creating an unnatural "floating aqueduct" effect where water hovers above the low valley ground.
3. **Minor Flora Discretization Offset**: 6 of 50 reeds along the river float 6.4cm to 9.6cm above the terrain mesh due to bilinear quad interpolation sag.

Remediation of these issues is straightforward and mathematically tractable in `terrain_hydrology.py`.

---

## 2. Adversarial Challenges

### [CRITICAL] Challenge 1: Lake Basin Elevation Fails Strict Water Surface Containment

- **Requirement Challenged**: "verify that the lake basin elevation strictly contains the water surface."
- **Empirical Observation**:
  - `Water_Lake` is modeled as a circular disc of radius $R = 31.0\text{ m}$ centered at $(-40.0, -40.0)$ at elevation $Z = 2.000\text{ m}$.
  - Evaluating terrain elevation along the 36 perimeter vertices of the lake water disc via BVH raycast against `Terrain_Mesh`:
    * **22 out of 36 perimeter vertices (61.1%) have `Water_Z > Terrain_Z + 0.01m`**.
    * At angle $\theta = 90.0^\circ$ (due North from the center at $(-40.0, -9.0)$), `Water_Z = 2.000m` while `Terrain_Z = 1.139m`. The water mesh edge is floating **+0.861m (86.1 cm)** in mid-air above the ground!
    * Between angles $350^\circ$ and $200^\circ$, the water disc edge hovers unsupported above the ground.
  - Furthermore, sweeping radially outwards from the lake center to find the true waterline ($Z_{terrain} \ge 2.0\text{ m}$):
    * Between angles $60^\circ$ and $110^\circ$, the terrain does NOT reach $2.0\text{ m}$ even at $R = 45\text{ m}$! In fact, at $(x=-40.0, y=0.0)$, the background valley terrain drops down to $0.450\text{ m}$ (bedrock clamp).
- **Attack Scenario & Blast Radius**:
  - The lake is hydrologically uncontained to the north. In any fluid simulation or physical game engine, the lake water would drain out into the valley.
  - Visually, the edge of the water disc is exposed as a sharp geometric edge floating 86cm in the air above the terrain, breaking visual immersion and PBR realism.
- **Root Cause**:
  In `terrain_hydrology.py` lines 41-55:
  ```python
  lake_cx, lake_cy = -40.0, -40.0
  d_lake = np.hypot(x_arr - lake_cx, y_arr - lake_cy)
  r_lake_rim, r_lake_bed = 42.0, 26.0
  mask_slope = (d_lake < r_lake_rim) & (d_lake >= r_lake_bed)
  if np.any(mask_slope):
      t_slope = (d_lake[mask_slope] - r_lake_bed) / (r_lake_rim - r_lake_bed)
      blend_slope = 1.0 - (3.0 * t_slope**2 - 2.0 * t_slope**3)
      z[mask_slope] = (1.0 - blend_slope) * z[mask_slope] + blend_slope * (0.9 + 1.5 * t_slope)
  ```
  When $d_{lake} \ge 42\text{ m}$, `blend_slope = 0`, smoothly restoring the terrain to the background hills equation. But the background hills equation `hills = 3.5 * sin(x * 0.04) * cos(y * 0.04) + ...` has a deep natural valley at $x \approx -40, y \approx 0$ where $z \approx -0.8\text{ m}$ (clamped to 0.45m). Because the background terrain is below 2.0m, blending back into it causes the rim to dip below the water level!
- **Recommended Remediation**:
  Enforce a minimum rim elevation guarantee around the lake perimeter:
  Ensure that for $d_{lake} \in [r_{shore}, r_{rim}]$, the lake rim elevation $Z_{rim}(\theta)$ is strictly bounded from below by $Z_{water} + \Delta h_{shore}$ (e.g., $Z \ge 2.2\text{ m}$ for all angles, except at the river entrance spline $\theta \approx 32^\circ$ where the river enters at $Z = 2.0\text{ m}$). Adjust `r_lake_mesh` to precisely match the inner shoreline contour.

---

### [HIGH] Challenge 2: River Water Ribbon Lacks Bank Containment (Floating Ribbon)

- **Requirement Challenged**: "verify that river coordinates continuously descend towards the lake and the lake basin elevation strictly contains the water surface."
- **Empirical Observation**:
  - The river mesh `Water_River` comprises 80 cross-sections of width $w(t) \in [4.0\text{ m}, 8.0\text{ m}]$, with elevation $Z_r(t) = 6.5 \cdot (1 - t) + 2.0 \cdot t$.
  - While $Z_r(t)$ continuously and monotonically descends ($\Delta Z = -0.057\text{ m}$ per step, 79/79 segments descending, 0 upward flow), **the adjacent riverbanks fail to contain the water ribbon**:
    * In **34 out of 80 cross-sections** (sections 46 through 79, spanning $t \in [0.58, 1.0]$):
      - Section 46 at $(-5.3, 13.9)$: Right edge floats **+0.290m** above terrain.
      - Section 50 at $(-9.9, 4.8)$: Left edge floats **+0.308m**, Right edge floats **+1.128m** above terrain.
      - Section 53 at $(-12.0, -2.5)$: Left edge floats **+0.607m**, Right edge floats **+1.383m** above terrain.
      - Section 60 at $(-13.1, -18.6)$: Left edge floats **+0.849m**, Right edge floats **+1.293m** above terrain.
- **Attack Scenario & Blast Radius**:
  - Instead of flowing within a carved river canyon or banked channel, the river ribbon hovers in mid-air like an aqueduct with no support pillars.
  - Wetland flora placed along this section of the river (`Flora_Reed_*`) sit on the true ground 1.3 meters below the hovering water surface.
- **Root Cause**:
  In `terrain_hydrology.py` line 81:
  ```python
  z[mask_river] = (1.0 - blend_riv) * z[mask_river] + blend_riv * (rz_near[mask_river] - 1.2)
  ```
  `blend_riv` approaches 0 at distance $w_{channel} = rw \cdot 0.5 + 3.0$. But if the background terrain $z$ at that location is already low ($1.0\text{ m}$ or $0.45\text{ m}$), blending down to $z$ causes the banks to be much lower than the river surface ($Z_r \approx 3.5\text{ m}$).
- **Recommended Remediation**:
  Modify river carving to raise riverbanks if the surrounding terrain is below the water level:
  `z_bank_target = np.maximum(z[mask_river], rz_near[mask_river] + 0.4)`
  Ensure the banks rise at least 0.3m–0.5m above $rz_{near}$ on both sides of the water ribbon.

---

### [LOW] Challenge 3: Bilinear Discretization Sag Causing Minor Flora Floating

- **Requirement Challenged**: "verify that flora instances do not float above terrain or sink excessively into the ground."
- **Empirical Observation**:
  - Evaluated all 180 flora instances in `collection_flora`:
    * `Flora_Broadleaf` (50 instances): 100% grounded within $[-0.008\text{ m}, +0.010\text{ m}]$. Mean offset: $+0.0013\text{ m}$. **0 floating, 0 sunken.**
    * `Flora_Conifer` (60 instances): 100% grounded within $[-0.138\text{ m}, +0.013\text{ m}]$. Mean offset: $-0.0001\text{ m}$. **0 floating, 0 sunken.** (Root embedding on mountain slopes prevents floating roots).
    * `Flora_Lily` (20 instances): 100% positioned at $Z = 2.0200\text{ m}$, exactly $+0.02\text{ m}$ above the lake water surface ($Z = 2.000\text{ m}$), $r \in [5.06\text{ m}, 24.28\text{ m}]$. **0 floating above water, 0 submerged.**
    * `Flora_Reed` (50 instances): 44 instances are within $[-0.04\text{ m}, +0.05\text{ m}]$, but **6 instances float slightly above the mesh**:
      - `Flora_Reed_003`: $(57.59, 40.69)$, Terrain Z = 9.59m, Object Z = 9.69m ($\Delta z = +0.096\text{ m}$).
      - `Flora_Reed_005`: $(19.80, 34.97)$, Terrain Z = 8.06m, Object Z = 8.14m ($\Delta z = +0.087\text{ m}$).
      - `Flora_Reed_006`: $(22.91, 25.32)$, Terrain Z = 7.15m, Object Z = 7.21m ($\Delta z = +0.064\text{ m}$).
      - `Flora_Reed_008`: $(36.83, 27.81)$, Terrain Z = 6.02m, Object Z = 6.10m ($\Delta z = +0.085\text{ m}$).
      - `Flora_Reed_014`: $(12.92, 23.10)$, Terrain Z = 7.00m, Object Z = 7.06m ($\Delta z = +0.065\text{ m}$).
- **Root Cause**:
  Flora instances are placed at $pz = \text{height\_func}(px, py)$ using the analytical function. Because the terrain is meshed as a discrete 160x160 quad grid (cell width $\approx 1.25\text{ m}$), curvature in the analytical function causes the planar quad facets to sag up to 9.6cm below the analytical curve.
- **Recommended Remediation**:
  Sink placed reed instances slightly (e.g., $pz = \text{height\_func}(px, py) - 0.05\text{ m}$) or query the meshed surface directly using BVH raycast or vertex interpolation.

---

## 3. Empirical Stress-Test Execution Results

| Test ID | Test Domain | Scenario & Assertion | Expected Behavior | Actual Behavior | Result |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **ST-01** | Mesh Topology | Check non-manifold internal edges across all 9 scene meshes | 0 non-manifold edges | 0 non-manifold internal edges | **PASS** |
| **ST-02** | Mesh Topology | Check degenerate faces (area < 1e-6 m²) across all 9 meshes | 0 degenerate faces | 0 degenerate faces | **PASS** |
| **ST-03** | Mesh Topology | Check degenerate edges (length < 1e-6 m) across all 9 meshes | 0 degenerate edges | 0 degenerate edges | **PASS** |
| **ST-04** | Elevation Gradient | Terrain elevation delta $\ge 15.0\text{ m}$, non-zero slopes | $\Delta Z \ge 15.0\text{ m}$, gradient $\ne 0$ | $\Delta Z = 33.104\text{ m}$, 96.85% faces with slope $\ge 0.05^\circ$ | **PASS** |
| **ST-05** | Hydrology | River monotonic continuous descent along spline | $dZ/dt \le 0$ for all segments | $dZ = -0.05696\text{ m}$ constant across all 79 segments | **PASS** |
| **ST-06** | Hydrology | River mouth confluence elevation matching lake surface | $\Delta Z_{confluence} = 0.00\text{ m}$ | River end $Z = 2.000\text{ m}$, Lake $Z = 2.000\text{ m}$ ($\Delta Z = 0.0\text{ m}$) | **PASS** |
| **ST-07** | Hydrology | River channel bed submerged below river water | $Z_{bed} < Z_{water}$ along centerline | $Z_{bed}$ is 0.55m to 1.25m below water (mean 1.09m) | **PASS** |
| **ST-08** | Hydrology | **Lake basin strictly contains water surface** | $Z_{rim}(\theta) \ge 2.0\text{ m}$ around perimeter | **22 of 36 perimeter vertices float up to +0.861m above ground; north valley drops to 0.45m** | **FAIL** |
| **ST-09** | Hydrology | **Riverbank edges contain river water ribbon** | $Z_{bank} \ge Z_{water}$ at ribbon edges | **34 of 80 river sections float up to +1.383m above terrain** | **FAIL** |
| **ST-10** | Flora Instancing | Broadleaf Oak instances grounded to terrain | $\Delta z \in [-0.15, +0.05]\text{ m}$ | Offset: $[-0.008\text{ m}, +0.010\text{ m}]$, 0 floating | **PASS** |
| **ST-11** | Flora Instancing | Alpine Conifer instances grounded to terrain | $\Delta z \in [-0.15, +0.05]\text{ m}$ | Offset: $[-0.138\text{ m}, +0.013\text{ m}]$, 0 floating | **PASS** |
| **ST-12** | Flora Instancing | Water Lily instances aligned to lake water surface | $\Delta z_{water} \in [0.0, 0.05]\text{ m}$ | Exactly $+0.0200\text{ m}$ above water, $r \in [5.1, 24.3]\text{ m}$ | **PASS** |
| **ST-13** | Flora Instancing | Wetland Reed instances grounded to terrain | $\Delta z \in [-0.15, +0.05]\text{ m}$ | 44/50 pass; 6 float by $+0.064\text{ m}$ to $+0.096\text{ m}$ | **WARN** |
| **ST-14** | Fauna Rigging | Armature skinning vertex weight normalization | 0 unweighted vertices | 0 unweighted vertices on Stag (222) and Eagle (72) | **PASS** |
| **ST-15** | Fauna Rigging | Stag ground contact / hoof alignment | Hooves at ground level | Hooves at $+0.063\text{ m}$ (+6.3 cm) above terrain at $(0, 15)$ | **PASS** |
| **ST-16** | Fauna Rigging | Eagle flight altitude above terrain | Airborne $> 15.0\text{ m}$ | Altitude is $26.05\text{ m}$ above terrain at $(15, -10)$ | **PASS** |
| **ST-17** | Deliverables | GLB binary format, materials, skins, animations | Valid glTF 2.0 $> 100\text{ KB}$ | 1.56 MB, 15 materials, 2 skins, 4 animations | **PASS** |
| **ST-18** | Deliverables | Render preview image resolution & shader integrity | 1920x1080 PNG, 0 magenta | 1920x1080 RGBA, std dev 19.45, 0.0000% magenta errors | **PASS** |

---

## 4. Robust Areas (Commended Implementations)

The deliverables exhibit exceptional software engineering in several complex 3D graphics areas:
1. **Mesh Manifoldness & Topological Cleanliness**: All 9 meshes across the scene have zero non-manifold internal edges, zero wire edges, and zero degenerate faces/edges.
2. **glTF 2.0 Export Architecture**: Multi-clip skeletal animations are cleanly baked into the binary buffer via NLA pushdown, with 100% vertex skin normalization and zero unweighted vertices.
3. **PBR Terrain Vertex Coloring**: `COLOR_0` point domain vertex colors cleanly blend 5 distinct biomes (sand, soil, grass, rock, snow) based on elevation and surface normal steepness.
4. **Botanical Instancing**: Linked duplicates preserve lightweight geometry in both `.blend` and `.glb`, while Broadleaf, Conifer, and Water Lily instances achieve sub-centimeter vertical grounding.

---

## 5. Required Remediations for APPROVAL

To transition from `REQUEST_CHANGES` to `APPROVE`:
1. **Fix Lake Basin Rim Containment in `terrain_hydrology.py`**:
   Ensure that the terrain rim encircling the lake depression ($r \in [28\text{ m}, 42\text{ m}]$) remains strictly $\ge 2.2\text{ m}$ across all angles $\theta$, preventing the rim from dipping into the northern 0.45m valley depression. Ensure that the water disc perimeter vertices at $r = 31.0\text{ m}$ are either flush with or recessed inside the rising shore.
2. **Fix Riverbank Levees in `terrain_hydrology.py`**:
   In `compute_terrain_elevation`, ensure that the terrain at distance $w_{channel}$ on either side of the river ribbon does not drop below $rz_{near} + 0.3\text{ m}$, preventing the water ribbon from hovering above low-lying valley areas.
3. **Re-export and Re-verify**:
   Run `python3 assets/blender_map/assemble_ecosystem.py`, run `python3 assets/blender_map/verify_ecosystem.py`, and ensure all 36 lake perimeter vertices and all 80 river cross-sections satisfy $Z_{terrain} \ge Z_{water}$ at water boundaries.
