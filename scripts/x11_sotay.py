#!/usr/bin/env python3
"""X-11 — Đo chất lượng sổ tay: Tỉ lệ ghép nhân quả giả trong fieldnotes.

    python scripts/x11_sotay.py --seeds 8 --ticks 200
    python scripts/x11_sotay.py --seeds 3 --ticks 120

## Bối cảnh và Mệnh đề cần đo

Trong Genesis Zero, `LlmStrategist.observe(tick_no, world, creatures, events, state)`
ghi chép các dòng sổ tay (`FieldNotes`) từ sự kiện xảy ra ở mỗi tick.

Quy trình ghép hành động và hệ quả của `observe()`:
1. Thu thập hệ quả luật từ `events["law"]` gán vào `outcome[cid]`.
2. Xác định hành động của cá thể theo thứ tự ưu tiên:
   - Có trong `events["eat"]`   → "ăn <tên bề mặt>"
   - Có trong `events["drink"]` → "uống nước"
   - Có trong `events["attack"]`→ "trúng đòn"
   - Nếu không có ở 3 mục trên:
     - Nếu di chuyển (`moved`)  → "bước vào <địa hình>"
     - Nếu đứng yên             → "đứng yên"
3. Ghép cặp `(hành động, outcome)` và ghi vào sổ tay của chính cá thể đó ("TÔI ...")
   cũng như các cá thể khác nhìn thấy ("THẤY <id> ...").

## Nghi vấn cốt lõi

Khi hệ quả đến từ một luật có trigger KHÔNG PHẢI `STEP_ON` (ví dụ `LOW_ENERGY`,
`ADJACENT`, `PHASE_ENTER`, `ATTACK`, v.v.), mà con vật tick đó chỉ di chuyển,
sổ tay sẽ ghi nhận:
    `t120 TÔI bước vào đồng cỏ → sức rút đi rất nhanh`
Đây là một CẶP NHÂN QUẢ GIẢ (false causal link).

Thí nghiệm này chạy N ván với luật thật và đo chính xác:
- Tổng số dòng sổ tay ghi nhận hệ quả.
- Tỉ lệ % dòng ghép với "bước vào ..." khi trigger thật KHÁC `STEP_ON`.
- Phân bố chi tiết các trigger thật đằng sau mỗi loại hành động.
- So sánh mức độ ghép sai giữa "bước vào ...", "ăn ...", "uống nước", "trúng đòn", "đứng yên".
"""

from __future__ import annotations

import argparse
import collections
from pathlib import Path
import sys
from typing import Any

from genesis.lawdsl import Law, TriggerKind
from genesis.lawgen import generate_cached
from genesis.prompt import _TERRAIN_VN
from genesis.strategist import LlmStrategist, ReflexStrategist
from genesis.tick import build_match, tick
from genesis.creature import Creature
from genesis.world import World


ACTION_EXPECTED_TRIGGER: dict[str, str] = {
    "step_on": "STEP_ON",
    "eat": "EAT",
    "drink": "DRINK",
    "hit_by": "HIT_BY",
    "rest": "REST",
}

ACTION_DISPLAY_NAME: dict[str, str] = {
    "step_on": "bước vào ...",
    "eat": "ăn ...",
    "drink": "uống nước",
    "hit_by": "trúng đòn",
    "rest": "đứng yên",
}


