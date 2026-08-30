#!/usr/bin/env python3
"""X-11 — Đo chất lượng sổ tay: Tỉ lệ ghép nhân quả giả và tính khả dĩ trong fieldnotes.

    python scripts/x11_sotay.py --seeds 8 --ticks 200
    python scripts/x11_sotay.py --seeds 2 --ticks 100

## Bối cảnh và Mệnh đề cần đo

Trong Genesis Zero, `LlmStrategist.observe(tick_no, world, creatures, events, state)`
ghi chép các dòng sổ tay (`FieldNotes`) từ sự kiện xảy ra ở mỗi tick.

Khi sinh vật nhận hệ quả từ luật (`events["law"]`), `observe()` chọn tiền đề theo thứ tự:
1. Có trong `events["eat"]`    → "ăn <tên bề mặt>" (ứng với trigger EAT)
2. Có trong `events["drink"]`  → "uống nước" (ứng với trigger DRINK)
3. Có trong `events["attack"]` → "trúng đòn" (ứng với trigger HIT_BY)
4. Nếu không ăn/uống/bị đánh, chọn theo 5 mức ưu tiên cố định (không nhìn vào luật):
   1. Chuyển pha ngày/đêm      → "trời vừa chuyển sang ban ngày/đêm" (PHASE_ENTER)
   2. Cạn năng lượng (< 25%)   → "sức đã cạn" (LOW_ENERGY)
   3. Có kẻ đứng sát (dist<=1) → "có kẻ đứng sát bên" (ADJACENT)
   4. Di chuyển (`moved`)      → "bước vào <địa hình>" (STEP_ON)
   5. Đứng yên                 → "đứng yên" (REST)

Ghép cặp `(tiền đề, outcome)` và ghi vào sổ tay của chính cá thể đó ("TÔI ...")
cũng như các cá thể khác nhìn thấy ("THẤY <id> ...").

## Thước đo chính: Tính khả dĩ của tiền đề (Plausibility)

Thước đo quan trọng nhất của script này là:
    "Tỉ lệ dòng có hệ quả mà tiền đề CÓ THỂ là nguyên nhân thật"
    = số dòng có tiền đề ánh xạ về một trigger CÓ TRONG bộ luật của ván ấy,
      chia cho tổng số dòng có hệ quả.

LƯU Ý QUAN TRỌNG VỀ PHẠM VI Ý NGHĨA:
- Con số này đo TÍNH KHẢ DĨ (tiền đề CÓ THỂ là nguyên nhân thật vì trigger tương ứng
  có tồn tại trong thế giới của ván đó). Nó phản ánh chất lượng dữ liệu đầu vào mà
  tầng quan sát (FieldNotes) cung cấp cho mô hình suy luận.
- Con số này KHÔNG ĐO model có giải được luật hay sử dụng được dữ liệu hay không.
  Không nên hứa quá hay đồng nhất tính khả dĩ của sổ tay với năng lực quy nạp của LLM.
- Đo lường riêng cho "bước vào ..." vẫn được duy trì để theo dõi tiến trình lịch sử
  (so sánh mức độ nhiễu nhân quả địa hình trước và sau khi bổ sung các mức ưu tiên).

## Trần của thước đo: 68% KHÔNG thể lên 100%, và lý do là thật

Nhiều luật nổ trong CÙNG một tick, còn sổ tay chỉ gọi tên được MỘT tiền đề. Nên
khi một con vừa ăn vừa uống trong một lượt và luật `DRINK` nổ, dòng "ăn … → …"
bị tính là giả — đúng, nhưng không phải vì trình bày sai mà vì **nhân quả trong
thế giới này vốn chồng lấn**.

Đo thật trên seed 1 và 2: cả hai **không có luật `EAT` nào**, nên mọi dòng
"ăn → hệ quả" đều bị xếp giả. Đó là bộ đếm chạy đúng, không phải bộ đếm hỏng.

Nói cách khác: phần còn lại sau khi trừ đi lỗi trình bày **là sự lẫn lộn nhân
quả mà một nhà khoa học thật cũng phải gỡ** — và đó chính là bài mà dự án này
đặt ra cho model. Đừng đuổi con số này lên 100%; đuổi được nghĩa là ta đã phát
đáp án.
"""

