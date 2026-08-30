"""Genesis Zero — prompt: năm khối, giữ prefix KV cache bất biến (B-02).

Đây là chỗ v5 đảo ngược v4 một cách có kiểm soát (docs/03-LUAT-AN-V5.md §0.4):
**nói luật nền, giấu luật ẩn**. Sai ở đây thì hoặc agent không biết mình phải đi
tìm gì, hoặc ta mớm luôn đáp án và cả thí nghiệm thành vô nghĩa.

Năm bất biến, theo docs/tasks/B-02-prompt.md §3:

1. `system_block` giống nhau **từng byte** giữa mọi lần gọi của cùng một cá thể
   trong một ván — điều kiện để prefix KV cache hoạt động. Vì thế SYSTEM chỉ
   chứa thứ thật sự bất biến; `brain` là trait duy nhất được phép ở đây, và chỉ
   vì khối D cắt theo nó.
2. Mọi thứ biến động nằm ở **cuối**, trong `user_block`.
3. Khối A nói cơ chế nền **định tính**, không bao giờ nói công thức số.
4. Khối A2 chứa nguyên văn câu "Bề ngoài ... không nói lên bản chất".
5. Không bao giờ xuất hiện tên **lớp** (`FRUIT_A`) — chỉ **bề mặt**.

Bất biến 5 được canh bằng `_check_no_leak`, và nó **ném lỗi** chứ không sửa
chuỗi. Một bộ lọc thay `FRUIT_A` bằng chữ khác trông thì an toàn nhưng nó biến
mọi test rò rỉ thành test rỗng: test không bao giờ đỏ được nữa, dù đường rò có
thật. Rò rỉ phải làm gãy ván, để ta thấy.
"""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING, Any, Iterable, Sequence

from genesis import config, law_config
from genesis.lawdsl import CondKind, EffectKind, TriggerKind, to_vietnamese, vocab_for_brain
from genesis.surface import SurfaceMap
from genesis.world import Terrain, phase_at

if TYPE_CHECKING:
    from genesis.codex import Codex
    from genesis.creature import Creature
    from genesis.fieldnotes import FieldNotes
    from genesis.world import World


def prompt_hash(system: str, user: str) -> str:
    """md5 của prompt đầy đủ. Chỉ hash này đi vào log, không bao giờ prompt gốc —
    ghi cả prompt thì log phình gấp ~20 lần (B-06 bất biến 1)."""
    return hashlib.md5(f"{system}\x00{user}".encode("utf-8")).hexdigest()


class PromptLeak(RuntimeError):
    """Prompt chứa thứ agent không được phép thấy. Ném ra, không vá âm thầm."""


# Tên lớp và định danh nội bộ: cấm ở MỌI khối, kể cả khối D.
_FORBIDDEN_ANYWHERE = re.compile(r"FRUIT_[A-Z]|law_id|match_seed")

# Tên enum DSL: hợp lệ ở khối D (đó là từ vựng agent phải dùng để phát biểu
# luật), cấm ở mọi khối kể chuyện — ở đó chúng là đáp án.
_DSL_NAMES: frozenset[str] = frozenset(
    [e.value for e in EffectKind]
    + [t.value for t in TriggerKind]
    + [c.value for c in CondKind]
)
_DSL_RE = re.compile(r"\b(" + "|".join(sorted(_DSL_NAMES, key=len, reverse=True)) + r")\b")


def _check_no_leak(text: str, where: str, *, allow_dsl_names: bool = False) -> str:
    m = _FORBIDDEN_ANYWHERE.search(text)
    if m:
        raise PromptLeak(f"{where}: rò định danh nội bộ {m.group(0)!r}")
    if not allow_dsl_names:
        m = _DSL_RE.search(text)
        if m:
            raise PromptLeak(f"{where}: rò tên enum DSL {m.group(0)!r} ngoài khối D")
    return text


# ─── Khối A: cơ chế nền ──────────────────────────────────────────────────────
# Bất biến 3: định tính. Không một công thức số nào. Nói `damage = 4 + 3*attack`
# thì model làm toán thay vì hành xử như con vật.

