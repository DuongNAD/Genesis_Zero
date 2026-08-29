#!/usr/bin/env python3
"""Genesis Zero — x07_pygame: Xem ván chạy bằng đồ hoạ Pygame (X-07).

CLI: python scripts/x07_pygame.py --seed 9 --ticks 400 [--fps 10] [--no-laws]

Đặc tả và ràng buộc (docs/02-SANDBOX-V4.md §5, web/watch.js):
- Cửa sổ pygame hiển thị lưới địa hình, quả, xác, sinh vật.
- Sinh vật vẽ bằng primitive suy từ vector trait HIỆN TẠI (không phải trait khai sinh).
- Màu sắc: hue = hash(species_id) % 360, lệch ±10 theo id cá thể, độ sáng theo energy/energy_max.
- Con chết vẽ mờ.
- Vẽ đồ thị "ai nghe được ai" (đường mảnh giữa các cặp trong tầm nghe, nhấp nháy khi SPEAK).
- Phím: SPACE tạm dừng, mũi tên phải bước một tick khi đang dừng, ESC thoát.
- CẤM KỴ: Kích thước sinh vật KHÔNG được phụ thuộc vào cỡ model.
- Không hiện luật ẩn trên màn hình trước khi hết ván. Sự kiện LAW_FIRED chỉ vẽ tia sáng ẩn danh.
  Hết ván in luật thật ra stdout (REVEAL).
"""

from __future__ import annotations

import argparse
import colorsys
import hashlib
from pathlib import Path
import random
import sys
from typing import Any

from genesis import config, law_config
from genesis.lawdsl import to_vietnamese
from genesis.lawgen import generate_cached
from genesis.tick import build_match, tick
from genesis.world import Terrain, World, phase_at


def hash_str(s: str) -> int:
    """Băm chuỗi tương đương web/watch.js."""
    h = 0
    for ch in s:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF
    return abs(h)


def hash_species_hue(species_id: str) -> int:
    """Tính hue gốc (0..359) cho loài."""
    digest = hashlib.md5(species_id.encode("utf-8")).hexdigest()
    return int(digest, 16) % 360


def hash_creature_shift(creature_id: str) -> int:
    """Độ lệch hue cho từng cá thể."""
    return hash_str(creature_id)


def hsl_to_rgb(h_deg: float, s_pct: float, l_pct: float) -> tuple[int, int, int]:
    """Chuyển đổi HSL sang RGB 0..255."""
    h = (h_deg % 360) / 360.0
    s = max(0.0, min(100.0, s_pct)) / 100.0
    l = max(0.0, min(100.0, l_pct)) / 100.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    # Kênh thứ ba là `b`, không phải `g` lần nữa. Lỗi gõ ở đây không làm gãy gì
    # cả: nó chỉ khiến mọi loài có hue ở nửa xanh lam hiện ra thành một đám xám
    # như nhau, và bất biến "hue = hash(species_id)" — thứ để phân biệt loài
    # bằng mắt — hỏng trong im lặng. Không bài test tĩnh nào bắt được.
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def get_creature_visuals(creature, cell_px: float) -> dict[str, Any]:
    """Tính toán hình học và màu sắc từ vector trait HIỆN TẠI của cá thể."""
    traits = creature.traits
    t_brain = traits.brain
    t_attack = traits.attack
    t_armor = traits.armor
    t_speed = traits.speed
    t_sense = traits.sense
    t_stomach = traits.stomach

    s = cell_px / 24.0

    body_w = (8.0 + t_stomach * 2.0) * s
    body_h = (10.0 + t_speed * 2.0) * s
    leg_count = 2 + min(4, t_speed)
    head_r = (3.0 + t_brain * 1.2) * s
    eye_r = (1.0 + t_sense * 0.6) * s
    eye_spread = (2.0 + t_sense * 1.0) * s
    armor_width = max(1, int(round((1.0 + t_armor * 0.7) * s)))
    fang_len = (2.0 + t_attack * 1.5) * s

    base_hue = hash_species_hue(creature.species)
    shift_hue = (hash_creature_shift(creature.id) % 21) - 10
    hue = (base_hue + shift_hue + 360) % 360

    e_max = traits.energy_max
    e_ratio = max(0.1, min(1.0, (creature.energy / e_max) if e_max > 0 else 0.1))
    lightness = 25 + int(round(50.0 * e_ratio))

    fill_rgb = hsl_to_rgb(hue, 70, lightness)
    stroke_rgb = hsl_to_rgb(hue, 90, 20)

    return {
        "body_w": body_w,
        "body_h": body_h,
        "leg_count": leg_count,
        "head_r": head_r,
        "eye_r": eye_r,
        "eye_spread": eye_spread,
        "armor_width": armor_width,
        "fang_len": fang_len,
        "fill_rgb": fill_rgb,
        "stroke_rgb": stroke_rgb,
        "traits": traits,
    }


