"""Genesis Zero — combat: giải quyết chiến đấu đồng thời và độc."""

from __future__ import annotations

from dataclasses import dataclass

from genesis import config
from genesis.creature import Creature, creature_sort_key
from genesis.world import World

# M6 sẽ chuyển lên SpeciesSpec, không rải "L5" ra chỗ khác.
POISON_SPECIES: tuple[str, ...] = ("L5",)

# Tầm đánh giáp lá cà: phải sát bên SAU khi cả hai đã di chuyển xong.
MELEE_RANGE: int = 1


@dataclass(frozen=True)
class Attack:
    attacker_id: str
    defender_id: str


@dataclass(frozen=True)
class CombatResult:
    target_id: str
    dmg: float
    poison_from: str | None = None
    # AI đã ra đòn. Một TUPLE, không phải một id: giữ đúng tính đồng thời của
    # W-11 — hai con cùng đánh một con trong một tick thì cả hai đều có mặt.
    #
    # Thiếu trường này thì log `ATTACK` ghi nạn nhân hai lần (`creature_id` và
    # `target_id` bằng nhau) và **không thể trả lời "ai giết ai"** — mà đó đúng
    # là câu hỏi cả thiết kế ba tầng của W-18 (kẻ săn · con mồi · chỗ trốn) dựng
    # lên để hỏi. Tìm ra khi muốn biết cái gì săn cá và phát hiện log không nói
    # được.
    attackers: tuple[str, ...] = ()


def resolve_combat(
    attacks: list[Attack],
    creatures: dict[str, Creature],
    world: World,
) -> list[CombatResult]:
    """Giải quyết TOÀN BỘ đòn của một tick, ĐỒNG THỜI.

    Bất biến B1: Hai con cùng đánh nhau trong một tick thì CẢ HAI nhận sát thương,
    tính từ chỉ số TRƯỚC tick. Hàm thuần, không sửa creatures.
    Bất biến B2: Độc phản lại mọi kẻ tấn công loài có độc trong tick đó.
    Bất biến B5: Trả danh sách đã sắp theo creature_sort_key của target.
    Bất biến B6: Gộp nhiều đòn vào cùng một mục tiêu thành MỘT CombatResult.
    """
    dmg_by_target: dict[str, float] = {}
    poison_by_target: dict[str, str] = {}
    attackers_by_target: dict[str, set[str]] = {}

    for att in attacks:
        attacker = creatures.get(att.attacker_id)
        defender = creatures.get(att.defender_id)
        if attacker is None or defender is None:
            continue
        if not attacker.alive or not defender.alive:
            continue
        # Bẫy: Intent tính từ vị trí TRƯỚC khi di chuyển, nhưng đòn đánh giải quyết
        # SAU khi mọi con đã đi. Không kiểm lại tầm ở đây thì đánh trúng cả kẻ vừa
        # chạy xa 9 ô, và FLEE thành vô dụng — bị nhắm là ăn đòn dù chạy đi đâu.
        if world.dist(attacker.pos, defender.pos) > MELEE_RANGE:
            continue

        # Sát thương = damage của attacker * dmg_taken_mult của defender,
        # rồi nhân tiếp hai hệ số đặc điểm (W-19): răng nanh của kẻ đánh, vảy
        # cứng / vỏ sò của kẻ đỡ.
        ka = getattr(attacker, "kit", None) or world.kits.get(attacker.species)
        kd = getattr(defender, "kit", None) or world.kits.get(defender.species)
        attackers_by_target.setdefault(defender.id, set()).add(attacker.id)
        dmg = (attacker.traits.damage * defender.traits.dmg_taken_mult
               * (getattr(ka, "damage_mult", 1.0) if ka else 1.0)
               * (getattr(kd, "dmg_taken_mult", 1.0) if kd else 1.0))
        dmg_by_target[defender.id] = dmg_by_target.get(defender.id, 0.0) + dmg

        # GAI ĐỘC: kẻ tấn công cũng chịu đòn. Không phụ thuộc nó đánh trúng bao
        # nhiêu — gai là thứ nằm sẵn trên mình kẻ bị đánh, ai chạm vào thì chịu.
        thorns = getattr(kd, "thorns", 0.0) if kd else 0.0
        if thorns > 0.0:
            dmg_by_target[attacker.id] = dmg_by_target.get(attacker.id, 0.0) + thorns
            # Gai là của kẻ BỊ đánh, nên nó là "kẻ ra đòn" của cú phản này.
            attackers_by_target.setdefault(attacker.id, set()).add(defender.id)

        # Độc phản lại mọi kẻ tấn công L5 trong tick đó
        if defender.species in POISON_SPECIES:
            if attacker.id not in poison_by_target:
                poison_by_target[attacker.id] = defender.id
            else:
                prev_src = poison_by_target[attacker.id]
                prev_c = creatures.get(prev_src)
                if prev_c is not None and creature_sort_key(defender) < creature_sort_key(prev_c):
                    poison_by_target[attacker.id] = defender.id

    all_targets = set(dmg_by_target.keys()) | set(poison_by_target.keys())
    results: list[CombatResult] = []
    for target_id in all_targets:
        dmg = dmg_by_target.get(target_id, 0.0)
        poison_from = poison_by_target.get(target_id)
        results.append(CombatResult(
            target_id=target_id, dmg=dmg, poison_from=poison_from,
            # Sắp xếp để log tái lập được: cùng seed phải cho cùng một file.
            attackers=tuple(sorted(attackers_by_target.get(target_id, ()))),
        ))

    # Sắp xếp kết quả tất định theo creature_sort_key của target
    results.sort(key=lambda r: creature_sort_key(creatures[r.target_id]))
    return results


def apply_combat(
    results: list[CombatResult],
    creatures: dict[str, Creature],
) -> None:
    """Áp dụng sát thương và gán trạng thái độc."""
    for res in results:
        target = creatures.get(res.target_id)
        if target is None or not target.alive:
            continue
        target.hp -= res.dmg
        if res.poison_from is not None:
            target.poison_ticks = config.POISON_DURATION
            target.poison_from = res.poison_from


def tick_poison(c: Creature) -> float:
    """Trừ sát thương độc của tick này, giảm bộ đếm. Trả sát thương đã trừ."""
    if not c.alive:
        return 0.0
    if c.poison_ticks > 0:
        c.hp -= config.POISON_DAMAGE
        c.poison_ticks -= 1
        if c.poison_ticks == 0:
            c.poison_from = None
        return float(config.POISON_DAMAGE)
    return 0.0


def tick_regen(c: Creature) -> float:
    """Hồi máu khi no. Trả lượng máu đã hồi."""
    if not c.alive or c.hp <= 0:
        return 0.0
    if c.hp >= config.HP_MAX:
        return 0.0
    if c.energy > config.HP_REGEN_ENERGY_RATIO * c.traits.energy_max:
        healed = min(float(config.HP_REGEN), float(config.HP_MAX - c.hp))
        c.hp += healed
        return healed
    return 0.0
