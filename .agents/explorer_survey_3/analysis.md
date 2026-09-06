# R3: 3D Visualizer & Compact Map Experience — Comprehensive Survey & Architecture Analysis

> **Target**: Comprehensive survey of Genesis Zero's 3D visualization stack, Three.js client architecture, map representations, biological trait morphology, 3-tier biomes, Law Journal / hidden physics event rendering, UX/performance gaps, and concrete improvements.
> **Date**: 2026-09-02 (Local: 2026-09-03)
> **Author**: Explorer 3 (R3: 3D Visualizer & Compact Map Experience)

---

## 1. Executive Summary

Genesis Zero simulates an ecosystem where LLM-controlled creatures interact on a 24×24 toroidal world, formulating and testing hypotheses about hidden physical laws. While the simulation backend (`genesis/`, `net/`) supports rich multi-tier ecology (3 domains, 8 terrain types, 12 biological features, 6 adaptive traits, dynamic Law Journal scoring, and 3 victory titles), the current 3D visualizer (`web/watch3d.html` and `web/watch3d.js`) is an **early minimal prototype (~288 lines)** that severely under-represents the simulation's visual and interactive potential.

### Key Survey Findings
1. **Critical Entity Omissions in 3D**: `web/watch3d.js` completely drops `plants` (fruits/food) and `corpses` from rendering, despite receiving them in every telemetry frame. Organisms only exist as floating blobs with no food or remains visible in the 3D scene.
2. **Missing 3-Tier Elevation & Domain Physics**: All organisms are hardcoded to ground elevation `y = 0.10` (`web/watch3d.js:176`). Aquatic species (`Domain.NUOC`, `W1`) do not swim submerged in water; flying species (`Domain.TROI`, `A1`) do not soar in the sky; tree climbers (`can_enter(TREE)`) do not climb into tree canopies; and caves (`C`) are rendered as flat opaque black blocks without interior cavities.
3. **Absence of Biological Features (W-19)**: The 12 biological features (`LUONG_CU`, `DAO_HANG`, `TREO_GIOI`, `CANH_LUOT`, `LONG_DAI`, `VAY_CUNG`, `GAI_DOC`, `VO_SO`, `MAT_DEM`, `RAU_CAM_UNG`, `RANG_NANH`, `TUI_MA`) and 3 domain silhouettes are completely unrendered in the procedural 3D model generator.
4. **Law Journal (Sổ Luật) & Victory Unrendered**: The visualizer lacks any real-time HUD for the Codex / Law Journal. During the `REVEAL` phase, the 3D scene does not highlight the true physical laws or celebrate the 3 victory titles (`Nhà khoa học`, `Kẻ sống sót`, `Người đầu tiên`).
5. **Framing & Camera UX Gaps**: The 24×24 grid floats disconnected in empty space without a framed diorama / pedestal base. Camera controls lack inertia, smooth framing, creature following/inspection mode, and tactical minimap overlays.
6. **High-Performance Foundation**: The underlying Three.js setup correctly leverages `InstancedMesh` for terrain boxes and avoids external CDNs/build steps (`web/vendor/three.min.js`), complying with offline-first project invariants.

---

## 2. Telemetry & Data Stream Architecture

### 2.1 WebSocket Protocol (`/v1/spectate`)
The real-time visualization stream is served via FastAPI WebSocket at `net/routes_spectate.py:42-81` and pushed from `net/match.py:553-590`.

