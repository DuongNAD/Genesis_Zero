# Handoff Report — Explorer Survey Rep 1 (Creature Ecosystem Overhaul)

## 1. Observation

Direct observations from examining the codebase, configuration files, existing generators, and specification requirements:

1. **Mandatory Request Specifications (`.agents/ORIGINAL_REQUEST.md:329-410`)**:
   - Section header: `## 2026-09-05T05:16:35Z`.
   - Core requirement: Complete overhaul of Genesis Zero creatures to photorealistic / scan-quality standard with organic anatomy, bio-PBR materials (SSS, bump/roughness, wet specular eyes), hierarchical armature rigging, full set of 8 animation actions, 4-angle concept turnaround sheets, and interactive 3D web viewer (`web/creature_viewer.html`).
   - 10 Target Species:
     - Land: Thằn lằn cát L1 (*Sand Skink*), Chồn tuyết L2 (*Snow Ferret*), Dê sừng núi L3 (*Alpine Ibex*), Thỏ đồng cỏ L4 (*Meadow Hare*), Cá sấu đầm lầy L5 (*Marsh Croc*).
     - Water: Cá săn mồi biển sâu W1 (*Abyssal Hunter* / *Leviathan*).
     - Air: Đại bàng săn mồi bầu trời A1 (*Storm Eagle*).
     - Special & Evolved: Nhện khổng lồ nhiều chân (*Giant Tarantula*), Sentinel cơ khí sinh học bọc giáp (*Armored Sentinel*), Quái thú săn mồi tiến hóa Apex (*Carnivore Apex* / *L1_Evo*).

2. **Trait Schema and Derived Math (`genesis/config.py:46-60`, `genesis/traits.py:28-66`)**:
   - 6 Core traits: `brain`, `attack`, `armor`, `speed`, `sense`, `stomach`.
   - Baseline Founder vectors (Sum = 12, range 0..5):
     - `L1`: `(4, 3, 1, 2, 1, 1)`
     - `L2`: `(3, 4, 2, 1, 2, 0)`
     - `L3`: `(3, 1, 1, 3, 3, 1)`
     - `L4`: `(1, 1, 5, 1, 2, 2)`
     - `L5`: `(0, 2, 0, 5, 3, 2)`
     - `W1`: `(1, 1, 0, 5, 4, 1)` (Domain NUOC)
     - `A1`: `(2, 2, 0, 4, 4, 0)` (Domain TROI)
   - Derived formulas:
     - `energy_max = 85 + 8 * stomach`
     - `token_budget = 32 + 36 * brain`
     - `think_interval = max(2, 7 - brain)`
     - `damage = 4 + 3 * attack`
     - `dmg_taken_mult = 1.0 - 0.12 * armor`
     - `moves_per_tick = 1 + speed // 2`
     - `sight_radius = 2 + sense`
     - `upkeep = 1.0 + 0.15*brain + 0.25*attack + 0.20*armor + 0.30*speed + 0.10*sense + 0.25*stomach`

3. **Multi-Tier Point Scale in Procedural Builder (`genesis/creature_builder.py:1-66`)**:
   - `creature_builder.py:3`: "Hỗ trợ max điểm lên tới 7, tổng điểm 16, 20, 23 điểm theo từng bậc tiến hóa (Tier 1 con mồi, Tier 2 săn mồi, Tier 3 cự thú Apex)."
   - Morphological scale factors derived from traits:
     - `brain_scale = 0.75 + 0.12 * brain`
     - `attack_scale = 0.75 + 0.14 * attack`
     - `armor_scale = 0.75 + 0.12 * armor`
     - `speed_scale = 0.75 + 0.14 * speed`
     - `sense_scale = 0.75 + 0.12 * sense`
     - `stomach_scale = 0.75 + 0.12 * stomach`

4. **12 Biological Features (`genesis/features.py:72-154`)**:
   - Movement: `LUONG_CU` (amphibious), `DAO_HANG` (burrowing, enters CAVE/ROCK), `TREO_GIOI` (climb bonus +2 speed), `CANH_LUOT` (glider flaps).
   - Defense: `LONG_DAI` (fur, upkeep x0.85), `VAY_CUNG` (scales, dmg taken x0.80), `GAI_DOC` (spikes, thorns 2.0), `VO_SO` (shell, dmg taken x0.60, upkeep x1.15).
   - Sensory: `MAT_DEM` (night vision), `RAU_CAM_UNG` (whiskers, feel radius 2).
   - Foraging/Attack: `RANG_NANH` (fangs, damage x1.25), `TUI_MA` (cheek pouches, upkeep x0.90).

