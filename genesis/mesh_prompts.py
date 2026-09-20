"""Genesis Zero — mesh_prompts: mô tả 3D cho sinh vật, địa hình, vật thể, bản đồ.

Mọi thứ trong file này là **một hàm thuần** của dữ liệu đã có trong sim: vector
trait, `Terrain`, `MapSpec`, bề mặt quả. Không có tên người chơi, không có
persona, không có gì do client viết.

## Vì sao mô tả nằm ở đây chứ không nằm rải rác

Bất biến 1 của [N-13] là **"hình = trait, chỉ trait"**: hình thù phải là hàm của
vector trait, để hình và số không bao giờ rời nhau. Thẻ N-13 nói thẳng "đừng
viết bộ mô tả thứ hai" — và đúng: hai bộ mô tả độc lập thì sẽ có ngày một con
`attack=5` trông tay ngắn.

File này KHÔNG phải bộ mô tả thứ hai. Nó là **cùng một bộ**, mở rộng: phần số
vẫn lấy nguyên từ `prompt.body_line`, phần hình sinh từ CHÍNH sáu con số ấy qua
bảng tra. `net.mesh.body_prompt` gọi vào đây, nên tới Meshy vẫn chỉ có một đường.

## Vì sao quả được khoá theo BỀ MẶT chứ không theo lớp

Bề mặt bị hoán vị mỗi ván ([L-04]): `FRUIT_A` ván này là "quả đỏ tròn", ván sau
là "quả tím dẹt". Sinh mesh theo lớp thì hình quả sẽ đổi màu giữa hai ván và
người xem đọc được luật ẩn qua… hình 3D. Khoá theo bề mặt thì bốn mesh dùng
được cho mọi ván, và không mesh nào biết lớp của mình.
"""

from __future__ import annotations

from genesis import law_config
from genesis.maps import MAPS, MapSpec
from genesis.prompt import body_line
from genesis.traits import Traits
from genesis.world import Terrain

# Một câu đuôi dùng chung cho MỌI mesh. Không có nó thì mỗi vật một phong cách
# và cảnh 3D trông như ghép từ bốn trò chơi khác nhau.
STYLE = (
    "phong cách low-poly cách điệu, khối hình rõ, màu phẳng hơi ngả pastel, "
    "không chữ, không logo, nền trắng trơn, một vật thể duy nhất ở giữa khung"
)

NEGATIVE = (
    "chữ viết, chữ số, logo, hình mờ, nhiều vật thể, người thật, ảnh chụp, "
    "cảnh nền phức tạp, vũ khí hiện đại"
)

# ─── Sinh vật: sáu trait → sáu mệnh đề hình ─────────────────────────────────
# Mỗi bảng có đúng 6 mục cho giá trị 0..5. Trait nằm trong [0, 5] (config.TRAIT_MIN
# / TRAIT_MAX), và tổng luôn 12 — nên không bao giờ có con nào cả sáu đều to.

_BRAIN = (
    "đầu nhỏ dẹt, gần như không có sọ",
    "đầu nhỏ, trán thấp",
    "đầu vừa, trán hơi nhô",
    "sọ tròn cao, trán rộng",
    "sọ lớn phồng rõ, đường vân chạy dọc",
    "sọ rất lớn trong suốt mờ, thấy ánh sáng bên trong",
)
_ATTACK = (
    "chi trước ngắn tròn, không móng",
    "chi trước mảnh, móng bé",
    "chi trước vừa, ba móng ngắn",
    "chi trước cơ bắp, móng cong",
    "chi trước to khoẻ, móng dài sắc",
    "chi trước đồ sộ như càng, móng lớn cong ngược",
)
_ARMOR = (
    "da trần mềm, không mảnh che",
    "vài mảng sừng mỏng ở vai",
    "vảy nhỏ phủ lưng",
    "tấm giáp dày ở lưng và vai",
    "giáp phiến chồng nhau khắp thân",
    "mai dày liền khối, gờ nổi chạy dọc sống lưng",
)
_SPEED = (
    "chân cụt mập, thân sát đất",
    "chân ngắn chắc",
    "chân vừa, dáng đứng cân",
    "chân dài gân guốc",
    "chân rất dài, khớp gập ngược như chân chim",
    "chân mảnh cực dài, thân thon nhẹ, dáng chực lao đi",
)
_SENSE = (
    "hai chấm mắt nhỏ xíu",
    "hai mắt nhỏ, không râu",
    "hai mắt vừa, một cặp râu ngắn",
    "mắt lớn, hai cặp râu",
    "bốn mắt xếp vòng cung, râu dài",
    "sáu mắt quanh đầu, chùm râu cảm giác toả ra mọi phía",
)
_STOMACH = (
    "thân dẹt lép, bụng thóp",
    "bụng nhỏ gọn",
    "bụng vừa phải",
    "bụng tròn đầy",
    "bụng phình lớn trễ xuống",
    "bụng khổng lồ căng, gần chạm đất",
)

