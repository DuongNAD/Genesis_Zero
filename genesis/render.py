"""Genesis Zero — render: hiển thị terminal với Rich."""

from __future__ import annotations

import colorsys
import hashlib
from collections.abc import Sequence
from functools import lru_cache

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from genesis.creature import Creature, creature_sort_key
from genesis.world import (
    CORPSE_GLYPH,
    PLANT_GLYPH,
    TERRAIN_GLYPHS,
    Terrain,
    World,
)

# Pool ký tự hình học đơn rộng đúng một ô (B1)
GLYPH_POOL: tuple[str, ...] = tuple("◆◇○●□■△▲▽▼◈◉◍◎★☆✦✧⬩⬪⌾⍟⏥⌘⍚⌗⊕⊗⊙⊚")

TERRAIN_STYLES: dict[Terrain, str] = {
    Terrain.PLAIN: "dim #555555",
    Terrain.WATER: "bold #1e90ff",
    Terrain.BUSH: "bold #2e8b57",
    Terrain.ROCK: "bold #888888",
    Terrain.FIRE: "bold #ff3300",
}

FRUIT_GLYPHS: dict[str, str] = {
    "FRUIT_A": "*",
    "FRUIT_B": "%",
    "FRUIT_C": "$",
    "FRUIT_D": "@",
}


def glyph_of(species_id: str) -> str:
    """Vị trí BẮT ĐẦU trong pool cho một loài, tính bằng md5.

    Cảnh báo: hàm này CÓ THỂ trả cùng ký tự cho hai loài khác nhau. Để hiển thị
    thì luôn dùng `assign_glyphs()`, đừng gọi thẳng hàm này.
    """
    digest = hashlib.md5(species_id.encode("utf-8")).hexdigest()
    idx = int(digest, 16) % len(GLYPH_POOL)
    return GLYPH_POOL[idx]


def assign_glyphs(species_ids: Sequence[str]) -> dict[str, str]:
    """Gán glyph KHÔNG ĐỤNG NHAU cho một tập loài, tất định.

    Bẫy: băm độc lập rồi lấy mod cho từng loài là chưa đủ. Với 5 loài trên 30 ô,
    xác suất có ít nhất một cặp đụng đã là ~30% — và md5 của "L1", "L2", "L3",
    "L5" tình cờ cùng dư 12, nên bốn loài ra CÙNG một ký tự. Glyph tồn tại để
    phân biệt loài; đụng nhau là mất sạch mục đích của nó.

    Cách làm: băm ra vị trí bắt đầu rồi dò tuyến tính sang ô trống kế tiếp,
    duyệt loài theo thứ tự đã sắp để kết quả không phụ thuộc thứ tự đầu vào.
    (M6: khi có SpeciesRegistry, lưu kết quả này lên SpeciesSpec lúc /join.)
    """
    out: dict[str, str] = {}
    used: set[int] = set()          # chỉ kiểm tra thành viên, không bao giờ lặp qua
    for sid in sorted(species_ids):
        start = int(hashlib.md5(sid.encode("utf-8")).hexdigest(), 16) % len(GLYPH_POOL)
        for step in range(len(GLYPH_POOL)):
            idx = (start + step) % len(GLYPH_POOL)
            if idx not in used:
                used.add(idx)
                out[sid] = GLYPH_POOL[idx]
                break
        else:
            out[sid] = GLYPH_POOL[start]   # nhiều loài hơn số glyph: đành chấp nhận
    return out


@lru_cache(maxsize=32)
def _glyphs_for(species_key: tuple[str, ...]) -> dict[str, str]:
    return assign_glyphs(species_key)


def hue_of(species_id: str) -> int:
    """Tính hue màu (0..359) cố định cho loài bằng md5."""
    digest = hashlib.md5(species_id.encode("utf-8")).hexdigest()
    return int(digest, 16) % 360


def style_of(c: Creature, energy_max: float | None = None) -> str:
    """Chuỗi style của rich: màu theo hue loài, độ sáng theo energy / energy_max."""
    if energy_max is None:
        energy_max = c.traits.energy_max
    hue = hue_of(c.species)
    h = (hue % 360) / 360.0
    if not c.alive:
        # B5: Con chết vẽ mờ
        r, g, b = colorsys.hsv_to_rgb(h, 0.3, 0.35)
        ri, gi, bi = int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
        return f"dim #{ri:02x}{gi:02x}{bi:02x}"

    ratio = max(0.0, min(1.0, c.energy / energy_max)) if energy_max > 0 else 0.0
    v = 0.30 + 0.70 * ratio
    r, g, b = colorsys.hsv_to_rgb(h, 0.85, v)
    ri, gi, bi = int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def render_frame(world: World, creatures: list[Creature], tick: int) -> RenderableType:
    """Vẽ một khung hình: lưới bản đồ bên trái, bảng sinh vật bên phải."""
    # B4: gom sinh vật còn sống theo vị trí
    by_pos: dict[tuple[int, int], list[Creature]] = {}
    for c in creatures:
        if c.alive:
            by_pos.setdefault(world.wrap(*c.pos), []).append(c)

    glyphs = _glyphs_for(tuple(sorted({c.species for c in creatures})))

    map_text = Text()
    for y in range(world.h):
        for x in range(world.w):
            pos = (x, y)
            if pos in by_pos:
                # Ưu tiên sinh vật còn sống, giải quyết trùng ô bằng creature_sort_key
                winner = min(by_pos[pos], key=creature_sort_key)
                map_text.append(glyphs[winner.species], style=style_of(winner))
            elif pos in world.corpses:
                map_text.append(CORPSE_GLYPH, style="bold #ff3333")
            elif pos in world.fruits:
                fruit_cls = world.fruits[pos]
                glyph = FRUIT_GLYPHS.get(fruit_cls, PLANT_GLYPH)
                map_text.append(glyph, style="bold #00ff66")
            else:
                t = world.grid[y][x]
                glyph = TERRAIN_GLYPHS.get(t, ".")
                style = TERRAIN_STYLES.get(t, "dim")
                map_text.append(glyph, style=style)
        if y < world.h - 1:
            map_text.append("\n")

    map_panel = Panel(map_text, title=f"Bản đồ (Tick {tick})", border_style="blue")

    table = Table(title=f"Quần thể (Tick {tick})", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="bold")
    table.add_column("HP", justify="right")
    table.add_column("Energy", justify="right")
    table.add_column("Age", justify="right")
    table.add_column("Trạng thái")

    # B6: duyệt theo creature_sort_key
    for c in sorted(creatures, key=creature_sort_key):
        glyph = glyphs[c.species]
        st = style_of(c)
        if c.alive:
            id_text = Text(f"{glyph} {c.id}", style=st)
            hp_text = f"{int(c.hp)}"
            energy_text = f"{c.energy:.1f}"
            age_text = str(c.age)
            status_text = "ALIVE"
            table.add_row(id_text, hp_text, energy_text, age_text, status_text)
        else:
            rem = max(0, c.dead_until - tick) if c.dead_until >= 0 else 0
            id_text = Text(f"{glyph} {c.id}", style="dim")
            hp_text = "0"
            energy_text = "0.0"
            age_text = str(c.age)
            status_text = f"DEAD ({rem}t)"
            table.add_row(id_text, hp_text, energy_text, age_text, status_text, style="dim")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()
    grid.add_column()
    grid.add_row(map_panel, table)
    return grid
