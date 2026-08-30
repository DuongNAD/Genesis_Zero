"""Genesis Zero — domain: ba tầng nước · cạn · trời (W-18).

## Vì sao file này tồn tại

`World.passable(pos, creature=None)` mang tham số `creature` **từ ngày đầu và
chưa bao giờ dùng tới nó**: mọi sinh vật đi được đúng những ô như nhau. Nên năm
bản đồ khác nhau về mật độ chứ không khác nhau về **ổ sinh thái** — không có chỗ
nào mà loài này tới được còn loài kia thì không. Không có chỗ trốn thì không có
kẻ săn và con mồi, chỉ có mười lăm con vật cùng đi trên một mặt phẳng.

## Cái này KHÔNG phải trang trí

Genesis Zero đo đúng một thứ: agent có quy nạp ra được luật ẩn không. Ba tầng
**chia lại ai quan sát được cái gì**, và đó là phiên bản sâu nhất của Gate D
(*luật này có phát biểu được không*): một con cá không bao giờ quan sát được luật
về lửa — không phải vì nó ngu, mà vì nó chưa từng đứng gần lửa.

## Tầng là thuộc tính của LOÀI, trait là đường đi TRONG tầng

Tầng **không** nằm trong vector trait, và đó là quyết định khó nhất của W-18.
Vector trait là chiều thích nghi, dịch được lúc chạy (W-12, B-13) — nhét tầng vào
đó thì nó **hội tụ**, đúng lỗi W-12 đã dính một lần (luật dịch trait cũ kéo cả
năm loài về `(2,2,2,2,2,2)` sau ba lần dịch, xoá sạch bản sắc loài). Và Q1
(*brain có đáng giá không*) cần các nhóm ổn định suốt ván để so.

Nhưng **trong** một tầng thì trait vẫn mở khoá đường đi, và đó đúng là ca đề bài
đặt ra — *sư tử không trèo được cây, khỉ thì được*:

    CẠN + speed >= CLIMB_SPEED   ->  trèo được CÂY
    CẠN + armor >= FIRE_ARMOR    ->  băng được LỬA

Không hard-code loài nào cả: nó đọc thẳng từ vector trait. Sư tử là `attack` cao
`speed` thấp; khỉ là `speed` cao `attack` thấp. Nên một dòng dõi **học được cách
trèo** bằng cách dịch trait sang `speed`. Bản sắc tầng cố định; đường đi trong
tầng thì kiếm được — nửa hay của tiến hoá, không dính nửa dở.
"""

from __future__ import annotations

from enum import StrEnum

from genesis import config
from genesis.world import Terrain


class Domain(StrEnum):
    """Tầng sống. Cố định theo loài, không dịch được (W-18 bất biến 4)."""

    NUOC = "NUOC"
    CAN = "CAN"
    TROI = "TROI"


DOMAIN_VN: dict[Domain, str] = {
    Domain.NUOC: "dưới nước",
    Domain.CAN: "trên cạn",
    Domain.TROI: "trên trời",
}

# Ô mà mỗi tầng đi được KHÔNG cần điều kiện trait nào.
_BASE: dict[Domain, frozenset[Terrain]] = {
    Domain.NUOC: frozenset({Terrain.WATER, Terrain.DEEP}),
    Domain.CAN: frozenset({Terrain.PLAIN, Terrain.BUSH, Terrain.WATER}),
    # Trời bay qua TẤT CẢ — và đó mới là một nửa. Nửa kia ở `can_touch`: trời
    # phải HẠ XUỐNG mới chạm được. Không có nửa ấy thì tầng trời trội tuyệt đối
    # và hai tầng kia thành trang trí.
    Domain.TROI: frozenset(Terrain),
}

# Ô mà tầng CẠN chỉ vào được khi trait đủ ngưỡng. Đây là "sư tử / khỉ".
_GATED: dict[Terrain, tuple[str, int]] = {
    Terrain.TREE: ("speed", config.CLIMB_SPEED),
    Terrain.FIRE: ("armor", config.FIRE_ARMOR),
}


