# Survey Task: Dynamic Environmental System & Weather Phenomena (R2 & Weather Telemetry)

## Objectives
1. Read `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically section `## 2026-09-03T04:57:00Z`).
2. Read `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md` and `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`.
3. Investigate the current simulation engine and networking:
   - `genesis/world.py`
   - `genesis/lawhook.py`
   - `genesis/domain.py`
   - `genesis/creature.py`
   - `net/match.py`
   - `net/routes_spectate.py`
4. Formulate architectural and technical requirements for R2:
   - Macro-environmental cycles & phases: day/night illumination cycles, toxic spore storms, solar flares, magnetic shifts, etc.
   - Seed-deterministic phase transitions, cycle progress, and duration tracking.
   - Dynamic simulation modulations:
     - Terrain passability changes (e.g. frozen water, flooded ground, storm turbulence).
     - Resource depletion & plant regeneration rates.
     - Stamina & movement energy costs across grid/biomes.
     - Visibility / sensory ranges or domain modifiers.
   - Telemetry broadcast format: `/v1/spectate` schema extensions for current weather phase, cycle progress, and active global modifiers.
   - Backward compatibility with existing spectator clients and referee scoring.
5. Write your comprehensive analysis to `analysis.md` and final handoff to `handoff.md` in your directory.

## 2026-09-03T04:58:34Z
You are Explorer 2 (Dynamic Weather & Environment Specialist) for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_weather_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_weather_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md

Investigate:
- genesis/world.py
- genesis/lawhook.py
- genesis/domain.py
- genesis/creature.py
- net/match.py
- net/routes_spectate.py

Produce a structured survey report in analysis.md and a self-contained handoff.md in your working directory. Cover:
1. Macro-environmental cycles & phases (day/night, toxic spore storms, solar flares, magnetic shifts).
2. Seed-deterministic phase transitions, cycle progress, and duration tracking.
3. Mechanics for modulations of passability, resource depletion/growth, stamina costs, sensory/visibility ranges.
4. WebSocket /v1/spectate schema extensions for weather state, progress, and global modifiers.
5. Backward compatibility with existing spectator clients and referee scoring.
6. Potential risks, edge cases, and test requirements.

Send a concise completion message back to parent when done, linking to your handoff report.