class GuiLogCollector:
    """Bộ thu thập sự kiện nhẹ phục vụ hiệu ứng đồ hoạ."""

    def __init__(self) -> None:
        self.speak_events: list[dict[str, Any]] = []
        self.law_events: list[dict[str, Any]] = []
        self.last_tick: int = 0

    def write(self, t: int, kind: str, **fields: Any) -> None:
        self.last_tick = t
        if kind == "SPEAK":
            hearers = fields.get("hear_signal") or fields.get("hear_full") or []
            self.speak_events.append({
                "t": t,
                "speaker_id": fields.get("creature_id"),
                "hearer_ids": list(hearers),
            })
        elif kind == "LAW_FIRED":
            self.law_events.append({
                "t": t,
                "creature_id": fields.get("creature_id"),
                "pos": fields.get("pos"),
            })


def draw_creature(surface: Any, creature: Any, cell_px: float, cx: float, cy: float) -> None:
    """Vẽ một sinh vật lên surface của pygame."""
    import pygame

    v = get_creature_visuals(creature, cell_px)
    alive = creature.alive

    if not alive:
        box_dim = int(cell_px * 2)
        temp_surf = pygame.Surface((box_dim, box_dim), pygame.SRCALPHA)
        draw_cx = box_dim // 2
        draw_cy = box_dim // 2
        draw_target = temp_surf
    else:
        draw_cx = int(cx)
        draw_cy = int(cy)
        draw_target = surface

    fill_rgb = v["fill_rgb"]
    stroke_rgb = v["stroke_rgb"]
    body_w = v["body_w"]
    body_h = v["body_h"]
    leg_count = v["leg_count"]
    head_r = v["head_r"]
    eye_r = v["eye_r"]
    eye_spread = v["eye_spread"]
    armor_width = v["armor_width"]
    fang_len = v["fang_len"]
    traits = v["traits"]

    # 1. Vẽ chân (speed)
    for k in range(leg_count):
        leg_y = draw_cy - body_h / 2.0 + (k + 0.5) * (body_h / leg_count)
        pygame.draw.line(
            draw_target,
            stroke_rgb,
            (int(draw_cx - body_w / 2.0 - 3), int(leg_y)),
            (int(draw_cx + body_w / 2.0 + 3), int(leg_y)),
            max(1, int(1.5 * (cell_px / 24.0))),
        )

    # 2. Vẽ thân (stomach, speed)
    body_rect = pygame.Rect(
        int(draw_cx - body_w / 2.0),
        int(draw_cy - body_h / 2.0),
        max(2, int(body_w)),
        max(2, int(body_h)),
    )
    pygame.draw.ellipse(draw_target, fill_rgb, body_rect)
    pygame.draw.ellipse(draw_target, stroke_rgb, body_rect, width=armor_width)

    # 3. Vẽ giáp dọc sống lưng (armor)
    if traits.armor > 0:
        for a in range(traits.armor):
            plate_y = draw_cy - body_h / 3.0 + a * (body_h / (traits.armor + 1))
            pygame.draw.circle(
                draw_target,
                stroke_rgb,
                (int(draw_cx), int(plate_y)),
                max(1, int(2 * (cell_px / 24.0))),
            )

    # 4. Vẽ đầu (brain)
    head_y = draw_cy - body_h / 2.0 - head_r / 2.0
    head_center = (int(draw_cx), int(head_y))
    pygame.draw.circle(draw_target, fill_rgb, head_center, max(1, int(head_r)))
    pygame.draw.circle(draw_target, stroke_rgb, head_center, max(1, int(head_r)), width=1)

    # 5. Vẽ mắt (sense)
    left_eye = (int(draw_cx - eye_spread), int(head_y - 1))
    right_eye = (int(draw_cx + eye_spread), int(head_y - 1))
    eye_radius = max(1, int(eye_r))
    pupil_radius = max(1, int(eye_r * 0.5))

    pygame.draw.circle(draw_target, (255, 255, 255), left_eye, eye_radius)
    pygame.draw.circle(draw_target, (255, 255, 255), right_eye, eye_radius)
    pygame.draw.circle(draw_target, (0, 0, 0), left_eye, pupil_radius)
    pygame.draw.circle(draw_target, (0, 0, 0), right_eye, pupil_radius)

    # 6. Vẽ nanh/vuốt (attack)
    if traits.attack > 0:
        fang_color = (248, 250, 252)
        fang_w = max(1, int(1.5 * (cell_px / 24.0)))
        pygame.draw.line(
            draw_target,
            fang_color,
            (int(draw_cx - 2), int(head_y - head_r)),
            (int(draw_cx - 3), int(head_y - head_r - fang_len)),
            fang_w,
        )
        pygame.draw.line(
            draw_target,
            fang_color,
            (int(draw_cx + 2), int(head_y - head_r)),
            (int(draw_cx + 3), int(head_y - head_r - fang_len)),
            fang_w,
        )

    # Nếu con chết, vẽ mờ (translucent)
    if not alive:
        temp_surf.set_alpha(70)
        surface.blit(temp_surf, (int(cx - draw_cx), int(cy - draw_cy)))