def can_enter(domain: Domain, terrain: Terrain, traits=None, kit=None) -> bool:
    """Tầng `domain` + vector `traits` + ba đặc điểm `kit` có vào được ô này không.

    Hàm THUẦN, và là nguồn sự thật DUY NHẤT cho câu hỏi ấy (bất biến 2). Mọi
    đường khác — `reflex`, render, client, bộ sinh bản đồ — phải hỏi qua
    `World.passable`, chứ không dựng bảng thứ hai.

    Ba nấc, và thứ tự có nghĩa:

    1. **tầng** — cá không lên bờ, dù nó có đặc điểm gì đi nữa;
    2. **đặc điểm** — `DAO_HANG` mở khoá đá và hang, `CANH_LUOT` mở khoá đá;
    3. **trait** — `speed` để trèo, `armor` để băng lửa, và `TREO_GIOI` hạ
       ngưỡng trèo xuống, nên một con `speed` vừa phải mà có đặc điểm ấy vẫn
       lên cây được.

    Nấc 2 đứng TRƯỚC nấc 3 là cố ý: một đặc điểm là thứ con vật *sinh ra đã có*,
    còn trait thì nó **kiếm được** bằng dịch trait (B-13). Hai đường khác nhau
    tới cùng một chỗ, và cả hai đều mở.
    """
    if terrain in _BASE[domain]:
        return True
    if kit is not None:
        if terrain in getattr(kit, "extra_terrain", ()):
            return True
        # TẦNG cộng thêm — đây là `LUONG_CU`. Thiếu nhánh này thì "lưỡng cư" là
        # một đặc điểm thuần TRANG TRÍ: nó tả chân màng và da trơn trong prompt
        # 3D mà không đổi một ô nào trong vòng tick, tức là **hình nói dối**.
        # Đó đúng là điều W-19 dựng lên để chặn (`look` và `effect` phải khớp),
        # và tôi vẫn quên nó cho tới lúc in hai mặt cạnh nhau mới thấy.
        for d in getattr(kit, "extra_domains", ()):
            if terrain in _BASE[d]:
                return True
    if domain is not Domain.CAN:
        return False
    gate = _GATED.get(terrain)
    if gate is None or traits is None:
        return False
    name, need = gate
    if terrain is Terrain.TREE and kit is not None:
        need -= getattr(kit, "climb_bonus", 0)
    return getattr(traits, name, 0) >= need


def can_touch(domain: Domain, terrain: Terrain, traits=None) -> bool:
    """Có ĂN / UỐNG / ĐÁNH được ở ô này không — khác hẳn `can_enter`.

    Bất biến 3 của W-18: **trời phải hạ xuống mới chạm được.** Chim bay qua đá và
    qua biển thoải mái, nhưng muốn ăn thì phải đứng ở ô mà một sinh vật CẠN hoặc
    NƯỚC đứng được. Nên làm chim là *đi lại tự do đổi lấy tiếp xúc kém*, không
    phải "mạnh hơn ở mọi mặt".
    """
    if domain is not Domain.TROI:
        return can_enter(domain, terrain, traits)
    return terrain in _TROI_TOUCH


# Ô mà tầng TRỜI ĐẬU XUỐNG được. Nêu tường minh chứ không suy từ hai tầng kia —
# và chỗ khác biệt là chỗ đáng giá nhất:
#
#   · `TREE` có mặt: chim đậu cành. Đó là chỗ tầng TRỜI gặp tầng CẠN biết trèo.
#   · `DEEP` KHÔNG có mặt: chim bay qua biển được nhưng không kiếm ăn ở đó.
#     Nên cá ngoài khơi an toàn trước chim, còn cá vào **nước nông** thì không —
#     và nước nông vốn đã là chỗ duy nhất tầng CẠN với tầng NƯỚC gặp nhau.
#     Cả ba tầng dồn về một vành đai hẹp. Đó là bờ nước, và nó là cảnh hay nhất
#     của cả trò chơi.
#   · `ROCK`, `FIRE` không có mặt: không đậu được.
_TROI_TOUCH: frozenset[Terrain] = frozenset({
    Terrain.PLAIN, Terrain.BUSH, Terrain.WATER, Terrain.TREE,
})


def domain_of(species_id: str) -> Domain:
    """Tầng của một loài. Loài lạ (người chơi qua mạng) mặc định là CẠN."""
    return Domain(config.SPECIES_DOMAIN.get(species_id, Domain.CAN.value))