#### Telemetry Frame Schema (`frame`)
```json
{
  "t": 42,
  "phase": "RUNNING",
  "w": 24,
  "h": 24,
  "map": "DONG_CO",
  "terrain": ["PWP...", "..."], // Only sent at tick 0 or prepended for late-joiners
  "creatures": [
    {
      "id": "L1:0",
      "x": 12,
      "y": 8,
      "hp": 48.5,
      "e": 74.2,
      "e_max": 93.0,
      "alive": true,
      "feral": false,
      "tr": [4, 3, 1, 2, 1, 1]
    }
  ],
  "plants": [[5, 6], [12, 18]],
  "corpses": [[9, 14]],
  "terrain_delta": [],
  "events": [
    {
      "k": "SPEAK",
      "who": "L1:0",
      "sig": "ALARM",
      "hear": ["L1:1", "L2:0"]
    },
    {
      "k": "LAW_FIRED",
      "who": "L3:1",
      "law": "?",
      "pos": [12, 8]
    },
    {
      "k": "DEATH",
      "who": "L5:2",
      "cause": "COMBAT"
    }
  ]
}
```

### 2.2 Security & Invariant Boundaries
- **No Law Leak Invariant (`net/match.py:69-86`)**: Before the `REVEAL` phase, `LAW_FIRED` events obfuscate the law name with `"law": "?"`. Only the coordinates `pos` are sent so the visualizer can render a mysterious physical event spark without leaking the ground truth.
- **Pure Presentation Invariant (`net/routes_spectate.py:11-15`)**: Spectate routes attach an `asyncio.Queue` subscriber to `runner.subscribers`. It never patches simulation methods, avoiding race conditions or simulation drift when clients connect/disconnect.
- **Anti-Cheat / Scale Invariant (`docs/02 §5`)**: Organism sizes in 3D are strictly derived from biological traits (`tr`), never from LLM model parameter counts or client metadata (`test_spectate.py:125-136`).

---

## 3. Map Representation & Compact Framing Analysis

### 3.1 Map Grid & Layout
- **Dimensions**: Fixed 24×24 toroidal grid (`genesis/config.py:14-16`).
- **Map Rotation**: 5 distinct maps (`genesis/maps.py:53-85`):
  1. `DONG_CO` (Grassland): Balanced baseline map.
  2. `HOANG_MAC` (Desert): Arid, high rock, scarce water.
  3. `QUAN_DAO` (Archipelago): Fragmented islands separated by deep and shallow water.
  4. `HEM_NUI` (Canyon): Narrow cliff corridors, forced encounters.
  5. `RUNG_RAM` (Jungle): Dense bushes and trees, obstructed sight and hearing.

### 3.2 Terrain Height & Color Representation
In `web/watch3d.js:22-31`, the visualizer maps single-character terrain codes to basic heights and colors:

| Code | Terrain | Name | Current Height (`h`) | Current Color (`c`) | Biome Tier |
|:---:|:---|:---|:---:|:---:|:---|
| `P` | `PLAIN` | Đồng cỏ | 0.10 | `#3f6212` | Land (Surface) |
| `W` | `WATER` | Nước nông | 0.02 | `#1d4ed8` | Water (Shallow) |
| `B` | `BUSH` | Bụi rậm | 0.45 | `#14532d` | Land (Foliage) |
| `R` | `ROCK` | Đá vách | 0.95 | `#57534e` | Land (Obstacle) |
| `F` | `FIRE` | Lửa cháy | 0.16 | `#ea580c` | Land (Hazard) |
| `D` | `DEEP` | Nước sâu | 0.00 | `#0c2a6b` | Water (Abyss) |
| `T` | `TREE` | Cây cao | 1.40 | `#166534` | Canopy / Sky Interface |
| `C` | `CAVE` | Hang đá | 0.30 | `#1c1917` | Subterranean Core |

### 3.3 Framing & Camera Control Deficiencies
- **Disjointed Void Rendering**: The terrain is rendered as raw box meshes hovering over a dark void (`#06080f`). There is no diorama pedestal, no stone/wood framing bezel, no underwater bedrock skirt, and no shoreline water plane.
- **Fixed Center of Orbit**: Orbit controls (`web/watch3d.js:54-69`) pivot strictly around `cx = 12, cz = 12`. Users cannot pan the camera, frame specific sectors, or inspect individual organisms.
- **Lack of Camera Presets**:
  - Missing **Isometric View (45° tilt)**: Ideal for compact whole-map tactical overview.
  - Missing **Top-Down Tactical (90° ortho-style)**: For map-wide territory analysis.
  - Missing **Cinematic Follow-Cam**: Smoothly tracking a selected creature as it hunts, eats, or flees.
