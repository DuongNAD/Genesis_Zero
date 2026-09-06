"""Genesis Zero — genai: gọi Gemini để viết lại mô tả sinh vật cho Meshy (W-19).

## Vì sao cần một tầng viết lại

`mesh_prompts.creature_prompt` ghép ba mảnh: dáng theo tầng, ba đặc điểm, và
vector trait. Nó **đúng** nhưng nó là một danh sách, không phải một câu tả. Meshy
dựng hình tốt hơn hẳn khi được đọc một đoạn văn mạch lạc về một con vật, thay vì
một chuỗi mệnh đề nối bằng dấu chấm.

Nên: ta dựng mô tả **tất định** từ thế giới, rồi nhờ một model viết lại cho trôi,
rồi mới gửi sang Meshy.

## Ranh giới: viết lại được, THÊM thì không

Bất biến của file này. Model viết lại **chỉ được diễn đạt lại những gì đã có**;
nó không được bịa thêm bộ phận, không được đổi số chi, không được thêm màu.

Lý do không phải thẩm mỹ mà là đo đạc: hình 3D là một **kênh quan sát gián tiếp**
([03 §4](../docs/03-LUAT-AN-V5.md)) — người chơi nhìn con vật và suy ra nó làm
được gì. Nếu model tả thêm một cái vây mà con vật không có thì kênh ấy nói dối,
và nó nói dối theo cách không ai kiểm được. `verify_rewrite` giữ ranh giới ấy
bằng cách đòi mọi từ khoá giải phẫu của bản gốc phải còn nguyên trong bản viết
lại.

## Khoá

Đọc `GEMINI_API_KEYS` từ môi trường (nhiều khoá, cách nhau bằng dấu phẩy).
**Không có khoá nào trong kho** — xem `.env.example`. Hết hạn mức một khoá thì
xoay sang khoá kế tiếp; hết sạch thì trả `None` và người gọi dùng bản gốc.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any
import urllib.error
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
FALLBACK_MODELS = [
    MODEL,
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]


class GeminiKeyRouter:
    """Bộ định tuyến và xoay vòng khoá Gemini API (Round-Robin & Dynamic Failover).

    Khi một khoá bị 429 (Resource Exhausted) hoặc 403 (Quota Exceeded / Forbidden),
    router đánh dấu khoá vào danh sách cooldown (60s) và tự động chuyển sang khoá
    tiếp theo. Đồng thời mỗi lượt gọi xoay vòng đều giữa các khoá hoạt động.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._index = 0
        self._cooldowns: dict[str, float] = {}

    def get_rotated_keys(self, custom_key: str | None = None) -> list[str]:
        with self._lock:
            candidates: list[str] = []
            if custom_key and custom_key.strip():
                candidates.append(custom_key.strip())

            base = keys()
            if not base:
                return candidates

            now = time.time()
            available = [k for k in base if now >= self._cooldowns.get(k, 0.0)]
            if not available:
                self._cooldowns.clear()
                available = list(base)

            n = len(available)
            idx = self._index % n
            rotated = available[idx:] + available[:idx]
            self._index = (self._index + 1) % max(1, len(base))

            for k in rotated:
                if k not in candidates:
                    candidates.append(k)
            return candidates

    def mark_exhausted(self, key: str, cooldown_secs: float = 60.0) -> None:
        with self._lock:
            self._cooldowns[key] = time.time() + cooldown_secs

    def mark_success(self, key: str) -> None:
        with self._lock:
            self._cooldowns.pop(key, None)


KEY_ROUTER = GeminiKeyRouter()

MAX_REWRITE_TRIES = 2
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Từ khoá giải phẫu: nếu bản gốc có, bản viết lại phải giữ.
_ANATOMY: tuple[tuple[str, ...], ...] = (
    ("bốn chân", "bốn chi"),
    ("hai chân",),
    ("không có chân", "không chân", "chẳng có chân"),
    ("cánh",),
    ("vây",),
    ("đuôi",),
    ("màng bơi", "màng giữa", "chân màng", "có màng"),
    ("móng vuốt", "vuốt", "móng"),
    ("lông",),
    ("vảy",),
    ("gai",),
    ("râu",),
    ("nanh",),
    ("túi",),
)