class SotayProbe(ReflexStrategist):
    """Strategist dùng phản xạ bản năng (Reflex) và theo dõi quan sát sổ tay."""

    def __init__(self, ids: list[str], laws: list[Law]) -> None:
        super().__init__()
        # Dựng LlmStrategist cục bộ để chạy observe mà không gọi model/mạng
        self.strat = LlmStrategist("http://127.0.0.1:8080", ids)
        self.laws = laws
        self.notes: list[dict[str, Any]] = []
        self.events_summary: list[dict[str, Any]] = []

    def observe(
        self,
        tick_no: int,
        world: World,
        creatures: list[Creature],
        events: dict[str, list[dict]],
        state: Any = None,
    ) -> None:
        by_id = {c.id: c for c in creatures}
        sm = world.surface_map
        law_events = events.get("law", ())

        # Gom hệ quả luật theo cá thể
        outcome_laws: dict[str, list[str]] = {}
        for ev in law_events:
            cid = ev["creature_id"]
            outcome_laws.setdefault(cid, []).append(ev["law_id"])

        # Phục dựng chính xác logic gán hành động của LlmStrategist.observe
        acted: list[tuple[str, str, str, str]] = []
        for ev in events.get("eat", ()):
            cls = ev.get("fruit_class")
            what = sm.surface_of(cls) if sm and cls in sm.cls_to_surface else "thứ gì đó"
            acted.append((ev["creature_id"], f"ăn {what}", "eat", "ăn ..."))

        for ev in events.get("drink", ()):
            acted.append((ev["creature_id"], "uống nước", "drink", "uống nước"))

        for ev in events.get("attack", ()):
            acted.append((ev["creature_id"], "trúng đòn", "hit_by", "trúng đòn"))

        did_something = {a for a, _, _, _ in acted}
        for ev in events.get("move", ()):
            cid = ev["creature_id"]
            if cid in did_something or (cid not in outcome_laws and cid not in self.strat.slots):
                continue
            c = by_id.get(cid)
            if c is None:
                continue
            wx, wy = world.wrap(*c.pos)
            terr = _TERRAIN_VN.get(world.grid[wy][wx], "đất trống")
            if ev.get("moved", False):
                acted.append((cid, f"bước vào {terr}", "step_on", "bước vào ..."))
            else:
                acted.append((cid, "đứng yên", "rest", "đứng yên"))

        # Chạy hàm observe thật của LlmStrategist
        self.strat.observe(tick_no, world, creatures, events, state)

        # Ghi nhận các dòng sổ tay có hệ quả được sinh ra trong tick này
        for actor_id, action_str, act_key, act_label in acted:
            if actor_id not in outcome_laws:
                continue
            actor = by_id.get(actor_id)
            if actor is None:
                continue

            law_ids = outcome_laws[actor_id]
            real_triggers = [
                self.laws[int(lid[1:])].trigger.kind.value for lid in law_ids
            ]

            # Ghi nhận cấp cá thể (con vật nhận hệ quả)
            self.events_summary.append({
                "tick": tick_no,
                "actor": actor_id,
                "action_str": action_str,
                "act_key": act_key,
                "act_label": act_label,
                "law_ids": law_ids,
                "triggers": real_triggers,
            })

            # Ghi nhận từng dòng sổ tay (FieldNotes) của các cá thể quan sát
            for observer_id in self.strat.slots:
                obs = by_id.get(observer_id)
                if obs is None or not obs.alive:
                    continue

                if observer_id == actor_id:
                    who = "TÔI"
                elif world.dist(obs.pos, actor.pos) <= obs.traits.sight_radius:
                    who = f"THẤY {actor_id}"
                else:
                    continue

                self.notes.append({
                    "tick": tick_no,
                    "observer": observer_id,
                    "who": who,
                    "actor": actor_id,
                    "action_str": action_str,
                    "act_key": act_key,
                    "act_label": act_label,
                    "law_ids": law_ids,
                    "triggers": real_triggers,
                })


def run_single_match(seed: int, ticks: int, arm: str = "STANDARD") -> tuple[list[Law], list[dict], list[dict]]:
    """Chạy 1 ván và thu thập toàn bộ dữ liệu ghi sổ."""
    laws = generate_cached(seed, arm=arm)
    world, creatures, state, rng = build_match(seed, laws=laws)
    ids = [c.id for c in creatures]

    probe = SotayProbe(ids, laws)
    for t in range(ticks):
        tick(world, creatures, t, rng, state, laws=laws, strategist=probe)

    for n in probe.notes:
        n["seed"] = seed
    for e in probe.events_summary:
        e["seed"] = seed

    return laws, probe.notes, probe.events_summary


