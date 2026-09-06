# 5-Component Handoff Report — Empirical Challenger: Diorama Scene Boundary & Stress Testing

**Agent**: `teamwork_preview_challenger_diorama_1`  
**Role**: `critic`, `specialist` (Empirical Challenger)  
**Parent**: `teamwork_preview_orchestrator_4` (`fdb50731-d0ca-4df7-a6b6-87872373b756`)  
**Gate Verdict**: **`REQUEST_CHANGES`**

---

## 1. Observation

Direct empirical observations from test suite execution and headless Blender inspection (`/Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend`):

1. **Terrain Watertightness & Geomorphology**:
   - Mesh: `Diorama_Cutaway_Block_Mesh` (object `Diorama_Cutaway_Block`).
   - Vertex count: 21,762; Edge count: 43,776; Face count: 22,016.
   - Open boundary edges (`edge.is_boundary`): **0**.
   - Non-manifold edges (`not edge.is_manifold`): **0**.
   - Wire edges: **0**.
   - Bottom cap: Planar sealed at $Z = -14.0\text{m}$.
   - Elevation range: $[-14.0\text{m}, +22.7\text{m}]$ ($\Delta Z = 36.7\text{m} \ge 20.0\text{m}$).
   - Status: **PASS**.

2. **Subterranean Karst Cave System**:
   - Cavern mesh: `Cave_Cavern_Mesh` (object `Cave_Cavern`), center $(12.0, 12.0, -4.5\text{m})$.
   - Cave roof clearance to local surface elevation $Z_{\text{terrain}}(x, y) - Z_{\text{cavern}}$:
     - Minimum clearance: **$4.302\text{m}$** (at cavern apex).
     - Maximum clearance: **$17.134\text{m}$**.
     - Surface breaches count ($Z_{\text{cavern}} \ge Z_{\text{terrain}}$): **0**.
   - Speleothems (`Cave_Speleothems`) surface breaches: **0**.
   - Cave pool (`Water_CavePool`): $Z = -6.8\text{m}$ (fully underground).
   - Status: **PASS**.

3. **Flora Instances Adherence & Orientation**:
   - Total placed instances: **202** across 4 biomes.
   - Floating instances ($Z_{\text{flora}} - Z_{\text{terrain}} > 0.10\text{m}$): **0**.
   - Deeply sunken instances ($Z_{\text{flora}} - Z_{\text{terrain}} < -0.20\text{m}$): **0**.
   - Inverted instances ($\vec{N}_{\text{up}} \cdot \hat{z} < 0.7$): **0**.
   - Dry-land flora underwater (in lake $Z < 4.5\text{m}$ or bay $Z < 0.0\text{m}$): **0**.
   - Status: **PASS**.

4. **Fauna Rigging, Vertex Weights & Pose Deformation**:
   - 5 rigged species: Mountain Goat (26 bones), Golden Eagle (16 bones), Highland Red Stag (28 bones), Freshwater Trout (12 bones), Subterranean Bat (18 bones) — total 100 bones.
   - Zero-weight vertices across all 5 meshes: **0** (Goat: 0/204, Eagle: 0/64, Stag: 0/246, Trout: 0/53, Bat: 0/56).
   - Dynamic pose evaluation across all 10 actions (keyframes 1–60):
     - NaN / Inf coordinates: **0**.
     - Maximum edge length during animation: bounded $\le 0.478\text{m}$ (no mesh tearing or spiking).
     - Loop continuity: first vs last frame rotation difference = $0.0000\text{ rad}$, location difference = $0.0000\text{ m}$.
   - Status: **PASS**.

5. **Hydrology Defect 1 — Lake Water Disc Rim Breach & Mid-Air Levitation**:
   - Lake water mesh: `Water_Lake` (disc $r = 24.0\text{m}$, center $(-25.0, -10.0)$, $Z = 4.50\text{m}$).
   - In `assets/blender_map/terrain_hydrology.py`, lines 74–89:
     ```python
     d_lake = np.hypot(x_arr - lake_cx, y_arr - lake_cy)
     r_lake_rim, r_lake_bed = 28.0, 15.0
     mask_lake_slope = (d_lake < r_lake_rim) & (d_lake >= r_lake_bed)
     if np.any(mask_lake_slope):
         ...
         target_z = 1.8 + 2.7 * s_l
         z[mask_lake_slope] = np.minimum(z[mask_lake_slope], target_z + 1.2 * s_l)
     ```
   - On the western perimeter ($d_{\text{lake}} = 24.0\text{m}$), negative harmonic foothills depress the terrain to $Z = 0.36\text{m} - 1.86\text{m}$.
   - Because `np.minimum` was used, the terrain was never elevated to form a containing rim.
   - Out of 40 perimeter vertices, **18 vertices breach rim containment**.
   - Maximum mid-air water levitation at western lake perimeter:
     - `v[16]`: $(-41.97, 6.97)$, Water $Z = 4.50\text{m}$, Terrain $Z = 0.36\text{m}$ $\implies$ **water floats $4.14\text{m}$ in mid-air**.
     - `v[15]`: $(-39.11, 9.42)$, Water $Z = 4.50\text{m}$, Terrain $Z = 0.45\text{m}$ $\implies$ **water floats $4.05\text{m}$ in mid-air**.
     - `v[14]`: $(-35.90, 11.38)$, Water $Z = 4.50\text{m}$, Terrain $Z = 0.75\text{m}$ $\implies$ **water floats $3.75\text{m}$ in mid-air**.
   - Status: **CRITICAL DEFECT — FAIL**.