- **No Boundary Wrapping Indicator**: Because the world is toroidal, creatures moving past `x = 23` wrap to `x = 0`. Without a subtle visual wrapping edge or perimeter guide, movements near the boundary look like glitchy teleports.

---

## 4. 3-Tier Biome Ecosystem & Environmental Rendering

### 4.1 The 3-Tier Ecological Architecture (`genesis/domain.py`)
Genesis Zero implements a strict 3-tier domain ecosystem:
1. **Water Tier (`Domain.NUOC` / `W1` Fish)**: Can enter `WATER` and `DEEP`. Cannot walk on land. Survives on `ALGAE` in water.
2. **Land Tier (`Domain.CAN` / `L1..L5`)**: Can enter `PLAIN`, `BUSH`, and `WATER`. Gated by traits: `speed >= 3` allows climbing `TREE`; `armor >= 3` allows crossing `FIRE`; `DAO_HANG` allows entering `CAVE`.
3. **Sky Tier (`Domain.TROI` / `A1` Bird)**: Flies over all terrains (`PLAIN`, `BUSH`, `WATER`, `ROCK`, `DEEP`, `TREE`, `CAVE`, `FIRE`), but must descend (`can_touch`) onto land or trees to eat or interact.

### 4.2 Current Visualizer Flaws in 3-Tier Rendering

```
CURRENT (FLAT MAPPING):
============================================================
  Sky (A1 Bird)      --> Flattened to ground (y = 0.10) [INCORRECT]
  Tree Climber (L5)  --> Flattened to ground (y = 0.10) [INCORRECT]
  Surface (L1..L4)   --> Ground (y = 0.10)
  Fish (W1)          --> Floating on dry box (y = 0.10) [INCORRECT]
  Cave (C)           --> Solid dark box (no opening)    [INCORRECT]
============================================================

REQUIRED (TRUE 3-TIER ELEVATION):
============================================================
  Sky (TROI, A1)     --> Hovering / Gliding (y = 2.4 - 3.0) + flight bobbing
  Tree Canopy (T)    --> Perched on tree crown (y = 1.45)
  Land Surface (P,B) --> Surface walking (y = 0.12 - 0.48)
  Shallow Water (W)  --> Wading / Swimming at water line (y = 0.05)
  Deep Water (D, W1) --> Submerged aquatic swimming (y = -0.25 to 0.00)
  Cave Core (C)      --> Recessed cavern pocket inside rock mass (y = 0.05)
============================================================
```

### 4.3 Missing Environmental Effects
1. **Water Surface Simulation**: Current water (`W`, `D`) is a static colored box. A proper visualizer requires a semi-transparent water plane with vertex ripple displacement, specular glint, and depth color falloff (light cyan for `W`, deep midnight blue for `D`).
2. **Day/Night & Lighting Ambiance**: `genesis/config.py:96` defines `NIGHT_SIGHT_PENALTY`. A dynamic lighting cycle (warm daylight sun $\rightarrow$ golden sunset $\rightarrow$ cool blue moonlight) provides critical visual context for nocturnal traits (`MAT_DEM`).
3. **Map-Specific Weather Particles**:
   - `DONG_CO`: Floating dandelion seeds / pollen particles.
   - `HOANG_MAC`: Dust swirls and heat distortion shimmer.
   - `QUAN_DAO`: Soft tropical rain / sea mist.
   - `HEM_NUI`: Wind gust lines and rock dust.
   - `RUNG_RAM`: Glowing fireflies and falling leaf particles.

---

## 5. Organism 3D Morphology & Biological Features