5. **Existing Files & Assets in Repository**:
   - Blender CLI: `/Applications/Blender.app/Contents/MacOS/Blender` (verified working).
   - Existing meshes in `assets/creatures/`: `creature_L1_s1.glb` to `creature_L5_s1.glb`, `creature_W1_s1.glb`, `creature_A1_s1.glb`, `creature_L1_Evo_s1.glb` (~50-175 KB).
   - Existing prototype viewer in `web/test_creature.html`: Three.js viewer with animation buttons, wireframe, and bone skeleton toggle.
   - Missing directories that must be created: `docs/creatures/images/`, `web/creature_images/`, and `web/creature_viewer.html`.

---

## 2. Logic Chain

1. **Species Mapping Logic**:
   - The user request establishes 10 clear species across three domains plus special/evolved tiers.
   - 7 core founders map directly to `L1`..`L5`, `W1`, `A1`.
   - 3 specialized/evolved species (`giant_tarantula`, `armored_sentinel`, `carnivore_apex`) map to specialized arthropod mechanics, biomechanical defense units, and Tier 3 evolved apex beasts respectively.
   - The trait budget for founders is strictly 12; for evolved/specialist species, it follows the `creature_builder.py` tier scale: 16 points for specialist Tier 2, and 23 points for Tier 3 Apex Behemoth.

2. **Anatomy and Armature Rigging Logic**:
   - To avoid mesh tearing and rigid deformation during skeletal animation, bone hierarchies must be strictly parented with smooth skin weights (`ArmatureDeformModifier` with vertex groups).
   - Land quadrupeds share standard tetrapod bone hierarchies: `Root -> Pelvis -> Spine -> Chest -> Neck -> Head -> Jaw`, with symmetrical `Shoulder/Hip -> Upper/Thigh -> Fore/Shin -> Paw/Hoof/Claw` chains.
   - Aerial species require segmented wing chains (`Wing_Shoulder -> Wing_Arm -> Wing_Forearm -> Wing_Hand -> Primary_Feathers`) and fanned tail controls.
   - Aquatic species require carangiform/undulatory spine chains (`Spine_Main -> Thoracic -> Head` and `Tail_1`..`Tail_4 -> CaudalFin`).
   - Multipedal species (`giant_tarantula`) require dedicated prosoma-coxa-femur-tibia-tarsus chains across all 8 legs plus chelicerae and pedipalps.

3. **Animation Standard Logic**:
   - The requirement explicitly mandates 8 action clips per species:
     1. `Idle_Normal`, 2. `Idle_Alert`, 3. `Walk`, 4. `Run`, 5. `Attack`, 6. `Hurt_Defend`, 7. `Eat`, 8. `Death`.
   - Each action must have distinct keyframing (breathing chest scale, head cocking, gait phasing, strike anticipation/recovery, death collapse).
   - All clips must be baked into individual NLA tracks in Blender prior to glTF 2.0 export so that Three.js `AnimationMixer` detects and plays them seamlessly.

4. **Visual & Turnaround Asset Pipeline Logic**:
   - Following the successful flora pattern (`web/flora_images/<species>_turnaround.jpg` and `docs/flora/images/`), creature turnaround sheets must be rendered at standard 4-angle layout:
     - Upper half: 3/4 Perspective Hero View.
     - Lower half: Front Orthographic, Side Orthographic, and Top-Down Orthographic views.
   - High-fidelity PBR requires Principled BSDF with SSS on soft tissue (ears, throat, membranes), procedural micro-bump/displacement for scales/fur/exoskeleton, and dual-layer cornea/specular eyes with dark pupils.

---

## 3. Caveats

1. **Headless Generation Performance**:
   - Generating 10 high-poly procedural meshes with subdivision surface, full armatures, 8 baked actions, and multi-angle camera renders via Blender headless takes ~15-30 seconds per species.
2. **Zero-CORS Local Web Serving**:
   - When loading `.glb` models and turnaround JPEG images in `web/creature_viewer.html`, browsers require a local HTTP server (`python -m http.server` or `uvicorn net.server:app`) or base64 fallbacks to prevent local file CORS blocks.
