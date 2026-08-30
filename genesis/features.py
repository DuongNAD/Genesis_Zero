"""Genesis Zero — features: ba đặc điểm bốc thăm cho mỗi loài (W-19).

## Vì sao có file này

Đến W-18 thì một loài là **một vector sáu số** cộng một tầng. Hai loài cùng vector
là hai loài giống hệt nhau, và cái tên `L1`..`L5` không mang thêm nghĩa gì. Nhưng
sinh vật thật khác nhau ở những thứ **không cộng lại thành một điểm số**: con thì
đào hang, con thì lưỡng cư, con thì lông dài, con thì có nọc.

`Feature` là những thứ ấy. Mỗi loài bốc **ba** cái lúc sinh ra.

## Đặc điểm là CẦU NỐI giữa cơ chế và ngoại hình

Đây là điều đáng nói nhất về thiết kế này, và là lý do nó không phải trang trí.

Một `Feature` mang **hai** mặt, và chúng buộc phải khớp nhau:

* `effect` — nó đổi gì trong vòng tick (đi được ô nào, chịu đòn ra sao, thấy xa
  bao nhiêu vào ban đêm).
* `look` — nó **trông** như thế nào, viết đủ cụ thể để dựng hình 3D.

Nên hình dáng con vật **không phải minh hoạ cho luật chơi, nó LÀ luật chơi**. Ai
nhìn thấy một con vật lông dài, chân màng, mõm dài thì đọc được là nó chịu lạnh,
bơi được, và đào bới — trước khi nó kịp làm gì. Đó đúng là thứ [03 §4](../docs/03-LUAT-AN-V5.md)
gọi là quan sát gián tiếp, và nó là một kênh thông tin thật cho agent.

## Cái này KHÔNG vào từ vựng luật ẩn (chưa)

Cùng kỷ luật với W-18 bất biến 5: đặc điểm vào **thế giới** trước, vào **DSL**
sau, và có phép đo ở giữa. Miền `SUBJECT` mà thêm mười hai đặc điểm là law space
rộng gấp mấy lần, mà quy nạp thì đang hỏng sẵn.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from genesis.domain import Domain
from genesis.world import Terrain


@dataclass(frozen=True)
class Feature:
    """Một đặc điểm sinh học. Hai mặt: đổi cơ chế, và trông ra sao."""

    key: str
    vn: str
    look: str                       # cho Meshy — phải cụ thể tới mức dựng được
    note: str                       # đổi gì trong vòng tick, một câu
    # ── mặt cơ chế ───────────────────────────────────────────────────────
    extra_terrain: frozenset[Terrain] = frozenset()   # ô đi thêm được
    domains: frozenset[Domain] = frozenset()          # tầng CỘNG THÊM (lưỡng cư)
    upkeep_mult: float = 1.0
    damage_mult: float = 1.0
    dmg_taken_mult: float = 1.0
    thorns: float = 0.0             # đòn phản lại kẻ tấn công
    # Loài mang đặc điểm này thì ngưỡng trèo cây hạ xuống bấy nhiêu điểm speed.
    climb_bonus: int = 0
    # Xoá được khoản phạt tầm nhìn ban đêm. KHAI ĐÚNG MỘT LẦN — bản trước khai
    # hai lần trong cùng dataclass, và Python im lặng lấy dòng sau. Hôm nay vô
    # hại vì hai dòng giống hệt; ngày ai đó sửa một dòng thì dòng kia âm thầm
    # thắng, và cái thắng là dòng người sửa KHÔNG nhìn vào.
    night_sight: bool = False
    # Bán kính CẢM được kẻ nấp trong bụi / trên cây. 0 = không có râu.
    feel_radius: int = 0


# Mười hai đặc điểm, trải đều ba tầng và bốn nhóm (đi lại · phòng thủ · giác
# quan · kiếm ăn). Bốc 3 trong 12 cho **220 tổ hợp** — đủ để không ván nào giống
# ván nào, mà vẫn ít tới mức đọc bảng này là hiểu hết thế giới.
FEATURES: tuple[Feature, ...] = (
    # ── đi lại ───────────────────────────────────────────────────────────
    Feature(
        "LUONG_CU", "lưỡng cư",
        "chân có màng bơi giữa các ngón, da trơn ẩm bóng, đuôi dẹt bè sang hai bên",
        "sống được cả dưới nước lẫn trên cạn",
        domains=frozenset({Domain.NUOC}),
    ),
    Feature(
        "DAO_HANG", "biết đào hang",
        "chi trước ngắn chắc với móng vuốt bè to để bới đất, mõm dài nhọn, "
        "tai cụp về sau, thân thuôn hình ống",
        "vào được HANG — chỗ trốn mà kẻ săn không lách vào nổi",
        # Cả ROCK lẫn CAVE: hang nằm lọt giữa đá, nên vào được hang nghĩa là
        # xuyên qua được lớp đá bao quanh. Đây là chỗ trốn TUYỆT ĐỐI — kẻ săn
        # thấy con mồi biến mất vào vách và không có đường nào theo vào.
        extra_terrain=frozenset({Terrain.ROCK, Terrain.CAVE}),
    ),
    Feature(
        "TREO_GIOI", "trèo giỏi",
        "bốn chi dài mảnh, bàn tay năm ngón đối nhau nắm được cành, "
        "đuôi dài cuốn được",
        "hạ ngưỡng trèo cây xuống hai điểm speed",
        climb_bonus=2,
    ),
    Feature(
        "CANH_LUOT", "màng lượn",
        "màng da căng nối chi trước với chi sau, xoè ra thành cánh lượn khi nhảy",
        "lượn qua được vách đá",
        extra_terrain=frozenset({Terrain.ROCK}),
    ),
    # ── phòng thủ ────────────────────────────────────────────────────────
    Feature(
        "LONG_DAI", "lông dài",
        "bộ lông dài rậm phủ kín thân, bờm dày quanh cổ và vai, lông đuôi xù",
        "đỡ hao sức, nhưng nặng nề",
        upkeep_mult=0.85,
    ),
    Feature(
        "VAY_CUNG", "vảy cứng",
        "vảy sừng xếp lớp chồng lên nhau như ngói, gờ nổi dọc sống lưng",
        "chịu đòn tốt hơn",
        dmg_taken_mult=0.8,
    ),
    Feature(
        "GAI_DOC", "gai độc",
        "gai nhọn dựng dọc sống lưng và hai bên sườn, đầu gai sẫm màu",
        "kẻ đánh nó cũng chịu đòn",
        thorns=2.0,
    ),
    Feature(
        "VO_SO", "vỏ sò",
        "mai cứng khum trùm lưng, mép mai có khía, chân co được vào trong",
        "rất khó bị thương, nhưng chậm chạp",
        dmg_taken_mult=0.6, upkeep_mult=1.15,
    ),
    # ── giác quan ────────────────────────────────────────────────────────
    Feature(
        "MAT_DEM", "mắt đêm",
        "hai mắt to tròn chiếm phần lớn khuôn mặt, đồng tử rộng, không có mí trên",
        "ban đêm nhìn không kém ban ngày — xoá hẳn khoản phạt tầm nhìn của đêm",
        night_sight=True,
    ),
    Feature(
        "RAU_CAM_UNG", "râu cảm ứng",
        "chùm râu dài cứng toả ra hai bên mõm, chóp râu cong nhẹ",
        "thấy được kẻ nấp trong bụi và trên cây ở khoảng cách 2 thay vì 1",
        feel_radius=2,
    ),
    # ── kiếm ăn ──────────────────────────────────────────────────────────
    Feature(
        "RANG_NANH", "răng nanh",
        "hai nanh trên dài chìa ra ngoài môi, hàm bạnh, cơ má nổi rõ",
        "đòn nặng hơn",
        damage_mult=1.25,
    ),
    Feature(
        "TUI_MA", "túi má",
        "hai bên má phồng thành túi chứa, cổ ngắn mập",
        "ăn dự trữ được, đỡ hao sức",
        upkeep_mult=0.9,
    ),
)

BY_KEY: dict[str, Feature] = {f.key: f for f in FEATURES}

N_FEATURES = 3


def roll(rng: random.Random, n: int = N_FEATURES) -> tuple[Feature, ...]:
    """Bốc `n` đặc điểm KHÔNG trùng nhau.

    Trả về theo thứ tự CỐ ĐỊNH (theo `key`), không theo thứ tự bốc: hai ván cùng
    seed phải cho hai con vật giống hệt nhau, kể cả trong chuỗi mô tả gửi sang
    Meshy — nếu không thì cùng một sinh vật lại sinh ra hai hình khác nhau và
    đệm mesh mất tác dụng.
    """
    got = rng.sample(FEATURES, min(n, len(FEATURES)))
    return tuple(sorted(got, key=lambda f: f.key))


def roll_for_species(species_id: str, seed: int, n: int = N_FEATURES) -> tuple[Feature, ...]:
    """Đặc điểm của một loài — tất định theo `(species_id, seed)`.

    Tất định là bắt buộc: bộ đệm mesh khoá theo mô tả, `--replay` dựng lại ván cũ,
    và bộ chấm so hai ván với nhau. Bốc ngẫu nhiên mỗi lần chạy thì cả ba đường
    ấy gãy cùng lúc.
    """
    return roll(random.Random(f"{species_id}@{seed}".encode().hex()), n)


# ── mặt cơ chế: gộp ba đặc điểm thành các hệ số ─────────────────────────────

@dataclass
class Kit:
    """Ba đặc điểm đã gộp lại thành thứ vòng tick đọc được."""

    features: tuple[Feature, ...] = ()
    extra_terrain: frozenset[Terrain] = frozenset()
    extra_domains: frozenset[Domain] = frozenset()
    upkeep_mult: float = 1.0
    damage_mult: float = 1.0
    dmg_taken_mult: float = 1.0
    thorns: float = 0.0
    climb_bonus: int = 0
    night_sight: bool = False
    feel_radius: int = 0
    keys: tuple[str, ...] = field(default_factory=tuple)

    def has(self, key: str) -> bool:
        return key in self.keys


def kit_of(features: tuple[Feature, ...]) -> Kit:
    """Gộp. Hệ số NHÂN vào nhau, không cộng — hai đặc điểm cùng giảm sát thương
    thì nhân lại vẫn > 0, còn cộng trừ thì đủ hai cái là bất tử."""
    k = Kit(features=features, keys=tuple(f.key for f in features))
    for f in features:
        k.extra_terrain |= f.extra_terrain
        k.extra_domains |= f.domains
        k.upkeep_mult *= f.upkeep_mult
        k.damage_mult *= f.damage_mult
        k.dmg_taken_mult *= f.dmg_taken_mult
        k.thorns += f.thorns
        k.climb_bonus += f.climb_bonus
        k.night_sight = k.night_sight or f.night_sight
        k.feel_radius = max(k.feel_radius, f.feel_radius)
    return k


def describe(features: tuple[Feature, ...]) -> str:
    """Câu mô tả NGOẠI HÌNH, ghép từ ba đặc điểm. Đầu vào cho Meshy."""
    return " ".join(f.look.rstrip(".") + "." for f in features)