_TABLES = (
    ("brain", _BRAIN), ("attack", _ATTACK), ("armor", _ARMOR),
    ("speed", _SPEED), ("sense", _SENSE), ("stomach", _STOMACH),
)


def creature_visual(tr: Traits) -> str:
    """Sáu mệnh đề hình, sinh từ CHÍNH sáu con số của `body_line`."""
    parts = []
    for name, table in _TABLES:
        v = getattr(tr, name)
        parts.append(table[max(0, min(len(table) - 1, int(v)))])
    return ", ".join(parts)


# Dáng cơ bản theo TẦNG. Số chi và tư thế là thứ Meshy cần biết trước tiên, và
# nó không suy ra được từ vector trait — một con `speed 5` có thể là con báo bốn
# chân hay con chim hai chân, hai hình rất khác nhau.
_DANG = {
    "NUOC": ("Sinh vật SỐNG DƯỚI NƯỚC, thân thuôn hình thoi, không có chân, "
             "hai vây ngực và một vây đuôi dựng đứng, mang xẻ hai bên đầu"),
    "CAN": ("Sinh vật BỐN CHÂN sống trên cạn, thân đối xứng, đứng trên bốn chi, "
            "đầu hướng về trước, có đuôi"),
    "TROI": ("Sinh vật BIẾT BAY, hai cánh lớn xoè rộng hai bên, hai chân sau "
             "có vuốt quắp, thân ngắn gọn, đuôi xoè hình quạt"),
}


def creature_prompt(tr: Traits, domain: str = "CAN", features=()) -> str:
    """Prompt Meshy cho một cá thể: TẦNG + đặc điểm + vector trait.

    Ba lớp, và thứ tự là thứ tự Meshy cần đọc:

    1. **dáng cơ bản theo tầng** — bốn chân / có vây / có cánh. Đây là thứ vector
       trait không nói được: `speed 5` có thể là con báo hoặc con chim.
    2. **ba đặc điểm bốc thăm** (W-19) — lông dài, chân màng, gai lưng… Đây là
       chỗ hai con cùng vector trait trông khác hẳn nhau.
    3. **vector trait** — vẫn là `body_line` nguyên văn, giữ đúng "một chỗ duy
       nhất" của [N-13]: đổi thang trait thì cả câu chữ lẫn hình đổi cùng lúc.

    Lớp 2 là lớp làm cho hình 3D **mang thông tin** chứ không chỉ trang trí: ai
    nhìn thấy chân màng và mõm dài thì đọc được là con này bơi được và đào bới,
    trước khi nó kịp làm gì. Đó là quan sát gián tiếp theo đúng nghĩa của
    [03 §4](../docs/03-LUAT-AN-V5.md).
    """
    from genesis.features import describe

    parts = [_DANG.get(domain, _DANG["CAN"]) + f": {creature_visual(tr)}."]
    if features:
        parts.append(describe(tuple(features)))
    parts.append(f"Chỉ số: {body_line(tr)}")
    parts.append(f"{STYLE}.")
    return " ".join(parts)


# ─── Địa hình: năm loại ô ───────────────────────────────────────────────────

_TERRAIN: dict[Terrain, str] = {
    Terrain.PLAIN: "một mảng đất bằng phủ cỏ ngắn, vài hòn sỏi nhỏ, mặt trên phẳng",
    Terrain.WATER: "một vũng nước nông trong, đáy cát sáng, mặt nước gợn nhẹ",
    Terrain.BUSH: "một bụi cây rậm thấp, lá dày che kín bên trong, cành đan nhau",
    Terrain.ROCK: "một khối đá xám nứt nẻ, cạnh vỡ sắc, chân phủ rêu mỏng",
    Terrain.FIRE: "một mảng đất cháy đen, than đỏ âm ỉ, khói mỏng bốc lên",
    Terrain.DEEP: "mặt nước sâu xanh thẫm, không thấy đáy, sóng lăn tăn chậm",
    Terrain.TREE: "một thân cây to có tán lá rộng che kín ô, cành thấp vươn ngang",
    Terrain.CAVE: "miệng hang tối trong lòng đá, vòm đá nhẵn, nền phủ cát khô",
}


def terrain_prompt(t: Terrain) -> str:
    """Ô địa hình, dựng theo lát ghép vuông để xếp cạnh nhau không hở."""
    return (
        f"Ô địa hình vuông dùng để lát bản đồ: {_TERRAIN[t]}. "
        f"Cạnh ô thẳng để ghép liền với ô bên cạnh. {STYLE}."
    )