3. **DSL Law Hook Integration**:
   - Evolved trait totals (>12) are valid for simulation and visual display, but in competitive strict online mode, founder validation enforces `TRAIT_SUM = 12`.

---

## 4. Conclusion: 10 Target Species Detailed Specification Matrix

### Summary Table

| Species Slug | Common Name / Tier | Domain | Traits (Brain, Atk, Arm, Spd, Sns, Stm) | Key Features | Key Anatomical Markers |
|---|---|---|---|---|---|
| `sand_skink` | Thằn lằn cát L1 | `CAN` | `(4, 3, 1, 2, 1, 1)` | `VAY_CUNG`, `DAO_HANG` | Streamlined wedge snout, granular scales, sprawling limbs, whip tail |
| `snow_ferret` | Chồn tuyết L2 | `CAN` | `(3, 4, 2, 1, 2, 0)` | `LONG_DAI`, `MAT_DEM`, `DAO_HANG` | Tubular mustelid body, white thermal fur, sharp carnassials, bushy tail |
| `alpine_ibex` | Dê sừng núi L3 | `CAN` | `(3, 1, 1, 3, 3, 1)` | `TREO_GIOI`, `VAY_CUNG` | Sturdy ungulate frame, curved ridged horns, split adhesion hooves, beard |
| `meadow_hare` | Thỏ đồng cỏ L4 | `CAN` | `(1, 1, 5, 1, 2, 2)` | `VO_SO`, `VAY_CUNG`, `DAO_HANG` | Dorsal osteoderm shell, long swivel ears, powerful spring hindlegs |
| `marsh_croc` | Cá sấu đầm lầy L5 | `CAN` | `(0, 2, 0, 5, 3, 2)` | `LUONG_CU`, `GAI_DOC` | Flattened body, raised orbits, interlocking conical teeth, webbed toes, scuted tail |
| `abyssal_hunter` | Cá săn mồi biển sâu W1 | `NUOC` | `(1, 1, 0, 5, 4, 1)` | `RAU_CAM_UNG`, `CAMOUFLAGE` | Hydrodynamic torpedo, needle teeth, bioluminescent photophores, crescent caudal |
| `storm_eagle` | Đại bàng săn mồi A1 | `TROI` | `(2, 2, 0, 4, 4, 0)` | `CANH_LUOT`, `MAT_DEM` | Aerodynamic raptor body, expansive fanned wings, hooked beak, sharp talons |
| `giant_tarantula` | Nhện khổng lồ | `CAN` | `(2, 4, 2, 3, 4, 1)` | `GAI_DOC`, `DAO_HANG`, `RAU_CAM_UNG` | Prosoma + bulbous opisthosoma, 8 segmented legs, chelicerae fangs, 8 ocelli |
| `armored_sentinel` | Sentinel bọc giáp | `CAN` | `(3, 3, 6, 1, 3, 0)` | `VO_SO`, `GAI_DOC`, `MAT_DEM` | Biomechanical chassis, faceted carapace shields, optical sensor slit, pistons |
| `carnivore_apex` | Quái thú Apex L1_Evo | `CAN` | `(5, 6, 3, 4, 3, 2)` | `RANG_NANH`, `VAY_CUNG`, `GAI_DOC` | Muscular behemoth frame, cranial horn crest, double saber fangs, spiked tail |

### 10 Species Deep Profiles

#### 1. `sand_skink` (Thằn lằn cát L1)
- **Target Traits**: `brain: 4, attack: 3, armor: 1, speed: 2, sense: 1, stomach: 1` (Sum: 12).
  - Derived: HP max 50, Energy max 93, Upkeep 3.35, Damage 13, Dmg taken 88%, Moves/tick 2, Sight radius 3.