def draw_grid_and_terrain(surface: Any, world: World, cell_px: int, header_h: int) -> None:
    """Vẽ nền địa hình lưới và viền ô."""
    import pygame

    terrain_colors = {
        Terrain.PLAIN: ((38, 61, 30), (34, 56, 27)),
        Terrain.WATER: (30, 144, 255),
        Terrain.BUSH: (46, 139, 87),
        Terrain.ROCK: (80, 80, 80),
        Terrain.FIRE: (255, 69, 0),
    }

    for y in range(world.h):
        for x in range(world.w):
            t = world.grid[y][x]
            rect = pygame.Rect(x * cell_px, y * cell_px + header_h, cell_px, cell_px)
            if t == Terrain.PLAIN:
                color = terrain_colors[Terrain.PLAIN][(x + y) % 2]
            else:
                color = terrain_colors.get(t, (34, 56, 27))

            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (27, 44, 21), rect, width=1)


def draw_fruits_and_corpses(surface: Any, world: World, cell_px: int, header_h: int) -> None:
    """Vẽ quả và xác trên bản đồ."""
    import pygame

    # 1. Quả
    for (px, py) in sorted(world.fruits.keys()):
        cx = int(px * cell_px + cell_px / 2.0)
        cy = int(py * cell_px + cell_px / 2.0 + header_h)
        r = max(2, int(cell_px * 0.22))
        pygame.draw.circle(surface, (34, 197, 94), (cx, cy), r)
        pygame.draw.circle(surface, (21, 128, 61), (cx, cy), r, width=1)

    # 2. Xác
    for (cx_pos, cy_pos) in sorted(world.corpses.keys()):
        cx = int(cx_pos * cell_px + cell_px / 2.0)
        cy = int(cy_pos * cell_px + cell_px / 2.0 + header_h)
        arm = max(2, int(cell_px * 0.25))
        pygame.draw.line(surface, (153, 27, 27), (cx - arm, cy - arm), (cx + arm, cy + arm), 2)
        pygame.draw.line(surface, (153, 27, 27), (cx + arm, cy - arm), (cx - arm, cy + arm), 2)


