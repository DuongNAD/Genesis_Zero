#!/usr/bin/env python3
"""
Genesis Zero — Synchronize 3D Creature Models to Embedded Base64 Data JS
Encodes all .glb models from assets/creatures/ (and related creature assets) into Base64
and writes to web/creature_models_data.js for Zero-CORS offline viewing via file:// protocol.
"""

import base64
import glob
import hashlib
import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_CREATURES = PROJECT_ROOT / "assets" / "creatures"
WEB_DIR = PROJECT_ROOT / "web"
OUTPUT_JS = WEB_DIR / "creature_models_data.js"

# Aliases mapping matching SPECIES_METADATA in test_creature_assets.py and verify_creatures_pipeline.py
SPECIES_ALIASES = {
    "sand_skink": ["creature_L1_s1", "L1", "L1_s1"],
    "snow_ferret": ["creature_L2_s1", "L2", "L2_s1"],
    "alpine_ibex": ["creature_L3_s1", "L3", "L3_s1"],
    "meadow_hare": ["creature_L4_s1", "L4", "L4_s1"],
    "marsh_croc": ["creature_L5_s1", "L5", "L5_s1"],
    "abyssal_hunter": ["creature_W1_s1", "W1", "W1_s1"],
    "storm_eagle": ["creature_A1_s1", "A1", "A1_s1"],
    "giant_tarantula": ["creature_giant_tarantula", "Tarantula"],
    "armored_sentinel": ["genesis_sentinel", "creature_armored_sentinel", "Sentinel"],
    "carnivore_apex": ["creature_L1_Evo_s1", "L1_Evo", "L1_Evo_s1"],
}

# Reverse lookup: from alias / filename stem to canonical species key
STEM_TO_CANONICAL = {}
for canonical, aliases in SPECIES_ALIASES.items():
    STEM_TO_CANONICAL[canonical] = canonical
    for alias in aliases:
        STEM_TO_CANONICAL[alias] = canonical


def collect_creature_glb_files() -> dict[str, Path]:
    """Collect all creature .glb files from assets/creatures/."""
    files_by_stem: dict[str, Path] = {}

    if ASSETS_CREATURES.exists():
        for p in sorted(ASSETS_CREATURES.glob("*.glb")):
            files_by_stem[p.stem] = p

    return files_by_stem


def sync_all_creatures_to_js() -> Path:
    """Encode .glb files into Base64 and output web/creature_models_data.js."""
    glb_files = collect_creature_glb_files()
    print(f"[*] Found {len(glb_files)} source .glb files:")
    for stem, p in glb_files.items():
        print(f"    - {stem}: {p} ({p.stat().st_size} bytes)")

    # Build entry dictionary: key -> base64_str
    entries: dict[str, str] = {}

    for stem, glb_path in glb_files.items():
        raw_bytes = glb_path.read_bytes()
        b64_str = base64.b64encode(raw_bytes).decode("ascii")

        # Map by exact file stem
        entries[stem] = b64_str

        # If this stem corresponds to a known species or alias, map all aliases and canonical name
        canonical = STEM_TO_CANONICAL.get(stem)
        if canonical:
            entries[canonical] = b64_str
            for alias in SPECIES_ALIASES.get(canonical, []):
                entries[alias] = b64_str

    # Format output file
    lines = [
        "/* Genesis Zero — Embedded 3D Creature Binary Bundles (Zero-CORS offline file:// support) */",
        '(typeof window !== "undefined" ? window : globalThis).CREATURE_MODELS_BASE64 = {'
    ]

    keys = sorted(entries.keys())
    for idx, k in enumerate(keys):
        comma = "," if idx < len(keys) - 1 else ""
        lines.append(f'  "{k}": "{entries[k]}"{comma}')

    lines.append("};")
    lines.append("")

    content = "\n".join(lines)
    OUTPUT_JS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(content)

    out_size_mb = OUTPUT_JS.stat().st_size / (1024 * 1024)
    print(f"[✓] Successfully wrote {len(entries)} keys to {OUTPUT_JS} ({out_size_mb:.2f} MB)")
    return OUTPUT_JS


if __name__ == "__main__":
    sync_all_creatures_to_js()
