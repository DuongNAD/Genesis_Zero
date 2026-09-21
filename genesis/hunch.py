"""Genesis Zero v5 — hunch: Linh cảm, chỗ để ĐOÁN mà không phải TIN (B-14).

Sổ Luật đang gánh hai việc khác nhau: vừa là chỗ ghi giả thuyết, vừa là chỗ nộp
bài. Nhưng ô sổ thì ít (brain 0 có đúng MỘT), ghi thì tốn năng lượng và tốn
`CLAIM_COOLDOWN`. Nên *thử nghĩ ra một khả năng* trả giá y hệt *tuyên bố đã
biết* — hai hành vi rất khác nhau, một bảng giá.

Đo được hậu quả ở cả hai đầu: `L5:1` **tìm ra luật ở tick 99 rồi phải xoá ở tick
148** để lấy chỗ ghi thứ khác; và model viết **24/45 mục về ăn quả** vì thử một
hướng khác quá đắt.

Linh cảm là chỗ rẻ để sai. Nó không chiếm ô Sổ Luật, **không bao giờ được chấm**,
và thế giới tự đếm hộ nó đúng bao nhiêu lần trên bao nhiêu lần thử.

## Ranh giới "được biết cái gì" — đọc trước khi sửa file này

`observe` so ở mức `EffectKind` và **không** so `mag`/`dur`. Con vật cảm được
"máu tụt hẳn xuống"; nó không cảm được "DAMAGE mức MED kéo dài SHORT". So tới
`mag`/`dur` là đưa cho nó một độ chính xác nó không quan sát được — tức là rò
đáp án qua cửa sau, và nó rò **im lặng**: `match` chỉ nhích lên và trông y như
model vừa giỏi hơn.

Cùng lý do, `verify.agree` không được gọi ở đây. `agree` trả điểm từng phần trên
`mag`/`dur` — nó là thước của bộ chấm. Đưa thước ấy vào vòng tick thì con vật dò
được `mag` bằng cách xem điểm nhích lên hay xuống.

Hệ quả cố ý: một linh cảm **yếu hơn hẳn** một mục Sổ Luật. Nó chỉ ra hướng,
không ra bài.
"""

from __future__ import annotations

from dataclasses import dataclass

from genesis import law_config
from genesis.lawdsl import EffectKind, Law, to_vietnamese
from genesis.laweval import LawEvent, evaluate
from genesis.surface import SurfaceMap
from genesis.validate import Verdict


@dataclass
class Hunch:
    """Một giả thuyết đang được theo dõi, kèm bảng đếm của chính nó."""

    law: Law
    born_at: int
    tried: int = 0      # số lần trigger + cond khớp
    hit: int = 0        # trong đó, số lần hệ quả ĐÚNG LOẠI thật sự xảy ra

    @property
    def confidence(self) -> float:
        """Độ tin cậy xác suất Bayes với làm mịn Laplace: P(H|E) = (hit + 1) / (tried + 2)."""
        if self.tried == 0:
            return 0.5
        return (self.hit + 1.0) / (self.tried + 2.0)


