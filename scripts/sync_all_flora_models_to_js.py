"""
sync_all_flora_models_to_js.py - Syncs all 103 GLB models into web/flora_models_data.js
"""

import base64
import glob
import os
from pathlib import Path

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
ASSETS_FLORA = ROOT / "assets" / "flora"
OUTPUT_JS = ROOT / "web" / "flora_models_data.js"

def sync_models():
    glb_files = sorted(glob.glob(str(ASSETS_FLORA / "**/*.glb"), recursive=True))
    print(f"Found {len(glb_files)} .glb files to sync into {OUTPUT_JS}...")

    lines = [
        "/* Genesis Zero — Embedded 3D Flora Binary Bundles (Zero-CORS offline file:// support) */",
        '(typeof window !== "undefined" ? window : globalThis).FLORA_MODELS_BASE64 = {'
    ]

    for idx, gf in enumerate(glb_files):
        slug = Path(gf).stem
        data = Path(gf).read_bytes()

        b64_str = base64.b64encode(data).decode("ascii")
        comma = "," if idx < len(glb_files) - 1 else ""
        lines.append(f'  "{slug}": "{b64_str}"{comma}')

    lines.append("};")
    lines.append("")

    content = "\n".join(lines)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(content)

    out_size = os.path.getsize(OUTPUT_JS)
    print(f"✓ Synchronized {len(glb_files)} models into {OUTPUT_JS} ({out_size / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    sync_models()