6. **Hydrology Defect 2 — 100% Floating River Ribbon (Hovering Aqueduct)**:
   - River mesh: `Water_River` (180 vertices, 65 quad faces).
   - In `assets/blender_map/terrain_hydrology.py`, `_evaluate_river_spline_points` specifies hardcoded spline heights $Z \in [0.0\text{m}, 22.0\text{m}]$.
   - In `compute_terrain_elevation` lines 123–130, channel carving evaluates `bed_cut = rz_near - 0.9` and `z = (1.0 - s_bank) * np.minimum(z, bed_cut) + s_bank * z`.
   - Along the entire river path, the uncarved terrain $Z(x, y)$ was already lower than `bed_cut`, so `np.minimum` took no effect and never raised ground to meet the water.
   - Quantitative measurement across all 180 river vertices:
     - Vertices with $Z_{\text{water}} > Z_{\text{terrain}} + 0.05\text{m}$: **180 / 180 (100%)**.
     - Minimum levitation above terrain: **$0.215\text{m}$**.
     - Average levitation above terrain: **$3.602\text{m}$**.
     - Maximum levitation above terrain: **$7.343\text{m}$** (at gorge outlet $t \approx 0.90$).
     - At headwaters $t=0.00$: $(-10.0, 45.0)$, Water $Z = 22.00\text{m}$, Terrain $Z = 16.52\text{m}$ $\implies$ floats **$5.48\text{m}$**.
   - Status: **CRITICAL DEFECT — FAIL**.

7. **Hydrology Defect 3 — Coastal Bay Water Discontinuity & Exposed Sub-Sea Bed**:
   - Coastal bay water mesh: `Water_Bay` (disc $r = 34.0\text{m}$, center $(42.0, -42.0)$, $Z = 0.0\text{m}$).
   - In `compute_terrain_elevation`, the marine bay depression extends out to $r_{\text{bay\_rim}} = 46.0\text{m}$.
   - At the water mesh perimeter ($r = 34.0\text{m}$), the underlying seabed is at $Z = -1.69\text{m}$.
   - The water mesh ends abruptly in open space with a **$1.69\text{m}$ vertical drop** to the seabed.
   - Between $r = 34.0\text{m}$ and $r \approx 43.0\text{m}$ (where terrain reaches sea level $0.0\text{m}$), there is an annular strip of submerged ground with no water mesh covering it.
   - Status: **DEFECT — FAIL**.

8. **Test Suite Execution**:
   - Command: `pytest tests/test_diorama_empirical_challenger.py -v`
   - Result: `3 failed, 4 passed in 1.61s`.
     - `test_diorama_mesh_watertightness_and_bounds`: PASSED.
     - `test_subterranean_karst_cave_depth_clearance`: PASSED.
     - `test_flora_ground_adherence_and_rotation`: PASSED.
     - `test_fauna_rigging_and_pose_deformation`: PASSED.
     - `test_lake_water_basin_containment`: **FAILED** (AssertionError: 18 perimeter breaches, floating up to 4.14m).
     - `test_river_water_ribbon_elevation_containment`: **FAILED** (AssertionError: 180/180 vertices floating, avg 3.602m, max 7.343m).
     - `test_coastal_bay_water_margin_containment`: **FAILED** (AssertionError: 1.69m perimeter drop).

---

## 2. Logic Chain