- **Anatomy**: Low-profile desert skink, tapered wedge snout for sand-burrowing, sleek cylindrical torso, fringed 5-toed feet, smooth overlapping granular scales, long tapering tail.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine_Mid -> Chest -> Neck -> Head -> Jaw`, `Shoulder.L/R -> UpperArm -> Forearm -> Foot`, `Hip.L/R -> Thigh -> Shin -> Foot.Hind`, `Tail_1` to `Tail_5`.
- **8 Actions**:
  - `Idle_Normal`: Low breathing chest pulse, throat gular flutter, lateral head scan.
  - `Idle_Alert`: Raises head high, forelimbs stiffen, tongue/snout scans environment.
  - `Walk`: Lateral spinal undulation with alternating sprawling foot placement.
  - `Run`: High-frequency sand-skimming sprint with tail whip counter-balance.
  - `Attack`: Rapid lateral coil anticipation into sudden jaw snap clamp.
  - `Hurt_Defend`: Flattens body flush to ground, tucks neck, lateral tail twitch.
  - `Eat`: Quick head dip, biting down, rapid jaw mastication.
  - `Death`: Spine spasms, limbs curl inward, rolls onto flank with open jaw.
- **PBR Details**: Sandy ochre base with dark chevron markings. Roughness 0.50, Specular 0.55 with Voronoi micro-scale bump. Ventral throat SSS (0.15). Glossy amber slit eyes.
- **Turnaround Paths**:
  - `web/creature_images/sand_skink_turnaround.jpg`
  - `docs/creatures/images/sand_skink_turnaround.jpg`

#### 2. `snow_ferret` (Chồn tuyết L2)
- **Target Traits**: `brain: 3, attack: 4, armor: 2, speed: 1, sense: 2, stomach: 0` (Sum: 12).
  - Derived: HP max 50, Energy max 85, Upkeep 3.35, Damage 16, Dmg taken 76%, Moves/tick 1, Sight radius 4.
- **Anatomy**: Sleek elongated mustelid body, triangular skull with short rounded ears, long flexible cervical/lumbar spine, sharp canine carnassials, short sturdy digging paws, plumed tail.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine_Lower -> Spine_Mid -> Chest -> Neck -> Head -> Jaw`, `Ear.L/R`, `Shoulder.L/R -> UpperArm -> Forearm -> Paw`, `Hip.L/R -> Thigh -> Shin -> Paw.Hind`, `Tail_1` to `Tail_4`.
- **8 Actions**:
  - `Idle_Normal`: Rhythmic chest breathing, twitching nose, subtle tail sweep.
  - `Idle_Alert`: Rears up on hind legs into vertical periscope pose, ears perked.
  - `Walk`: Low bounding mustelid step with arching back.
  - `Run`: Fast undulating gallop with extreme lumbar contraction and extension.
  - `Attack`: Pounce leap, forepaw grapple, lethal throat latch bite.
  - `Hurt_Defend`: Arches back high, hisses, flattens ears, springs backward.
  - `Eat`: Paws hold down food, head jerks sideways to tear meat chunks.
  - `Death`: Hindlimbs collapse, body slides forward into snow, spine relaxes.
- **PBR Details**: Ermine white winter coat with cream undertones, black tail tip. Anisotropic velvet fur sheen, roughness 0.70. SSS on ear flaps and pink paw pads (0.30). Wet black nose and glossy obsidian eyes.
- **Turnaround Paths**:
  - `web/creature_images/snow_ferret_turnaround.jpg`
  - `docs/creatures/images/snow_ferret_turnaround.jpg`

#### 3. `alpine_ibex` (Dê sừng núi L3)
- **Target Traits**: `brain: 3, attack: 1, armor: 1, speed: 3, sense: 3, stomach: 1` (Sum: 12).
  - Derived: HP max 50, Energy max 93, Upkeep 3.40, Damage 7, Dmg taken 88%, Moves/tick 2, Sight radius 5.
