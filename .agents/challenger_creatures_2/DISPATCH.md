## 2026-09-05T10:06:02Z

You are challenger_creatures_2.
Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_creatures_2.
Workspace root: /Users/duongnad/Documents/project/Genesis_Zero.
Mandatory reading: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md. Subagents MUST read it before starting work.

IMPORTANT: DO NOT invoke subagents. You are a challenger agent; inspect and verify files directly.

Your Mission:
Adversarially challenge the Web Viewer, Zero-CORS offline data, turnaround images, and system regressions:
1. Zero-CORS Offline Data Integrity:
   - Verify SHA256 checksums: decode base64 strings from web/creature_models_data.js and verify exact byte-level match with assets/creatures/<species>.glb for all 10 species.
2. Web Viewer Self-Containment:
   - Verify web/creature_viewer.html has 0 external CDN script tags (uses local vendor/three.min.js and vendor/GLTFLoader.js).
3. Turnaround Image Conformance:
   - Verify JPEG SOI (\xff\xd8) and EOI (\xff\xd9) markers, file sizes, and 1024x1084 resolutions across all 20 image files in web/creature_images/ and docs/creatures/images/.
4. Regression Testing:
   - Run pytest tests/test_creature.py tests/test_creature_builder.py to verify existing simulation logic has no regressions.

Deliverables:
- Keep progress.md updated.
- Render an empirical verdict in handoff.md: APPROVE or REQUEST_CHANGES.
- Write handoff.md in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_creatures_2/handoff.md.
- Send message to caller with your verdict.
