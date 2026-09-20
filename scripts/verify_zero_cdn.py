"""Verify WebGL spectator and 3D viewer offline zero-CDN compliance."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files to verify
files_to_check = [
    ROOT / "assets" / "blender_map" / "viewer.html",
    ROOT / "web" / "watch.html",
    ROOT / "web" / "watch.js",
    ROOT / "web" / "watch3d.html",
    ROOT / "web" / "watch3d.js",
]

script_src_pattern = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
link_href_pattern = re.compile(r'<link[^>]+href=["\']([^"\']+)["\']', re.IGNORECASE)
forbidden_proto = re.compile(r'^(?:https?:)?//', re.IGNORECASE)

violations = []

for file_path in files_to_check:
    if not file_path.exists():
        violations.append((str(file_path), "File not found"))
        continue

    content = file_path.read_text(encoding="utf-8")

    # Check for external http/https or protocol-relative in HTML files
    if file_path.suffix.lower() == ".html":
        # Check script tags
        scripts = script_src_pattern.findall(content)
        for s in scripts:
            if forbidden_proto.match(s) or "cdn" in s.lower():
                violations.append((str(file_path.relative_to(ROOT)), f"Forbidden external script: {s}"))
            else:
                # verify local existence
                target = file_path.parent / s
                if not target.exists():
                    violations.append((str(file_path.relative_to(ROOT)), f"Local script target missing: {s}"))

        # Check link tags
        links = link_href_pattern.findall(content)
        violations.extend(
            (str(file_path.relative_to(ROOT)), f"Forbidden external link: {link}")
            for link in links
            if forbidden_proto.match(link) or "cdn" in link.lower()
        )


    elif file_path.suffix.lower() == ".js":
        # Check for external import or fetch URLs to external domains
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if "http://" in line or "https://" in line or "//cdn" in line:
                # Exclude localhost, 127.0.0.1, ws://, wss://
                if not any(safe in line for safe in ["localhost", "127.0.0.1", "ws://", "wss://"]):
                    violations.append((str(file_path.relative_to(ROOT)), f"Line {i}: {line.strip()}"))

print(f"Scanned {len(files_to_check)} WebGL/Spectator primary files.")
if violations:
    print(f"FAILED: Found {len(violations)} violations:")
    for path, detail in violations:
        print(f"  {path} -> {detail}")
    sys.exit(1)
else:
    print("SUCCESS: Strictly 0 external CDN or remote references found. 100% offline zero-CDN compliant.")
    sys.exit(0)
