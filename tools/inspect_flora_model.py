#!/usr/bin/env python3
"""
Genesis Zero — tools/inspect_flora_model.py
Automated Quality Verification Pipeline for 3D Botanical Models.
Executes Blender 5.2.1 headless to render 4 camera angles (Hero 3/4, Front, Side, Top),
composites a 2x2 verification contact sheet, and syncs to artifacts & docs.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"
CONV_ARTIFACTS = Path(os.environ.get("CONV_ARTIFACTS", "/Users/duongnad/.gemini/antigravity/brain/feae8c52-2578-4d4d-915a-29a62f276716"))


def compose_sheet(rendered_items, output_path, title):
    tile_w, tile_h = 1024, 1024
    sheet = Image.new("RGB", (tile_w * 2, tile_h * 2 + 100), (8, 12, 20))
    draw = ImageDraw.Draw(sheet)

    # Load high quality system font
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_badge = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception:
        font_title = font_sub = font_badge = None

    # Title header banner
    draw.rectangle([0, 0, tile_w * 2, 90], fill=(13, 19, 33))
    header_text = f"GENESIS ZERO 3D FLORA INSPECTION - {title.upper()}"
    draw.text((32, 28), header_text, fill=(56, 189, 248), font=font_title)
    draw.text((tile_w * 2 - 460, 36), "Blender 5.2.1 LTS | Multi-Angle Quality Check", fill=(148, 163, 184), font=font_sub)

    positions = [
        (0, 95),              # Top-Left: Hero 3/4
        (tile_w, 95),         # Top-Right: Front
        (0, tile_h + 95),     # Bottom-Left: Side
        (tile_w, tile_h + 95) # Bottom-Right: Top
    ]

    for idx, (img_file, label) in enumerate(rendered_items):
        if idx >= len(positions):
            break
        x, y = positions[idx]
        if os.path.exists(img_file):
            with Image.open(img_file) as im:
                sheet.paste(im, (x, y))
        # Label badge
        badge_box = [x + 20, y + 20, x + 460, y + 68]
        draw.rectangle(badge_box, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((x + 36, y + 32), label, fill=(241, 245, 249), font=font_badge)

    sheet.save(output_path, quality=95)
    print(f"[OK] Composite Contact Sheet created: {output_path}")


def inspect_model(blend_file_path, species_name=None, output_dir="/tmp/flora_inspection"):
    blend_path = Path(blend_file_path).resolve()
    if not blend_path.exists():
        print(f"Error: Blend file not found: {blend_path}", file=sys.stderr)
        return False

    if not species_name:
        species_name = blend_path.stem.replace("canopy_", "").replace("understory_", "").replace("succulent_", "").replace("carnivorous_", "").replace("cave_", "").replace("aquatic_", "").replace("grass_", "")

    out_dir = Path(output_dir) / species_name
    out_dir.mkdir(parents=True, exist_ok=True)

    inspector_script = Path(__file__).resolve().parent.parent / "assets" / "flora" / "generators" / "render_inspector.py"

    cmd = [
        BLENDER_BIN,
        "--background",
        str(blend_path),
        "--python",
        str(inspector_script),
        "--",
        str(blend_path),
        str(out_dir),
        species_name
    ]

    print(f"[...] Running Blender multi-angle renderer on: {blend_path.name}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Blender render error:", res.stderr, file=sys.stderr)
        print(res.stdout)
        return False

    rendered_items = [
        (str(out_dir / f"{species_name}_01_hero_34.png"), "1. Phối Cảnh 3/4 (Hero Perspective)"),
        (str(out_dir / f"{species_name}_02_front.png"), "2. Mặt Trước (Front View)"),
        (str(out_dir / f"{species_name}_03_side.png"), "3. Mặt Bên (Side View)"),
        (str(out_dir / f"{species_name}_04_top.png"), "4. Nhìn Từ Trên Xuống (Top-Down Plan)")
    ]

    sheet_path = out_dir / f"{species_name}_inspection_sheet.png"
    compose_sheet(rendered_items, str(sheet_path), species_name)

    # Sync to Artifact directory and docs/web
    targets = [
        CONV_ARTIFACTS / f"{species_name}_inspection_sheet.png",
        Path("docs/flora/images") / f"{species_name}_inspection_sheet.png",
        Path("web/flora_images") / f"{species_name}_inspection_sheet.png"
    ]

    for t in targets:
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sheet_path, t)
        print(f"[OK] Synced to: {t}")

    return str(sheet_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect 3D botanical models from multiple angles.")
    parser.add_argument("blend_file", help="Path to .blend file")
    parser.add_argument("--name", help="Species name identifier", default=None)
    parser.add_argument("--out", help="Output directory", default="/tmp/flora_inspection")
    args = parser.parse_args()

    inspect_model(args.blend_file, args.name, args.out)
