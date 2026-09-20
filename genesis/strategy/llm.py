"""Genesis Zero — genesis/strategy/llm.py
Hiện thực chiến lược LLM cục bộ (LlmStrategist) và các tiện ích kết nối mô hình.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import httpx

from genesis import config, law_config, speech
from genesis.codex import Codex
from genesis.fieldnotes import FieldNotes, Note
from genesis.lawdsl import Law, to_json
from genesis.lineage import forget_on_death
from genesis.llm_client import CircuitBreaker, ask
from genesis.minds import Minds
from genesis.prompt import _TERRAIN_VN, PromptCache, prompt_hash, user_block
from genesis.provenance import law_key
from genesis.reflex import ActiveGoal, choose_goal
from genesis.reveal import law_from_surface_dict
from genesis.strategy.base import payload_to_goal
from genesis.strategy.law_schema import schema_for
from genesis.traits import Traits
from genesis.validate import (
    Verdict,
    validate_codex,
    validate_decide,
    validate_hunch,
    validate_shift,
)
from genesis.world import phase_at

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.world import World


# ─── B-05: ghép LLM vào vòng tick ────────────────────────────────────────────

_OUTCOME_VN: dict[str, str] = {
    # Agent phải SUY RA hệ quả từ cảm giác, nên sổ tay ghi cảm giác chứ không ghi
    # tên hệ quả. `sanitize_outcome` chặn tên enum, nhưng chặn xong mà để lại
    # "[ẩn]" thì sổ tay vô dụng — phải dịch sang thứ quan sát được ngay từ đây.
    "DAMAGE": "máu tụt hẳn xuống",
    "HEAL": "vết thương liền lại",
    "ENERGY_GAIN": "thấy khoẻ hẳn ra",
    "ENERGY_DRAIN": "sức rút đi rất nhanh",
    "POISON": "trong người cồn cào, máu cứ tụt dần",
    "STUN": "cứng đờ, không nhúc nhích được",
    "TELEPORT": "chớp mắt đã đứng ở chỗ khác",
}


_PHASE_NOTE = {"DAY": "ngày", "NIGHT": "đêm"}
_BAND_NOTE = {"LOW": "thấp", "MID": "vừa", "HIGH": "cao"}
# Phải phủ HẾT TriggerKind. Thiếu tên nào thì đường rơi về `k.lower()` in ra
# nguyên tên enum ("low_energy", "phase_enter") giữa một câu tiếng Việt — vừa lạc
# giọng vừa là một mẩu từ vựng nội bộ rò ra chỗ không nên có.
_RECENT_NOTE = {
    "EAT": "ăn", "DRINK": "uống nước", "ATTACK": "đánh", "HIT_BY": "trúng đòn",
    "STEP_ON": "bước đi", "REST": "đứng yên", "SPEAK": "lên tiếng",
    "ADJACENT": "có kẻ đứng cạnh", "DEATH_NEAR": "thấy kẻ chết",
    "PHASE_ENTER": "trời đổi", "LOW_ENERGY": "kiệt sức",
}


def ctx_to_pairs(ctx, brain: int) -> tuple[tuple[str, str], ...]:
    """Ngữ cảnh của một dòng sổ tay, theo ĐÚNG các chiều mà DSL hỏi được.

    Đây là chỗ quyết định đề bài có giải được hay không, và bản đầu làm hỏng nó.
    Nó ghi ba thứ — pha, địa hình, hướng gió tuyệt đối — trong khi `CondKind` có
    mười: PHASE, TERRAIN, HP, ENERGY, RECENT, COUNT, AGE, WIND, SUBJECT, ALONE.
    Đọc thật một cuốn sổ như thế (seed 9): luật là `KHI năng lượng dưới 25% THÌ
    chịu sát thương`, mà sổ không có lấy một chữ về năng lượng — nên "máu tụt hẳn
    xuống" hiện ra như chuyện ngẫu nhiên, và **không ai**, model hay người, suy
    ra nổi. Ngữ cảnh sổ tay phải phủ đúng không gian giả thuyết, không hơn không
    kém: thiếu chiều nào thì luật dùng chiều ấy là câu đố không có lời giải.

    Cắt theo `brain` giống khối D: con không phát biểu được `COUNT` thì đọc số
    hàng xóm cũng chỉ là nhiễu chiếm chỗ trong context.
    """
    out: list[tuple[str, str]] = [
        ("pha", _PHASE_NOTE.get(ctx.phase, "ngày")),
        ("địa hình", _TERRAIN_VN.get(ctx.terrain, "đất trống")),
        ("máu", _BAND_NOTE.get(ctx.hp_band, "?")),
        ("sức", _BAND_NOTE.get(ctx.energy_band, "?")),
    ]
    if brain <= 1:
        return tuple(out)

    out.append(("", "một mình" if ctx.alone else "có kẻ bên cạnh"))
    out.append(("gió", "thuận" if ctx.wind_rel == "WITH" else "ngược"))
    same = ctx.counts.get("SAME_SP", {}).get(1, 0)
    other = ctx.counts.get("OTHER_SP", {}).get(1, 0)
    out.append(("cạnh", f"{same} cùng {other} khác"))
    if brain <= 3:
        return tuple(out)

    out.append(("tuổi", "trẻ" if ctx.age_band == "YOUNG" else "già"))
    recent = sorted(ctx.recent.items(), key=lambda kv: (kv[1], kv[0]))[:1]
    # Luôn ghi mục "vừa", kể cả khi chưa làm gì: để trống thì model học "có mục
    # này = có chuyện", một tương quan giả do chính tầng định dạng tạo ra
    # (B-07 bất biến 2).
    out.append(("vừa", ", ".join(
        f"{_RECENT_NOTE.get(k, '?')} {v} lượt trước" for k, v in recent
    ) or "chưa làm gì"))
    return tuple(out)


# Lời nhắc ngắn ghép vào CUỐI khối E cho từng loại lời gọi. Đặt ở cuối vì mọi thứ
# đứng trước phải giữ nguyên từng byte (B-02 bất biến 1) — chèn vào giữa là vỡ cache.
_CLAIM_TAIL = {
    "decide": "",
    "shift": (
        "\n\n[DỊCH CƠ THỂ]\nNgươi đã tích đủ để đổi cơ thể một điểm. Lấy một điểm "
        "từ chỗ nào, dồn vào chỗ nào? Chỗ lấy phải còn ít nhất 1, chỗ dồn phải "
        "chưa đầy. Nói ngắn vì sao."
    ),
    "codex": (
        "\n\n[GHI SỔ LUẬT]\nNgươi đã xin ghi sổ. Hãy phát biểu MỘT luật ngươi tin là "
        "thật, theo khuôn KHI ... THÌ ..., và chọn ô để ghi. Không ai nói cho ngươi "
        "biết đúng hay sai."
    ),
    # Câu này phải nói rõ ba điều, vì cả ba đều trái trực giác: linh cảm KHÔNG
    # được chấm, nó KHÔNG cần đúng, và thế giới sẽ ĐẾM HỘ. Thiếu điều thứ ba thì
    # model coi ô linh cảm như một ô Sổ Luật hạng hai và chỉ ghi vào đó thứ nó
    # đã tin — tức là xoá sạch lý do cơ chế này tồn tại.
    # Ba câu cuối là ba LUẬT CHƠI chỉ tồn tại trong code cho tới khi được viết ra
    # đây, và đo được là model không đoán ra cái nào:
    #
    #   · ghi đè một ô **xoá sạch bảng đếm** của ô ấy. Model ghi đè 3–4 lần mỗi
    #     200 tick, nên 23 ô linh cảm chỉ tích được **3 lượt thử** — giá trị cốt
    #     lõi của B-14 chưa một lần được giao.
    #   · giả thuyết càng nhiều điều kiện càng **hiếm được thử**: trigger và mọi
    #     cond phải cùng khớp. Model viết 2 điều kiện là chuyện thường.
    #   · bảng đếm cần THỜI GIAN. "Chưa thử lần nào" nghĩa là hãy chờ, không
    #     nghĩa là đoán sai.
    #
    # Đây là lần thứ ba trong dự án phải viết ra một luật vốn chỉ nằm trong code
    # (trước đó: `want_codex`, `want_hunch`). Xem [09-HO-LOI](../docs/09-HO-LOI.md) họ 2.
    "hunch": (
        "\n\n[LINH CẢM]\nĐây KHÔNG phải Sổ Luật và nó không được chấm điểm. Hãy nêu "
        "một điều ngươi NGHI, chưa cần tin. Từ giờ mỗi lần chuyện ấy đáng lẽ xảy "
        "ra, ngươi sẽ được cho biết nó có xảy ra thật không — kể cả những lần "
        "không có gì. Nghi sai không mất gì; nghi thứ ngươi đã chắc thì phí ô.\n"
        "Ba điều nên biết trước khi chọn ô:\n"
        "- Ghi đè lên một ô sẽ XOÁ SẠCH bảng đếm của ô đó. Muốn giữ một linh cảm "
        "đang được đếm thì hãy chọn ô TRỐNG, hoặc ô mà ngươi thấy đã sai.\n"
        "- Càng NHIỀU điều kiện thì càng HIẾM được thử: phải khớp cả trigger lẫn "
        "mọi điều kiện mới tính một lượt. Nêu ít điều kiện thì ngươi biết kết quả "
        "sớm hơn.\n"
        "- 'chưa thử lần nào' nghĩa là hãy CHỜ, không nghĩa là ngươi đoán sai."
    ),
}


def _budget(traits: Traits, kind: str) -> int:
    """Trần `n_predict` cho một lượt gọi.

    Cộng `TOKEN_JSON_HEADROOM`: `token_budget` là ngân sách **kinh tế** (tính
    tiền theo token THỰC SINH, B-05 bất biến 3), không phải một cái kéo cắt giữa
    câu. Cắt đúng ngân sách thì JSON đứt và **cả lượt gọi mất trắng** — đo thật:
    6/35 lời gọi hỏng vì thế, tức 17% trong khi ngưỡng là 1%. Người trả lời dài
    vẫn trả tiền cho phần dài; chỉ là cấu trúc được phép đóng lại.
    """
    if kind == "codex":
        # Đệm GẤP BA cho lượt ghi sổ. Payload của nó là một cây JSON lồng ba
        # tầng (trigger / conds / effect), và llama.cpp sinh JSON **có xuống
        # dòng và thụt lề** — khoảng trắng ăn token thật.
        #
        # Đo trực tiếp (Qwen2.5-1.5B, 10 lượt mỗi loại): `decide` dùng nhiều nhất
        # 106 token, `shift` 95, còn `codex` chạm đúng trần 200 và **đứt giữa
        # trường `effect`**. Đó là toàn bộ 3/13 lượt hỏng của ván thật — không
        # phải model kém, mà là cái kéo đặt sai chỗ.
        base = law_config.CLAIM_BUDGET_BY_BRAIN[traits.brain]
        return base + 3 * config.TOKEN_JSON_HEADROOM
    if kind == "hunch":
        # Cùng hình dạng JSON với `codex` (cây ba tầng), nên cùng headroom —
        # thiếu nó thì linh cảm đứt giữa trường `effect` y hệt lỗi đã đo ở
        # `codex`, và triệu chứng lại là "model không chịu nêu giả thuyết".
        base = law_config.CLAIM_BUDGET_BY_BRAIN[traits.brain]
        return base + 3 * config.TOKEN_JSON_HEADROOM
    if kind == "oracle":
        # Ngân sách theo SỐ CÂU HỎI, không theo brain. Tất cả đều bị hỏi đúng
        # `ORACLE_QUERIES` câu, nên cấp theo `token_budget` là cấp theo một đại
        # lượng chẳng liên quan gì tới độ dài câu trả lời.
        #
        # Đo: một đáp án `{"q":0,"effect":{"kind","mag","dur"}}` in kèm xuống
        # dòng và thụt lề tốn ~30 token, nên 8 câu tốn ~337. Bản cũ hard-code
        # `CLAIM_BUDGET_BY_BRAIN * 2` ngay trong `oracle_run`, cho L1 **208** và
        # L5 **48** — thiếu 1,6 lần và 7 lần. Hậu quả đúng như mọi lần trước:
        # hỏng IM LẶNG. `pred_acc` ra **đúng 0.000 trên cả 65 dòng, cả 5 loài,
        # cả hai seed** — phương sai bằng không, thứ không một model nào tạo ra
        # được, nhưng nó đọc y hệt "model không tiên đoán được".
        return (law_config.ORACLE_QUERIES * config.TOKEN_PER_ORACLE_ANSWER
                + config.TOKEN_JSON_HEADROOM)
    base = max(48, traits.token_budget // 2) if kind == "shift" else traits.token_budget
    return base + config.TOKEN_JSON_HEADROOM


class LlmStrategist:
    """Tầng chiến lược gọi model cục bộ (B-05).

    Bốn bất biến của phiếu B-05 §2:

    1. LLM trả **goal**, không trả nước đi; tầng phản xạ vẫn chạy mọi tick.
       Gọi model mỗi tick cho mỗi con là hiểu sai kiến trúc.
    2. Gọi khi `tick % think_interval == offset`, offset **rải đều** giữa các cá
       thể cùng loài — cùng tổng tải, không dồn cục.
    3. Trừ `cost_think` theo **số token thực sinh**, không theo `max_tokens`.
    4. `Strategist` là Protocol; đây là một trong ba hiện thực.

    Bẫy §3: thu hết kết quả LLM rồi **mới** sang pha resolve. Vì thế lớp này
    tách làm hai nhịp — `begin_tick` bắn cả đàn bằng `asyncio.gather` và giữ kết
    quả lại, `decide` chỉ tra bảng và không chạm mạng. Áp goal ngay lúc nó về,
    giữa pha thu intent, là phá bất biến đồng thời của W-11.
    """

    def __init__(
        self,
        base_url: str,
        creature_ids: Iterable[str],
        personas: dict[str, str] | None = None,
        log: Any = None,
        timeout: float = law_config.LLM_TIMEOUT_S,
        transport: Any = None,
    ) -> None:
        ids = sorted(creature_ids, key=lambda cid: (cid.rpartition(":")[0], int(cid.rpartition(":")[2])))
        # Bất biến 2 của B-03: một creature_id giữ NGUYÊN một slot suốt ván.
        # Slot đổi là prefix cache của llama-server mất trắng.
        # Kiểm URL NGAY lúc dựng, không để tới lúc gọi. `ask` nuốt lỗi và trả None
        # theo bất biến 3 của B-03, nên một URL gõ sai sẽ thành 400 lượt chạy phản
        # xạ trông rất bình thường — hỏng im lặng, kiểu tệ nhất.
        if not str(base_url).startswith(("http://", "https://")):
            raise ValueError(f"base_url phải bắt đầu bằng http:// hoặc https://, nhận {base_url!r}")
        self.base_url = base_url
        self.slots: dict[str, int] = {cid: i for i, cid in enumerate(ids)}
        # Số chỗ THẬT của server, dò một lần ở lời gọi đầu (`/props.total_slots`).
        # `None` = chưa dò. Xem `_ensure_slots`.
        self._n_slots: int | None = None
        # Hạn chờ TỰ HIỆU CHỈNH theo model đang cắm. `None` = chưa đo.
        self._call_ms: float | None = None
        self.personas: dict[str, str] = dict(personas or {})
        self.log = log
        self.timeout = timeout
        self.transport = transport
        self.cache = PromptCache()
        self.breaker = CircuitBreaker()
        # Trí nhớ và tầng xã hội nằm ở `Minds` — MỘT bản, chế độ mở dùng chung.
        # Xem `genesis/minds.py` về vì sao: năm lần đường mạng thiếu thứ đường
        # cục bộ có, và bản nào ít người nhìn hơn thì bản ấy mục.
        self.minds = Minds()
        self.notepad: dict[str, str] = self.minds.notepad
        self._pending: dict[str, ActiveGoal] = {}
        # CLAIM hai pha (B-08 bất biến 2): `want_codex` là 1–2 token trong quyết
        # định thường, con nào cũng gánh được; lượt ghi sổ là một lời gọi RIÊNG ở
        # tick sau, có ngân sách riêng. Nhồi cả hai vào một schema thì L5 với 32
        # token không bao giờ tham gia được vào phần được chấm.
        self._want_codex: set[str] = self.minds.want_codex
        # B-13: con nào đã tích đủ điểm thích nghi thì lượt nghĩ kế tiếp dùng để
        # CHỌN HƯỚNG DỊCH. Gọi riêng, không nhét vào schema quyết định thường —
        # cùng lý do với CLAIM hai pha: nhồi vào một schema thì con 32 token
        # không bao giờ tham gia được.
        self.want_shift: set[str] = set()
        self.shift_choice: dict[str, tuple[str, str]] = {}
        self.shift_why: dict[str, str | None] = {}
        # `creature_id -> adapt_points lúc đã hỏi`. Nếu không có bảng này thì một
        # câu trả lời sai làm con vật hỏi lại **mãi mãi**: `take_shift` xếp hàng
        # mỗi tick còn `adapt_points` chưa tiêu, nên từ đó trở đi MỌI lượt nghĩ
        # của nó đổ vào một câu hỏi nó liên tục trả lời sai. Đo thật ở seed 44:
        # L1:0 hỏi hướng dịch 8 lượt liên tiếp từ t=60 tới t=81 và không quyết
        # định nào khác được đưa ra nữa. Phiếu nói rõ "sai thì bỏ lượt, KHÔNG
        # thử lại" — bảng này là cách "không thử lại" được thi hành.
        self._shift_asked: dict[str, int] = {}
        # Cẩm nang theo LOÀI, sống qua nhiều ván (W-16). Rỗng thì `system_block`
        # không thêm gì — mọi ván cũ chạy y hệt.
        self.handbooks: dict[str, str] = self.minds.handbooks
        self._pending_say: dict[str, speech.Say] = {}
        self.reputation: dict[str, speech.Reputation] = self.minds.reputation
        self.ledger = self.minds.ledger
        self.offers: dict[str, list[tuple[str, Law, bool]]] = self.minds.offers
        self.teach_events: list = self.minds.teach_events
        self.stats: dict[str, int] = {
            "call": 0, "miss": 0, "semantic_fail": 0, "skipped_open": 0,
            "codex_ok": 0, "codex_bad": 0, "hunch_ok": 0, "hunch_bad": 0,
        }

    # ── bộ nhớ mỗi cá thể ────────────────────────────────────────────────
    # Uỷ quyền sang `Minds`. Giữ nguyên tên cũ để không phải sửa 550 bài test —
    # và quan trọng hơn: để không có BẢN SAO nào, chỉ có một chỗ giữ sự thật.
    @property
    def notes(self) -> dict[str, FieldNotes]:
        return self.minds.notes

    @property
    def codices(self) -> dict[str, Codex]:
        return self.minds.codices

    @property
    def heard(self) -> dict[str, list[str]]:
        return self.minds.heard

    def notes_of(self, c: Creature) -> FieldNotes:
        return self.minds.notes_of(c)

    def codex_of(self, c: Creature) -> Codex:
        return self.minds.codex_of(c)

    @staticmethod
    def offset_of(c: Creature) -> int:
        """Rải đều trong loài: con thứ n lệch pha n bước.

        Không rải thì cả đàn cùng nghĩ ở đúng một tick, model nhận 15 yêu cầu
        một lúc rồi im 3 tick — cùng tổng tải, gấp mấy lần độ trễ đuôi.
        """
        return int(c.id.rpartition(":")[2]) % max(1, c.traits.think_interval)

    def is_due(self, c: Creature, tick_no: int) -> bool:
        return tick_no % c.traits.think_interval == self.offset_of(c)

    def build_prompt(
        self, c: Creature, world: World, seen: list[Creature], tick_no: int
    ) -> tuple[str, str]:
        """Dùng chung cho gọi thật và cho replay — replay so hash của CHÍNH nó.

        Đặt `world.phase` ngay tại đây, và đó là chỗ ĐÚNG để đặt nó.
        """
        world.phase = phase_at(tick_no)
        from genesis.weather import weather_at
        world.weather = weather_at(getattr(world, "seed", 0), tick_no)
        system = self.cache.get(
            c, self.personas.get(c.species, ""), world.surface_map, tick_no, self.log,
            handbook=self.handbooks.get(c.species, ""),
            hunch=self.minds.hunch_enabled,
        )
        user = user_block(
            c, world, tick_no,
            self.notes_of(c), self.codex_of(c),
            heard=self.heard.get(c.id, ()),
            notepad=self.notepad.get(c.id, ""),
            seen=seen,
            hunches=self.minds.hunches.get(c.id) if self.minds.hunch_enabled else None,
        )
        return system, user

    # ── nhịp 1: bắn cả đàn ───────────────────────────────────────────────
    async def _ensure_slots_for(self, base_url: str, transport) -> int:
        """`_ensure_slots` nhưng tự mở client — cho đường gọi ngoài `think`."""
        if self._n_slots is not None:
            return self._n_slots
        async with httpx.AsyncClient(timeout=30.0, transport=transport) as c:
            return await self._ensure_slots(c)

    async def _ensure_slots(self, client: httpx.AsyncClient) -> int:
        """Số chỗ song song của server, dò một lần rồi nhớ."""
        if self._n_slots is not None:
            return self._n_slots
        n = law_config.LLM_PARALLEL_FALLBACK
        try:
            resp = await client.get(self.base_url.rstrip("/") + "/props")
            if resp.status_code == 200:
                n = int(resp.json().get("total_slots") or n)
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            pass        # server không nói thì dùng mặc định — đừng làm hỏng ván
        n = max(1, n)
        self._n_slots = n
        return n

    async def think(self, creatures: list[Creature], world: World, tick_no: int) -> None:
        from genesis.creature import creature_sort_key
        from genesis.world import visible

        self._pending.clear()
        if self.breaker.is_open_at(tick_no):
            self.stats["skipped_open"] += 1
            return

        due = [
            c for c in sorted(creatures, key=creature_sort_key)
            if c.alive and c.id in self.slots and self.is_due(c, tick_no)
        ]
        if not due:
            return

        jobs = []
        for c in due:
            system, user = self.build_prompt(c, world, visible(c, world, creatures), tick_no)
            ready = tick_no - self.codex_of(c).last_claim >= law_config.CLAIM_COOLDOWN
            hunch_ready = (
                self.minds.hunch_enabled
                and c.id in self.minds.want_hunch
                and tick_no - self.minds.hunch_last_write(c.id) >= law_config.HUNCH_COOLDOWN
            )
            if c.id in self.want_shift:
                kind = "shift"
            elif c.id in self._want_codex and ready:
                kind = "codex"
            elif hunch_ready:
                kind = "hunch"
            else:
                kind = "decide"
            jobs.append((c, kind, system, user, prompt_hash(system, user),
                         [o.id for o in visible(c, world, creatures)]))

        n_slots = self._n_slots or law_config.LLM_PARALLEL_FALLBACK
        waves = max(1, -(-len(jobs) // max(1, n_slots)))
        timeout = max(self.timeout, 3.0 * (self._call_ms or 0.0) / 1000.0) * waves
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            n = await self._ensure_slots(client)
            gate = asyncio.Semaphore(n)

            async def _one(c, kind, system, user, tg):
                async with gate:
                    return await ask(
                        self.base_url, self.slots[c.id] % n,
                        system, user + _CLAIM_TAIL[kind],
                        _budget(c.traits, kind),
                        schema_for(c.traits, kind, targets=tg, sm=world.surface_map,
                                   hunch=self.minds.hunch_enabled),
                        client=client,
                    )

            t0 = time.perf_counter()
            results = await asyncio.gather(*[
                _one(c, kind, system, user, tg)
                for c, kind, system, user, _, tg in jobs
            ])
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
            if any(r is not None for r in results):
                per_wave = elapsed_ms / waves
                self._call_ms = (per_wave if self._call_ms is None
                                 else 0.7 * self._call_ms + 0.3 * per_wave)

        for (c, kind, _system, _user, phash, _tg), r in zip(jobs, results):
            if kind == "shift":
                self.want_shift.discard(c.id)
                self._absorb_shift(c, tick_no, phash, r, elapsed_ms)
            elif kind == "codex":
                self._want_codex.discard(c.id)
                self._absorb_codex(c, world, tick_no, phash, r, elapsed_ms)
            elif kind == "hunch":
                self.minds.want_hunch.discard(c.id)
                self._absorb_hunch(c, world, tick_no, phash, r, elapsed_ms)
            else:
                self._absorb(c, world, creatures, tick_no, phash, r, elapsed_ms)

    def _absorb(self, c, world, creatures, tick_no, phash, r, elapsed_ms) -> None:
        from genesis.world import visible

        if r is None:
            self.breaker.record(False, tick_no)
            self.stats["miss"] += 1
            self._write(tick_no, "LLM_MISS", c, prompt_hash=phash, ms=elapsed_ms)
            return
        self.breaker.record(True, tick_no)

        tokens = int(r["n"])
        cost = round(tokens / config.TOKENS_PER_ENERGY, 4)
        c.energy -= cost
        self.stats["call"] += 1
        self._write(
            tick_no, "LLM_CALL", c,
            prompt_hash=phash, raw=r["raw"],
            tokens_used=tokens, cost_think=cost, ms=elapsed_ms,
            think_interval=c.traits.think_interval, offset=self.offset_of(c),
        )

        verdict = validate_decide(r["json"], c, world, visible(c, world, creatures))
        if not verdict.ok:
            self.stats["semantic_fail"] += 1
            self._write(tick_no, "LLM_SEMANTIC_FAIL", c, reason=verdict.reason)
            return

        goal = payload_to_goal(r["json"])
        if goal is not None:
            self._pending[c.id] = goal
            for rep in self.reputation.values():
                rep.observe_goal(c.id, goal.goal.value, tick_no)
        note = r["json"].get("note")
        if isinstance(note, str) and note.strip():
            self.notepad[c.id] = speech.sanitize_free_text(
                note, law_config.NOTEPAD_MAX_CHARS
            )
        if r["json"].get("want_codex"):
            self._want_codex.add(c.id)
        if r["json"].get("want_hunch"):
            self.minds.want_hunch.add(c.id)
        say = speech.Say.parse(r["json"].get("say"))
        if say is not None:
            self._pending_say[c.id] = say

    def rep_of(self, cid: str) -> speech.Reputation:
        return self.minds.rep_of(cid)

    def take_says(self) -> dict[str, speech.Say]:
        """Lấy VÀ xoá hàng chờ nói. Vòng tick gọi đúng một lần mỗi tick."""
        out, self._pending_say = self._pending_say, {}
        return out

    def _absorb_codex(self, c, world, tick_no, phash, r, elapsed_ms) -> None:
        if r is None:
            self.breaker.record(False, tick_no)
            self.stats["miss"] += 1
            self._write(tick_no, "LLM_MISS", c, prompt_hash=phash, ms=elapsed_ms, kind_asked="codex")
            return
        self.breaker.record(True, tick_no)
        tokens = int(r["n"])
        cost = round(tokens / config.TOKENS_PER_ENERGY, 4) + law_config.COST_CLAIM
        c.energy -= cost
        self.stats["call"] += 1
        self._write(
            tick_no, "LLM_CALL", c, prompt_hash=phash, raw=r["raw"],
            tokens_used=tokens, cost_think=cost, ms=elapsed_ms, kind_asked="codex",
            think_interval=c.traits.think_interval, offset=self.offset_of(c),
        )

        payload = r["json"]
        cx = self.codex_of(c)
        verdict = validate_codex(payload, c, world.surface_map, tick_no, cx.last_claim)
        law = None
        if verdict.ok and payload.get("law") is not None:
            try:
                law = law_from_surface_dict(payload["law"], world.surface_map)
            except (KeyError, ValueError, TypeError) as exc:
                verdict = Verdict(ok=False, reason=f"CODEX_MALFORMED_LAW:{type(exc).__name__}")
        if verdict.ok:
            verdict = cx.apply(
                payload.get("op", "SET"), int(payload.get("slot", 0)), law,
                int(payload.get("conf", 3)), tick_no,
            )

        if verdict.ok and law is not None:
            key = law_key(law)
            self.ledger.learn(c.id, key, tick_no)
            self.ledger.award(c.id, key, tick_no)
        self.stats["codex_ok" if verdict.ok else "codex_bad"] += 1
        self._write(
            tick_no, "CODEX_OP", c,
            ok=verdict.ok, reason=verdict.reason,
            op=payload.get("op"), slot=payload.get("slot"), conf=payload.get("conf"),
            law=to_json(law) if law is not None else None,
        )

    def _absorb_hunch(self, c, world, tick_no, phash, r, elapsed_ms) -> None:
        """Ghi một linh cảm (B-14). Không `Ledger`, không điểm, không danh tiếng."""
        if r is None:
            self.breaker.record(False, tick_no)
            self.stats["miss"] += 1
            self._write(tick_no, "LLM_MISS", c, prompt_hash=phash, ms=elapsed_ms,
                        kind_asked="hunch")
            return
        self.breaker.record(True, tick_no)
        tokens = int(r["n"])
        cost = round(tokens / config.TOKENS_PER_ENERGY, 4)
        c.energy -= cost
        self.stats["call"] += 1
        self._write(
            tick_no, "LLM_CALL", c, prompt_hash=phash, raw=r["raw"],
            tokens_used=tokens, cost_think=cost, ms=elapsed_ms, kind_asked="hunch",
            think_interval=c.traits.think_interval, offset=self.offset_of(c),
        )

        payload = r["json"]
        hb = self.minds.hunch_of(c)
        verdict = validate_hunch(payload, c, world.surface_map, tick_no, hb.last_write)
        law = None
        if verdict.ok and payload.get("law") is not None:
            try:
                law = law_from_surface_dict(payload["law"], world.surface_map)
            except (KeyError, ValueError, TypeError) as exc:
                verdict = Verdict(ok=False, reason=f"HUNCH_MALFORMED_LAW:{type(exc).__name__}")
        if verdict.ok:
            verdict = hb.apply(payload.get("op", "SET"), int(payload.get("slot", 0)),
                               law, tick_no)
        self.stats["hunch_ok" if verdict.ok else "hunch_bad"] += 1
        self._write(
            tick_no, "HUNCH_OP", c,
            ok=verdict.ok, reason=verdict.reason,
            op=payload.get("op"), slot=payload.get("slot"),
            law=to_json(law) if law is not None else None,
        )

    def begin_tick(self, creatures: list[Creature], world: World, tick_no: int) -> None:
        """Cầu nối đồng bộ cho `genesis.run`. Server (track N) gọi `think` thẳng."""
        asyncio.run(self.think(creatures, world, tick_no))

    # ── nhịp 2: tra bảng, không chạm mạng ────────────────────────────────
    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        g = self._pending.pop(c.id, None)
        if g is not None:
            return g
        if current is not None and current.ttl > 0:
            return None
        if rng is None:
            rng = random.Random(0)
        return choose_goal(c, world, seen, rng)

    def _absorb_speech(self, tick_no, world, by_id, speak_events) -> None:
        self.minds.absorb_speech(tick_no, world, by_id, speak_events)

    def _absorb_shift(self, c, tick_no, phash, r, elapsed_ms) -> None:
        """Hướng dịch trait do chính LLM của con đó chọn (B-13)."""
        if r is None:
            self.breaker.record(False, tick_no)
            self._write(tick_no, "LLM_MISS", c, prompt_hash=phash, kind_asked="shift")
            return
        self.breaker.record(True, tick_no)
        tokens = int(r["n"])
        c.energy -= round(tokens / config.TOKENS_PER_ENERGY, 4)
        self._write(tick_no, "LLM_CALL", c, prompt_hash=phash, raw=r["raw"],
                    tokens_used=tokens, cost_think=round(tokens / config.TOKENS_PER_ENERGY, 4),
                    ms=elapsed_ms, kind_asked="shift",
                    think_interval=c.traits.think_interval, offset=self.offset_of(c))

        verdict = validate_shift(r["json"], c)
        if not verdict.ok:
            self.stats["semantic_fail"] += 1
            self._write(tick_no, "LLM_SEMANTIC_FAIL", c, reason=verdict.reason,
                        kind_asked="shift")
            return
        why = r["json"].get("why")
        self.shift_choice[c.id] = (r["json"]["from"], r["json"]["to"])
        self.shift_why[c.id] = str(why)[:80] if isinstance(why, str) else None

    def take_shift(self, c) -> tuple[str, str] | None:
        """Vòng tick lấy hướng đã chọn. Chưa hỏi thì xin đúng MỘT lượt nghĩ."""
        got = self.shift_choice.pop(c.id, None)
        if got is not None:
            self._shift_asked.pop(c.id, None)
            return got
        if self._shift_asked.get(c.id) == c.adapt_points:
            return None          # đã hỏi ở đúng mức điểm này và hỏng: bỏ lượt
        self._shift_asked[c.id] = c.adapt_points
        self.want_shift.add(c.id)
        return None

    def _write(self, tick_no: int, kind: str, c: Creature, **fields: Any) -> None:
        if self.log is not None:
            self.log.write(tick_no, kind, creature_id=c.id, species_id=c.species, **fields)

    # ── sổ tay ───────────────────────────────────────────────────────────
    def observe(
        self,
        tick_no: int,
        world: World,
        creatures: list[Creature],
        events: dict[str, Any],
        state: Any = None,
    ) -> None:
        """Ghi sổ tay từ sự kiện có thật của tick vừa rồi (B-07 §nạp)."""
        from genesis.lawhook import build_ctx

        by_id = {c.id: c for c in creatures}
        sm = world.surface_map

        for ev in events.get("death", ()):
            cid = ev.get("creature_id")
            if cid in self.notes or cid in self.codices:
                forget_on_death(self.notes.get(cid), self.codices.get(cid))

        self._absorb_speech(tick_no, world, by_id, events.get("speak", ()))
        last_did = getattr(state, "last_did", {}) if state is not None else {}
        ctx_cache: dict[str, object] = {}

        def ctx_of(cr: Creature):
            got = ctx_cache.get(cr.id)
            if got is None:
                recent = {k: tick_no - v for k, v in last_did.get(cr.id, {}).items()}
                got = build_ctx(cr, world, tick_no, creatures, recent)
                ctx_cache[cr.id] = got
            return got
        outcome: dict[str, list[str]] = {}
        for ev in events.get("law", ()):
            phrase = _OUTCOME_VN.get(ev.get("effect", ""), "có gì đó vừa xảy ra")
            cid = ev["creature_id"]
            parts = outcome.setdefault(cid, [])
            if phrase not in parts:
                parts.append(phrase)

        acted: list[tuple[str, str]] = []
        for ev in events.get("eat", ()):
            cls = ev.get("fruit_class")
            what = sm.surface_of(cls) if cls in sm.cls_to_surface else "thứ gì đó"
            acted.append((ev["creature_id"], f"ăn {what}"))
        acted.extend((ev["creature_id"], "uống nước") for ev in events.get("drink", ()))
        acted.extend((ev["creature_id"], "trúng đòn") for ev in events.get("attack", ()))

        did_something = {a for a, _ in acted}
        for ev in events.get("move", ()):
            cid = ev["creature_id"]
            if cid in did_something or (cid not in outcome and cid not in self.slots):
                continue
            c = by_id.get(cid)
            if c is None:
                continue
            if tick_no % law_config.PHASE_LEN == 0:
                p = "ban ngày" if phase_at(tick_no) == "DAY" else "ban đêm"
                action = f"trời vừa chuyển sang {p}"
            elif c.energy < 0.25 * c.traits.energy_max:
                action = "sức đã cạn"
            elif any(
                o.alive and o.id != c.id and world.dist(c.pos, o.pos) <= 1
                for o in creatures
            ):
                action = "có kẻ đứng sát bên"
            elif ev["moved"]:
                wx, wy = world.wrap(*c.pos)
                terr = _TERRAIN_VN.get(world.grid[wy][wx], "đất trống")
                action = f"bước vào {terr}"
            else:
                action = "đứng yên"
            acted.append((cid, action))

        for actor_id, action in acted:
            actor = by_id.get(actor_id)
            if actor is None:
                continue
            out = "; ".join(outcome.get(actor_id, ())) or "không thấy gì"
            for observer_id in self.slots:
                obs = by_id.get(observer_id)
                if obs is None or not obs.alive:
                    continue
                if observer_id == actor_id:
                    who = "TÔI"
                elif world.dist(obs.pos, actor.pos) <= obs.traits.sight_radius:
                    who = f"THẤY {actor_id}"
                else:
                    continue
                self.notes_of(obs).record(Note(
                    t=tick_no, who=who, action=action, outcome=out,
                    ctx=ctx_to_pairs(ctx_of(obs), obs.traits.brain),
                ))


__all__ = [
    "_BAND_NOTE",
    "_CLAIM_TAIL",
    "_OUTCOME_VN",
    "_PHASE_NOTE",
    "_RECENT_NOTE",
    "LlmStrategist",
    "_budget",
    "ctx_to_pairs",
]
