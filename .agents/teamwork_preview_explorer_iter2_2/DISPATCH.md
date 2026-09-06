## 2026-09-03T17:06:11Z
You are teamwork_preview_explorer_iter2_2.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_2
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (read section ## 2026-09-03T16:45:06Z).
Challenger 1 Handoff: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_1/handoff.md
Current Terrain Code: /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/terrain_hydrology.py

Failure Context:
Challenger 1 reported REQUEST_CHANGES due to Riverbank Containment Failure:
"In 34 out of 80 cross-sections (sections 46 to 79), water ribbon edges float up to +1.383m above terrain. E.g. Section 53 at (-12.0, -2.5): left edge floats +0.607m, right edge floats +1.383m above terrain. The water ribbon is not recessed in a carved channel in low-lying valley sections."

Your Mission:
1. Inspect assets/blender_map/terrain_hydrology.py and analyze the river carving function and lateral bank levee calculation.
2. Formulate a precise mathematical fix in compute_terrain_elevation (and vectorized heightfield generation) that guarantees:
   - Along all 80 river cross-sections, the riverbed is carved below water level (depth >= 0.4m), and the lateral banks at distance w_channel rise strictly >= 0.3m above local river water level rz_near.
   - The river ribbon edges are strictly contained/recessed within the river trench, with 0 floating edges across all cross-sections.
   - Smooth confluence with the lake basin at (-18.0, -35.0) where river mouth elevation Z = 2.0m meets lake surface Z = 2.0m.
3. Recommend exact code modifications for the Worker. Do NOT modify source code directly.
4. Write your report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_2/survey_report.md and /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_2/handoff.md. Notify caller via send_message.