class HunchBook:
    """Cuốn sổ nháp của một cá thể. Nhiều ô hơn Sổ Luật, và không ô nào được chấm."""

    def __init__(self, size: int) -> None:
        self.size: int = max(0, size)
        self._entries: list[Hunch | None] = [None] * self.size
        self.last_write: int = -law_config.HUNCH_COOLDOWN

    # ── ghi ──────────────────────────────────────────────────────────────
    def apply(self, op: str, slot: int, law: Law | None, tick: int) -> Verdict:
        """`SET` hoặc `DROP` một ô. KHÔNG phản hồi gì về tính đúng/sai của luật.

        Cùng bất biến B2 của `Codex.apply`, và vì cùng một lý do: một `Verdict`
        biết luật đúng hay sai là một oracle miễn phí đội lốt mã lỗi.
        """
        if slot < 0 or slot >= self.size:
            return Verdict(ok=False, reason="HUNCH_BAD_SLOT")
        if tick - self.last_write < law_config.HUNCH_COOLDOWN:
            return Verdict(ok=False, reason="HUNCH_COOLDOWN")

        if op == "SET":
            if law is None:
                return Verdict(ok=False, reason="HUNCH_MISSING_LAW")
            self._entries[slot] = Hunch(law=law, born_at=tick)
            self.last_write = tick
            return Verdict(ok=True)

        if op == "DROP":
            self._entries[slot] = None
            self.last_write = tick
            return Verdict(ok=True)

        return Verdict(ok=False, reason="HUNCH_UNKNOWN_OP")

    # ── đếm ──────────────────────────────────────────────────────────────
    def observe(self, ev: LawEvent, happened: frozenset[EffectKind]) -> None:
        """Một sự kiện của cá thể này vừa xảy ra; cập nhật mọi linh cảm nói về nó.

        `happened` là tập hệ quả **thật sự giáng xuống con vật trong tick đó** —
        không phải hệ quả của riêng luật nó đang đoán. Nên bảng đếm CÓ NHIỄU, và
        điều đó đúng: đó chính là sự lẫn lộn nhân quả mà một nhà khoa học thật
        phải gỡ. Đừng "sửa" bằng cách lọc theo `law_id` — lọc thế là nói thẳng
        cho con vật biết luật nào tồn tại.

        `tried` tăng CẢ KHI KHÔNG CÓ GÌ XẢY RA. Bỏ những lần ấy thì mọi linh cảm
        đều đúng 100% và bảng đếm thành vô dụng — mà "chuyện không xảy ra cũng
        là bằng chứng" là đúng nửa giá trị của cả cơ chế.
        """
        for h in self._entries:
            if h is None:
                continue
            if evaluate(h.law, ev) is None:
                continue          # giả thuyết này không nói gì về tick đó
            h.tried += 1
            if h.law.effect.kind in happened:
                h.hit += 1

    # ── đọc ──────────────────────────────────────────────────────────────
    def entries(self) -> list[Hunch | None]:
        return list(self._entries)

    def best_hunch(self, min_tried: int = 2) -> tuple[Hunch, float] | None:
        """Trả về linh cảm có độ tin cậy Bayes cao nhất đã thử ít nhất `min_tried` lần."""
        best: tuple[Hunch, float] | None = None
        for h in self._entries:
            if h is not None and h.tried >= min_tried:
                conf = h.confidence
                if best is None or conf > best[1]:
                    best = (h, conf)
        return best

    def resize(self, new_size: int) -> None:
        """Brain tụt thì KHÔNG cắt sổ đang có, chỉ chặn ghi thêm — như `Codex.resize`."""
        new_size = max(0, new_size)
        self.size = new_size
        if new_size > len(self._entries):
            self._entries.extend([None] * (new_size - len(self._entries)))

    def on_death(self) -> int:
        """Sang đời sau: **giữ** câu hỏi, **co** bảng đếm. Trả số ô còn lại.

        Bản đầu của B-14 xoá sạch, với lý do "linh cảm là trạng thái đang điều
        tra, không phải niềm tin". Phép đo bác bỏ lý do ấy — xem
        `law_config.HUNCH_DECAY_PER_GEN`: sinh vật chết 4,4–4,9 lần một ván và
        tuổi trung vị lúc ghi Sổ Luật là **27 tick**, nên xoá sạch nghĩa là linh
        cảm thừa hưởng đúng cái lỗ khoá 27 tick đang làm hỏng mọi thứ, và cơ chế
        này không mua được gì.

        Bảng của [W-17](../docs/tasks/W-17-doi.md) đã có câu trả lời đúng, tôi
        chỉ xếp nhầm hàng: *Sổ Luật sống qua đời vì nó là thứ ngươi đã **viết
        ra**; sổ tay chết theo vì trải nghiệm thô không truyền được.* Một linh
        cảm là một **phát biểu đã viết ra** — nên nó thuộc hàng trên. Còn bảng
        đếm thì đúng là quan sát thô, nên nó co lại thay vì đi theo nguyên vẹn.

        Co chứ không xoá giữ được TỈ LỆ (thứ đã học) mà bỏ bớt SỐ LẦN (thứ đã tự
        tay đo). Hệ quả phụ đáng muốn: một linh cảm mới thử một hai lần sẽ co về
        `0/0` — "chưa thử lần nào" — nên một cú đoán chưa kiểm không truyền được
        sự chắc chắn nào cả, đúng tinh thần `CODEX_CONF_DECAY_PER_GEN`.
        """
        k = law_config.HUNCH_DECAY_PER_GEN
        n = 0
        for h in self._entries:
            if h is None:
                continue
            h.tried = int(h.tried * k)
            h.hit = min(h.tried, int(h.hit * k))
            n += 1
        self.last_write = -law_config.HUNCH_COOLDOWN
        return n

    def clear(self) -> int:
        """Xoá SẠCH. Dùng ở ranh giới VÁN, không phải ranh giới đời."""
        n = sum(1 for e in self._entries if e is not None)
        self._entries = [None] * len(self._entries)
        self.last_write = -law_config.HUNCH_COOLDOWN
        return n

    def render(self, sm: SurfaceMap) -> str:
        """Khối E6. Rỗng thì trả chuỗi rỗng — ván không bật linh cảm chạy y hệt."""
        rows = []
        for i, h in enumerate(self._entries):
            if h is None:
                continue
            text = to_vietnamese(h.law, sm)
            tally = "chưa thử lần nào" if h.tried == 0 else f"đúng {h.hit} / thử {h.tried}"
            rows.append(f"{i}. {text} — {tally}")
        if not rows:
            return ""
        return ("[LINH CẢM] — ngươi đang thử những điều này. "
                "Chưa cái nào là kết luận.\n" + "\n".join(rows))