- **Anatomy**: Muscular compact ungulate body, deep ribcage, backward-arching ridged keratin horns, chin beard, surefooted split cloven hooves with concave suction pads.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine_Lumbar -> Spine_Thoracic -> Chest -> Neck_Lower -> Neck_Upper -> Head -> Jaw`, `Horn_L.1..2`, `Horn_R.1..2`, `Scapula.L/R -> Humerus -> Radius -> Hoof`, `Hip.L/R -> Femur -> Tibia -> Hoof.Hind`, `Tail_Short`.
- **8 Actions**:
  - `Idle_Normal`: Weight shifts between hooves, steady breathing, subtle ear flick.
  - `Idle_Alert`: Head thrusts upward, horns swept back, nostrils flare, stomps front hoof.
  - `Walk`: Surefooted cloven-hoof gait with horizontal level spine.
  - `Run`: Uphill bounding leap across crags with strong hindlimb propulsion.
  - `Attack`: Headbutt clash: rears slightly and slams forehead/horns downward.
  - `Hurt_Defend`: Steps back, lowers horns into protective defensive wedge.
  - `Eat`: Lowers head to graze rock moss, rhythmic circular cud chewing.
  - `Death`: Forelegs buckle, slides laterally against slope, horns tip downward.
- **PBR Details**: Earthy weathered gray-brown fleece, lighter belly. Keratin horns with prominent growth ridges (roughness 0.75). Split polished hooves. Horizontal ruminant pupils with gold iris.
- **Turnaround Paths**:
  - `web/creature_images/alpine_ibex_turnaround.jpg`
  - `docs/creatures/images/alpine_ibex_turnaround.jpg`

#### 4. `meadow_hare` (Thỏ đồng cỏ L4)
- **Target Traits**: `brain: 1, attack: 1, armor: 5, speed: 1, sense: 2, stomach: 2` (Sum: 12).
  - Derived: HP max 50, Energy max 101, Upkeep 3.65, Damage 7, Dmg taken 40%, Moves/tick 1, Sight radius 4.
- **Anatomy**: Compact lagomorph body reinforced with interlocking dorsal osteoderm plates (armored shell), long upright rotatable ears, powerful elongated spring hind feet, soft tail puff.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine_Mid -> Chest -> Neck -> Head -> Jaw`, `Ear_Base.L/R -> Ear_Mid -> Ear_Tip`, `Shoulder.L/R -> UpperArm -> Forearm -> Foot`, `Hip.L/R -> Thigh -> Shin -> Foot_Hind`, `Tail_Puff`.
- **8 Actions**:
  - `Idle_Normal`: Rapid nose twitching, breathing flank expansion, ear micro-turns.
  - `Idle_Alert`: Freezes in low crouch, ears swivel 180 degrees independently.
  - `Walk`: Creeping low foraging hop through grass.
  - `Run`: High-leverage zig-zag escape bounding sprint.
  - `Attack`: Double hindlimb rabbit kick or defensive claw scratch.
  - `Hurt_Defend`: Tucks into tight armored ball, carapace plates shield neck, ears fold flat.
  - `Eat`: Nibbles clover/grass, rapid vertical jaw chewing, whiskers tremble.
  - `Death`: Flops sideways onto turf, ears droop back, hind legs extend limp.
- **PBR Details**: Tawny agouti fur paired with ceramic matte bone-carapace plates. High SSS on thin ear membranes (0.35, pinkish transmission). Bulging dark hemispherical glossy eyes.
- **Turnaround Paths**:
  - `web/creature_images/meadow_hare_turnaround.jpg`
  - `docs/creatures/images/meadow_hare_turnaround.jpg`

#### 5. `marsh_croc` (Cá sấu đầm lầy L5)
- **Target Traits**: `brain: 0, attack: 2, armor: 0, speed: 5, sense: 3, stomach: 2` (Sum: 12).
  - Derived: HP max 50, Energy max 101, Upkeep 3.80, Damage 10, Dmg taken 100%, Moves/tick 3, Sight radius 5.
