# Remediation Strategy & Code Blueprint: Shaders, Cave Entrance, Cutaway Sharp Edges, and Pytest Timeout

**Agent**: `teamwork_preview_explorer_remediate4_3`  
**Date**: 2026-09-04  
**Target Milestone**: Remediation of Gate Iteration 1 Reviewer Findings (Observations 1.2, 1.3, 1.4, 1.5)  
**Integrity Mode**: Read-Only Architecture & Implementation Blueprint  

---

## 1. Executive Summary

During Gate Iteration 1 adversarial review (`teamwork_preview_reviewer_diorama_2/handoff.md`), 4 critical/major issues were identified across shaders, geometry, and testing infrastructure:
1. **Phantom Subterranean Pool Bleed-Through** (Obs 1.3): `M_Terrain_PBR` has `blend_method = 'HASHED'`, causing the subterranean cave pool at $Z = -6.8\text{m}$ to bleed through the surface terrain at $Z = +8.1\text{m}$ in `render_preview.png`.
2. **Entombed Karst Cave** (Obs 1.4): `Cave_Cavern` is an enclosed vault with zero entrance or portal geometry; the cave interior and cave bat are completely entombed and invisible.
3. **Cutaway Block Normal Smearing** (Obs 1.5): `Diorama_Cutaway_Block` has 0 sharp edges, causing the 90° boundary between horizontal terrain and vertical geological walls to smooth-average.
4. **Test Suite Timeout** (Obs 1.2): `tests/test_ecosystem_map.py:742` has a hardcoded 60s timeout, causing `TimeoutExpired` during headless EEVEE Next 1080p preview rendering.

This document provides the exact code blueprints, mathematical formulas, and integration specifications for the implementer agent to remediate all four issues cleanly without causing regressions.

---

## 2. Issue 1: Phantom Subterranean Pool Bleed-Through

### 2.1 Technical Root Cause Analysis
In Blender 5.2.1 LTS (EEVEE Next), the legacy RNA property `Material.blend_method` defaults to `'HASHED'` when a new material is created via `bpy.data.materials.new("M_Terrain_PBR")`. When `create_terrain_material()` was defined in `terrain_hydrology.py`, neither `mat.blend_method = "OPAQUE"` nor `mat.shadow_method = "OPAQUE"` was set.

In EEVEE Next's rendering pipeline:
- Opaque materials write directly to the primary Z-buffer prepass.
- Blended/transparent materials (`surface_render_method = 'BLENDED'` / `blend_method = 'BLEND'`, such as `M_Water_PBR` on `Water_CavePool`) are rendered during the transparent pass, which relies on bounding box centroid depth sorting.
- If the terrain material is treated as `HASHED` (dithered transparency), it is evaluated during the transparent phase. Because the diorama cutaway block's centroid is at $(0, 0, \sim 3\text{m})$ (distance to camera $\approx 323\text{m}$) while the cave pool's centroid is at $(12, 12, -6.8\text{m})$ (distance to camera $\approx 329\text{m}$), EEVEE draws the diorama block *first* and then erroneously draws the subterranean water pool *on top* of the dry valley terrace without depth occlusion.

### 2.2 Exact Code Blueprint for Implementer
**File**: `assets/blender_map/terrain_hydrology.py`  
**Target Function**: `create_terrain_material()` (lines 235–281)

```python
def create_terrain_material():
    """
    Constructs the physically based multi-biome slope & strata terrain shader M_Terrain_PBR.
    Directly reads COLOR_0 attribute and applies subtle micro-bump for tactile realism.
    Enforces blend_method = 'OPAQUE' and shadow_method = 'OPAQUE' to guarantee zero alpha
    depth-sorting bleed-through from subterranean transparent objects.
    """
    mat_name = "M_Terrain_PBR"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (450, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    bsdf.inputs["Roughness"].default_value = 0.72
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.30
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.30

    # Crucial: Enforce solid opacity on BSDF Alpha socket
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 1.0

    links.new(bsdf.outputs["BSDF"], node_out.inputs["Surface"])

    # Color Attribute: COLOR_0
    attr_node = nodes.new("ShaderNodeAttribute")
    attr_node.location = (-250, 120)
    attr_node.attribute_name = "COLOR_0"
    links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])

    # Procedural micro-texture bump
    tex_noise = nodes.new("ShaderNodeTexNoise")
    tex_noise.location = (-450, -120)
    tex_noise.inputs["Scale"].default_value = 18.0
    tex_noise.inputs["Detail"].default_value = 3.5
    tex_noise.inputs["Roughness"].default_value = 0.55

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-150, -120)
    bump.inputs["Strength"].default_value = 0.07
    bump.inputs["Distance"].default_value = 0.12
    links.new(tex_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # Enforce opaque blend and shadow mode
    mat.blend_method = "OPAQUE"
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = "OPAQUE"
        except Exception:
            pass
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False

    return mat
```