from __future__ import annotations

import argparse
import collections
import sys
from typing import Any

from genesis import law_config
from genesis.creature import Creature
from genesis.lawdsl import Law
from genesis.lawgen import generate_cached
from genesis.prompt import _TERRAIN_VN
from genesis.strategist import LlmStrategist, ReflexStrategist
from genesis.tick import build_match, tick
from genesis.world import World, phase_at

ACTION_EXPECTED_TRIGGER: dict[str, str] = {
    "phase_enter": "PHASE_ENTER",
    "low_energy": "LOW_ENERGY",
    "adjacent": "ADJACENT",
    "step_on": "STEP_ON",
    "eat": "EAT",
    "drink": "DRINK",
    "hit_by": "HIT_BY",
    "rest": "REST",
}

ACTION_DISPLAY_NAME: dict[str, str] = {
    "phase_enter": "trời vừa chuyển ...",
    "low_energy": "sức đã cạn",
    "adjacent": "có kẻ đứng sát bên",
    "step_on": "bước vào ...",
    "eat": "ăn ...",
    "drink": "uống nước",
    "hit_by": "trúng đòn",
    "rest": "đứng yên",
}

ACTION_ORDER: list[str] = [
    "phase_enter",
    "low_energy",
    "adjacent",
    "step_on",
    "eat",
    "drink",
    "hit_by",
    "rest",
]


