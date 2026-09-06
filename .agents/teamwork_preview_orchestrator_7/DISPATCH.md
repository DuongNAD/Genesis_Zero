## 2026-09-05T05:17:22Z

You are teamwork_preview_orchestrator_7 (Role: Project Orchestrator).
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_7.
The workspace root is /Users/duongnad/Documents/project/Genesis_Zero.

Your mission is to lead and orchestrate the full execution of the latest user request recorded in /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md:
"Tái thiết kế và nâng cấp toàn diện hệ sinh thái sinh vật cốt lõi trong Genesis Zero đạt chất lượng tả thực cao (Photorealistic / Scan-Quality), cấu trúc giải phẫu học hữu cơ mượt mà, vật liệu PBR sinh học chi tiết (vảy sừng, lông mao, màng da thấu quang, mắt ướt phản quang), gắn bộ xương Rigging Armature phân cấp hoàn chỉnh và tạo trọn bộ 8 animation chuyển động sống động chuẩn Game Engine, kèm bản vẽ concept Turnaround 4 góc nhìn và Trình xem Sinh vật 3D Web chuyên dụng."

Target Species:
1. Land: Sand Skink (sand_skink), Snow Ferret (snow_ferret), Alpine Ibex (alpine_ibex), Meadow Hare (meadow_hare), Marsh Croc (marsh_croc)
2. Water: Abyssal Hunter / Leviathan (abyssal_hunter / leviathan)
3. Air: Storm Eagle (storm_eagle)
4. Special & Evolutionary: Giant Tarantula (giant_tarantula), Armored Sentinel (armored_sentinel), Carnivore Apex / L1_Evo (carnivore_apex / l1_evo)

Key Deliverables:
- R1: Photorealistic organic 3D anatomy, clean manifold BMesh (0 loose vertices, 0 incontiguous edges, 0 ngons, 100% smooth shading) with .blend and .glb for all target species in assets/creatures/.
- R2: Hierarchical Rigging Armatures and full set of 8 action animation clips (Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death) baked into NLA tracks in glTF 2.0 (.glb).
- R3: Organic PBR shaders (Subsurface Scattering, Bump/Roughness, cornea/specular reflective eyes).
- R4: 4-Angle Concept Turnaround Sheets (Perspective 3/4, Front, Side, Top-Down) at web/creature_images/<species>_turnaround.jpg and docs/creatures/images/<species>_turnaround.jpg.
- R5: Interactive 3D Creature Web Viewer at web/creature_viewer.html with species selector, 8-animation control panel + playback speed, skeleton/armature toggle overlay, traits/features inspection, 4-angle modal viewer, and offline zero-CORS data support.
- R6: Automated verification suite: scripts/verify_creatures_pipeline.py and pytest tests/test_creature_assets.py passing 100% (exit code 0).