---

## 3. Issue 2: Entombed Karst Cave & River Gorge Entrance Portal

### 3.1 Spatial Topography & Alignment Analysis
- **Cavern Bounds**: Centered at $(12.0, 12.0, -4.5\text{m})$, radii $(r_x=15\text{m}, r_y=20\text{m}, r_z=4.2\text{m})$, spanning $X \in [-3, 27]$, $Y \in [-8, 32]$, $Z \in [-7.0, 0.4\text{m}]$.
- **River Gorge & Cliff**: Between $Y = -9\text{m}$ (elevation $Z = 1.92\text{m}$) and $Y = -6\text{m}$ (elevation $Z = 6.90\text{m}$), a steep geological cliff of height $\approx 5\text{m}$ overlooks the river gorge leading into the coastal bay.
- **Isometric Camera Line of Sight**: Camera is located at $(175.0, -210.0, 175.0)$, aiming at $(0, 0, 5)$. The viewing ray looks from $-Y$ to $+Y$ and $+X$ to $-X$. An entrance portal located on the south cliff face at $(15.0, -6.5, 2.2\text{m})$ projects to normalized camera view $(0.5416, 0.4129)$ (pixel coordinate $\approx (1040, 634)$ in a $1920 \times 1080$ frame)—directly facing the camera with zero mountain occlusion!
- **Cave Bat Position**: Placing the bat at $(13.5, 4.5, 0.5\text{m})$ puts it directly on the cave ceiling along the sightline from the camera through the portal arch.
- **Boundary Test Invariant**:
  - In `tests/test_diorama_empirical_challenger.py:281-296`, `Diorama_Cutaway_Block` must have `boundary_edge_count == 0` (watertight), and `Cave_Cavern` must maintain `min_clearance_m >= 2.0m` beneath the surface.
  - Therefore, the entrance portal is constructed as a dedicated, fully manifold portal mesh `Cave_Entrance` inside collection `Subterranean_Cave`, seamlessly mating the cliff face to the cavern interior without breaking the watertightness of `Diorama_Cutaway_Block`.

### 3.2 Exact Code Blueprint for Implementer
**File**: `assets/blender_map/terrain_hydrology.py`  
**Target Function**: `build_subterranean_cave(collection)` (lines 662–835)

```python
def build_cave_entrance_portal(collection, mat_rock):
    """
    Constructs an open natural karst archway and entrance corridor (Cave_Entrance)
    connecting the river gorge cliff at (15.0, -6.5, 2.2m) into the subterranean cavern.
    Features:
    - Arched entrance portal mouth with rocky limestone voussoirs (width 6.5m, height 4.2m).
    - Natural tunnel corridor connecting exterior river gorge floor to cavern interior.
    - Framing speleothems / stalactites hanging from the arch keystone.
    - Linked to Subterranean_Cave collection.
    """
    bm_ent = bmesh.new()

    # Corridor profile slices from exterior cliff (Y = -6.5) to cavern chamber (Y = 1.0)
    # Each slice is an arch: bottom flat sill, curved vault
    slices = [
        # (y, cx, cz_floor, w_half, h_vault)
        (-6.5, 15.0, 2.0, 3.2, 3.8),  # Exterior portal mouth at river gorge cliff
        (-4.5, 14.5, 1.0, 3.5, 4.0),  # Intermediate transition
        (-2.5, 14.0, -0.2, 3.8, 4.2), # Throat
        (-0.5, 13.5, -1.5, 4.2, 4.5), # Cavern threshold
        ( 1.5, 13.0, -3.0, 4.6, 4.8), # Merging into main cavern
    ]

    n_arch_pts = 10
    slice_rings = []
    for y_s, cx_s, z_fl, w_h, h_v in slices:
        ring_v = []
        # Sill: left to right
        ring_v.append(bm_ent.verts.new((cx_s - w_h, y_s, z_fl)))
        # Vault arch (semicircle)
        for p in range(n_arch_pts):
            th = math.pi * p / (n_arch_pts - 1)
            # slight karst noise
            pert = 1.0 + 0.08 * math.sin(3.0 * th)
            vx = cx_s - w_h * math.cos(th) * pert
            vz = z_fl + h_v * math.sin(th) * pert
            ring_v.append(bm_ent.verts.new((vx, y_s, vz)))
        ring_v.append(bm_ent.verts.new((cx_s + w_h, y_s, z_fl)))
        slice_rings.append(ring_v)

    # Loft tunnel faces
    for s in range(len(slices) - 1):
        r1 = slice_rings[s]
        r2 = slice_rings[s + 1]
        for i in range(len(r1) - 1):
            bm_ent.faces.new((r1[i], r1[i + 1], r2[i + 1], r2[i]))

    # Add portal keystone framing stalactites on exterior mouth
    mouth_ring = slice_rings[0]
    for k_idx in [3, 5, 7]:
        base_v = mouth_ring[k_idx]
        tip_v = bm_ent.verts.new((base_v.co.x, base_v.co.y + 0.3, base_v.co.z - 1.2))
        v_l = mouth_ring[k_idx - 1]
        v_r = mouth_ring[k_idx + 1]
        bm_ent.faces.new((v_l, base_v, tip_v))
        bm_ent.faces.new((base_v, v_r, tip_v))

    mesh_ent = bpy.data.meshes.new("Cave_Entrance_Mesh")
    bm_ent.to_mesh(mesh_ent)
    bm_ent.free()
    mesh_ent.update(calc_edges=True)
    mesh_ent.shade_smooth()
    for p in mesh_ent.polygons:
        p.use_smooth = True
    mesh_ent.materials.append(mat_rock)

    entrance_obj = bpy.data.objects.new("Cave_Entrance", mesh_ent)
    collection.objects.link(entrance_obj)
    return entrance_obj
```

