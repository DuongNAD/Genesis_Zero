## 2026-09-05T05:18:40Z
Objective:
Investigate and document the exact requirements and biological/technical specifications for the 10 target Genesis Zero species:
1. Sand Skink (sand_skink)
2. Snow Ferret (snow_ferret)
3. Alpine Ibex (alpine_ibex)
4. Meadow Hare (meadow_hare)
5. Marsh Croc (marsh_croc)
6. Abyssal Hunter / Leviathan (abyssal_hunter / leviathan)
7. Storm Eagle (storm_eagle)
8. Giant Tarantula (giant_tarantula)
9. Armored Sentinel (armored_sentinel)
10. Carnivore Apex / L1_Evo (carnivore_apex / l1_evo)

Investigate:
1. Explore existing creature assets, schemas, simulation configs, traits, and documentation in /Users/duongnad/Documents/project/Genesis_Zero (e.g. docs/creatures/, assets/creatures/, web/, simulation logic).
2. Extract and define for each of the 10 species:
   - Biological traits: Brain, Speed, Armor, Attack, Sense, Stomach
   - Anatomical features and morphology (dimensions, body segments, limbs, tail, jaw, horn/claws/wings/fins)
   - Armature bone hierarchy (Root, Pelvis, Spine, Chest, Neck, Head, Jaw, Tail, Limbs, Paws/Claws, Wings/Fins)
   - 8 action animation clips requirements: Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death (motion dynamics, loop behavior, duration/frame ranges)
   - Organic PBR shader requirements (BaseColor, Subsurface Scattering, Roughness/Bump maps, Eye cornea/specular)
   - 4-angle turnaround image layout (Perspective 3/4, Front, Side, Top-Down)
   - Web viewer requirements (species listing, traits display, skeleton toggle, 8 animations, offline zero-CORS)
   - Verification acceptance criteria (mesh cleanliness: 0 loose vertices, 0 incontiguous edges, 0 ngons, 100% smooth shading; glTF skinning & 8 animations; image markers).

Deliverables:
- Maintain progress.md with liveness timestamp.
- Write full, self-contained handoff.md in /Users/duongnad/Documents/project/Genesis_Zero/.agents/spec_miner_creatures/handoff.md.
- Send message to caller when complete with summary and path to handoff.md.