BLOCK_A = """[CƠ CHẾ NỀN]
Thế giới là một lưới ô vuông phẳng, đi khỏi mép bên này thì hiện ra ở mép bên kia.
Thời gian trôi theo chu kỳ ngày rồi đêm, luân phiên mãi.
Mặt đất có đồng cỏ đi được, ô nước để uống, bụi rậm che tầm nhìn, mỏm đá chắn đường, và lửa.
Sống thì tốn sức, làm gì cũng tốn thêm. Hết sức thì cơ thể suy kiệt và chết.
Quả mọc rải rác trên đồng cỏ; ăn quả lấy lại sức, uống nước ở ô nước cũng vậy.
Ngươi có thể đi, nghỉ, ăn, uống, đánh, hoặc lên tiếng cho kẻ khác nghe.
Giáp dày thì chịu đòn nhẹ hơn; tay khoẻ thì đánh đau hơn. Kẻ chết để lại xác, rồi một thời gian sau sống lại."""

# ─── Khối A2: giao kèo ───────────────────────────────────────────────────────
# Chép nguyên văn docs/03-LUAT-AN-V5.md §8. Đừng viết lại cho hoa mỹ: câu cuối
# là câu quan trọng nhất trong toàn bộ prompt, nó nói thẳng rằng prior không
# dùng được. Thiếu nó, ta chỉ đo được model nào cứng đầu hơn.

BLOCK_A2 = """[GIAO KÈO]
Thế giới này có 2 hoặc 3 quy luật ẩn mà không sinh vật nào được cho biết trước. Chúng đổi mỗi lần thế giới sinh ra. Chúng là quan hệ nhân quả: một việc xảy ra, trong một hoàn cảnh nào đó, dẫn tới một hệ quả.
Cách duy nhất để biết là thử và quan sát — của chính ngươi, hoặc của kẻ khác. Thử có thể giết ngươi.
Khi ngươi tin mình đã tìm ra, hãy ghi vào Sổ Luật. Không ai xác nhận đúng sai cho ngươi.
Bề ngoài của sự vật ở thế giới này không nói lên bản chất. Màu sắc, hình dạng, âm thanh được xáo lại mỗi lần thế giới sinh ra. Điều ngươi tin ở nơi khác có thể sai ở đây."""

COVENANT_SENTENCE = "Bề ngoài của sự vật ở thế giới này không nói lên bản chất."

_TERRAIN_VN: dict[str, str] = {
    Terrain.PLAIN: "đồng cỏ",
    Terrain.WATER: "ô nước",
    Terrain.BUSH: "bụi rậm",
    Terrain.ROCK: "mỏm đá",
    Terrain.FIRE: "lửa",
}

_PHASE_VN = {"DAY": "ngày", "NIGHT": "đêm"}
_WIND_VN = {"N": "bắc", "S": "nam", "E": "đông", "W": "tây"}


def _band(x: float, hi: float) -> str:
    """Mô tả định tính một tỉ lệ. Không đưa số — xem bất biến 3."""
    if hi <= 0:
        return "không rõ"
    r = x / hi
    if r >= 0.85:
        return "đầy"
    if r >= 0.6:
        return "khá"
    if r >= 0.35:
        return "vơi"
    if r >= 0.15:
        return "cạn"
    return "kiệt"


def body_line(tr: Traits) -> str:
    """Một câu mô tả cơ thể, sinh HOÀN TOÀN từ vector trait.

    Một chỗ duy nhất: khối E dùng nó, và [N-13] dùng đúng nó làm prompt cho
    MeshyAI. Viết bộ mô tả thứ hai là mở lại cửa cho hình và trait rời nhau —
    mà "hình = trait, chỉ trait" là bất biến 1 của N-13.
    """
    return (
        f"đầu óc {tr.brain} · tay {tr.attack} · giáp {tr.armor} · chân {tr.speed} · "
        f"giác quan {tr.sense} · bụng {tr.stomach}. "
        f"Nhìn xa {tr.sight_radius} ô, mỗi lượt đi được {tr.moves_per_tick} ô."
    )


# ─── SYSTEM ──────────────────────────────────────────────────────────────────