- **Anatomy**: Heavily armored dorsoventrally flattened crocodilian, broad predatory snout with protruding teeth, elevated eye orbits and nostrils for surface skimming, webbed clawed toes, laterally flattened swimming tail.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine_1 -> Spine_2 -> Chest -> Neck -> Head -> Jaw_Lower`, `Shoulder.L/R -> UpperArm -> Forearm -> Hand_Claw`, `Hip.L/R -> Thigh -> Shin -> Foot_Webbed`, `Tail_1` to `Tail_5`.
- **8 Actions**:
  - `Idle_Normal`: Low shallow breathing, gular throat pump, motionless ambush repose.
  - `Idle_Alert`: Raises snout above waterline, pupils narrow, tail tip stiffens.
  - `Walk`: High-walk posture with belly lifted clear of mud.
  - `Run`: Explosive belly-sledging mud gallop or water charge.
  - `Attack`: Rapid forward lunge, crushing jaw clamp, violent death-roll twist.
  - `Hurt_Defend`: Wide-jaw hiss showing yellow-pink mouth cavity, defensive tail sweep.
  - `Eat`: Thrashing head shakes tear meat, rapid backward gulping swallows.
  - `Death`: Flips belly-up in water/mud, lower jaw slackens, limbs float motionless.
- **PBR Details**: Olive-brown to swamp green scute pattern with black rosettes. Heavy normal map for rough osteoderms. High clearcoat (0.85) for wet swamp sheen. Slit reptilian yellow-green eyes.
- **Turnaround Paths**:
  - `web/creature_images/marsh_croc_turnaround.jpg`
  - `docs/creatures/images/marsh_croc_turnaround.jpg`

#### 6. `abyssal_hunter` / `leviathan` (Cá săn mồi biển sâu W1)
- **Target Traits**: `brain: 1, attack: 1, armor: 0, speed: 5, sense: 4, stomach: 1` (Sum: 12).
  - Derived: HP max 50, Energy max 93, Upkeep 3.55, Damage 7, Dmg taken 100%, Moves/tick 3, Sight radius 6.
- **Anatomy**: Hydrodynamic pelagic predator, sleek fusiform torso, pectoral and pelvic hydrofoil fins, dorsal stabilizer, bioluminescent flank nodes, hinged jaws with needle teeth, crescent caudal tail fin.
- **Bone Hierarchy**: `Root -> Spine_Main -> Spine_Thoracic -> Head -> Jaw_Lower`, `PectoralFin.L/R -> PectoralFin_Tip`, `PelvicFin.L/R`, `DorsalFin`, `Tail_1` to `Tail_3 -> CaudalFin_Upper/Lower`.
- **8 Actions**:
  - `Idle_Normal`: Gentle cruising fin strokes, rhythmic opercular gill flare.
  - `Idle_Alert`: Fins brake forward, bioluminescent photophores illuminate bright cyan.
  - `Walk` (Cruise): Smooth sinusoidal body undulation across water column.
  - `Run` (Sprint): High-frequency, high-amplitude caudal tail burst charge.
  - `Attack`: Jaw hyperextension ram-feeding snap with needle teeth locking.
  - `Hurt_Defend`: Convulsive body flex, lateral fin shudder, banking evasive dive.
  - `Eat`: Jaws clamp over prey, water expels through gills, throat expands.
  - `Death`: Tail stops pulsating, fish rolls onto side/belly-up, slowly sinks into abyss.
- **PBR Details**: Deep midnight blue countershading into silvery cyan belly. Emissive cyan glow nodes (strength 3.0). Wet iridescent sheen (specular 0.9, roughness 0.15). Spherical high-refraction glass eyes.
- **Turnaround Paths**:
  - `web/creature_images/abyssal_hunter_turnaround.jpg`
  - `docs/creatures/images/abyssal_hunter_turnaround.jpg`

#### 7. `storm_eagle` (Đại bàng săn mồi A1)
- **Target Traits**: `brain: 2, attack: 2, armor: 0, speed: 4, sense: 4, stomach: 0` (Sum: 12).
  - Derived: HP max 50, Energy max 85, Upkeep 3.40, Damage 10, Dmg taken 100%, Moves/tick 3, Sight radius 6.
- **Anatomy**: Aerodynamic predatory raptor, expansive feathered wings with separated primary flight feathers, hooked raptorial beak with yellow cere, supraorbital brow ridge, sharp curved black talons, fanned steering tail.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine -> Chest -> Neck_Lower -> Neck_Upper -> Head -> Beak_Lower`, `Wing_Shoulder.L/R -> Wing_Arm -> Wing_Forearm -> Wing_Hand -> Feathers_Primary`, `Leg_Upper.L/R -> Leg_Lower -> Talon_Base -> Claws`, `Tail_Feathers`.
- **8 Actions**:
  - `Idle_Normal`: Perched chest breathing, wing settling ruffle, sharp head rotations.
  - `Idle_Alert`: Leans forward into launch posture, wings slightly unfurl, screech call.
  - `Walk` (Shuffle): Ground hop with half-spread wings balancing.
  - `Run` (Flap Flight): Powerful rhythmic downward wing strokes driving forward flight.
  - `Attack`: High-speed stoop dive, wings tuck back, talons thrust forward in strike grapple.
  - `Hurt_Defend`: Wings raise like twin shields, snaps beak, body recoils backward.
  - `Eat`: Foot pins prey to ground, hooked beak rips upward tearing meat.
  - `Death`: Wings fold loosely, neck droops, body rolls forward into limp plumage.
