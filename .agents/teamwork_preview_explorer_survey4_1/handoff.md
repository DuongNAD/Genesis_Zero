# Handoff Report: Geomorphology, Hydrology & Karst Cave Network Survey

**Agent**: teamwork_preview_explorer_survey4_1  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1`  
**Parent**: teamwork_preview_orchestrator_4 (`fdb50731-d0ca-4df7-a6b6-87872373b756`)  
**Type**: Hard Handoff (Phase 0 Survey Complete)  
**Target Codebase**: `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/`  

---

## 1. Observation

1. **User Specification & Reference Visuals**:
   - `ORIGINAL_REQUEST.md:127-176`: Mandates 3D isometric diorama cutaway block with stratified underground cross-sections, multi-tier hydrology (alpine waterfall $\to$ meandering river $\to$ central lake $\to$ coastal marine bay with beaches and coral cutaways), subterranean karst cave network with entrance, cavern room, stalactites/stalagmites, underground pool, and bioluminescent shaders.
   - Reference images inspected directly via `view_file`:
     * `media_1788455668720.jpg`: Detailed 24-panel geological cutaway, elevation heatmaps, slope analysis, water depth analysis, cross-sections A-A and B-B.
     * `media_1788455686621.jpg`: Global ecological zoning map illustrating alpine snow peaks, rivers, lake, coastal bay, and biomes.
     * `media_1788455807967.jpg`: Master Blender 3D viewport of the diorama block with horizontal geological strata on vertical walls, cascading mountain waterfall, central lake with sandy perimeter, and lower coastal marine bay with underwater coral shelf.

2. **Codebase Inspection**:
   - `terrain_hydrology.py:232-257`: Terrain is generated as an open 2D grid plane ($160 \times 160$ vertices, $200\text{m} \times 200\text{m}$) with zero vertical walls, zero bottom cap, and zero underground strata cross-sections.
   - `terrain_hydrology.py:308-374`: Hydrology contains only a single river ribbon and a single lake disc at $Z = 2.0\text{m}$. There is no coastal marine bay, no lower sea basin, no waterfalls, and no subterranean karst cave.
   - `terrain_hydrology.py:106-167`: Water material `M_Water_PBR` is a basic Principled BSDF with noise bump and no Volume Absorption node.
   - `assemble_ecosystem.py:133-138`: Creates only 6 collections (`Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`). Missing `Diorama_Block`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`.
   - `verify_ecosystem.py:51`: Verifies only 6 legacy collections and does not check diorama cutaway walls, geological strata, coastal bay, or karst cave features.

3. **Blender Execution & Prototyping**:
   - Executed `/Applications/Blender.app/Contents/MacOS/Blender --version`: Running Blender 5.2.1 LTS on macOS Apple Silicon (Darwin).
   - Executed prototype scripts `test_diorama_math.py`, `prototype_survey.py`, and `test_render.py` headlessly:
     * Verified continuous elevation $Z(x, y)$ yielding $Z_{\text{min}} = -4.5\text{m}$, $Z_{\text{max}} = 28.5\text{m}$, $\Delta Z = 33.0\text{m}$ (exceeding $\ge 20\text{m}$ requirement).
     * Validated watertight 3D diorama block generation ($14,877$ vertices, $15,113$ polygons) with vertical cutaway walls stitched down to $Z_{\text{base}} = -14.0\text{m}$.
     * Validated subterranean karst cave mesh generation ($408$ vertices, $384$ polygons) with ceiling stalactites, floor stalagmites, and underground pool at $Z = -6.8\text{m}$.
     * Validated `ShaderNodeVolumeAbsorption` attached to `Material Output` Volume socket and `ShaderNodeEmission` for bioluminescent fungi.
     * Rendered 3/4 isometric preview (`test_render.png`) confirming clean diorama framing.

---

## 2. Logic Chain