### 5.1 Trait Vector Mapping (`tr: [brain, attack, armor, speed, sense, stomach]`)
The simulation defines 6 traits (`genesis/traits.py`), each in $[0, 5]$ with $\sum = 12$. The current visualizer (`web/watch3d.js:122-168`) procedural generator only handles basic trait primitives:

| Trait | Simulation Meaning | Current 3D Primitive (`watch3d.js`) | Gap / Enhancement Opportunity |
|:---|:---|:---|:---|
| **Brain** | Token budget, interval, codex vocabulary | Head sphere radius (`0.07 + brain*0.028`) | Add pulsating neural glow / cranial ridge patterns |
| **Attack** | Melee damage (`4 + 3*atk`) | Single snout cone (`0.05 + atk*0.022`) | Dual curved fangs / predator mandibles / sharpened horn |
| **Armor** | Damage reduction ($12\%$/pt) | $0..5$ spine cones along back | Segmented dorsal armor plates / chitinous shell banding |
| **Speed** | Moves per tick ($1 + \lfloor \text{spd}/2 \rfloor$) | Body Z-stretch scale (`1 + spd*0.14`) | Articulated limb count / tail propulsion rudder / sprint posture |
| **Sense** | Sight & hearing radius ($2 + \text{sense}$) | 2 white eye spheres | Multi-eye cluster ($2 \rightarrow 4 \rightarrow 6$ eyes) + sensory antennae / whiskers |
| **Stomach** | Energy capacity ($85 + 8*\text{stm}$) | Body sphere radius (`0.16 + stm*0.035`) | Plump abdominal girth / metabolic fullness glow |

