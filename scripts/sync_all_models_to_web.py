import base64
import glob
import os
import re
from pathlib import Path

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
ASSETS_FLORA = ROOT / "assets" / "flora"
WEB_DIR = ROOT / "web"
MODELS_JS_PATH = WEB_DIR / "flora_models_data.js"
VIEWER_HTML_PATH = WEB_DIR / "flora_viewer.html"

# 1. Gather all GLB files
glb_files = sorted(glob.glob(str(ASSETS_FLORA / "**/*.glb"), recursive=True))
print(f">>> Found {len(glb_files)} .glb files on disk across assets/flora/.")

# 2. Build Base64 dictionary
b64_dict = {}
for gf in glb_files:
    slug = Path(gf).stem
    data = Path(gf).read_bytes()
    b64_dict[slug] = base64.b64encode(data).decode("ascii")

print(f">>> Encoded {len(b64_dict)} species to Base64.")

# Write flora_models_data.js
js_content = "/* Genesis Zero — Embedded 3D Flora Binary Bundles (Zero-CORS offline file:// support) */\n"
js_content += "(typeof window !== \"undefined\" ? window : globalThis).FLORA_MODELS_BASE64 = {\n"

entries = [f'  "{slug}": "{b64_dict[slug]}"' for slug in sorted(b64_dict.keys())]


js_content += ",\n".join(entries) + "\n};\n"

MODELS_JS_PATH.write_text(js_content, encoding="utf-8")
print(f"✓ Written {len(b64_dict)} models into {MODELS_JS_PATH} ({os.path.getsize(MODELS_JS_PATH)/1024:.1f} KB).")

# 3. Update flora_viewer.html
html = VIEWER_HTML_PATH.read_text(encoding="utf-8")

# For any slug that now has a dedicated GLB, remove representativeId or point directly
for slug in b64_dict:
    # Replace representativeId: "..." with representativeId: null for this species
    pattern = rf'(id:\s*"{slug}"[\s\S]*?representativeId:\s*)"[^"]+"'
    html = re.sub(pattern, rf'\1"{slug}"', html)

VIEWER_HTML_PATH.write_text(html, encoding="utf-8")
print(f"✓ Updated {VIEWER_HTML_PATH} to link all {len(b64_dict)} dedicated models!")
