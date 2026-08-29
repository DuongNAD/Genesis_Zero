"""Genesis Zero — traits: vector 6 chỉ số và các giá trị dẫn xuất."""

from __future__ import annotations

from dataclasses import astuple, dataclass

from genesis import config


@dataclass(frozen=True)
class Traits:
    brain: int
    attack: int
    armor: int
    speed: int
    sense: int
    stomach: int

    def __post_init__(self) -> None:
        values = astuple(self)
        assert sum(values) == config.TRAIT_SUM, (
            f"Tổng trait phải bằng {config.TRAIT_SUM}, nhận {sum(values)}"
        )
        assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in values), (
            f"Trait phải nằm trong [{config.TRAIT_MIN}, {config.TRAIT_MAX}], nhận {values}"
        )

    @property
    def energy_max(self) -> float:
        return float(config.ENERGY_BASE + config.ENERGY_PER_STOMACH * self.stomach)

    @property
    def token_budget(self) -> int:
        return config.TOKEN_BASE + config.TOKEN_PER_BRAIN * self.brain

    @property
    def think_interval(self) -> int:
        return max(config.THINK_MIN, config.THINK_BASE - self.brain)

    @property
    def damage(self) -> float:
        return float(config.DAMAGE_BASE + config.DAMAGE_PER_ATTACK * self.attack)

    @property
    def dmg_taken_mult(self) -> float:
        return 1.0 - config.ARMOR_REDUCTION * self.armor

    @property
    def moves_per_tick(self) -> int:
        return 1 + self.speed // config.SPEED_DIVISOR

    @property
    def sight_radius(self) -> int:
        return config.SIGHT_BASE + self.sense

    @property
    def upkeep(self) -> float:
        return (
            config.UPKEEP_BASE
            + config.UPKEEP_BRAIN * self.brain
            + config.UPKEEP_ATTACK * self.attack
            + config.UPKEEP_ARMOR * self.armor
            + config.UPKEEP_SPEED * self.speed
            + config.UPKEEP_SENSE * self.sense
            + config.UPKEEP_STOMACH * self.stomach
        )

    def shift(self, frm: str, to: str) -> Traits:
        """Dịch 1 điểm từ trait frm sang trait to, trả về Traits mới.

        Bẫy: kiểm tra cả 2 đầu frm và to trước khi tạo vector mới để báo lỗi rõ ràng.
        """
        if frm not in config.TRAIT_NAMES:
            raise ValueError(f"Trait nguồn không hợp lệ: {frm!r}")
        if to not in config.TRAIT_NAMES:
            raise ValueError(f"Trait đích không hợp lệ: {to!r}")
        if getattr(self, frm) <= config.TRAIT_MIN:
            raise ValueError(
                f"Không thể giảm trait {frm}: đã ở mức tối thiểu {config.TRAIT_MIN}"
            )
        if getattr(self, to) >= config.TRAIT_MAX:
            raise ValueError(
                f"Không thể tăng trait {to}: đã ở mức tối đa {config.TRAIT_MAX}"
            )
        kwargs = {name: getattr(self, name) for name in config.TRAIT_NAMES}
        kwargs[frm] -= 1
        kwargs[to] += 1
        return Traits(**kwargs)


# Loài đăng ký lúc chạy (`/v1/join`). `config.FOUNDERS` chỉ có năm loài dựng sẵn.
_DYNAMIC_FOUNDERS: dict[str, Traits] = {}


def register_founder(species_id: str, traits: Traits) -> None:
    """Ghi vector khai sinh của một loài đăng ký lúc chạy.

    PHẢI gọi khi `/v1/join` cấp trait, nếu không `founder_traits` rơi về vector
    mặc định và `adapt.reset_body` **xoá sạch lựa chọn của người chơi lúc chết**
    — xem docstring dưới.
    """
    _DYNAMIC_FOUNDERS[species_id] = traits


def clear_dynamic_founders() -> None:
    """Xoá sổ loài động (dùng cho test và khi dựng ván mới)."""
    _DYNAMIC_FOUNDERS.clear()


def founder_traits(species_id: str) -> Traits:
    """Vector trait khởi đầu của loài.

    Ba tầng: `config.FOUNDERS` (năm loài dựng sẵn) -> sổ loài động
    (`register_founder`, do `/v1/join` ghi) -> vector chia đều làm cứu cánh.

    **Vì sao tầng giữa phải có.** `adapt.reset_body` gọi hàm này mỗi lần một con
    chết, và người chơi qua mạng chọn `brain_tier` lúc `/join`. Thiếu tầng giữa
    thì một người chọn brain 5 sẽ nhận `brain=5` lúc vào, rồi **chết một lần là
    tụt về brain 2** — vector mặc định. Hỏng im lặng: không lỗi, không log, và
    một ván 200 tick có tới 64 lượt chết.

    Hậu quả không nhỏ. Brain quyết định từ vựng Sổ Luật (`ADJACENT` và
    `PHASE_ENTER` chỉ có từ brain 4), số ô sổ, và ngân sách token. Nên một người
    chơi mang model 70B mất đúng thứ họ trả 5 điểm trait để mua, ngay sau cái
    chết đầu tiên — và cả mệnh đề trung tâm của dự án ("model to hơn thành loài
    đỉnh") không đo được nữa vì mọi loài hội tụ về cùng một vector.
    """
    if species_id in config.FOUNDERS:
        return Traits(*config.FOUNDERS[species_id])
    if species_id in _DYNAMIC_FOUNDERS:
        return _DYNAMIC_FOUNDERS[species_id]
    # Cứu cánh: loài lạ chưa đăng ký -> chia đều TRAIT_SUM cho các trait.
    default_val = config.TRAIT_SUM // len(config.TRAIT_NAMES)
    return Traits(*(default_val for _ in config.TRAIT_NAMES))