1. **Observation 1 & 2** demonstrate that the static bedrock volume and subterranean cavern are geometrically robust: the cutaway block is closed with 0 non-manifold edges, and the karst cavern has ample roof clearance ($\ge 4.3\text{m}$) beneath the surface.
2. **Observation 3 & 4** confirm that botanical and zoological assets conform to physical and kinematic standards: 0 zero-weight vertices, 0 mid-air floating trees, and fluid, non-tearing loopable skeletal animations.
3. However, **Observation 5** reveals that the lake basin in `terrain_hydrology.py` fails physical containment: because `compute_terrain_elevation` only applied `np.minimum` rather than blending or raising the lake rim to $Z \ge 4.5\text{m}$, the water disc floats $0.5\text{m} - 4.14\text{m}$ above the valley floor on its western side.
4. **Observation 6** reveals that the river ribbon was constructed using independent, hardcoded Z spline heights that do not track the analytical terrain surface. Because the terrain was lower than the spline heights, the river ribbon hovers as an elevated glass aqueduct $3.6\text{m}$ (up to $7.34\text{m}$) in the air for its entire length.
5. **Observation 7** shows that the coastal bay water disc terminates prematurely at $r = 34\text{m}$ where water depth is $1.69\text{m}$, leaving an uncontained cliff edge of water dropping onto exposed sub-sea topography instead of meeting the shoreline.
6. Therefore, the scene violates the physical containment and realism requirements mandated in `ORIGINAL_REQUEST.md` (2026-09-03T17:21:58Z: "filling a deep central freshwater lake with shoreline sand, and discharging into a lower coastal marine bay").
7. A quality gate verdict of **`REQUEST_CHANGES`** is mandatory until these 3 hydrology containment defects are remediated.

---

## 3. Caveats

- The worker's `verify_ecosystem.py` and `tests/test_ecosystem_map.py` passed only because they tested for the *presence* of objects and collections (`has_river`, `has_lake`, `has_bay`), but did not perform empirical geometric elevation difference checks ($Z_{\text{water}} - Z_{\text{terrain}}$) or boundary containment tests.
- Remediating these defects requires adjustments in `terrain_hydrology.py`:
  1. Enforcing a minimum terrain elevation $\ge 4.5\text{m}$ along the lake basin rim ($r \in [23.5\text{m}, 28.0\text{m}]$ except at the river inlet and outlet).
  2. Dynamically deriving or anchoring river spline heights $rz(t)$ to local ground elevation, or ensuring the river channel carving properly creates retaining banks along both sides.
  3. Extending the bay water disc radius to $r = 44\text{m} - 46\text{m}$ or adjusting the bay basin rim slope so the water disc seamlessly meets the $Z = 0.0\text{m}$ coastline.
- Per constraint ("Review-only — do NOT modify implementation code"), this agent does not edit implementation code in `assets/blender_map/terrain_hydrology.py`.

---

## 4. Conclusion

**Gate Verdict**: **`REQUEST_CHANGES`**

While the diorama mesh watertightness, subterranean karst cave depth, flora instancing, and fauna skeletal rigging/animations are empirically solid and verified, the hydrology system exhibits severe physical containment failures:
1. The lake water disc hangs in mid-air up to $4.14\text{m}$ above the uncontained western ground.
2. 100% of the river ribbon vertices float between $0.21\text{m}$ and $7.34\text{m}$ (average $3.60\text{m}$) above the terrain surface.
3. The coastal bay water mesh terminates at $1.69\text{m}$ depth, creating an open vertical water wall over an exposed dry seabed.

Remediation by the worker is required to anchor the water geometries to the terrain.

---

## 5. Verification Method

To independently reproduce and verify all findings:

1. **Run the empirical challenger boundary test suite**:
   ```bash
   pytest tests/test_diorama_empirical_challenger.py -v
   ```
   *Expected Output*: 4 passed, 3 failed with explicit AssertionError messages detailing exact vertex coordinates and levitation heights.

2. **Run headless Blender river elevation delta query**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python-expr '
   import bpy, sys
   sys.path.insert(0, "assets/blender_map")
   import terrain_hydrology
   river = bpy.data.objects["Water_River"].data
   diffs = [v.co.z - terrain_hydrology.compute_terrain_elevation(v.co.x, v.co.y) for v in river.vertices]
   print(f"Floating: {sum(1 for d in diffs if d > 0.05)}/{len(diffs)}, Avg: {sum(diffs)/len(diffs):.2f}m, Max: {max(diffs):.2f}m")
   '
   ```
   *Expected Output*: `Floating: 180/180, Avg: 3.60m, Max: 7.34m`.

3. **Run headless Blender lake rim containment query**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python-expr '
   import bpy, sys
   sys.path.insert(0, "assets/blender_map")
   import terrain_hydrology
   lake = bpy.data.objects["Water_Lake"].data
   breaches = [v for v in lake.vertices[1:] if terrain_hydrology.compute_terrain_elevation(v.co.x, v.co.y) < 4.0 and terrain_hydrology.compute_river_distance(v.co.x, v.co.y) > 5.0]
   print(f"Lake perimeter rim breaches: {len(breaches)}/40")
   '
   ```
   *Expected Output*: `Lake perimeter rim breaches: 18/40`.