def system_block(c: Creature, persona: str, sm: SurfaceMap,
                 handbook: str = "", hunch: bool = False) -> str:
    """A + A2 + B + C + D — bất biến cả ván với cùng một cá thể.

    Chỉ đổi khi `c.traits.brain` đổi (B-13 dịch trait). Người gọi phải phát
    `PREFIX_INVALIDATED` khi đó — xem `PromptCache`.
    """
    tr = c.traits

    persona = (persona or "").strip()
    if len(persona) > law_config.PERSONA_MAX_CHARS:
        raise ValueError(
            f"persona dài {len(persona)} ký tự, trần là {law_config.PERSONA_MAX_CHARS}"
        )

    block_b = f"[LOÀI]\nNgươi thuộc loài {c.species}. {persona}".rstrip()

    # KHÔNG có khối C ở SYSTEM. Toàn bộ số đo cơ thể — brain luôn — nằm ở khối E.
    #
    # Đo thật (seed 1–5, 400 tick, 15 con): in `brain` ở SYSTEM làm prefix vỡ
    # 79–91 lần một ván, ~5.3 lần mỗi con — đúng ngưỡng thẻ B-02 §4 gọi là "ăn
    # hết throughput". Thủ phạm không phải W-11 mà là `reset_body`: chết thì cơ
    # thể về founder, brain đổi, prefix vỡ. Mà brain dao động chủ yếu trong
    # 4↔5 và 3↔4 — những cặp DÙNG CHUNG từ vựng, nên prompt lẽ ra không cần đổi
    # một byte nào. Giữ ở SYSTEM đúng thứ quyết định từ vựng, không hơn.

    vocab = vocab_for_brain(tr.brain)
    surfaces = ", ".join(sorted(sm.cls_to_surface.values()))
    lines = [
        "[TỪ VỰNG SỔ LUẬT]",
        "Một luật viết theo khuôn: KHI <việc xảy ra> [VÀ <hoàn cảnh>] THÌ <hệ quả>.",
        "việc xảy ra: " + ", ".join(t.value for t in vocab.triggers),
    ]
    if vocab.max_conds > 0:
        lines.append(
            f"hoàn cảnh (nhiều nhất {vocab.max_conds}): "
            + ", ".join(k.value for k in vocab.conds)
        )
    else:
        lines.append("hoàn cảnh: ngươi không phát biểu được hoàn cảnh nào.")
    lines.append("hệ quả: " + ", ".join(e.value for e in vocab.effects))
    lines.append("thứ có thể nhắc tới: " + surfaces + ", nước, xác chết, đồng loại, kẻ khác loài")
    # CƠ CHẾ, không phải lời khuyên. Thiếu dòng này thì agent biết nó "nên ghi
    # vào Sổ Luật" (khối A2 có nói) nhưng KHÔNG biết bằng cách nào — và cửa duy
    # nhất, trường `want_codex`, chỉ là một cái tên trơ trong schema.
    #
    # Đo thật với model đầu tiên chạy được (Qwen2.5-1.5B, seed 9, 200 tick):
    # 44 quyết định đọc được, `want_codex` bật **0 lần**, nên **0 CODEX_OP** và
    # điểm bằng 0 trên cả ba luật. Một trong các `note` nó tự viết là "nên ghi
    # vào sổ luật nếu bạn đã tìm ra sự thật đúng sai" — nó biết mình nên ghi, nó
    # chỉ không biết nút ở đâu. Phiếu B-10 dặn đúng thứ tự chẩn đoán, và dặn
    # thêm: **đừng chẩn đoán bằng cách đổi model.**
    lines.append(
        "Muốn ghi vào Sổ Luật thì đặt want_codex = true. Lượt sau ngươi sẽ được "
        "hỏi RIÊNG để phát biểu một luật và chọn ô ghi. Ghi sổ tốn sức, và sổ "
        "chỉ có vài ô — đầy thì muốn ghi mới phải xoá cũ."
    )
    # Cùng bài học, lần thứ hai — và lần này tôi đã biết trước mà vẫn quên.
    #
    # B-14 dựng cả cơ chế Linh cảm rồi thêm `want_hunch` vào schema, nhưng KHÔNG
    # nói ở đâu rằng nó là cánh cửa. Chạy thật (Qwen-7B, X-09, hai ván): model
    # nhắc tới `want_hunch` đúng **1 lần trên hơn 85 lời gọi**, và **`HUNCH_OP`
    # bằng 0** ở cả hai ván. Nhánh thí nghiệm của X-09 **không bao giờ chạy** —
    # tôi suýt để nó đo hai tiếng một thứ không xảy ra.
    #
    # Đúng nguyên văn chuyện đã xảy ra với `want_codex` (0/44 lượt, xem khối chú
    # thích ngay trên). Bài học không phải "nhớ thêm câu giải thích" mà là:
    # **một trường trong schema không tự nói nó dùng để làm gì.**
    if hunch:
        lines.append(
            "Muốn nêu một LINH CẢM thì đặt want_hunch = true. Lượt sau ngươi sẽ "
            "được hỏi RIÊNG để nói ra một điều ngươi NGHI — chưa cần tin. Linh "
            "cảm KHÔNG phải Sổ Luật: nó không được chấm điểm, không tốn ô sổ, và "
            "từ lúc nêu ra thì mỗi lần chuyện ấy đáng lẽ xảy ra ngươi sẽ được cho "
            "biết nó có xảy ra thật không — kể cả những lần không có gì. Nghi sai "
            "không mất gì."
        )
    block_d = "\n".join(lines)

    _check_no_leak(BLOCK_A, "khối A")
    _check_no_leak(BLOCK_A2, "khối A2")
    _check_no_leak(block_b, "khối B")
    _check_no_leak(block_d, "khối D", allow_dsl_names=True)

    parts = [BLOCK_A, BLOCK_A2, block_b, block_d]
    if handbook:
        # Cẩm nang vào SYSTEM, không vào USER: nó bất biến cả ván, nên đặt ở đây
        # thì prefix cache vẫn trúng. Đặt ở khối E là trả giá prefill cho một
        # thứ không bao giờ đổi.
        #
        # Vẫn qua `_check_no_leak`: cẩm nang do agent viết ở ván TRƯỚC, nên nó là
        # chữ của người khác đối với ván này. `handbook.sanitize_lesson` đã chặn
        # ở đầu vào; đây là lớp thứ hai, và nó rẻ.
        parts.append(_check_no_leak(handbook, "cẩm nang"))
    return "\n\n".join(parts)