# ─── Vật thể: bốn quả + xác ─────────────────────────────────────────────────

_COLOR = {"đỏ": "đỏ tươi", "xanh": "xanh lá đậm", "vàng": "vàng nghệ", "tím": "tím sẫm"}
_SHAPE = {
    "tròn": "hình cầu nhẵn",
    "dài": "thuôn dài như quả bầu nhỏ",
    "gai": "phủ gai ngắn tù khắp mặt",
    "dẹt": "dẹt như cái đĩa úp, mép mỏng",
}


def fruit_prompt(color: str, shape: str) -> str:
    """Quả, mô tả theo BỀ MẶT (màu + dáng) — thứ ai cũng nhìn thấy.

    Không có tham số nào mang lớp `FRUIT_x`: hoán vị bề mặt mỗi ván sẽ gán lớp
    nào cho mesh này là chuyện của sim, mesh không được biết.
    """
    return (
        f"Một quả dại {_COLOR[color]}, {_SHAPE[shape]}, cuống ngắn màu nâu. "
        f"{STYLE}."
    )


def corpse_prompt() -> str:
    return (
        "Bộ xương nhỏ của một sinh vật bốn chân nằm nghiêng trên đất, "
        f"xương màu ngà, không máu, không nội tạng. {STYLE}."
    )


# ─── Bản đồ: năm thế giới ───────────────────────────────────────────────────

_MAP_SCENE = {
    "DONG_CO": "đồng cỏ rộng thoáng, cỏ xanh tới đầu gối, vài vũng nước và tảng đá rải rác",
    "HOANG_MAC": "hoang mạc đá sỏi khô, nền đất nứt, đá tảng chất đống, hầu như không có nước",
    "QUAN_DAO": "quần đảo nhỏ giữa mặt nước nông, từng mảng đất tách rời nối bằng bãi cạn",
    "HEM_NUI": "hẻm núi đá cao dựng hai bên, chừa một hành lang hẹp chạy giữa",
    "RUNG_RAM": "rừng rậm bụi cây dày đặc, tán thấp che kín tầm nhìn, ánh sáng lọt thành đốm",
}


def map_prompt(spec: MapSpec) -> str:
    """Cảnh nền của một bản đồ. Tỉ lệ địa hình lấy thẳng từ `MapSpec.seeds`,
    nên đổi cân bằng bản đồ thì mô tả 3D đổi theo — không lệch được."""
    mix = ", ".join(
        f"{t.name.lower()} {n} cụm" for t, n in sorted(spec.seeds.items(), key=lambda kv: -kv[1])
    )
    return (
        f"Cảnh nền thế giới nhìn từ trên cao chếch: {_MAP_SCENE[spec.name]}. "
        f"Mật độ địa hình: {mix}. {STYLE}."
    )


# ─── Xuất toàn bộ ───────────────────────────────────────────────────────────

_SLUG = {"đỏ": "do", "xanh": "xanh", "vàng": "vang", "tím": "tim",
         "tròn": "tron", "dài": "dai", "gai": "gai", "dẹt": "det"}


def all_static_prompts() -> list[dict[str, str]]:
    """Mọi mesh KHÔNG phụ thuộc người chơi — sinh một lần, dùng mãi.

    Sinh vật không có ở đây: chúng phụ thuộc vector trait, mà trait chỉ biết lúc
    `/join`. `net.mesh` lo phần đó theo quota.
    """
    out: list[dict[str, str]] = [
        {"id": f"terrain_{t.name.lower()}", "nhom": "dia_hinh", "prompt": terrain_prompt(t)}
        for t in Terrain
    ]

    for color, shape in law_config.FRUIT_SURFACES:
        # id không dấu: nó thành tên file và một phần URL.
        out.append({"id": f"fruit_{_SLUG[color]}_{_SLUG[shape]}", "nhom": "vat_the",
                    "prompt": fruit_prompt(color, shape)})
    out.append({"id": "corpse", "nhom": "vat_the", "prompt": corpse_prompt()})
    for name, spec in MAPS.items():
        out.append({"id": f"map_{name.lower()}", "nhom": "ban_do",
                    "prompt": map_prompt(spec)})
    return out


def meshy_payload(prompt: str, *, mode: str = "preview") -> dict:
    """Body gửi thẳng tới `net_config.MESHY_URL`.

    Giữ đúng những trường Meshy cần và không thêm gì lạ: `net.mesh` gửi
    `{"prompt": ...}` trần, còn đây là bản đầy đủ cho lần sinh hàng loạt.
    """
    return {
        "mode": mode,
        "prompt": prompt,
        "negative_prompt": NEGATIVE,
        "art_style": "sculpture",
        "should_remesh": True,
    }
