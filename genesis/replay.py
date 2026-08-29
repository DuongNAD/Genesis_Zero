"""Genesis Zero — replay: dựng lại một ván có LLM từ log (B-06).

Tính tất định từ seed **không còn giữ được** khi có LLM: sampling ở
`temperature > 0` đã ngẫu nhiên, timeout mạng càng không. M0–M1 tái lập từ
**seed**; M2 trở đi chỉ tái lập từ **log**. Đừng hứa quá.

Hai bất biến, theo docs/tasks/B-06-replay.md §2:

1. Mỗi `LLM_CALL` ghi `prompt_hash` (md5) + phản hồi **thô**, KHÔNG ghi prompt
   đầy đủ — log sẽ phình gấp 20 lần.
2. Replay so `prompt_hash`; lệch thì **dừng** và báo rõ tick nào. Replay lệch
   âm thầm tệ hơn không có replay: nó cho ta một file kết quả trông như thật.

Vì (2), lớp này **không** có đường đoán mò. Không có "lấy tạm quyết định gần
nhất của con đó", không có "thử vài tên trường xem trường nào có goal". Thiếu
bản ghi thì trả None và vòng tick rơi về phản xạ; sai bản ghi thì ném.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import TYPE_CHECKING, Callable

from genesis.prompt import prompt_hash
from genesis.reflex import ActiveGoal
from genesis.strategist import payload_to_goal

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.world import World

# (system, user) -> hai chuỗi prompt của một lời gọi
PromptFn = Callable[["Creature", "World", list["Creature"], int], tuple[str, str]]


class ReplayMismatch(RuntimeError):
    """Prompt dựng lại khác prompt lúc chạy thật. Dừng ngay, đừng chạy tiếp."""


@dataclass(frozen=True)
class LLMCall:
    t: int
    creature_id: str
    prompt_hash: str
    raw: str            # phản hồi thô của model, chưa parse
    cost_think: float   # sức đã trừ ở ván thật — phải trừ lại y hệt
    kind: str           # "decide" | "codex" | "shift"


class ReplayStrategist:
    """Phát lại quyết định LLM từ log JSONL thay vì gọi model.

    `prompt_fn` là cách duy nhất kiểm được bất biến 2. Không truyền thì lớp này
    chạy ở chế độ **không kiểm** và nói thẳng ra qua `self.verifying is False` —
    dùng cho test đơn vị, không dùng để tuyên bố "replay khớp".
    """

    def __init__(
        self,
        log_path: str | Path,
        prompt_fn: PromptFn | None = None,
        mind: object | None = None,
    ) -> None:
        # `mind` là một LlmStrategist chỉ dùng để DỰNG LẠI prompt: nó giữ sổ tay,
        # Sổ Luật, cache prefix — đúng thứ prompt phụ thuộc vào. Không có nó thì
        # hash dựng lại được từ đâu? Từ hư không, và bất biến 2 thành trang trí.
        self.mind = mind
        if prompt_fn is None and mind is not None:
            prompt_fn = mind.build_prompt
        self.log_path = Path(log_path)
        self.prompt_fn = prompt_fn
        self.verifying = prompt_fn is not None
        self.calls: dict[tuple[int, str], LLMCall] = {}
        # Hướng dịch trait do LLM chọn (B-13) cũng phải phát lại: nó đổi
        # `brain` -> đổi khối D -> đổi prompt, nên bỏ qua nó thì ván rẽ nhánh và
        # `prompt_hash` lệch ở lượt sau — đúng triệu chứng đã gặp: khớp tới t=57
        # rồi lệch ở t=60, không phải ở lượt đầu.
        self.shifts: dict[tuple[int, str], tuple[str, str]] = {}
        # Ghi Sổ Luật cũng phải phát lại: nội dung Sổ Luật nằm TRONG khối E, nên
        # một lần ghi thành công làm prompt của mọi lượt sau đổi. Không phát lại
        # thì ván rẽ nhánh ngay ở lượt gọi kế tiếp — và bài test replay cũ không
        # bắt được vì model giả của nó chưa bao giờ ghi sổ.
        self.codex_ops: dict[tuple[int, str], dict] = {}
        # Lời nói cũng phải phát lại: nó tốn energy của người nói VÀ đi vào khối
        # "NGHE ĐƯỢC" của người nghe. Không phát lại thì `observe` nhận danh sách
        # rỗng, `heard` của mọi con đứng yên, và ván rẽ nhánh.
        self.says: dict[tuple[int, str], dict] = {}
        self.n_replayed = 0
        self._tick = 0
        self.n_missing = 0
        self._load()

    def _load(self) -> None:
        if not self.log_path.exists():
            raise FileNotFoundError(f"không có log để replay: {self.log_path}")
        with self.log_path.open("r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)      # log hỏng thì ném, không bỏ qua
                if row.get("kind") == "SPEAK":
                    self.says[(int(row["t"]), row["creature_id"])] = row
                    continue
                if row.get("kind") == "CODEX_OP" and row.get("ok"):
                    self.codex_ops[(int(row["t"]), row["creature_id"])] = row
                    continue
                if row.get("kind") == "TRAIT_SHIFT" and row.get("by") == "llm":
                    self.shifts[(int(row["t"]), row["creature_id"])] = (
                        row["frm"], row["to"]
                    )
                    continue
                if row.get("kind") != "LLM_CALL":
                    continue
                key = (int(row["t"]), row["creature_id"])
                if key in self.calls:
                    raise ValueError(
                        f"{self.log_path}:{lineno}: hai LLM_CALL cho cùng "
                        f"(t={key[0]}, {key[1]}) — log không dùng replay được"
                    )
                self.calls[key] = LLMCall(
                    t=key[0],
                    creature_id=key[1],
                    prompt_hash=row["prompt_hash"],
                    raw=row["raw"],
                    cost_think=float(row.get("cost_think", 0.0)),
                    # Không có trường này thì replay coi MỌI phản hồi là một
                    # quyết định `decide`. Ván thật hỏi hướng dịch trait ở lượt
                    # đó và **vứt** câu trả lời (nó không hợp lệ), còn replay lại
                    # đem chính câu ấy ra làm goal — hai ván rẽ nhánh đúng ở tick
                    # đầu tiên có một lời gọi khác `decide`, không sớm hơn một tick.
                    kind=row.get("kind_asked") or "decide",
                )

    def begin_tick(self, creatures: list[Creature], world: World, tick_no: int) -> None:
        """Lặp lại NHỊP của ván thật, không chỉ lặp lại quyết định.

        Ván thật dựng prompt rồi mới trừ `cost_think` (B-05 bất biến 3), và cả
        hai việc đó xảy ra TRƯỚC pha thu intent. Replay phải theo đúng thứ tự
        ấy, nếu không sức của con vật lệch dần và tới lượt thứ hai thì prompt đã
        khác — đúng cái đã xảy ra lần đầu viết lớp này: hash lệch ở t=3 trong khi
        mọi quyết định đều được phát lại đúng.
        """
        from genesis.world import visible

        # `take_shift` được gọi ở pha 3, không có tham số tick — nên nhớ lại
        # tick hiện tại ở đây, chỗ duy nhất vòng tick đưa nó cho ta mỗi lượt.
        self._tick = tick_no
        for c in creatures:
            rec = self.calls.get((tick_no, c.id))
            if rec is None or not c.alive:
                continue
            if self.verifying:
                assert self.prompt_fn is not None
                system, user = self.prompt_fn(c, world, visible(c, world, creatures), tick_no)
                got = prompt_hash(system, user)
                if got != rec.prompt_hash:
                    raise ReplayMismatch(
                        f"t={tick_no} {c.id}: prompt_hash lệch "
                        f"(log {rec.prompt_hash[:8]}, dựng lại {got[:8]}). "
                        f"Ván đã rẽ nhánh TRƯỚC lượt này — dừng, đừng đọc kết quả sau đây."
                    )
            c.energy -= rec.cost_think

        # Áp lại GHI CHÚ RIÊNG: `_absorb` của ván thật cất `note` vào notepad, và
        # notepad nằm trong khối E — nên bỏ qua nó là ván rẽ nhánh ở lượt gọi kế
        # tiếp. Model giả trước đây không viết `note` nên không bài test nào bắt
        # được; model thật viết mọi lượt, và hash lệch ngay ở t=3.
        self._replay_notepad(creatures, tick_no)

        # Áp lại thao tác Sổ Luật SAU khi đã dựng và đối chiếu prompt. Ván thật
        # theo đúng thứ tự ấy: `think()` dựng prompt -> gọi model -> `_absorb_codex`
        # mới ghi sổ. Áp trước thì prompt của CHÍNH lượt ghi sổ đã thấy mục mới,
        # và hash lệch ngay tại tick đó.
        self._replay_codex(creatures, tick_no)

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        rec = self.calls.get((tick_no, c.id))
        if rec is None:
            # Ván thật không gọi model cho con này ở lượt này. Đó là chuyện
            # bình thường (LLM chỉ gọi theo nhịp), nên trả None để rơi về phản xạ.
            self.n_missing += 1
            return None
        self.n_replayed += 1
        if rec.kind != "decide":
            # Lượt ấy dùng để ghi sổ hoặc chọn hướng dịch, không phải để chọn ý
            # đồ. Trả None và vòng tick giữ goal cũ — đúng như ván thật.
            return None
        try:
            payload = json.loads(rec.raw)
        except json.JSONDecodeError:
            # Ván thật cũng gặp JSON hỏng ở đây và đã ghi LLM_MISS; lặp lại y hệt.
            return None
        return payload_to_goal(payload)

    def _replay_notepad(self, creatures, tick_no: int) -> None:
        from genesis import law_config, speech

        if self.mind is None:
            return
        for c in creatures:
            rec = self.calls.get((tick_no, c.id))
            if rec is None or rec.kind != "decide":
                continue
            try:
                payload = json.loads(rec.raw)
            except json.JSONDecodeError:
                continue
            note = payload.get("note")
            if isinstance(note, str) and note.strip():
                self.mind.notepad[c.id] = speech.sanitize_free_text(
                    note, law_config.NOTEPAD_MAX_CHARS
                )
            if payload.get("want_codex"):
                self.mind._want_codex.add(c.id)

    def _replay_codex(self, creatures, tick_no: int) -> None:
        from genesis.lawdsl import from_json

        if self.mind is None:
            return
        for c in creatures:
            row = self.codex_ops.get((tick_no, c.id))
            if row is None:
                continue
            law = from_json(row["law"]) if row.get("law") else None
            self.mind.codex_of(c).apply(
                row.get("op", "SET"), int(row.get("slot", 0)), law,
                int(row.get("conf", 3) or 3), tick_no,
            )

    # Vòng tick gọi hai móc này trên bất kỳ strategist nào có chúng; chuyển
    # thẳng cho `mind` để sổ tay của bản replay lớn lên đúng như ván thật.
    def observe(self, tick_no, world, creatures, events, state=None) -> None:
        if self.mind is not None:
            self.mind.observe(tick_no, world, creatures, events, state)

    # ── B-13 ─────────────────────────────────────────────────────────────
    @property
    def slots(self) -> dict:
        """Vòng tick hỏi cái này để biết con nào do tầng chiến lược làm chủ."""
        return getattr(self.mind, "slots", {})

    @property
    def shift_why(self) -> dict:
        return getattr(self.mind, "shift_why", {})

    def take_shift(self, c) -> tuple[str, str] | None:
        return self.shifts.get((self._tick, c.id))

    def take_says(self, ) -> dict:
        """Lời nói của tick hiện tại, dựng lại từ log.

        Cùng chữ ký với `LlmStrategist.take_says` để vòng tick không phải biết
        nó đang chạy bản nào.
        """
        from genesis.speech import Say

        out = {}
        for (t, cid), row in self.says.items():
            if t == self._tick:
                out[cid] = Say(row.get("signal", "NEUTRAL"), row.get("text", ""),
                               row.get("teach"))
        return out