# ─── USER ────────────────────────────────────────────────────────────────────

def user_block(
    c: Creature,
    world: World,
    tick_no: int,
    notes: FieldNotes | None,
    codex: Codex | None,
    heard: Sequence[str] = (),
    notepad: str = "",
    seen: Iterable[Creature] = (),
    hunches: Any = None,
) -> str:
    """E1..E5 — toàn bộ phần biến động, luôn đứng SAU system_block."""
    sm = world.surface_map
    x, y = world.wrap(*c.pos)
    terrain = _TERRAIN_VN.get(world.grid[y][x], "đất trống")

    tr = c.traits
    e1 = [
        "[TA]",
        "Cơ thể: " + body_line(tr),
        f"lượt {tick_no}, trời {_PHASE_VN.get(phase_at(tick_no), 'ngày')}, gió thổi về {_WIND_VN.get(world.wind, world.wind)}.",
        f"Ngươi đứng trên {terrain}. Máu {_band(c.hp, config.HP_MAX)}, "
        f"sức {_band(c.energy, tr.energy_max)}.",
    ]
    if c.poison_ticks > 0:
        e1.append("Trong người có gì đó đang cồn cào.")
    if c.stun_ticks > 0:
        e1.append("Ngươi choáng, chưa cử động được.")

    here = world.fruits.get((x, y))
    if here is not None:
        e1.append(f"Dưới chân có {sm.surface_of(here)}.")
    nearby = [
        f"{sm.surface_of(cls)} cách {world.dist(c.pos, p)} ô"
        for p, cls in sorted(world.fruits.items())
        if 0 < world.dist(c.pos, p) <= tr.sight_radius
    ]
    if nearby:
        e1.append("Thấy quả: " + "; ".join(nearby[:6]) + ".")

    others = [
        f"{o.id} ({'đồng loại' if o.species == c.species else 'khác loài'}) cách {world.dist(c.pos, o.pos)} ô"
        for o in seen
    ]
    e1.append("Thấy: " + ("; ".join(others) if others else "không có ai") + ".")

    notes_txt = notes.render(law_config.EVENTS_BY_BRAIN[tr.brain]) if notes else ""
    e2 = "[SỔ TAY]\n" + (notes_txt or "trống.")

    if codex is not None and any(e is not None for e in codex.entries()):
        rows = [
            f"[{i}] {to_vietnamese(e.law, sm)} (tin: {e.conf}, từ: {e.source})"
            for i, e in enumerate(codex.entries())
            if e is not None
        ]
        e3 = "[SỔ LUẬT CỦA TA]\n" + "\n".join(rows)
    else:
        e3 = "[SỔ LUẬT CỦA TA]\ntrống."

    # `heard` và `notepad` là chữ do MODEL hoặc CLIENT viết. Làm sạch ở ĐÂY, một
    # chỗ, thay vì tin mọi người gọi đều nhớ làm.
    #
    # Lỗi này đã xuất hiện ba lần ở ba đường khác nhau — lời nói (B-11), ghi chú
    # riêng, và persona — nên nó không phải ba lỗi mà là một chỗ hở trong thiết
    # kế: `_check_no_leak` **ném**, và ném là đúng cho phần server tự dựng
    # (bề mặt, sổ tay, sổ luật), nhưng với chữ của người khác thì ném nghĩa là
    # **họ làm gãy ván của ta**. Chữ của người khác phải được VÔ HIỆU HOÁ, còn
    # ném để dành cho lỗi của chính ta.
    from genesis.speech import sanitize_free_text

    heard_clean = [sanitize_free_text(h, 200) for h in heard]
    pad_clean = sanitize_free_text(notepad, law_config.NOTEPAD_MAX_CHARS)
    e4 = "[NGHE ĐƯỢC]\n" + ("\n".join(heard_clean) if heard_clean else "chưa nghe ai nói gì.")
    e5 = "[GHI CHÚ RIÊNG]\n" + (pad_clean or "trống.")

    # E6 — linh cảm (B-14). Rỗng thì KHÔNG thêm khối nào: ván không bật linh
    # cảm phải dựng ra đúng cùng một prompt như trước, tới từng ký tự, nếu không
    # thì `prompt_hash` lệch và mọi log cũ mất giá trị huấn luyện.
    e6 = hunches.render(sm) if hunches is not None else ""
    blocks = ["\n".join(e1), e2, e3, e4, e5]
    if e6:
        blocks.insert(3, e6)      # ngay dưới Sổ Luật, trên [NGHE ĐƯỢC]
    out = "\n\n".join(blocks)
    return _check_no_leak(out, "khối E")


# ─── Cache prefix ────────────────────────────────────────────────────────────

class PromptCache:
    """Giữ system_block theo creature_id và phát hiện lúc prefix vỡ.

    Bẫy B-02 §4: `brain` dịch được giữa ván (B-13) → khối D đổi → cache vỡ.
    Chấp nhận được, nhưng phải log `PREFIX_INVALIDATED`. Nhiều hơn ~5 lần/ván
    thì tần suất dịch trait đang ăn hết throughput.
    """

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self.invalidations: int = 0

    def get(
        self,
        c: Creature,
        persona: str,
        sm: SurfaceMap,
        tick_no: int = 0,
        log=None,
        handbook: str = "",
        hunch: bool = False,
    ) -> str:
        text = system_block(c, persona, sm, handbook=handbook, hunch=hunch)
        old = self._cache.get(c.id)
        if old is not None and old != text:
            self.invalidations += 1
            if log is not None:
                log.write(
                    tick_no,
                    "PREFIX_INVALIDATED",
                    creature_id=c.id,
                    species_id=c.species,
                    brain=c.traits.brain,
                    n=self.invalidations,
                )
        self._cache[c.id] = text
        return text