def classify_action(action: str) -> tuple[str, str]:
    """Phân loại chuỗi hành động thành (act_key, act_label)."""
    if action.startswith("trời vừa chuyển"):
        return "phase_enter", ACTION_DISPLAY_NAME["phase_enter"]
    if action == "sức đã cạn":
        return "low_energy", ACTION_DISPLAY_NAME["low_energy"]
    if action == "có kẻ đứng sát bên":
        return "adjacent", ACTION_DISPLAY_NAME["adjacent"]
    if action.startswith("bước vào"):
        return "step_on", ACTION_DISPLAY_NAME["step_on"]
    if action.startswith("ăn"):
        return "eat", ACTION_DISPLAY_NAME["eat"]
    if action == "uống nước":
        return "drink", ACTION_DISPLAY_NAME["drink"]
    if action == "trúng đòn":
        return "hit_by", ACTION_DISPLAY_NAME["hit_by"]
    if action == "đứng yên":
        return "rest", ACTION_DISPLAY_NAME["rest"]
    return "unknown", action


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

        # Phục dựng chính xác logic gán tiền đề hành động của LlmStrategist.observe
        acted: list[tuple[str, str, str, str]] = []
        for ev in events.get("eat", ()):
            cls = ev.get("fruit_class")
            what = sm.surface_of(cls) if sm and cls in sm.cls_to_surface else "thứ gì đó"
            act_str = f"ăn {what}"
            act_key, act_label = classify_action(act_str)
            acted.append((ev["creature_id"], act_str, act_key, act_label))

        for ev in events.get("drink", ()):
            act_str = "uống nước"
            act_key, act_label = classify_action(act_str)
            acted.append((ev["creature_id"], act_str, act_key, act_label))

        for ev in events.get("attack", ()):
            act_str = "trúng đòn"
            act_key, act_label = classify_action(act_str)
            acted.append((ev["creature_id"], act_str, act_key, act_label))

        did_something = {a for a, _, _, _ in acted}
        for ev in events.get("move", ()):
            cid = ev["creature_id"]
            if cid in did_something or (cid not in outcome_laws and cid not in self.strat.slots):
                continue
            c = by_id.get(cid)
            if c is None:
                continue

            # 5 mức ưu tiên cố định theo LlmStrategist.observe
            if tick_no % law_config.PHASE_LEN == 0:
                p = "ban ngày" if phase_at(tick_no) == "DAY" else "ban đêm"
                action_str = f"trời vừa chuyển sang {p}"
            elif c.energy < 0.25 * c.traits.energy_max:
                action_str = "sức đã cạn"
            elif any(
                o.alive and o.id != c.id and world.dist(c.pos, o.pos) <= 1
                for o in creatures
            ):
                action_str = "có kẻ đứng sát bên"
            elif ev.get("moved", False):
                wx, wy = world.wrap(*c.pos)
                terr = _TERRAIN_VN.get(world.grid[wy][wx], "đất trống")
                action_str = f"bước vào {terr}"
            else:
                action_str = "đứng yên"

            act_key, act_label = classify_action(action_str)
            acted.append((cid, action_str, act_key, act_label))

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

    # Tính toán thước đo chính: Tỉ lệ tiền đề CÓ THỂ là nguyên nhân thật
    # (Trigger ánh xạ từ tiền đề có mặt trong bộ luật của ván đó)
    triggers_by_seed = {
        seed: {law.trigger.kind.value for law in laws}
        for seed, laws in laws_by_seed.items()
    }
    plausible_count = sum(
        1 for n in all_notes
        if ACTION_EXPECTED_TRIGGER.get(n["act_key"]) in triggers_by_seed.get(n["seed"], set())
    )
    plausible_pct = (plausible_count / total_notes * 100) if total_notes > 0 else 0.0

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
    print(
        f"Tỉ lệ dòng có hệ quả mà tiền đề CÓ THỂ là nguyên nhân thật: "
        f"{plausible_pct:.2f}% ({plausible_count:,}/{total_notes:,} dòng)"
    )
    print("-" * 84)
    print(f"{'Hành động trong sổ':<20} | {'Trigger kỳ vọng':<15} | {'Số dòng':>8} | {'% Tổng':>7} | {'Đúng (%)':>9} | {'SAI / GIẢ (%)':>13}")
    print("-" * 20 + "-+-" + "-" * 15 + "-+-" + "-" * 8 + "-+-" + "-" * 7 + "-+-" + "-" * 9 + "-+-" + "-" * 13)

    for key in ACTION_ORDER:
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

    # 2. CÁC CON SỐ TỔNG KẾT QUAN TRỌNG
    step_notes = notes_by_act.get("step_on", [])
    step_count = len(step_notes)
    step_false = sum(1 for n in step_notes if "STEP_ON" not in n["triggers"])
    step_false_pct = (step_false / step_count * 100) if step_count > 0 else 0.0

    print()
    print("2. CÁC CON SỐ TỔNG KẾT QUAN TRỌNG:")
    print(
        f"   ▶ THƯỚC ĐO CHÍNH (TÍNH KHẢ DĨ CỦA TIỀN ĐỀ):\n"
        f"     - Tỉ lệ dòng có hệ quả mà tiền đề CÓ THỂ là nguyên nhân thật: "
        f"{plausible_pct:.2f}% ({plausible_count:,}/{total_notes:,} dòng)\n"
        f"     (= số dòng có tiền đề ánh xạ về trigger có trong bộ luật của ván, chia cho tổng số dòng có hệ quả)"
    )
    print(
        f"   ▶ ĐO LƯỜNG LỊCH SỬ (HÀNH ĐỘNG 'BƯỚC VÀO ...'):\n"
        f"     - Tổng số dòng ghi 'bước vào <địa hình>': {step_count:,} dòng\n"
        f"     - Số dòng ghép SAI (Trigger thật KHÁC STEP_ON): {step_false:,} dòng\n"
        f"     ==> TỶ LỆ GHÉP NHÂN QUẢ GIẢ CHO 'BƯỚC VÀO': {step_false_pct:.2f}% <=="
    )

    # 3. PHÂN BỐ TRIGGER THẬT CHO TỪNG LOẠI HÀNH ĐỘNG
    print()
    print("3. PHÂN BỐ TRIGGER THẬT ĐẰNG SAU TỪNG LOẠI HÀNH ĐỘNG GHI SỔ:")
    print("=" * 84)

    for key in ACTION_ORDER:
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
    print(f"{'Seed':<6} | {'Số luật':>7} | {'Tổng dòng':>10} | {'Khả dĩ (%)':>11} | {'Bước vào':>9} | {'Bước sai':>9} | {'% Bước sai':>11}")
    print("-" * 6 + "-+-" + "-" * 7 + "-+-" + "-" * 10 + "-+-" + "-" * 11 + "-+-" + "-" * 9 + "-+-" + "-" * 9 + "-+-" + "-" * 11)

    for seed in sorted(laws_by_seed.keys()):
        seed_notes = [n for n in all_notes if n["seed"] == seed]
        seed_step = [n for n in seed_notes if n["act_key"] == "step_on"]
        seed_step_false = sum(1 for n in seed_step if "STEP_ON" not in n["triggers"])
        pct_step_f = (seed_step_false / len(seed_step) * 100) if seed_step else 0.0

        seed_triggers = triggers_by_seed.get(seed, set())
        seed_plausible = sum(
            1 for n in seed_notes
            if ACTION_EXPECTED_TRIGGER.get(n["act_key"]) in seed_triggers
        )
        pct_plausible = (seed_plausible / len(seed_notes) * 100) if seed_notes else 0.0

        n_laws = len(laws_by_seed[seed])
        print(f"{seed:<6} | {n_laws:>7} | {len(seed_notes):>10} | {pct_plausible:>10.1f}% | {len(seed_step):>9} | {seed_step_false:>9} | {pct_step_f:>10.1f}%")

    print("-" * 84)

    # 5. ĐỌC VÀ ĐÁNH GIÁ KẾT QUẢ (PHẦN KẾT LUẬN)
    print()
    print("5. ĐỌC KẾT QUẢ VÀ BÀN LUẬN:")
    print("=" * 84)
    print(
        "1. THƯỚC ĐO CHÍNH — TÍNH KHẢ DĨ CỦA TIỀN ĐỀ:\n"
        f"   - Tỉ lệ dòng có hệ quả mà tiền đề CÓ THỂ là nguyên nhân thật đạt {plausible_pct:.2f}%\n"
        f"     ({plausible_count:,}/{total_notes:,} dòng có tiền đề ánh xạ về trigger tồn tại trong bộ luật).\n"
        "   - Ý nghĩa: Đây là thước đo tính khả dĩ (plausibility) ở tầng quan sát/sổ tay —\n"
        "     dữ liệu thực địa có cung cấp tiền đề liên quan đến các quy luật hiện hữu hay không.\n"
        "   - Giới hạn: Thước đo này KHÔNG ĐO việc LLM có suy luận hay giải được luật hay không.\n"
        "     Nó chỉ đảm bảo tầng sổ tay không 'bịt mắt' mô hình bằng các tiền đề hoàn toàn lạc đề.\n"
        "\n"
        "2. ĐỐI CHIẾU LỊCH SỬ — HÀNH ĐỘNG 'BƯỚC VÀO ...':\n"
        f"   - Tỉ lệ ghép nhân quả giả cho 'bước vào <địa hình>' là {step_false_pct:.2f}%.\n"
        "   - Trước khi có cơ chế phân tầng ưu tiên (chuyển pha -> cạn sức -> kẻ đứng sát -> bước vào),\n"
        "     mọi hành vi di chuyển đều bị dán nhãn 'bước vào', biến địa hình thành vật tế thần\n"
        "     cho mọi hệ quả không rõ nguyên nhân (nhiễu nhân quả địa hình).\n"
        "\n"
        "3. TÁC ĐỘNG TỚI TẦNG SUY LUẬN (FIELDNOTES / INDUCTION BOTTLENECK):\n"
        "   - Sổ tay thực địa là cầu nối giữa thế giới và trí tuệ mô hình. Nếu tiền đề được ghi\n"
        "     nhận đúng hoàn cảnh tự nhiên, LLM sẽ nhận được các mối tương quan hợp lý hơn để hình thành\n"
        "     giả thuyết (Hunch) và kiểm chứng thành Sổ Luật (Codex).\n"
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
