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
import urllib.error
import urllib.request

# Tên model do CHÍNH API chỉ định khi bản cũ bị gỡ: gọi `gemini-2.0-flash`
# trả 404 kèm câu "no longer available, please update to gemini-3.6-flash".
# Đổi được bằng biến môi trường để không phải sửa code lần sau.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
# Số lần thử với KHOÁ CHẠY ĐƯỢC trước khi chịu dùng bản gốc. Khoá hỏng
# không tính vào đây — xem `rewrite`.
MAX_REWRITE_TRIES = 2
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Từ khoá giải phẫu: nếu bản gốc có, bản viết lại phải giữ. Đây là hàng rào
# chống "model tả thêm một bộ phận không tồn tại".
# Mỗi dòng là một NHÓM ĐỒNG NGHĨA: bản gốc chạm vào nhóm nào thì bản viết lại
# phải chạm lại nhóm ấy, bằng bất cứ từ nào trong nhóm.
#
# Nhóm chứ không phải từ đơn, vì bộ kiểm bản đầu bắt oan ngay lần chạy thật đầu
# tiên: Gemini viết "đứng vững vàng trên bốn **chi**" — đúng nghĩa, đúng số chi,
# và bị loại vì bản gốc viết "bốn **chân**".
#
# Cố ý KHÔNG có "mang" và "mai": chúng là từ quá thường trong tiếng Việt ("mang
# theo", "ngày mai") nên chúng khớp nhầm ở khắp nơi, và một hàng rào khớp nhầm
# thì tệ hơn không có hàng rào — nó dạy người sửa code sau này bỏ qua cảnh báo.
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

# Ba lần sửa mới ra được câu này, và hai lần hỏng đều đáng ghi.
#
# Bản có câu *"Tối đa 90 từ"*: model **đếm từ ra thành chữ** — nó trả về
# `(48) Bốn(49) chi(50) ngắn(51) chắc,(52) riêng…`. Một ràng buộc đếm được là
# một lời mời đếm, và model làm đúng thế, ngay giữa câu trả lời.
#
# Bản có câu *"không dùng số"*: nó dội sang cả chữ số trong "bốn chân".
#
# Nên: nói giới hạn bằng **số CÂU** chứ không bằng số từ, và nói cái không được
# mang bằng tên gọi ("chỉ số trò chơi") chứ không bằng hình thức ("số").
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
        # 2000, không phải 300. Gemini 3 **nghĩ trước khi trả lời** và phần nghĩ
        # ăn cùng ngân sách: đo thật trên một mô tả 168 token đầu vào thì
        # `thoughtsTokenCount = 1110` còn câu trả lời chỉ 101 token. Với trần 300
        # thì nó trả về một mẩu suy nghĩ dở (`/no digits like "4", use "bốn`) —
        # JSON hợp lệ, `finishReason: STOP`, và rác. Kiểu hỏng tệ nhất: trông y
        # như model kém.
        #
        # Rồi 2000 vẫn chưa đủ: phần nghĩ ~1100 cộng một đoạn văn bốn câu là
        # chạm trần, và câu trả lời **đứt giữa chừng** — bản viết lại mất chữ
        # "móng vuốt" ở cuối và bị bộ kiểm loại vì "đánh rơi bộ phận", trong khi
        # model đã tả nó đúng, chỉ là chưa kịp viết ra.
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4000},
    }).encode("utf-8")
    req = urllib.request.Request(
        URL.format(model=MODEL) + f"?key={key}",
        data=body, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    cands = data.get("candidates") or []
    if not cands:
        return None
    # Đứt vì chạm trần thì VỨT, đừng trả về một câu dở.
    #
    # Một đoạn văn cụt trông y như một đoạn văn đánh rơi bộ phận, nên nếu để nó
    # đi tiếp thì `verify_rewrite` báo "đánh rơi 'móng vuốt'" và ta đi sửa nhầm
    # chỗ — sửa hàng rào, trong khi lỗi nằm ở ngân sách token.
    if cands[0].get("finishReason") not in (None, "STOP"):
        return None
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = " ".join(p.get("text", "") for p in parts).strip()
    return text or None


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