SYSTEM = (
    "Bạn viết lại mô tả một sinh vật hư cấu thành một đoạn văn tiếng Việt liền "
    "mạch, dùng để dựng mô hình 3D.\n"
    "QUY TẮC:\n"
    "· Chỉ diễn đạt lại. Không thêm bộ phận cơ thể, không đổi số lượng chi, "
    "không thêm màu sắc hay hoa văn không có trong bản gốc.\n"
    "· Giữ lại MỌI chi tiết giải phẫu đã nêu, kể cả số lượng chi.\n"
    "· Viết như đang tả một con vật có thật đứng trước mặt: hình khối, tỉ lệ, "
    "tư thế, chất da lông.\n"
    "· Bỏ hết phần chỉ số trò chơi và phần dặn về phong cách ảnh.\n"
    "· Ba đến bốn câu.\n"
    "Trả về đúng đoạn văn ấy, không mở đầu, không giải thích, không đánh số."
)


def keys() -> list[str]:
    """Danh sách khoá, theo thứ tự dùng. Rỗng nghĩa là chưa cấu hình."""
    raw = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or ""
    return [k.strip() for k in raw.split(",") if k.strip()]


def _one_call(key: str, prompt: str, timeout: float) -> str | None:
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4000},
    }).encode("utf-8")

    models_to_try = []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    for m in models_to_try:
        req = urllib.request.Request(
            URL.format(model=m) + f"?key={key}",
            data=body, headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            KEY_ROUTER.mark_success(key)
            cands = data.get("candidates") or []
            if not cands:
                return None
            if cands[0].get("finishReason") not in (None, "STOP"):
                return None
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = " ".join(p.get("text", "") for p in parts).strip()
            return text or None
        except urllib.error.HTTPError as e:
            if e.code in (429, 403):
                KEY_ROUTER.mark_exhausted(key)
                return None
            if e.code == 404:
                continue
            return None
        except Exception:
            return None
    return None


def verify_rewrite(original: str, rewritten: str) -> tuple[bool, str]:
    """Bản viết lại có giữ đủ giải phẫu của bản gốc không.

    Trả `(ok, lý_do)`. Kiểm theo MỘT chiều: từ khoá nào có trong bản gốc thì phải
    có trong bản viết lại. Chiều ngược lại cố tình không kiểm — model được phép
    dùng từ đồng nghĩa và thêm chữ nối, nó chỉ không được **đánh rơi** bộ phận.
    """
    lo_o, lo_r = original.lower(), rewritten.lower()
    for group in _ANATOMY:
        if any(w in lo_o for w in group) and not any(w in lo_r for w in group):
            return False, f"đánh rơi {group[0]!r}"
    if len(rewritten.split()) > 140:
        return False, "dài quá 140 từ"
    if re.search(r"\d", rewritten):
        return False, "còn sót chữ số — mô tả hình không được mang chỉ số"
    return True, ""


def rewrite(prompt: str, timeout: float = 20.0) -> tuple[str, str]:
    """Viết lại `prompt`. Trả `(văn_bản, nguồn)` — `nguồn` là `gemini` hoặc `goc`.

    **Không bao giờ ném.** Hỏng khoá, hết hạn mức, mất mạng, hay model trả về một
    bản đánh rơi bộ phận — tất cả đều rơi về bản gốc, vì bản gốc đã đúng sẵn. Cái
    ta mua ở đây là văn phong, không phải sự thật; trả tiền bằng một ván gãy thì
    quá đắt.
    """
    ks = keys()
    if not ks:
        return prompt, "goc"

    # Hai loại hỏng, hai cách xử lý — và gộp chúng làm một là lỗi đã trả giá.
    #
    # · **khoá hỏng / hết hạn mức** -> xoay sang khoá kế tiếp. Đúng.
    # · **model trả bản đánh rơi bộ phận** -> KHÔNG xoay khoá. Đó không phải lỗi
    #   khoá; khoá khác cũng cho ra một bản tương tự.
    #
    # Bản đầu gộp cả hai, nên một bản bị bộ kiểm từ chối làm nó thử hết **14
    # khoá**, mỗi lần ~30 giây. Năm sinh vật mất hơn 25 phút thay vì 2 phút rưỡi,
    # và không có gì trong log nói vì sao — nó chỉ *chậm*.
    tries_left = MAX_REWRITE_TRIES
    for key in ks:
        if tries_left <= 0:
            break
        try:
            out = _one_call(key, prompt, timeout)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            continue          # khoá này hỏng hoặc hết hạn mức -> khoá kế tiếp
        except (ValueError, KeyError):
            continue
        # Từ đây trở đi là khoá CHẠY ĐƯỢC: mọi thất bại còn lại là chuyện của
        # model, và nó ăn vào ngân sách thử chứ không ăn vào danh sách khoá.
        tries_left -= 1
        if not out:
            continue
        ok, _why = verify_rewrite(prompt, out)
        if ok:
            return out, "gemini"
    return prompt, "goc"


# ── Ma Trận 27 Archetypes Sinh Thái Chuẩn Mực (3x3x3) ──
# (Domain, Diet, Strategy) -> metadata
ECOLOGICAL_ARCHETYPES_27: dict[tuple[str, str, str], dict[str, Any]] = {
    # 🌿 TRÊN CẠN (CAN)
    ("CAN", "HERBIVORE", "STRAT_R"): {
        "name": "Thỏ Đồng Cỏ",
        "scientific_name": "Sylvilagus Campestris",
        "niche_summary": "Loài gặm nhấm bầy đàn tầng thấp, sinh sản cực nhanh.",
        "behavior_lore": "Gặm cỏ dại và quả mọng trên mặt đất, liên tục di chuyển theo bầy để phân tán nguy cơ bị săn.",
        "recommended_traits": [1, 0, 1, 4, 3, 3],
    },
    ("CAN", "HERBIVORE", "STRAT_K"): {
        "name": "Tê Giác Thiết Giáp",
        "scientific_name": "Rhinoceros Titanus",
        "niche_summary": "Động vật ăn thực vật khổng lồ đơn độc, giáp dày sừng lớn.",
        "behavior_lore": "Thong thả gặm cây bụi cứng, lớp da sừng bảo vệ nó khỏi hầu hết các đòn tấn công vật lý.",
        "recommended_traits": [1, 2, 4, 1, 1, 3],
    },
    ("CAN", "HERBIVORE", "STRAT_SOCIAL"): {
        "name": "Linh Dương Du Mục",
        "scientific_name": "Antilocapra Socialis",
        "niche_summary": "Đàn ăn cỏ cơ động, cảnh báo thính giác tương trợ.",
        "behavior_lore": "Di cư liên tục qua các thảm cỏ rộng, cá thể đầu đàn dùng tiếng kêu để báo động khi có thú dữ.",
        "recommended_traits": [2, 1, 1, 3, 3, 2],
    },
    ("CAN", "CARNIVORE", "STRAT_R"): {
        "name": "Cáo Đỏ Bầy Đàn",
        "scientific_name": "Vulpes Gregaria",
        "niche_summary": "Kẻ săn mồi nhỏ bé số lượng đông, áp đảo con mồi bằng tốc độ.",
        "behavior_lore": "Săn chuột và côn trùng theo nhóm nhỏ, luân phiên rượt đuổi để con mồi kiệt sức.",
        "recommended_traits": [1, 3, 0, 4, 3, 1],
    },
    ("CAN", "CARNIVORE", "STRAT_K"): {
        "name": "Hổ Nanh Kiếm",
        "scientific_name": "Smilodon Solitarius",
        "niche_summary": "Thợ săn thượng tầng uy lực, đơn độc kiểm soát lãnh thổ.",
        "behavior_lore": "Phục kích từ trong bụi rậm và tung đòn kết liễu bằng răng nanh uy lực, không chia sẻ thức ăn.",
        "recommended_traits": [1, 5, 2, 2, 1, 1],
    },
    ("CAN", "CARNIVORE", "STRAT_SOCIAL"): {
        "name": "Lang Tộc Đồng Cỏ",
        "scientific_name": "Canis Pratorum",
        "niche_summary": "Bầy sói săn mồi kỷ luật, vây hãm và hạ gục con mồi lớn.",
        "behavior_lore": "Giao tiếp bằng tiếng hú và phối hợp tác chiến chặt chẽ, chia sẻ chiến lợi phẩm sau khi hạ gục mục tiêu.",
        "recommended_traits": [2, 3, 1, 3, 2, 1],
    },
    ("CAN", "OMNIVORE", "STRAT_R"): {
        "name": "Chuột Chù Cơ Hội",
        "scientific_name": "Sorex Opportunus",
        "niche_summary": "Ăn tạp cơ hội, tận dụng mọi nguồn hạt quả và xác vụn.",
        "behavior_lore": "Lùng sục mọi ngóc ngách mặt đất để tìm thức ăn, thích nghi cực tốt với mọi điều kiện biến đổi.",
        "recommended_traits": [1, 1, 1, 3, 3, 3],
    },
    ("CAN", "OMNIVORE", "STRAT_K"): {
        "name": "Hùng Tinh Rừng Già",
        "scientific_name": "Ursus Robur",
        "niche_summary": "Động vật ăn tạp khổng lồ, một mình thống trị khu rừng.",
        "behavior_lore": "Ăn từ củ rễ, mật ong đến săn thú nhỏ, thể lực dồi dào và bảo vệ nghiêm ngặt khu vực hang trú ngụ.",
        "recommended_traits": [2, 3, 3, 1, 1, 2],
    },
    ("CAN", "OMNIVORE", "STRAT_SOCIAL"): {
        "name": "Linh Trưởng Thảo Nguyên",
        "scientific_name": "Simia Sapiens",
        "niche_summary": "Bầy đàn thông minh, hợp tác chia sẻ thức ăn và chế ngự tự nhiên.",
        "behavior_lore": "Trí tuệ cao, biết dùng công cụ thô sơ và chia sẻ tài nguyên quả chín cũng như thịt săn được trong đàn.",
        "recommended_traits": [4, 1, 1, 2, 2, 2],
    },

    # 🌊 DƯỚI NƯỚC (NUOC)
    ("NUOC", "HERBIVORE", "STRAT_R"): {
        "name": "Thủy Điệp Đầm Nông",
        "scientific_name": "Hydrolepis Minuta",
        "niche_summary": "Đàn cá nhỏ gặm rêu tảo, bơi thành dải sóng ảo ảnh.",
        "behavior_lore": "Bơi lội sát đáy đầm lầy để gặm tảo lam, phản ứng bầy đàn đồng loạt khi nước gợn sóng.",
        "recommended_traits": [1, 0, 1, 4, 3, 3],
    },
    ("NUOC", "HERBIVORE", "STRAT_K"): {
        "name": "Hải Ngưu Biển Sâu",
        "scientific_name": "Sirenia Gigantea",
        "niche_summary": "Thủy quái ăn thực vật đáy, lớp da dày chống va đập.",
        "behavior_lore": "Thong dong hấp thu rong biển tại các rạn ngầm, hầu như không có kẻ thù tự nhiên nào dám tấn công.",
        "recommended_traits": [1, 1, 4, 1, 1, 4],
    },
    ("NUOC", "HERBIVORE", "STRAT_SOCIAL"): {
        "name": "Kình Ngư Thảo Bộc",
        "scientific_name": "Delphinus Herbivorus",
        "niche_summary": "Bầy động vật biển ăn tảo, di chuyển bảo bọc nhau.",
        "behavior_lore": "Bơi theo đội hình hình chữ V để giảm sức cản dòng nước, che chở con non ở tâm bầy.",
        "recommended_traits": [2, 1, 2, 3, 2, 2],
    },
    ("NUOC", "CARNIVORE", "STRAT_R"): {
        "name": "Cá Răng Đao",
        "scientific_name": "Serrasalmus Vorax",
        "niche_summary": "Đàn cá săn mồi hung tợn, xé toạc con mồi tức thì.",
        "behavior_lore": "Đánh hơi thấy máu là lao vào cắn xé cuồng loạn, số lượng áp đảo khiến con mồi không kịp trở tay.",
        "recommended_traits": [1, 4, 0, 4, 2, 1],
    },
    ("NUOC", "CARNIVORE", "STRAT_K"): {
        "name": "Hải Quái Nanh Nhọn",
        "scientific_name": "Leviathan Monodon",
        "niche_summary": "Sát thủ biển sâu cô độc, lực cắn nghiền nát vỏ giáp.",
        "behavior_lore": "Ẩn mình dưới đáy vực tối tăm và phóng lên đớp gọn con mồi bằng cú cắn kinh hoàng.",
        "recommended_traits": [1, 5, 2, 2, 1, 1],
    },
    ("NUOC", "CARNIVORE", "STRAT_SOCIAL"): {
        "name": "Kình Sát Hải Đội",
        "scientific_name": "Orcinus Socialis",
        "niche_summary": "Bầy cá voi săn mồi theo nhóm, dồn ép con mồi bằng bọt khí.",
        "behavior_lore": "Phối hợp quẫy đuôi tạo sóng làm choáng con mồi, giao tiếp phức tạp bằng sóng siêu âm định vị.",
        "recommended_traits": [2, 4, 1, 3, 1, 1],
    },
    ("NUOC", "OMNIVORE", "STRAT_R"): {
        "name": "Tôm Giáp Dọn Bể",
        "scientific_name": "Caridea Vulgata",
        "niche_summary": "Thủy sinh dọn vụn đáy nước, xử lý mọi phế phẩm hữu cơ.",
        "behavior_lore": "Chân kìm linh hoạt lọc xác vụn và mầm rêu trên nền cát, sinh sản theo từng đợt trăng tròn.",
        "recommended_traits": [1, 1, 1, 3, 3, 3],
    },
    ("NUOC", "OMNIVORE", "STRAT_K"): {
        "name": "Bạch Tuộc Vực Thẳm",
        "scientific_name": "Octopus Abyssi",
        "niche_summary": "Kẻ ăn tạp bí ẩn trí tuệ cao, săn mồi và ăn xác ngầm.",
        "behavior_lore": "Đổi màu da hòa nhập hoàn toàn vào san hô, dùng xúc tu khéo léo mở các lớp vỏ cứng tìm thức ăn.",
        "recommended_traits": [3, 2, 2, 2, 2, 1],
    },
    ("NUOC", "OMNIVORE", "STRAT_SOCIAL"): {
        "name": "Hải Cẩu Bầy Đảo Đá",
        "scientific_name": "Phoca Gregaria",
        "niche_summary": "Đàn thú lưỡng cư ăn cá và rong biển, chia sẻ điểm sưởi nắng.",
        "behavior_lore": "Bơi lội kiếm ăn theo nhóm ven bờ và cùng leo lên các tảng đá phơi nắng, hỗ trợ canh gác cá mập.",
        "recommended_traits": [2, 2, 2, 2, 2, 2],
    },

    # 🦅 TRÊN KHÔNG (TROI)
    ("TROI", "HERBIVORE", "STRAT_R"): {
        "name": "Tước Điểu Hạt Cỏ",
        "scientific_name": "Passer Granivora",
        "niche_summary": "Chim nhỏ ăn hạt theo đàn lớn, phát tán hạt giống khắp nơi.",
        "behavior_lore": "Sà xuống các vạt cỏ chín mọng rồi bay vút lên khi có động tĩnh, tiếng đập cánh rào rào xua tan mối nguy.",
        "recommended_traits": [1, 0, 0, 5, 3, 3],
    },
    ("TROI", "HERBIVORE", "STRAT_K"): {
        "name": "Tiên Hạc Thượng Tầng",
        "scientific_name": "Grus Titanica",
        "niche_summary": "Sải cánh khổng lồ lướt gió vô tận, ăn quả ngọt trên tán rừng.",
        "behavior_lore": "Bay lượn ở độ cao cực lớn tận dụng luồng nhiệt, chỉ đáp xuống các ngọn cây cổ thụ để kiếm quả chín.",
        "recommended_traits": [2, 1, 2, 3, 2, 2],
    },
    ("TROI", "HERBIVORE", "STRAT_SOCIAL"): {
        "name": "Vẹt Rừng Giao Cảm",
        "scientific_name": "Psittacula Harmonica",
        "niche_summary": "Đàn chim ăn trái thông minh, hót vang cảnh báo thời tiết bão.",
        "behavior_lore": "Sống thành cặp và bầy nhỏ bền vững, truyền dạy nhau lộ trình tìm cây ăn trái theo mùa khí hậu.",
        "recommended_traits": [3, 1, 0, 3, 3, 2],
    },
    ("TROI", "CARNIVORE", "STRAT_R"): {
        "name": "Dơi Đêm Săn Mồi",
        "scientific_name": "Microchiroptera Velox",
        "niche_summary": "Đàn thú bay săn mồi đêm, lùng sục sinh vật nhỏ và côn trùng.",
        "behavior_lore": "Tung cánh hàng loạt lúc hoàng hôn, định vị hồi âm siêu nhạy giúp tóm gọn mục tiêu trong bóng tối.",
        "recommended_traits": [1, 3, 0, 4, 3, 1],
    },
    ("TROI", "CARNIVORE", "STRAT_K"): {
        "name": "Kim Ưng Đỉnh Núi",
        "scientific_name": "Aquila Excelsa",
        "niche_summary": "Thợ săn bầu trời tối thượng, bổ nhào đoạt mạng từ tầng mây.",
        "behavior_lore": "Thị giác tinh tường phát hiện con mồi từ độ cao hàng trăm mét, bổ nhào như sấm sét với móng vuốt thép.",
        "recommended_traits": [1, 5, 1, 3, 2, 0],
    },
    ("TROI", "CARNIVORE", "STRAT_SOCIAL"): {
        "name": "Ưng Săn Bầy Hợp Lực",
        "scientific_name": "Falco Sociabilis",
        "niche_summary": "Biệt đội chim săn phối hợp ép góc và lùa con mồi.",
        "behavior_lore": "Phân công cá thể bay cao quan sát và cá thể sà thấp rượt đuổi, ép con mồi chạy thẳng vào bẫy mai phục.",
        "recommended_traits": [2, 3, 1, 4, 1, 1],
    },
    ("TROI", "OMNIVORE", "STRAT_R"): {
        "name": "Hải Âu Duyên Hải",
        "scientific_name": "Larus Vagrans",
        "niche_summary": "Chim cơ hội ven biển, ăn xác cá trôi dạt và hạt quả.",
        "behavior_lore": "Bay dập dờn theo các ngọn sóng nhặt nhạnh thức ăn thừa, tranh giành quyết liệt nhưng gắn kết theo bầy.",
        "recommended_traits": [1, 1, 0, 4, 3, 3],
    },
    ("TROI", "OMNIVORE", "STRAT_K"): {
        "name": "Quạ Thần Rừng Cổ",
        "scientific_name": "Corvus Arcanus",
        "niche_summary": "Chim ăn tạp tuổi thọ cao, hiểu rõ quy luật địa hình và bão.",
        "behavior_lore": "Trí nhớ siêu phàm ghi nhớ vị trí cất giấu thức ăn, sống cô độc và quan sát diễn biến toàn bộ hệ sinh thái.",
        "recommended_traits": [4, 1, 1, 2, 3, 1],
    },
    ("TROI", "OMNIVORE", "STRAT_SOCIAL"): {
        "name": "Bồ Nông Hợp Sức",
        "scientific_name": "Pelecanus Cooperator",
        "niche_summary": "Đàn chim bắt cá và gắp quả, chia sẻ vị trí luồng gió.",
        "behavior_lore": "Quây thành vòng cung trên mặt nước để dồn cá vào giữa, chiếc túi cổ họng rộng lớn chia sẻ thức ăn cho đồng loại.",
        "recommended_traits": [2, 2, 1, 3, 2, 2],
    },
}


def generate_ecological_name(
    domain: str,
    diet: str,
    strategy: str,
    traits: list[int] | None = None,
    features: list[str] | None = None,
    custom_api_key: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Đặt tên sinh vật phù hợp với các đặc điểm sinh thái (Domain, Diet, r/K Strategy).

    Sử dụng Gemini API với bộ định tuyến xoay vòng khoá và failover tự động.
    Rơi về Ma Trận 27 Archetypes Sinh Thái Chuẩn Mực nếu offline hoặc hết quota.
    """
    dom = (domain or "CAN").upper()
    dt = (diet or "HERBIVORE").upper()
    strat = (strategy or "STRAT_R").upper()

    if dom not in ("CAN", "NUOC", "TROI"):
        dom = "CAN"
    if dt not in ("HERBIVORE", "CARNIVORE", "OMNIVORE"):
        dt = "HERBIVORE"
    if strat not in ("STRAT_R", "STRAT_K", "STRAT_SOCIAL"):
        strat = "STRAT_R"

    key_tuple = (dom, dt, strat)
    fallback = ECOLOGICAL_ARCHETYPES_27.get(
        key_tuple,
        ECOLOGICAL_ARCHETYPES_27[("CAN", "HERBIVORE", "STRAT_R")],
    )

    tr = traits or fallback["recommended_traits"]
    feat_list = features or []

    candidate_keys = KEY_ROUTER.get_rotated_keys(custom_api_key)
    if not candidate_keys:
        res = dict(fallback)
        res["source"] = "procedural"
        res["domain"] = dom
        res["diet"] = dt
        res["strategy"] = strat
        res["recommended_traits"] = fallback["recommended_traits"]
        return res

    DOM_VN = {"CAN": "Trên cạn (địa hình cỏ, bụi rậm, đá)", "NUOC": "Dưới nước (đầm lầy, biển sâu)", "TROI": "Trên không (bầu trời, lướt gió)"}
    DIET_VN = {"HERBIVORE": "Ăn thực vật / Tự dưỡng (hoa quả, mầm cây, rêu)", "CARNIVORE": "Ăn thịt / Săn mồi (thịt động vật, rượt đuổi)", "OMNIVORE": "Ăn tạp / Phân hủy (hoa quả, xác vụn sinh học)"}
    STRAT_VN = {"STRAT_R": "Chiến lược r (Bầy đàn nhỏ, sinh sản cực nhanh)", "STRAT_K": "Chiến lược K (Đơn độc khổng lồ, giáp dày máu trâu)", "STRAT_SOCIAL": "Chiến lược Xã hội (Social Pack, đàn săn/bảo bọc hợp tác)"}

    system_instruction = (
        "Bạn là nhà sinh học tiến hóa và chuyên gia cổ sinh vật học.\n"
        "Nhiệm vụ: Đặt tên cho một loài sinh vật hư cấu dựa trên các tiêu chí sinh thái học nghiêm ngặt.\n"
        "QUY TẮC CỐT LÕI:\n"
        "- KHÔNG đặt tên siêu nhân, quái thai hay thần thoại phóng đại. Phải mang tính sinh thái học tự nhiên.\n"
        "- Trả về duy nhất JSON hợp lệ:\n"
        "{\n"
        '  "name": "Tên tiếng Việt tự nhiên (2 đến 4 từ, ví dụ: \'Thủy Điệp Đầm Lầy\', \'Lang Tộc Đồng Cỏ\')",\n'
        '  "scientific_name": "Tên danh pháp khoa học Latin 2 từ giả tưởng (ví dụ: \'Sylvapus campestris\')",\n'
        '  "niche_summary": "Tóm tắt vị trí sinh thái trong chuỗi thức ăn (1 câu ngắn tối đa 18 từ)",\n'
        '  "behavior_lore": "Mô tả ngắn gọn 1-2 câu về tập tính kiếm ăn và sinh tồn"\n'
        "}"
    )

    prompt = (
        f"Môi trường sống: {DOM_VN.get(dom, dom)}\n"
        f"Phương thức dinh dưỡng: {DIET_VN.get(dt, dt)}\n"
        f"Chiến lược sinh tồn: {STRAT_VN.get(strat, strat)}\n"
        f"Chỉ số thuộc tính: Trí tuệ={tr[0]}, Tấn công={tr[1]}, Giáp={tr[2]}, Tốc độ={tr[3]}, Giác quan={tr[4]}, Dạ dày={tr[5]}\n"
        f"Đặc điểm sinh học: {', '.join(feat_list) if feat_list else 'Chưa có đột biến phụ'}\n"
    )

    models_to_try = []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    for k in candidate_keys:
        for m in models_to_try:
            try:
                body = json.dumps({
                    "system_instruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.5,
                        "maxOutputTokens": 1000,
                        "responseMimeType": "application/json",
                    },
                }).encode("utf-8")
                req = urllib.request.Request(
                    URL.format(model=m) + f"?key={k}",
                    data=body,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    raw_data = json.loads(r.read().decode("utf-8"))
                KEY_ROUTER.mark_success(k)
                cands = raw_data.get("candidates") or []
                if not cands:
                    continue
                parts = (cands[0].get("content") or {}).get("parts") or []
                raw_text = "".join(p.get("text", "") for p in parts).strip()
                match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    name = str(parsed.get("name") or "").strip()
                    if name:
                        return {
                            "name": name,
                            "scientific_name": str(parsed.get("scientific_name") or fallback["scientific_name"]).strip(),
                            "niche_summary": str(parsed.get("niche_summary") or fallback["niche_summary"]).strip(),
                            "behavior_lore": str(parsed.get("behavior_lore") or fallback["behavior_lore"]).strip(),
                            "recommended_traits": fallback["recommended_traits"],
                            "domain": dom,
                            "diet": dt,
                            "strategy": strat,
                            "source": "gemini",
                        }
            except urllib.error.HTTPError as e:
                if e.code in (429, 403):
                    KEY_ROUTER.mark_exhausted(k)
                    break
                if e.code == 404:
                    continue
                break
            except Exception:
                break

    res = dict(fallback)
    res["source"] = "procedural"
    res["domain"] = dom
    res["diet"] = dt
    res["strategy"] = strat
    res["recommended_traits"] = fallback["recommended_traits"]
    return res
