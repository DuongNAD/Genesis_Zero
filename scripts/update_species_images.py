import os
from pathlib import Path

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
IMG_DIR = ROOT / "docs" / "flora" / "images"
SPECIES_DIR = ROOT / "docs" / "flora" / "species"

for img_file in IMG_DIR.glob("*_turnaround.jpg"):
    slug = img_file.name.replace("_turnaround.jpg", "")
    md_file = SPECIES_DIR / f"{slug}.md"
    if md_file.exists():
        content = md_file.read_text(encoding="utf-8")
        if "_turnaround.jpg" not in content:
            img_embed = f"""
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Bản vẽ 3D Turnaround Concept Sheet - {slug}](file://{img_file.resolve()})

---
"""
            # Insert right after the header block
            parts = content.split("---", 1)
            if len(parts) == 2:
                new_content = parts[0] + "---\n" + img_embed + parts[1]
                md_file.write_text(new_content, encoding="utf-8")
                print(f"✓ Đã nhúng ảnh model sheet vào: {md_file.name}")

print("Hoàn tất cập nhật ảnh concept turnaround vào các file đặc tả loài!")