### 5.2 Missing Biological Features (W-19 Features)
In `genesis/features.py:72-154`, each species rolls **3 distinct biological features**. These are completely missing in `watch3d.js`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       12 BIOLOGICAL FEATURES (W-19)                         │
├───────────────────┬───────────────────────────────┬─────────────────────────┤
│ Category          │ Feature Key & Name            │ Procedural 3D Visual    │
├───────────────────┼───────────────────────────────┼─────────────────────────┤
│ Locomotion        │ LUONG_CU (Lưỡng cư)          │ Webbed flippers & tail  │
│                   │ DAO_HANG (Biết đào hang)     │ Heavy digging claws     │
│                   │ TREO_GIOI (Trèo giỏi)        │ Prehensile curling tail │
│                   │ CANH_LUOT (Màng lượn)         │ Lateral gliding membrane│
├───────────────────┼───────────────────────────────┼─────────────────────────┤
│ Defense           │ LONG_DAI (Lông dài)           │ Shaggy fibrous mantle   │
│                   │ VAY_CUNG (Vảy cứng)          │ Overlapping scute scales│
│                   │ GAI_DOC (Gai độc)             │ Bioluminescent spikes   │
│                   │ VO_SO (Vỏ sò)                 │ Heavy dome carapace     │
├───────────────────┼───────────────────────────────┼─────────────────────────┤
│ Senses & Feeding  │ MAT_DEM (Mắt đêm)             │ Large luminescent pupils│
│                   │ RAU_CAM_UNG (Râu cảm ứng)     │ Flexible twin vibrissae │
│                   │ RANG_NANH (Răng nanh)         │ Prominent saber tusks   │
│                   │ TUI_MA (Túi má)               │ Bulging lateral pouches │
└───────────────────┴───────────────────────────────┴─────────────────────────┘
```

### 5.3 Missing Entities: Plants, Algae & Corpses
- **Fruits / Plants (`frame.plants`)**: `genesis/law_config.py` defines 4 surface permutations (`FRUIT_A..D` with color/shape). The 3D visualizer currently ignores `frame.plants`. It should render fruit clusters with distinct low-poly meshes (spherical, oblong, star-spiked) atop grass cells.
- **Aquatic Algae**: For `Domain.NUOC`, algae clusters should be rendered as undulating green kelp fronds in `WATER` and `DEEP` cells.
- **Corpses (`frame.corpses`)**: Currently ignored. Should render skeletal remains (ribcage / bone pile) with a decaying opacity timer.

### 5.4 Smooth Movement & Interpolation
- **Current Behavior**: Teleports instantaneously between discrete grid coordinates `(x, y)`.
- **Enhanced Behavior**: Position lerping ($\text{lerp}(p_{\text{prev}}, p_{\text{curr}}, \alpha)$) with heading alignment (rotating the creature mesh to face its direction of travel) and subtle walk/swim/glide bobbing oscillations.

---

## 6. Law Journal (Sổ Luật) & Hidden Physics VFX

### 6.1 Hidden Law Activation VFX (`LAW_FIRED`)
- **Simulation Mechanics**: When an organism triggers a condition (e.g. eating a certain fruit while adjacent to rock at night), a hidden law fires (`net/match.py:82-86`).
- **Current 3D Implementation**: A single expanding yellow wireframe ring (`RingGeometry(0.2, 0.28)`) that fades in 500ms.
- **Enhanced Visualizer VFX**:
  - Distinct elemental pulse waves depending on context:
    - **Energy / Metabolism**: Rising golden photon spiral.
    - **Combat / Poison**: Purple shockwave ring with lingering caustic mist.
    - **Healing / Recovery**: Ascending emerald sparkles.
    - **Spatial / Resonance**: Concentric chromatic ripples expanding across the terrain mesh.

### 6.2 Law Journal (Sổ Luật) Live UI HUD
- **Codex State Tracking (`genesis/codex.py`)**: Organisms record hypothesis entries in their Codex slots ($1..5$ confidence).
- **Missing HUD Panel**: The visualizer needs a collapsible "Sổ Luật / Codex" panel displaying:
  - Real-time active hypotheses recorded by observing creatures.
  - Confidence stars ($★1..★5$).
  - Discovery timeline sparklines.

### 6.3 `REVEAL` Phase Grand Unmasking & Victory Podium
- When `frame.phase === "REVEAL"`:
  - The true physical laws (`laws_public()`) are transmitted in natural Vietnamese.
  - The 3D UI should trigger a dramatic celebratory transition:
    - A top banner displaying the **True Revealed Laws of the Universe**.
    - A 3D Victory Podium highlighting the 3 championship titles (`genesis/victory.py`):
      1. 🏆 **Nhà khoa học (The Scientist)**: Highest scientific reward $R$.
      2. 🛡️ **Kẻ sống sót (The Survivor)**: Longest survival tick percentage.
      3. ⚡ **Người đầu tiên (The Pioneer)**: First organism to discover and retain the true law.

---

## 7. UI/UX & Interactive Capabilities Matrix

| Feature Component | Current Visualizer State (`watch3d.js`) | Gap / Flaw | Target Experience |
|:---|:---|:---|:---|
| **Scene Framing** | Raw 24×24 boxes in void | No aesthetic framing, feels empty | Compact diorama island with stone base, ocean edge & boundary bezel |
| **Camera Navigation** | Orbit drag around (12,12) | No panning, no focus, abrupt stops | Smooth orbit with inertia, pan support, preset angles (Iso, Top, Orbit) |
| **Creature Inspection** | None (non-interactive) | Cannot view stats or identify creatures | Click creature $\rightarrow$ Camera tracks creature, opens floating status HUD |
| **Plants & Corpses** | Completely absent | Food and corpses invisible | Low-poly fruit meshes, kelp fronds, and bone pile remains |
| **3-Tier Elevations** | Flat $y=0.10$ | Birds and fish look identical to ground | True 3D heights: Sky ($y=2.5$), Trees ($y=1.45$), Water ($y=-0.25$) |
| **Biological Traits** | 6 basic primitives | Generic, no domain silhouette | Distinct Fish / Quadruped / Bird bases + 12 feature props |
| **Hearing Graph** | Single cyan/grey lines | High GC churn from buffer reallocations | Instanced/shared line segments with glowing signal pulses |
| **Law Activation** | Generic flat yellow ring | Lack of visual impact | Thematic multi-ring particle shockwaves and mystical aura |
| **Law Journal HUD** | Missing | Spectators cannot see what agents believe | Live Codex tracker HUD with confidence ratings and hypothesis log |
| **Victory Celebration** | Text log only | No grand conclusion at game end | 3D Victory pedestal and Revealed Laws showcase |
| **Tactical Minimap** | None | Hard to track overall map activity | Compact 2D/orthographic minimap in corner with domain filters |
| **Weather & Night** | Static lighting | Night penalties not visible | Smooth day/night cycle, ambient moonlight, weather particle effects |

---

## 8. Performance & Architecture Constraints

### 8.1 Zero External Dependencies & Build-less Protocol
- **Local Three.js (`web/vendor/three.min.js`)**: All 3D rendering must run directly from local static assets without CDN requests or npm build steps (`test_spectate.py:138-148`).
- **Memory & Garbage Collection (GC) Optimization**:
  - Avoid creating `new THREE.BufferGeometry()` inside the `requestAnimationFrame` loop (current flaw in `drawHearing`).
  - Use pre-allocated object pools for particle sparks and hearing connection lines.
  - Retain `InstancedMesh` for terrain and food assets to maintain stable 60 FPS on standard integrated GPUs.

---

## 9. Concrete Implementation Roadmap for R3

To transform `web/watch3d.html` and `web/watch3d.js` into a vivid, compact, engaging visualizer, the following concrete modifications are planned:

### Phase 1: Scene Architecture & Compact Diorama Base
- Add an elegant floating island diorama pedestal around the 24×24 map with wooden/stone bezels and deep-water drop-off skirts.
- Implement semi-transparent multi-layer water shaders for `W` and `D` with subtle wave vertex oscillations.
- Add camera presets (Isometric 45°, Top-down tactical, Free Orbit, Creature Follow) with smooth damping.

### Phase 2: 3-Tier Ecosystem & Entity Rendering
- Position entities at accurate 3-tier elevations (Sky $y=2.5$, Tree canopy $y=1.45$, Ground $y=0.25$, Submerged water $y=-0.2$).
- Render fruits/plants on land (`frame.plants`), algae in water, and skeletal corpses (`frame.corpses`).
- Implement smooth position interpolation (lerping) and creature heading rotation.

### Phase 3: Procedural 3D Morphology & Biological Features
- Differentiate 3 core domain silhouettes:
  - `NUOC` (Aquatic/Fish): Streamlined body, dorsal/pectoral fins, vertical caudal fin.
  - `CAN` (Terrestrial): Quadrupedal body with articulated limbs and head posture.
  - `TROI` (Avian): Aerodynamic fuselage with outstretched wings and tail fan.
- Add procedural accessories for the 12 W-19 features (`LUONG_CU`, `DAO_HANG`, `TREO_GIOI`, `CANH_LUOT`, `LONG_DAI`, `VAY_CUNG`, `GAI_DOC`, `VO_SO`, `MAT_DEM`, `RAU_CAM_UNG`, `RANG_NANH`, `TUI_MA`).

### Phase 4: Law Journal HUD & Hidden Physics VFX
- Build the live Law Journal / Codex HUD overlay displaying active hypotheses and confidence ratings.
- Upgrade `LAW_FIRED` visual effects to dynamic multi-ring shockwaves with contextual particle emissions.
- Implement the `REVEAL` phase celebration modal and 3D Victory Leaderboard displaying the 3 championship titles.

### Phase 5: Creature Inspection Card & Tactical Minimap
- Implement Raycaster mouse selection: clicking any creature focuses the camera and displays its detailed biological card (HP, Energy, Domain, Features, Brain tier, Generation, Active Goal, Codex entries).
- Add a collapsible corner tactical minimap with domain entity filters.
