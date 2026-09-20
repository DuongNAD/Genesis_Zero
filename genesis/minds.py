"""Genesis Zero — minds: trí nhớ và tầng xã hội, DÙNG CHUNG cho cả hai đường chạy.

## Vì sao file này tồn tại

Ván cục bộ chạy qua `LlmStrategist`; chế độ mở chạy qua `RemoteClientStrategist`
+ `net.routes_work`. Hai đường, và đường mạng **liên tục thiếu thứ đường cục bộ
có**. Đếm được năm lần chỉ trong một ngày:

| | triệu chứng |
|---|---|
| `schema_for` thiếu `targets` lẫn `sm` | luật ăn quả **bất khả về cấu trúc** qua mạng |
| `founder_traits` không biết loài đăng ký lúc chạy | người chơi **mất brain** sau cái chết đầu |
| quên-khi-chết chỉ ở `strategist.observe` | sinh vật qua mạng **không quên gì** |
| `heard=()` cứng | người chơi qua mạng **không bao giờ nghe thấy ai** |
| không ghi `prompt_hash` | log ván mở **không dựng lại được mẫu huấn luyện** |

Bốn lần đầu tôi vá từng cái. Đến lần thứ năm thì rõ là vá từng cái không phải
cách sửa — mẫu là **hai bản của cùng một khái niệm**, và bản nào ít người nhìn
hơn thì bản ấy mục.

`Minds` giữ đúng phần trạng thái mà cả hai đường đều cần, cùng logic thao tác
lên nó. Đường nào cũng gọi vào đây; không đường nào giữ bản sao.

## Cái gì KHÔNG thuộc về đây

Việc gọi model, ngân sách token, cầu dao, hạn chờ — đó là chuyện của
`LlmStrategist`. `Minds` không biết model là gì, và điều đó cố ý: chế độ mở
**không gọi model**, nó chỉ nhận quyết định client gửi về.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genesis import law_config, speech
from genesis.codex import Codex
from genesis.fieldnotes import FieldNotes
from genesis.hunch import HunchBook
from genesis.lineage import forget_on_death
from genesis.provenance import Ledger

if TYPE_CHECKING:
    from genesis.creature import Creature


class Minds:
    """Trí nhớ và quan hệ xã hội của cả đàn, khoá theo `creature_id`."""

    def __init__(self) -> None:
        self.notes: dict[str, FieldNotes] = {}
        self.codices: dict[str, Codex] = {}
        self.heard: dict[str, list[str]] = {}
        self.notepad: dict[str, str] = {}
        self.want_codex: set[str] = set()
        # ── Linh cảm (B-14), TẮT mặc định ───────────────────────────────
        # Bật lên là **đổi luật chơi**, nên mọi con số ghi trước đó không so
        # được với con số sau đó. Nó là một nhánh thí nghiệm, đúng cách cẩm nang
        # của W-16 được đối xử: mệnh đề "linh cảm rút ngắn t_discover" phải
        # được ĐO, không được giả định.
        self.hunch_enabled: bool = False
        self.hunches: dict[str, HunchBook] = {}
        self.want_hunch: set[str] = set()
        # Cẩm nang theo LOÀI, sống qua nhiều ván (W-16). Rỗng thì `system_block`
        # không thêm gì — mọi ván cũ chạy y hệt.
        self.handbooks: dict[str, str] = {}
        self.reputation: dict[str, speech.Reputation] = {}
        self.ledger = Ledger()
        self.offers: dict[str, list[tuple[str, Any, bool]]] = {}
        self.teach_events: list = []

    # ── tra cứu, tạo khi cần ────────────────────────────────────────────
    def notes_of(self, c: Creature) -> FieldNotes:
        n = self.notes.get(c.id)
        cap = law_config.EVENTS_BY_BRAIN[c.traits.brain]
        if n is None:
            n = FieldNotes(cap=cap)
            self.notes[c.id] = n
        elif n.cap != cap:
            n.cap = cap
        return n

    def codex_of(self, c: Creature) -> Codex:
        cx = self.codices.get(c.id)
        size = law_config.CODEX_SIZE_BY_BRAIN[c.traits.brain]
        if cx is None:
            cx = Codex(size=size)
            self.codices[c.id] = cx
        elif cx.size != size:
            cx.resize(size)
        return cx

    def hunch_of(self, c: Creature) -> HunchBook:
        hb = self.hunches.get(c.id)
        size = law_config.HUNCH_BY_BRAIN[c.traits.brain]
        if hb is None:
            hb = HunchBook(size=size)
            self.hunches[c.id] = hb
        elif hb.size != size:
            hb.resize(size)
        return hb

    def hunch_last_write(self, cid: str) -> int:
        """Lần ghi linh cảm gần nhất — TRA CỨU thuần, không tạo sổ.

        `hunch_of` tạo sổ khi chưa có, nên gọi nó chỉ để hỏi hạn nguội sẽ dựng
        một cuốn sổ rỗng cho MỌI cá thể ở MỌI lượt nghĩ. Không sai, nhưng nó làm
        `self.hunches` đầy sổ rỗng và mất luôn tính chất "có mặt ở đây nghĩa là
        đã từng nêu một linh cảm" — thứ mà cả log lẫn bài kiểm đều dựa vào.
        """
        hb = self.hunches.get(cid)
        return hb.last_write if hb is not None else -law_config.HUNCH_COOLDOWN

    def rep_of(self, cid: str) -> speech.Reputation:
        r = self.reputation.get(cid)
        if r is None:
            r = speech.Reputation()
            self.reputation[cid] = r
        return r

    # ── tầng xã hội ─────────────────────────────────────────────────────
    def absorb_speech(self, tick_no: int, world, by_id: dict[str, Creature],
                      speak_events) -> None:
        """Lời nói vào hàng chờ của người nghe, và vào trí nhớ về kẻ nói.

        Người nghe **không tự động tin** (B-12 bất biến 2): luật nghe được nằm ở
        khối "NGHE ĐƯỢC" kèm ai nói và độ tin quá khứ của kẻ đó, chứ không vào
        Sổ Luật. Muốn vào sổ thì chính agent phải `SET` — tốn một ô, tốn energy.
        Chép mù thì hết ô để chứa thứ mình tự tìm ra.
        """
        from genesis.teach import apply_teach, hide_effect, render_offer

        for ev in speak_events:
            speaker = by_id.get(ev.get("creature_id"))
            if speaker is None:
                continue
            say = speech.Say(ev.get("signal"), ev.get("text"), ev.get("teach"))
            full = [by_id[i] for i in (ev.get("hear_full") or ()) if i in by_id]
            sig = [by_id[i] for i in (ev.get("hear_signal") or ()) if i in by_id]
            both = [(h, True) for h in full] + [(h, False) for h in sig]

            for who, is_full in both:
                self.rep_of(who.id).record_speech(speaker.id, say.signal, tick_no)
                self._push_heard(who.id,
                                 speech.render_heard(speaker.id, say, full=is_full))

            if say.teach is None:
                continue
            entries = self.codex_of(speaker).entries()
            if not (0 <= say.teach < len(entries)):
                continue
            entry = entries[say.teach]
            if entry is None:
                continue
            law = entry.law
            self.teach_events.extend(
                apply_teach(speaker, law, full, sig, tick_no, self.ledger)
            )
            for who, is_full in both:
                offered = law if is_full else hide_effect(law)
                self.offers.setdefault(who.id, []).append(
                    (speaker.id, offered, is_full))
                del self.offers[who.id][:-law_config.HEARD_MAX]
                self._push_heard(who.id, render_offer(
                    speaker.id, offered, world.surface_map,
                    self.rep_of(who.id).trust(speaker.id), is_full,
                ))

    def _push_heard(self, cid: str, line: str) -> None:
        q = self.heard.setdefault(cid, [])
        q.append(line)
        del q[:-law_config.HEARD_MAX]

    # ── vòng đời ────────────────────────────────────────────────────────
    def on_death(self, cid: str) -> int:
        """Sang đời mới: sổ tay chết theo, Sổ Luật bớt chắc chắn (W-17).

        Linh cảm đi cùng SỔ LUẬT, không đi cùng sổ tay: nó là một phát biểu đã
        **viết ra**, nên nó sống qua đời — nhưng bảng đếm co lại, vì bảng đếm là
        quan sát thô. Xem `HunchBook.on_death`.
        """
        hb = self.hunches.get(cid)
        if hb is not None:
            hb.on_death()
        return forget_on_death(self.notes.get(cid), self.codices.get(cid))

    def new_match(self) -> None:
        """Ranh giới giữa hai ván: xoá mọi thứ **trong ván**, GIỮ cẩm nang.

        Đây là chỗ duy nhất trong lớp này phân biệt hai tầng trí nhớ của W-16.
        Sổ tay và Sổ Luật là của một ván — mang sang ván sau là chép đáp án, mà
        luật đổi mỗi ván nên đáp án cũ vừa sai vừa làm phép đo mất nghĩa. Cẩm
        nang thì ngược lại: nó chứa **cách tìm**, và cách tìm mới là thứ đáng
        sống qua nhiều thế giới.

        Danh tiếng cũng chết theo ván: nó khoá theo `creature_id`, mà `L2:0` ở
        ván sau là một con khác hẳn do người khác điều khiển.
        """
        for d in (self.notes, self.codices, self.heard, self.notepad,
                  self.reputation, self.offers, self.hunches):
            d.clear()
        self.want_codex.clear()
        self.want_hunch.clear()
        self.teach_events.clear()
        self.ledger = Ledger()

    def clear(self) -> None:
        """Xoá SẠCH, cẩm nang cũng đi. Dùng lúc dựng lại từ đầu, không phải giữa hai ván."""
        self.new_match()
        self.handbooks.clear()