- **PBR Details**: Charcoal and slate flight feathers with golden mantle coverts, white crown/tail feathers. Keratin golden beak and claws (roughness 0.25). Penetrating gold iris with pinpoint pupil.
- **Turnaround Paths**:
  - `web/creature_images/storm_eagle_turnaround.jpg`
  - `docs/creatures/images/storm_eagle_turnaround.jpg`

#### 8. `giant_tarantula` (Nhện khổng lồ nhiều chân)
- **Target Traits**: Specialized Arthropod Hunter (Sum: 16).
  - `brain: 2, attack: 4, armor: 2, speed: 3, sense: 4, stomach: 1`
  - Derived: HP max 50, Energy max 93, Upkeep 3.90, Damage 16, Dmg taken 76%, Moves/tick 2, Sight radius 6.
- **Anatomy**: Two-part arachnid body: compact cephalothorax and large bulbous abdomen, 8 multi-jointed walking legs, 2 tactile pedipalps, curved downward chelicerae fangs, 8 clustered eye ocelli, posterior spinnerets.
- **Bone Hierarchy**: `Root -> Cephalothorax -> Abdomen -> Spinnerets`, `Chelicera.L/R -> Fang`, `Pedipalp_1..3.L/R`, `Leg_1..4_Coxa.L/R -> Femur -> Tibia -> Tarsus` (8 complete leg chains).
- **8 Actions**:
  - `Idle_Normal`: Abdomen pulsates, legs micro-step, pedipalps groom chelicerae.
  - `Idle_Alert`: Threat pose: rears cephalothorax high, raises front 4 legs, bares dripping fangs.
  - `Walk`: Classic alternating tetrapod gait (4 legs move, 4 support).
  - `Run`: Rapid scurrying sprint with fluid coordinated multi-leg cycling.
  - `Attack`: Downward venom strike: lunges forward and plunges fangs deep into prey.
  - `Hurt_Defend`: Curls all 8 legs tightly over body in impenetrable defensive ball.
  - `Eat`: Chelicerae pump digestive enzymes, mouthparts masticate food.
  - `Death`: Spider death curl: all 8 legs curl inwards under thorax, abdomen sags.
- **PBR Details**: Velvety dark brown-black chitin with bright fiery orange knee rings. Hair/fuzz anisotropic specular rim. Glossy jet-black fangs with translucent venom droplet. 8 glistening jet ocelli.
- **Turnaround Paths**:
  - `web/creature_images/giant_tarantula_turnaround.jpg`
  - `docs/creatures/images/giant_tarantula_turnaround.jpg`

#### 9. `armored_sentinel` (Sentinel cơ khí sinh học bọc giáp)
- **Target Traits**: Biomechanical Guardian (Sum: 16).
  - `brain: 3, attack: 3, armor: 6, speed: 1, sense: 3, stomach: 0`
  - Derived: HP max 50, Energy max 85, Upkeep 4.05, Damage 13, Dmg taken 28%, Moves/tick 1, Sight radius 5.
- **Anatomy**: Heavy quad biomechanical walker, faceted chiseled carapace shield plates, reinforced reactor chest core, glowing multispectral visor slit, hydraulic limb pistons, stabilizing tail boom.
- **Bone Hierarchy**: `Root -> Chassis_Core -> Reactor_Chest -> Sensor_Head -> Mandibles`, `Carapace_Shield.L/R`, `Shoulder_Piston.L/R -> UpperLeg -> LowerLeg -> Foot_Pad`, `Hip_Piston.L/R -> UpperLeg_H -> LowerLeg_H -> Foot_Pad_H`, `Tail_Stabilizer`.
- **8 Actions**:
  - `Idle_Normal`: Low mechanical engine hum, core pulse breathing, subtle servo adjustments.
  - `Idle_Alert`: Sensor head extends, optical visor spins/focuses, carapace panels open.
  - `Walk`: Heavy mechanical rhythmic stomp with hydraulic compression and ground impact.
  - `Run`: Stomping charge with lowered center of mass and elevated engine whine.
  - `Attack`: Pneumatic pincer smash or explosive kinetic shell bash with spark flare.
  - `Hurt_Defend`: Carapace plates lock shut into impenetrable dome shield, protecting core.
  - `Eat` (Recharge): Clamps energy conduit or mineral rock, reactor vents pulse intensely.
  - `Death`: Reactor core flickers and explodes in flash, hydraulics depressurize and collapse.