1. **From Observation 1 to Geometry Scope**: The user's visual references depict a distinct isometric diorama block (a cube cutaway) rather than an infinite open terrain. Therefore, `terrain_hydrology.py` must be upgraded to construct a watertight solid mesh with top surface, 4 vertical cutaway side walls, and a flat bottom base.
2. **From Observation 1 to Geological Strata**: Because the cutaway walls are prominently exposed to the camera in 3/4 isometric view, strata layers (topsoil, subsoil, bedrock with horizontal striations) must be calculated procedurally as a function of wall depth below local surface elevation ($\text{depth} = Z_{\text{rim}} - z$) and baked into `COLOR_0` vertex attribute to guarantee full glTF 2.0 compatibility.
3. **From Observation 1 & 2 to Hydrology Architecture**: The requirement specifies a cascading hydrological chain. A single water level is physically and visually insufficient. We must implement: (1) Alpine headwaters & waterfall cascades ($Z \approx 22\text{m} \to 10\text{m}$); (2) Meandering river ($Z \approx 10\text{m} \to 4.5\text{m}$); (3) Central freshwater lake ($Z = 4.5\text{m}$); (4) Outlet river & coastal waterfall plunge ($Z \approx 4.5\text{m} \to 0.0\text{m}$); (5) Lower coastal marine bay ($Z = 0.0\text{m}$, seabed $Z = -4.5\text{m}$) with vertical water cutaway boundaries.
4. **From Observation 2 & 3 to Water Shader**: A simple surface transparency cannot capture water depth variation. Integrating `ShaderNodeVolumeAbsorption` with absorption coefficient $\sigma = 0.22$ and deep sapphire color reproduces natural physical absorption where shallow waters appear crystal emerald and deep waters appear dark sapphire blue.
5. **From Observation 1 & 2 to Subterranean Karst Cave**: The cave system must reside inside the solid diorama block ($Z \in [-7.0\text{m}, +0.5\text{m}]$), beneath the mountain/valley, featuring natural cavern geometry, ceiling stalactites, floor stalagmites, an underground pool, and emissive bioluminescent fungi shaders.

---

## 3. Caveats

1. **EEVEE Volume Absorption & glTF**: While `ShaderNodeVolumeAbsorption` renders natively in Blender EEVEE and Cycles, glTF export relies on the `KHR_materials_volume` extension. To ensure universal compatibility across all external web visualizers, the surface Principled BSDF must also carry an emerald-cyan base color and high transmission weight ($0.95$).
2. **Geometry Nodes Scope Separation**: This survey strictly specifies the geomorphology, hydrology, and cave geometry/materials. The distribution of flora onto this terrain using Blender Geometry Nodes belongs to the Flora track (Explorer 4.2), for which we provide explicit attribute interfaces (`COLOR_0`, `Altitude`, `Slope`, `Water_Proximity`).
3. **Fauna Rigging Separation**: Animal armatures and locomotion animations belong to the Fauna track (Explorer 4.3), for which we provide exact spatial anchor points across all 4 biomes.

---

## 4. Conclusion

The existing codebase provides an excellent algorithmic baseline but requires substantial refactoring to satisfy the `2026-09-03T17:21:58Z` specification. The complete technical blueprint, mathematical equations, and downstream contracts have been documented in `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1/survey_report.md`.

Key Deliverables Specified:
1. Watertight Diorama Cutaway Block ($160\text{m} \times 160\text{m}$, base at $Z = -14\text{m}$) with topsoil/subsoil/bedrock strata.
2. Multi-tier hydrology: Alpine Cascades $\to$ River $\to$ Central Lake ($Z = 4.5\text{m}$) $\to$ Lower Coastal Marine Bay ($Z = 0.0\text{m}$) with Volume Absorption sapphire/emerald shader.
3. Subterranean Karst Cave Network ($Z \in [-7\text{m}, +0.5\text{m}]$) with cavern vault, stalactites, stalagmites, underground pool ($Z = -6.8\text{m}$), and emissive bioluminescent fungi.
4. Slope-aware procedural terrain shading: cliffs $>40^\circ$ rock strata, scree $25^\circ-40^\circ$, flats $<25^\circ$ grass, snow $\ge 20\text{m}$, shoreline sand.

---

## 5. Verification Method

To independently verify the survey findings and prototype implementation:

1. **Execute Prototype Build & Assertions**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b --python /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1/prototype_survey.py
   ```
   *Expected Result*: Exits with code 0; asserts watertight diorama block ($>14,000$ vertices), cave cavern ($>400$ vertices), speleothems ($>190$ vertices), and compiled shaders.

2. **Execute Headless 3/4 Isometric Render**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b --python /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1/test_render.py
   ```
   *Expected Result*: Generates `test_render.png` with file size $> 100\text{ KB}$, displaying the complete 3D isometric diorama block, mountain snow caps, river, and cutaway walls.

3. **Inspect Survey Report**:
   Review `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1/survey_report.md` for full mathematical equations, code diffs, and interface contracts.