def draw_hearing_network(
    surface: Any,
    world: World,
    creatures: list[Any],
    speak_flashes: list[dict[str, Any]],
    cell_px: int,
    header_h: int,
) -> None:
    """Vẽ đồ thị ai nghe được ai, nhấp nháy khi có SPEAK."""
    import pygame

    alive_creatures = [c for c in creatures if c.alive]
    now_ms = pygame.time.get_ticks()

    for i in range(len(alive_creatures)):
        for j in range(i + 1, len(alive_creatures)):
            cA = alive_creatures[i]
            cB = alive_creatures[j]
            dist = world.dist(cA.pos, cB.pos)
            sightA = cA.traits.sight_radius
            sightB = cB.traits.sight_radius
            if dist > sightA and dist > sightB:
                continue

            x1 = int(cA.pos[0] * cell_px + cell_px / 2.0)
            y1 = int(cA.pos[1] * cell_px + cell_px / 2.0 + header_h)
            x2 = int(cB.pos[0] * cell_px + cell_px / 2.0)
            y2 = int(cB.pos[1] * cell_px + cell_px / 2.0 + header_h)

            is_flash = False
            for f in speak_flashes:
                if now_ms - f["start_time"] <= 300:
                    if (f["speaker_id"] == cA.id and cB.id in f["hearer_ids"]) or (
                        f["speaker_id"] == cB.id and cA.id in f["hearer_ids"]
                    ):
                        is_flash = True
                        break

            if is_flash:
                pygame.draw.line(surface, (56, 189, 248), (x1, y1), (x2, y2), 3)
            else:
                pygame.draw.line(surface, (60, 75, 70), (x1, y1), (x2, y2), 1)


def draw_law_flashes(
    surface: Any,
    law_flashes: list[dict[str, Any]],
    cell_px: int,
    header_h: int,
) -> None:
    """Vẽ tia sáng ẩn danh khi sự kiện LAW_FIRED diễn ra (không kèm chữ/luật)."""
    import pygame

    now_ms = pygame.time.get_ticks()
    for flash in list(law_flashes):
        dt = now_ms - flash["start_time"]
        if dt > 350:
            if flash in law_flashes:
                law_flashes.remove(flash)
            continue
        progress = dt / 350.0
        pos = flash.get("pos") or (0, 0)
        cx = int(pos[0] * cell_px + cell_px / 2.0)
        cy = int(pos[1] * cell_px + cell_px / 2.0 + header_h)
        r = int(cell_px * (0.3 + 0.5 * progress))
        alpha = max(0, int(255 * (1.0 - progress)))

        spark_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(spark_surf, (253, 224, 71, alpha), (r + 2, r + 2), r, width=2)
        surface.blit(spark_surf, (cx - r - 2, cy - r - 2))


