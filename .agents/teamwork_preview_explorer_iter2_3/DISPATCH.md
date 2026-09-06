## 2026-09-03T17:06:12Z
You are teamwork_preview_explorer_iter2_3.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_3
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (read section ## 2026-09-03T16:45:06Z).
Challenger 1 Handoff: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_1/handoff.md
Current Terrain Code: /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/terrain_hydrology.py
Current Flora Code: /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/flora_generator.py

Failure Context:
Challenger 1 noted:
"6/50 Reeds float 6-9.6cm due to 160x160 quad facet sag. Also verify that lake rim and riverbank fixes preserve overall terrain elevation delta >= 15m and slope diversity."

Your Mission:
1. Inspect assets/blender_map/flora_generator.py, specifically how reeds and plants sample terrain elevation.
2. Formulate an exact raycast or bilinear interpolation surface-snapping improvement for plant instances (e.g. using `mathutils.bvhtree.BVHTree.FromBMesh` or bilinear interpolation of the 4 quad corners) to eliminate even millimeter/centimeter float.
3. Verify that the combined terrain remediation preserves:
   - Span: 200m x 200m
   - Delta Z >= 15m (actual ~33m)
   - Color attribute `COLOR_0` mapping for PBR terrain shader.
4. Recommend exact code modifications for the Worker. Do NOT modify source code directly.
5. Write your report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_3/survey_report.md and /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_3/handoff.md. Notify caller via send_message.