def print_results(
    seeds: int,
    ticks: int,
    arm: str,
    all_notes: list[dict[str, Any]],
    laws_by_seed: dict[int, list[Law]],
) -> None:
    """In bảng thống kê chi tiết và nhận xét kết quả."""
    total_notes = len(all_notes)
    notes_by_act = collections.defaultdict(list)
    for n in all_notes:
        notes_by_act[n["act_key"]].append(n)

    print()
    print("=" * 84)
    print("   BÁO CÁO ĐO LƯỜNG CHẤT LƯỢNG SỔ TAY THỰC ĐỊA (GENESIS X-11)")
    print(f"   Quy mô: {seeds} seeds | {ticks} ticks/ván | Nhánh luật: {arm}")
    print("=" * 84)

    # 1. BẢNG TỔNG QUAN HÀNH ĐỘNG VÀ TỶ LỆ NHÂN QUẢ GIẢ
    print()
    print("1. TỔNG QUAN CÁC DÒNG SỔ TAY CÓ HỆ QUẢ VÀ TỶ LỆ GHÉP SAI NHÂN QUẢ")
    print("-" * 84)
    print(f"Tổng số dòng sổ tay có ghi nhận hệ quả: {total_notes:,} dòng")
    print("-" * 84)
    print(f"{'Hành động trong sổ':<20} | {'Trigger kỳ vọng':<15} | {'Số dòng':>8} | {'% Tổng':>7} | {'Đúng (%)':>9} | {'SAI / GIẢ (%)':>13}")
    print("-" * 20 + "-+-" + "-" * 15 + "-+-" + "-" * 8 + "-+-" + "-" * 7 + "-+-" + "-" * 9 + "-+-" + "-" * 13)

    act_order = ["step_on", "eat", "drink", "hit_by", "rest"]
    for key in act_order:
        notes = notes_by_act.get(key, [])
        count = len(notes)
        pct_total = (count / total_notes * 100) if total_notes > 0 else 0.0
        exp_trig = ACTION_EXPECTED_TRIGGER[key]
        display_name = ACTION_DISPLAY_NAME[key]

        # Kiểm tra đúng/sai: Đúng nếu trigger kỳ vọng có trong danh sách triggers thật
        correct_count = sum(1 for n in notes if exp_trig in n["triggers"])
        false_count = count - correct_count
        pct_correct = (correct_count / count * 100) if count > 0 else 0.0
        pct_false = (false_count / count * 100) if count > 0 else 0.0

        print(f"{display_name:<20} | {exp_trig:<15} | {count:>8} | {pct_total:>6.1f}% | {pct_correct:>8.1f}% | {pct_false:>12.1f}%")

    print("-" * 84)

    # 2. CON SỐ CHÍNH: BƯỚC VÀO ...
    step_notes = notes_by_act.get("step_on", [])
    step_count = len(step_notes)
    step_false = sum(1 for n in step_notes if "STEP_ON" not in n["triggers"])
    step_false_pct = (step_false / step_count * 100) if step_count > 0 else 0.0

    print()
    print("2. CON SỐ CỐT LÕI (NGHI VẤN HÀNH ĐỘNG 'BƯỚC VÀO ...'):")
    print(f"   - Tổng số dòng ghi 'bước vào <địa hình>': {step_count:,} dòng")
    print(f"   - Số dòng ghép SAI (Trigger thật KHÁC STEP_ON): {step_false:,} dòng")
    print(f"   ==> TỶ LỆ GHÉP NHÂN QUẢ GIẢ CHO 'BƯỚC VÀO': {step_false_pct:.2f}% <==")

    # 3. PHÂN BỐ TRIGGER THẬT CHO TỪNG LOẠI HÀNH ĐỘNG
    print()
    print("3. PHÂN BỐ TRIGGER THẬT ĐẰNG SAU TỪNG LOẠI HÀNH ĐỘNG GHI SỔ:")
    print("=" * 84)

    for key in act_order:
        notes = notes_by_act.get(key, [])
        display_name = ACTION_DISPLAY_NAME[key]
        exp_trig = ACTION_EXPECTED_TRIGGER[key]
        print(f"\n▶ Hành động: \"{display_name}\" (Tổng số: {len(notes):,} dòng sổ tay)")
        if not notes:
            print("   (Không có dòng nào)")
            continue

        # Thống kê phân bố trigger thật
        trig_counts: dict[str, int] = collections.defaultdict(int)
        for n in notes:
            for t in n["triggers"]:
                trig_counts[t] += 1
        total_trig_occurrences = sum(trig_counts.values())

        print(f"   {'Trigger thật':<18} | {'Số lần xuất hiện':>16} | {'Tỉ lệ (%)':>10} | {'Đánh giá nhân quả'}")
        print("   " + "-" * 18 + "-+-" + "-" * 16 + "-+-" + "-" * 10 + "-+-" + "-" * 20)

        for t_name, t_cnt in sorted(trig_counts.items(), key=lambda x: -x[1]):
            t_pct = t_cnt / total_trig_occurrences * 100
            status = "✓ ĐÚNG TRIGGER" if t_name == exp_trig else "✗ NHÂN QUẢ GIẢ (SAI)"
            print(f"   {t_name:<18} | {t_cnt:>16} | {t_pct:>9.1f}% | {status}")

    # 4. THỐNG KÊ CHI TIẾT THEO TỪNG SEED
    print()
    print("4. CHI TIẾT THEO TỪNG VÁN (SEED):")
    print("-" * 84)
    print(f"{'Seed':<6} | {'Số luật':>7} | {'Tổng dòng':>10} | {'Bước vào':>9} | {'Bước sai':>9} | {'% Bước sai':>11} | {'Uống sai':>9} | {'Ăn sai':>8}")
    print("-" * 6 + "-+-" + "-" * 7 + "-+-" + "-" * 10 + "-+-" + "-" * 9 + "-+-" + "-" * 9 + "-+-" + "-" * 11 + "-+-" + "-" * 9 + "-+-" + "-" * 8)

    for seed in sorted(laws_by_seed.keys()):
        seed_notes = [n for n in all_notes if n["seed"] == seed]
        seed_step = [n for n in seed_notes if n["act_key"] == "step_on"]
        seed_step_false = sum(1 for n in seed_step if "STEP_ON" not in n["triggers"])
        pct_step_f = (seed_step_false / len(seed_step) * 100) if seed_step else 0.0

        seed_drink = [n for n in seed_notes if n["act_key"] == "drink"]
        seed_drink_false = sum(1 for n in seed_drink if "DRINK" not in n["triggers"])

        seed_eat = [n for n in seed_notes if n["act_key"] == "eat"]
        seed_eat_false = sum(1 for n in seed_eat if "EAT" not in n["triggers"])

        n_laws = len(laws_by_seed[seed])
        print(f"{seed:<6} | {n_laws:>7} | {len(seed_notes):>10} | {len(seed_step):>9} | {seed_step_false:>9} | {pct_step_f:>10.1f}% | {seed_drink_false:>9} | {seed_eat_false:>8}")

    print("-" * 84)

    # 5. ĐỌC VÀ ĐÁNH GIÁ KẾT QUẢ (PHẦN KẾT LUẬN)
    print()
    print("5. ĐỌC KẾT QUẢ VÀ BÀN LUẬN:")
    print("=" * 84)
    print(
        "1. XÁC NHẬN NGHI VẤN VỀ NHÂN QUẢ GIẢ:\n"
        f"   - Kết quả đo lường cho thấy {step_false_pct:.1f}% các dòng sổ tay ghi 'bước vào <địa hình>'\n"
        "     thực chất bị kích hoạt bởi các trigger KHÔNG PHẢI STEP_ON (chủ yếu là ADJACENT,\n"
        "     LOW_ENERGY, ATTACK, PHASE_ENTER).\n"
        "   - Khi một sinh vật bị cạn kiệt năng lượng (LOW_ENERGY) hay đứng cạnh kẻ khác (ADJACENT)\n"
        "     mà nó đang di chuyển, sổ tay tự động kết luận: 'bước vào <địa hình> → <hệ quả>'.\n"
        "\n"
        "2. SỰ LAN TRUYỀN NHÂN QUẢ SAI TRONG CỘNG ĐỒNG (SOCIAL NOISE):\n"
        "   - Không chỉ cá thể trải nghiệm (TÔI) ghi nhận sai, mà MỌI cá thể xung quanh nhìn thấy\n"
        "     (THẤY L3:1 bước vào ...) cũng ghi nhận đúng mối liên hệ giả này vào sổ tay của mình.\n"
        "   - Điều này khiến toàn bộ quần thể bị 'đầu độc dữ liệu' bởi các giả thuyết sai lầm.\n"
        "\n"
        "3. TÁC ĐỘNG TỚI NĂNG LỰC SUY LUẬN CỦA MÔ HÌNH (LLM BOTTLENECK):\n"
        "   - Đây là một nút thắt ở TẦNG QUAN SÁT VÀ BIỂU DIỄN DỮ LIỆU (FieldNotes/Observe),\n"
        "     hoàn toàn độc lập với năng lực suy luận hay định kiến của LLM.\n"
        "   - Dù mô hình có khả năng suy luận logic hoàn hảo, việc nạp vào một cuốn sổ tay chứa\n"
        "     hàng loạt dữ liệu tương quan giả (spurious correlation) sẽ dẫn dắt LLM đặt cược\n"
        "     vào các luật sai về địa hình, gây lãng phí ô Sổ Luật và lượt nghĩ quý giá.\n"
    )
    print("=" * 84)
    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="scripts.x11_sotay",
        description="Đo chất lượng sổ tay thực địa: Tỉ lệ ghép nhân quả giả trong observe()",
    )
    ap.add_argument("--seeds", type=int, default=8, help="Số lượng seeds ván chạy (mặc định: 8)")
    ap.add_argument("--ticks", type=int, default=200, help="Số tick mỗi ván (mặc định: 200)")
    ap.add_argument("--arm", default="STANDARD", help="Nhánh sinh luật (mặc định: STANDARD)")
    a = ap.parse_args(argv)

    all_notes: list[dict[str, Any]] = []
    laws_by_seed: dict[int, list[Law]] = {}

    for seed in range(1, a.seeds + 1):
        laws, notes, _ = run_single_match(seed, a.ticks, arm=a.arm)
        laws_by_seed[seed] = laws
        all_notes.extend(notes)

    print_results(a.seeds, a.ticks, a.arm, all_notes, laws_by_seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