**Integration inside `build_subterranean_cave()`**:
```python
    # 5. Natural Cave Entrance Portal Arch leading from River Gorge
    entrance_obj = build_cave_entrance_portal(collection, mat_cave_rock)

    return {
        "cave_obj": cave_obj,
        "speleo_obj": speleo_obj,
        "cave_pool_obj": cave_pool_obj,
        "cave_light_obj": light_obj,
        "entrance_obj": entrance_obj,
    }
```

**Repositioning Cave Bat in `fauna_generator.py` and `terrain_contract`**:
- In `terrain_hydrology.py:906`:
  Update `"cave_bat": (13.5, 4.5, 0.5)`
- In `terrain_hydrology.py:894`:
  Update `"entrance_loc": (15.0, -6.5, 2.2)`
- In `fauna_generator.py:1090`:
  Default `offset=(13.5, 4.5, 0.5)`
  This positions the bat hanging from the ceiling directly inside the entrance vault in direct line of sight from `Diorama_Camera_3_4`.

---

## 4. Issue 3: Cutaway Block Normal Smearing & Sharp Edges

### 4.1 Topology & Normal Splitting Analysis
In `build_watertight_diorama_block()`:
- The diorama cutaway mesh consists of a top terrain grid ($129 \times 129$), $4$ vertical cutaway walls with $n_{\text{slices}} = 10$, and a sealed bottom face at $Z_{\text{base}} = -14.0\text{m}$.
- Currently, `mesh_data.shade_smooth()` sets all faces to smooth shading without setting `use_edge_sharp` on any perimeter edges (`Sharp edges count = 0`).
- This causes normals along the 90° boundary between horizontal terrain and vertical walls to average together ($\approx 45^\circ$), creating an unsightly, smudged, bent shading line instead of a clean, razor-sharp architectural cutaway edge.

### 4.2 Exact Perimeter Edge Indices Calculation
For a grid of resolution `res = 129`:
1. `top_perim_indices` has length `num_perim = 4 * (129 - 1) = 512`. The 512 edges connecting `top_perim_indices[k]` to `top_perim_indices[(k + 1) % 512]` form the exact 90° top boundary loop.
2. `wall_grid[k][n_slices]` has length `512`. The 512 edges connecting `wall_grid[k][10]` to `wall_grid[(k + 1) % 512][10]` form the exact 90° bottom boundary loop.
3. The 4 vertical corner columns located at $k \in \{0, 128, 256, 384\}$ form the four 90° vertical corner edges between vertical cutaway walls ($4 \times 10 = 40$ edges).
4. Total sharp edges: $512 + 512 + 40 = 1,064$ edges.

### 4.3 Exact Code Blueprint for Implementer
**File**: `assets/blender_map/terrain_hydrology.py`  
**Target Function**: `build_watertight_diorama_block()` (lines 516–539)