def run_gui(seed: int, total_ticks: int, fps: int = 10, no_laws: bool = False) -> None:
    """Chạy vòng lặp giao diện đồ hoạ pygame."""
    import pygame

    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont("sans-serif", 14)

    laws = None if no_laws else generate_cached(seed, arm="STANDARD")
    world, creatures, state, rng = build_match(seed, laws=laws)

    cell_px = 30
    grid_w_px = world.w * cell_px
    grid_h_px = world.h * cell_px
    header_h = 44
    win_w = grid_w_px
    win_h = grid_h_px + header_h

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption(f"Genesis Zero · Seed {seed}")
    clock = pygame.time.Clock()

    collector = GuiLogCollector()
    speak_flashes: list[dict[str, Any]] = []
    law_flashes: list[dict[str, Any]] = []

    current_tick = 0
    paused = False
    running = True

    while running and current_tick < total_ticks:
        step_one = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    if paused:
                        step_one = True

        # Tiến triển thế giới một tick
        if not paused or step_one:
            collector.speak_events.clear()
            collector.law_events.clear()

            tick(
                world,
                creatures,
                current_tick,
                rng,
                state,
                log=collector,
                laws=laws,
            )

            now_ms = pygame.time.get_ticks()
            for sp_ev in collector.speak_events:
                speak_flashes.append({
                    "speaker_id": sp_ev["speaker_id"],
                    "hearer_ids": sp_ev["hearer_ids"],
                    "start_time": now_ms,
                })
            for lw_ev in collector.law_events:
                law_flashes.append({
                    "pos": lw_ev["pos"],
                    "start_time": now_ms,
                })

            current_tick += 1

        # Dọn dẹp flash cũ
        now_ms = pygame.time.get_ticks()
        speak_flashes = [f for f in speak_flashes if now_ms - f["start_time"] <= 300]

        # ── Vẽ khung hình ──
        screen.fill((15, 23, 42))

        # 1. Thanh trạng thái
        phase = phase_at(current_tick)
        alive_count = sum(1 for c in creatures if c.alive)
        status_str = (
            f"Tick: {current_tick}/{total_ticks} | Pha: {phase} | "
            f"Sống: {alive_count}/{len(creatures)} | Quả: {len(world.fruits)} | Xác: {len(world.corpses)}"
        )
        if paused:
            status_str += " | [TẠM DỪNG: SPACE tiếp tục, -> bước 1 tick]"

        text_surf = font.render(status_str, True, (226, 232, 240))
        screen.blit(text_surf, (12, 12))

        # 2. Địa hình & lưới
        draw_grid_and_terrain(screen, world, cell_px, header_h)

        # 3. Quả & xác
        draw_fruits_and_corpses(screen, world, cell_px, header_h)

        # 4. Đồ thị ai nghe được ai
        draw_hearing_network(screen, world, creatures, speak_flashes, cell_px, header_h)

        # 5. Hiệu ứng tia sáng ẩn danh khi luật kích hoạt
        draw_law_flashes(screen, law_flashes, cell_px, header_h)

        # 6. Sinh vật (suy từ trait hiện tại)
        for c in creatures:
            cx = c.pos[0] * cell_px + cell_px / 2.0
            cy = c.pos[1] * cell_px + cell_px / 2.0 + header_h
            draw_creature(screen, c, cell_px, cx, cy)

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()

    # Hết ván / Thoát -> REVEAL công bố luật thật ra stdout
    if laws:
        print("\n" + "=" * 64)
        print("REVEAL · BỘ LUẬT ẨN CỦA VÁN ĐẤU:")
        print("=" * 64)
        for i, law in enumerate(laws):
            viet = to_vietnamese(law, world.surface_map)
            print(f"  Luật {i + 1} ({law.tier()}): {viet}")
        print("=" * 64 + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="scripts.x07_pygame",
        description="Genesis Zero — Xem ván chạy bằng đồ hoạ Pygame",
    )
    ap.add_argument("--seed", type=int, default=9, help="Match seed (mặc định: 9)")
    ap.add_argument("--ticks", type=int, default=400, help="Số tick tối đa (mặc định: 400)")
    ap.add_argument("--fps", type=int, default=10, help="Tốc độ khung hình/giây (mặc định: 10)")
    ap.add_argument("--no-laws", action="store_true", help="Tắt luật ẩn (chế độ WORLD_FLAT)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        import pygame
    except ImportError:
        print(
            "Pygame chưa được cài đặt. Vui lòng cài đặt bằng: pip install pygame",
            file=sys.stderr,
        )
        return 2

    args = parse_args(argv)
    run_gui(args.seed, args.ticks, fps=args.fps, no_laws=args.no_laws)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