- **PBR Details**: Brushed dark tungsten and gunmetal plates with edge wear and scratches (metallic 0.85, roughness 0.35). Bright emissive cyan/amber channels along vents and visor (strength 2.5).
- **Turnaround Paths**:
  - `web/creature_images/armored_sentinel_turnaround.jpg`
  - `docs/creatures/images/armored_sentinel_turnaround.jpg`

#### 10. `carnivore_apex` / `l1_evo` (Quái thú săn mồi tiến hóa Apex)
- **Target Traits**: Tier 3 Apex Behemoth (Sum: 23 - Max Evolutionary Tier).
  - `brain: 5, attack: 6, armor: 3, speed: 4, sense: 3, stomach: 2`
  - Derived: HP max 50, Energy max 101, Upkeep 5.25, Damage 22, Dmg taken 64%, Moves/tick 3, Sight radius 5.
- **Anatomy**: Massive muscular theropod-feline apex predator, armored cranial crest, double row of saber canines, muscular shoulder hump, heavily clawed digitigrade paws, thick spiked tail with bone club.
- **Bone Hierarchy**: `Root -> Pelvis -> Spine_Lower -> Spine_Mid -> Spine_Chest -> Neck_Base -> Neck_Top -> Head_Apex -> Jaw_Lower`, `Crest_Spine`, `Shoulder.L/R -> UpperArm -> Forearm -> Claw_Hand`, `Hip.L/R -> Thigh -> Shin -> Paw_Apex`, `Tail_Base -> Tail_Mid -> Tail_End -> Tail_Club`.
- **8 Actions**:
  - `Idle_Normal`: Deep resonant chest heave, low growl, slow sweeping tail club.
  - `Idle_Alert`: Intimidating roar stance: rears chest high, crest flares, jaws open wide in challenge.
  - `Walk`: Heavy prowling gait with muscular shoulder rolling under skin.
  - `Run`: Thundering predatory gallop, high momentum, massive ground stride.
  - `Attack`: Savage crushing bite accompanied by forward claw maul and tail club sweep.
  - `Hurt_Defend`: Snarls violently, plants hindlimbs, counter-swipes with razor foreclaw.
  - `Eat`: Dominant tearing of prey, violent head twists, crushing bone crunches.
  - `Death`: Monumental collapse: knees give out, heavy body crashes into earth with dust settle.
- **PBR Details**: Obsidian black scaly hide with crimson undertones and deep gold tiger stripes. Deep crimson oral cavity SSS (0.25). Polished ivory bone fangs and claws with blood grooves (roughness 0.18). Piercing glowing gold-red slit eyes.
- **Turnaround Paths**:
  - `web/creature_images/carnivore_apex_turnaround.jpg`
  - `docs/creatures/images/carnivore_apex_turnaround.jpg`

---

## 5. Verification Method

To independently verify these specifications and asset pipelines:

1. **Verify Trait Math & Constraints**:
   ```bash
   python3 - <<'PY'
   from genesis.traits import Traits
   from genesis import config
   for sp, v in config.FOUNDERS.items():
       t = Traits(*v)
       assert sum(v) == config.TRAIT_SUM
       print(f"{sp}: hp_max={config.HP_MAX}, energy_max={t.energy_max}, dmg={t.damage}, upkeep={t.upkeep:.2f}")
   print("All founder trait vectors verified.")
   PY
   ```

2. **Verify Procedural Generator Syntax & Mesh Armature Structure**:
   ```bash
   pytest tests/test_creature_builder.py
   ```

3. **Verify Asset Pipeline & glTF 2.0 Animation NLA Tracks**:
   Inspect existing or generated `.glb` files with `gltf-pipeline` or Python script:
   - Check that `Armature` object and `Skin` exist.
   - Assert all 8 action names are present (`Idle_Normal`, `Idle_Alert`, `Walk`, `Run`, `Attack`, `Hurt_Defend`, `Eat`, `Death`).
   - Assert BMesh clean manifold geometry: 0 loose vertices, 0 incontiguous edges, 0 ngons, 100% smooth shading.

4. **Verify Web Viewer & Turnaround Asset Presence**:
   Check that `web/creature_viewer.html` loads all 10 species models and displays their 4-angle turnaround images without CORS errors under local server:
   ```bash
   python3 -m http.server 8080 --directory web
   ```