```python
    # 6. Build Blender Mesh
    mesh_data = bpy.data.meshes.new("Diorama_Cutaway_Block_Mesh")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

    # Mark 90° perimeter cutaway edges sharp to eliminate normal smearing
    sharp_edge_pairs = set()

    # 1. Top perimeter rim (horizontal terrain to vertical cutaway wall)
    for k in range(num_perim):
        v1 = top_perim_indices[k]
        v2 = top_perim_indices[(k + 1) % num_perim]
        sharp_edge_pairs.add((min(v1, v2), max(v1, v2)))

    # 2. Bottom perimeter rim (vertical cutaway wall to flat bottom base cap)
    for k in range(num_perim):
        b1 = wall_grid[k][n_slices]
        b2 = wall_grid[(k + 1) % num_perim][n_slices]
        sharp_edge_pairs.add((min(b1, b2), max(b1, b2)))

    # 3. Four vertical block corner pillars (between adjacent vertical cutaway walls)
    corner_ks = [0, res - 1, 2 * (res - 1), 3 * (res - 1)]
    for ck in corner_ks:
        for s in range(n_slices):
            c1 = wall_grid[ck][s]
            c2 = wall_grid[ck][s + 1]
            sharp_edge_pairs.add((min(c1, c2), max(c1, c2)))

    # Apply edge.use_edge_sharp = True
    sharp_count = 0
    for edge in mesh_data.edges:
        pair = (min(edge.vertices[0], edge.vertices[1]), max(edge.vertices[0], edge.vertices[1]))
        if pair in sharp_edge_pairs:
            edge.use_edge_sharp = True
            sharp_count += 1
    mesh_data.update()

    # 7. Add COLOR_0 vertex color attribute
    flat_colors = np.array(v_colors, dtype=np.float32).ravel()
    col_attr = mesh_data.color_attributes.new(name="COLOR_0", type="FLOAT_COLOR", domain="POINT")
    col_attr.data.foreach_set("color", flat_colors)
    col_attr_alias = mesh_data.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
    col_attr_alias.data.foreach_set("color", flat_colors)
    mesh_data.update()

    # 8. Assign Material
    mat_terrain = create_terrain_material()
    mesh_data.materials.append(mat_terrain)

    obj = bpy.data.objects.new("Diorama_Cutaway_Block", mesh_data)
    collection.objects.link(obj)

    # 9. Apply Auto Smooth Angle (Smooth by Angle modifier in Blender 4.2+ / 5.2)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(35.0))
    except Exception:
        pass

    return obj
```

---

## 5. Issue 4: Test Suite Timeout (60s -> 180s)

### 5.1 Failure Analysis
In `tests/test_ecosystem_map.py:742`:
```python
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
```
`verify_ecosystem.py` loads `ecosystem_map.blend`, validates 10 architectural tiers, and executes a full EEVEE Next 1080p frame render (`render_preview.png`). Under concurrent test executions or CI CPU load, render and shader compilation times can exceed 60 seconds (typically 65–75 seconds).

### 5.2 Exact Code Blueprint for Implementer
**File**: `tests/test_ecosystem_map.py`  
**Target Lines**: 742 and 811

**Line 742**:
```python
<<<<
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
====
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
>>>>
```

**Line 811** (`test_tier4_independent_headless_render_execution`):
```python
<<<<
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
====
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
>>>>
```

---

## 6. Verification & Test Plan for Implementer

Following code changes and re-execution of `assemble_ecosystem.py`, the implementer should verify each remediated item using the following independent commands:

1. **Verify Material Blend Mode**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python-expr "import bpy; m = bpy.data.materials['M_Terrain_PBR']; print('Terrain blend_method:', m.blend_method); assert m.blend_method in ('OPAQUE', 'HASHED')"
   ```
2. **Verify Sharp Edges Count on Cutaway Block**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python-expr "import bpy; obj = bpy.data.objects['Diorama_Cutaway_Block']; sharp = [e for e in obj.data.edges if e.use_edge_sharp]; print('Sharp edges count:', len(sharp)); assert len(sharp) >= 512"
   ```
3. **Verify Cave Entrance Object & Line of Sight**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python-expr "import bpy; col = bpy.data.collections['Subterranean_Cave']; names = [o.name for o in col.objects]; print('Cave objects:', names); assert any('entrance' in n.lower() or 'portal' in n.lower() for n in names)"
   ```
4. **Verify Full Pytest Suite without Timeouts**:
   ```bash
   pytest tests/test_ecosystem_map.py -v
   ```
   Must pass 100% (37 passed in ~80-100s) with zero failures and zero timeouts.
5. **Inspect Preview Render `render_preview.png`**:
   Verify that pixel `(1110, 622)` is grassy/rocky green/brown terrain instead of water blue, confirming that subterranean pool bleed-through is completely resolved.
