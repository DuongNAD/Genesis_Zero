"""Genesis Zero — net/match: vòng đời một ván ở chế độ mở (N-04).

Vòng đời ván là đơn vị của cả trò chơi lẫn cộng đồng, nên máy trạng thái ở đây
quyết định trải nghiệm nhiều hơn bất cứ endpoint nào.

    LOBBY ──► SEEDING ──► RUNNING ──► REVEAL ──► COOLDOWN ──► LOBBY

Năm bất biến, theo docs/tasks/N-04-server-khung.md §2:

1. **Server là đồng hồ duy nhất.** Client không bao giờ gửi `tick`. Điểm v5 phụ
   thuộc **thời điểm** ghi sổ, nên client khai lùi được là gian lận được.
2. **Sảnh trống thì tự lấp bằng bot.** Ván LUÔN chạy.
3. **Vào giữa ván thì xếp hàng ván sau.** Luật đã bị khám phá một nửa; điểm của
   người vào muộn sẽ vô nghĩa.
4. **`T = OPEN_MATCH_TICKS = 200`** ở chế độ mở, không phải 400. Người lạ không
   chờ 27 phút.
5. **Luật thật không rời server trước `REVEAL`.** Đây là bất biến duy nhất trong
   file này mà một lỗi sẽ không gây ra triệu chứng nào — ván vẫn chạy, không ai
   báo gì, và cả thí nghiệm âm thầm vô nghĩa. Nên nó được giữ bằng **cấu trúc**:
   `self._laws` là riêng tư và chỉ ra ngoài qua `laws_public()`, hàm duy nhất
   biết cách đọc pha. Không có đường thứ hai, và `tests/test_no_law_leak.py`
   quét mọi phản hồi để chắc chắn thế.
"""

from __future__ import annotations

import asyncio
import collections
import contextlib
import json
import random
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import net_config
from genesis import config
from genesis.creature import Creature, creature_sort_key
from genesis.features import kit_of, roll_for_species
from genesis.handbook import Handbook
from genesis.lawdsl import to_json, to_vietnamese
from genesis.lawgen import generate_cached
from genesis.logio import LogWriter
from genesis.minds import Minds
from genesis.strategist import RemoteClientStrategist
from genesis.tick import SimState, build_match
from genesis.tick import tick as run_tick
from genesis.victory import Victory
from genesis.weather import weather_at
from genesis.world import World
from net.telemetry import creature_telemetry, envelope


class _FrameCollector:
    """Ống chữ Y: sự kiện đi vào log THẬT và đồng thời gom lại cho người xem.

    Không phải một bộ bọc thay `runner.log`: `run_tick` nhận nó cho đúng một
    tick rồi bỏ, nên không có trạng thái nào sống lâu hơn một tick và log thật
    không bao giờ đổi hình dạng.
    """

    def __init__(self, inner, on_record=None) -> None:
        self.inner = inner
        self.on_record = on_record
        self.events: list[dict] = []

    def write(self, t: int, kind: str, **fields) -> None:
        self.events.append({"kind": kind, **fields})
        if self.on_record is not None:
            self.on_record(t, kind, **fields)
        if self.inner is not None:
            self.inner.write(t, kind, **fields)


def _public_event(ev: dict, reveal: bool, pub: dict[str, str]) -> dict:
    """Sự kiện đã lọc cho người xem.

    `LAW_FIRED` đi ra với `"law": "?"` trước REVEAL, và **đó là chủ ý**: người
    xem thấy có gì đó vừa xảy ra mà không biết là gì — đúng trải nghiệm của sinh
    vật trong ván, và nó khiến người xem cũng chơi trò đoán luật.

    Danh sách TRẮNG: mọi `kind` không có tên ở đây ra ngoài chỉ với `k` và `who`.
    Danh sách đen thì hỏng ngay lần đầu ai đó thêm một loại sự kiện mới mang
    theo thông tin nhạy cảm.
    """
    kind = ev.get("kind", "")
    out = {"k": kind, "who": ev.get("creature_id", "")}
    if kind == "LAW_FIRED":
        out["law"] = pub.get(ev.get("law_id", ""), "?") if reveal else "?"
        # Vị trí thì gửi: người xem đã nhìn thấy con vật đứng ở đó rồi. Cái giấu
        # là luật NÀO, không phải chuyện có gì đó vừa xảy ra ở đâu.
        out["pos"] = ev.get("pos", [])
    elif kind == "SPEAK":
        out["sig"] = ev.get("signal", "NEUTRAL")
        # Đồ thị "ai nghe được ai" phải đến TỪ SERVER: nó phụ thuộc `sense` của
        # NGƯỜI NGHE và vị trí lúc đó. Bản đầu gửi trường rỗng rồi để trang xem
        # tự tính từ một bảng trait chép cứng trong JavaScript — sai ngay lần
        # dịch trait đầu tiên, và sai hẳn với loài do người lạ tạo ra.
        out["hear"] = list(ev.get("hear_full", ())) + list(ev.get("hear_signal", ()))
    elif kind in ("EAT", "DRINK", "RESPAWN"):
        out["pos"] = ev.get("pos", [])
    elif kind == "ATTACK":
        out["target"] = ev.get("target_id", "")
    elif kind == "DEATH":
        out["cause"] = ev.get("cause", "")
    elif kind == "TRAIT_SHIFT":
        out["frm"], out["to"] = ev.get("frm", ""), ev.get("to", "")
    elif kind == "REPRODUCE":
        out["child"] = ev.get("child", "")
        out["gen"] = ev.get("gen", 0)
        out["pos"] = ev.get("pos", [])
    elif kind == "EXTINCTION":
        out["species"] = ev.get("species", "")
    return out


class Phase(StrEnum):
    LOBBY = "LOBBY"
    SEEDING = "SEEDING"
    RUNNING = "RUNNING"
    REVEAL = "REVEAL"
    COOLDOWN = "COOLDOWN"


_NEXT: dict[Phase, Phase] = {
    Phase.LOBBY: Phase.SEEDING,
    Phase.SEEDING: Phase.RUNNING,
    Phase.RUNNING: Phase.REVEAL,
    Phase.REVEAL: Phase.COOLDOWN,
    Phase.COOLDOWN: Phase.LOBBY,
}

# Pha nào cho `/join` đi thẳng vào ván sắp tới. Ngoài hai pha này thì vẫn nhận
# đăng ký nhưng `queued: true` — bất biến 3.
JOINABLE = (Phase.LOBBY, Phase.COOLDOWN)


@dataclass
class Registration:
    """Một loài do người lạ đăng ký. Chưa chắc đã vào được ván đang chạy."""

    client_id: str
    token: str
    species_id: str
    display_name: str
    persona: str
    league: str
    brain_tier: int
    pop: int
    model_name: str = ""
    traits: Any = None                 # Traits do server cấp lúc /join
    creature_ids: list[str] = field(default_factory=list)
    last_heartbeat: float = 0.0
    feral_since: int | None = None


class MatchRunner:
    """Đồng hồ của thế giới. Một tiến trình, một ván tại một thời điểm."""

    def __init__(
        self,
        seed: int | None = None,
        ticks: int = net_config.OPEN_MATCH_TICKS,
        tick_ms: int = net_config.TICK_MS_DEFAULT,
        clock=time.monotonic,
        log_dir: Path | str | None = "runs/open",
    ) -> None:
        # `log_dir=None` -> không ghi file nào. Test dùng chế độ này rồi cắm log
        # giả vào; nếu không, mỗi lần chạy bộ test lại rải file vào runs/open.
        self.log_dir = Path(log_dir) if log_dir is not None else None
        self.phase: Phase = Phase.LOBBY
        self.ticks_total = ticks
        self.tick_ms = tick_ms
        self.tick_no = 0
        self.match_no = 0
        self.match_id = "m_00000"
        self._clock = clock
        self._phase_started = clock()
        self._seed_source = random.Random(seed if seed is not None else 20260829)

        self.registrations: dict[str, Registration] = {}
        self.queued: dict[str, Registration] = {}
        self.decisions: dict[str, Any] = {}      # creature_id -> ActiveGoal chờ áp
        self.strategist = RemoteClientStrategist(self.decisions)
        # MỘT bản trí nhớ, dùng chung với đường cục bộ (N-16). Trước đây
        # `net.routes_work` giữ năm cuốn sổ riêng khoá theo `(match_id,
        # creature_id)`, và mỗi lần đường cục bộ có thêm gì thì đường mạng lại
        # thiếu đúng thứ ấy — năm lần trong một ngày. `routes_work` giờ chỉ tra
        # cứu vào đây.
        self.minds = Minds()
        self.strategist.minds = self.minds
        # Cẩm nang theo LOÀI, sống qua nhiều ván (W-16). Đọc từ đĩa lúc dựng
        # runner, dựng lại chuỗi vào `minds.handbooks` ở mỗi `_seed_match`.
        self.handbook_dir: Path | None = (
            self.log_dir / "handbooks" if self.log_dir is not None else None
        )
        self.handbooks: dict[str, Handbook] = {}

        self.log: LogWriter | None = None
        self.latencies: collections.deque[int] = collections.deque(
            maxlen=net_config.LATENCY_WINDOW
        )
        self.applied: set[str] = set()      # work_id đã áp — bất biến theo work_id
        # Người xem đăng ký hàng đợi vào đây. Vòng tick ĐẨY, không ai kéo — và
        # quan trọng hơn: không ai được vá `step`/`advance_phase` lúc chạy để
        # chen vào. Bản đầu của N-12 làm đúng thế: nó thay hai method của runner
        # bằng closure ngay trong handler WebSocket, và bọc luôn `runner.log`.
        # Hậu quả: hành vi của sim phụ thuộc vào việc CÓ AI ĐANG XEM HAY KHÔNG,
        # log đổi hình dạng khi có người xem, và vá hai lần thì chồng lên nhau.
        # Trình bày không bao giờ được chạm vào mô phỏng.
        self.subscribers: list = []
        self.frames: list[dict] = []
        # Sự kiện THÔ của từng khung, giữ lại để dựng bản REVEAL. Không bao giờ
        # gửi đi: nó mang `law_id`.
        self._frame_raw: list[list[dict]] = []
        self.world: World | None = None
        self.creatures: list[Creature] = []
        self.state: SimState | None = None
        self.rng = random.Random(0)
        self._laws: list = []          # RIÊNG TƯ. Xem bất biến 5.
        self.seed = 0
        self.map_name = net_config.MAP_ROTATION[0]
        # Chữ ký "đề bài" của vài ván gần nhất. Xem `_seed_match`.
        self._recent_law_sigs: collections.deque = collections.deque(
            maxlen=net_config.LAW_NOVELTY_WINDOW
        )
        self._event_records: list[dict[str, Any]] = []
        self._last_truth: dict[str, Any] | None = None
        self.victory: Victory | None = None          # điền ở REVEAL, xem `_close_log`
        self.stopped = False
        self.preparing = False
        self.preparation_failed = False

    def _record_event(self, t: int, kind: str, **fields: Any) -> None:
        row: dict[str, Any] = {
            "t": t,
            "kind": kind,
            "match_id": self.match_id,
            "creature_id": fields.get("creature_id"),
            "species_id": fields.get("species_id"),
            "client_id": fields.get("client_id"),
            "model_name": fields.get("model_name"),
        }
        row.update(fields)
        self._event_records.append(row)

    # ── ranh giới tin cậy ────────────────────────────────────────────────
    def compute_victory(self) -> None:
        """Ba bảng danh hiệu, tính MỘT lần khi ván kết thúc (W-14)."""
        from genesis.victory import from_files, victory_standings_from_data

        if self._event_records and self._last_truth is not None:
            try:
                self.victory = victory_standings_from_data(self._event_records, self._last_truth)
                return
            except Exception:
                self.victory = None

        log_p = self.log_dir / f"{self.match_id}.jsonl" if self.log_dir else None
        truth_p = self.log_dir / f"{self.match_id}.truth.json" if self.log_dir else None
        if not (log_p and truth_p and log_p.exists() and truth_p.exists()):
            self.victory = None
            return
        try:
            self.victory = from_files(log_p, truth_p)
        except Exception:          # bảng kết quả hỏng KHÔNG được làm gãy ván sau
            self.victory = None

    def laws_public(self) -> list[dict]:
        """Đường DUY NHẤT để luật thật rời khỏi server. Trước REVEAL: rỗng.

        Không thêm đường thứ hai. Mỗi chỗ đọc `self._laws` trực tiếp rồi tự quyết
        có gửi hay không là một chỗ để bất biến 5 hỏng trong im lặng.
        """
        if self.phase not in (Phase.REVEAL, Phase.COOLDOWN) or self.world is None:
            return []
        return [
            {
                "law_id": f"L{i}",
                "tier": law.tier(),
                "vi": to_vietnamese(law, self.world.surface_map),
            }
            for i, law in enumerate(self._laws)
        ]

    def public_state(self) -> dict:
        """Thứ ai cũng xem được, ở mọi pha. Danh sách TRẮNG, không phải danh sách đen.

        Danh sách đen ("bỏ trường laws ra") hỏng ngay lần đầu ai đó thêm trường mới.
        """
        return {
            "phase": str(self.phase),
            "match_id": self.match_id,
            "tick": self.tick_no,
            "ticks_total": self.ticks_total,
            "tick_ms": self.tick_ms,
            "late_tolerance": net_config.LATE_TOLERANCE,
            "species": sorted(r.species_id for r in self.registrations.values()),
            "n_creatures": len(self.creatures),
            "n_alive": sum(1 for c in self.creatures if c.alive),
            "seconds_in_phase": round(self._clock() - self._phase_started, 1),
            "preparing": self.preparing,
            "preparation_failed": self.preparation_failed,
        }

    # ── máy trạng thái ───────────────────────────────────────────────────
    def phase_budget(self) -> float:
        """Giây còn được ở lại pha hiện tại. RUNNING tính theo tick, không theo giây."""
        return {
            Phase.LOBBY: net_config.LOBBY_SECONDS,
            Phase.SEEDING: net_config.SEEDING_SECONDS,
            Phase.RUNNING: self.ticks_total * self.tick_ms / 1000.0,
            Phase.REVEAL: net_config.REVEAL_SECONDS,
            Phase.COOLDOWN: net_config.COOLDOWN_SECONDS,
        }[self.phase]

    def advance_phase(self) -> Phase:
        prev, self.phase = self.phase, _NEXT[self.phase]
        self._phase_started = self._clock()
        if prev is Phase.RUNNING:
            self._close_log()
            self.compute_victory()
        if self.phase is Phase.SEEDING:
            self._seed_match()
        elif self.phase is Phase.LOBBY:
            # Người xếp hàng vào sảnh của ván kế. Bất biến 3: họ chờ TỚI ĐÂY,
            # không được nhét vào giữa một ván đã bị khám phá một nửa.
            self.registrations.update(self.queued)
            self.queued.clear()
        return prev

    def _close_log(self) -> None:
        """Đóng log VÀ ghi file truth. Ván ở chế độ mở phải chấm được như ván Lab.

        Ghi truth ở đúng lúc rời RUNNING chứ không sớm hơn: file này là đáp án,
        và nó nằm trên đĩa của server — nhưng nó chỉ được sinh ra khi ván đã hết,
        nên không có cửa sổ thời gian nào mà nó vừa tồn tại vừa còn hữu ích cho
        kẻ đọc trộm.
        """
        self._record_event(self.tick_no, "RUN_END", ticks=self.tick_no)
        if self.world is not None and self._laws:
            self._last_truth = {
                "seed": self.seed,
                "arm": "STANDARD",
                "laws": [to_json(l) for l in self._laws],
                "surface_map": self.world.surface_map.cls_to_surface,
            }
        if self.log is None or self.log_dir is None:
            return
        self.log.write(self.tick_no, "RUN_END", ticks=self.tick_no)
        self.log.close()
        self.log = None
        if self._last_truth is not None and self.log_dir is not None:
            (self.log_dir / f"{self.match_id}.truth.json").write_text(
                json.dumps(self._last_truth, ensure_ascii=False),
                encoding="utf-8",
            )

    def _seed_match(self) -> None:
        steps = self._seed_steps()
        request = next(steps)
        while True:
            laws = generate_cached(request[0], arm=request[1])
            try:
                request = steps.send(laws)
            except StopIteration:
                return

    async def seed_match_async(self) -> None:
        """Only pure law preparation runs off-loop; commit stays on the owner loop."""
        self.preparing = True
        self.preparation_failed = False
        steps = self._seed_steps()
        try:
            request = next(steps)
            while True:
                laws = await asyncio.to_thread(generate_cached, request[0], arm=request[1])
                if self.stopped:
                    return
                try:
                    request = steps.send(laws)
                except StopIteration:
                    return
        except BaseException:
            self.preparation_failed = True
            raise
        finally:
            steps.close()
            self.preparing = False

    def _seed_steps(self):
        self.match_no += 1
        self.match_id = f"m_{self.match_no:05d}"
        self.seed = self._seed_source.randrange(1, 2**31 - 1)
        # Xoay vòng bản đồ theo số ván: người xem thấy thế giới đổi, và mỗi bản
        # đồ hỏi một câu khác nhau (W-15). Xoay theo `match_no` chứ không bốc
        # ngẫu nhiên — để "ván sau là bản đồ nào" đoán được, và người chơi biết
        # mình đang chờ cái gì.
        self.map_name = net_config.MAP_ROTATION[
            (self.match_no - 1) % len(net_config.MAP_ROTATION)
        ]
        # Bản đồ đi vào khoá đệm: sa mạc và quần đảo cho hai thế giới khác nhau,
        # nên cổng khả giải phải chạy theo cặp (bản đồ, seed) — trộn chung một
        # khoá là dùng lại một bộ luật đã được duyệt cho một thế giới khác.
        #
        # **Ván sau phải là một ĐỀ BÀI KHÁC.** Seed mới gần như luôn cho luật
        # mới, nhưng "gần như" không đủ: cả dự án đứng trên chỗ người chơi phải
        # TỰ TÌM ra luật, và một ván trùng đề với ván trước biến điểm của nó
        # thành điểm trí nhớ. Đó đúng là điều [W-16] cấm cẩm nang làm — chép đáp
        # án sang ván sau — chỉ khác là ở đây chính thế giới phát lại đề cũ.
        #
        # Chữ ký là bộ cặp (trigger, hệ quả): đó là "chủ đề" mà người chơi thật
        # sự suy luận về, và hai bộ luật cùng chủ đề là cùng một câu hỏi dù
        # `mag`/`dur` có khác. Bốc lại tối đa `LAW_NOVELTY_TRIES` lần rồi CHẤP
        # NHẬN — vòng lặp không giới hạn ở đây nghĩa là server treo im lặng khi
        # không gian luật của một bản đồ hẹp hơn cửa sổ, và một ván trùng đề tệ
        # hơn nhiều so với một ván không bao giờ bắt đầu.
        rerolls: list[int] = []
        try:
            from net.routes_work import clear_work_state
            clear_work_state()
        except Exception:
            pass
        for _attempt in range(net_config.LAW_NOVELTY_TRIES):
            laws = yield (self.seed, f"STANDARD@{self.map_name}")
            sig = self._law_signature(laws)
            if sig not in self._recent_law_sigs:
                break
            # Gom lại, ghi SAU khi log của ván mới được mở. Ghi ngay ở đây là
            # ghi vào `self.log` của ván TRƯỚC — mà `_close_log` đã đóng nó.
            rerolls.append(self.seed)
            self.seed = self._seed_source.randrange(1, 2**31 - 1)
        self._recent_law_sigs.append(sig)
        self._laws = laws
        self.world, self.creatures, self.state, self.rng = build_match(
            self.seed, map_name=self.map_name
        )
        self.tick_no = 0
        self.frames.clear()
        self._frame_raw.clear()
        self.decisions.clear()
        self.applied.clear()
        self.latencies.clear()
        try:
            from net.routes_work import clear_work_state
            clear_work_state()
        except Exception:
            pass
        self._event_records = []
        self._record_event(0, "RUN_START", seed=self.seed, ticks=self.ticks_total,
                           arm="STANDARD", n_laws=len(self._laws))
        for i, dropped in enumerate(rerolls):
            self._record_event(0, "LAW_REPEAT", seed=dropped,
                               map=self.map_name, attempt=i + 1)
        if self.log_dir is not None:
            self.log = LogWriter(self.log_dir / f"{self.match_id}.jsonl", self.match_id)
            self.log.write(0, "RUN_START", seed=self.seed, ticks=self.ticks_total,
                           arm="STANDARD", n_laws=len(self._laws))
            for i, dropped in enumerate(rerolls):
                # Đề trùng với một ván gần đây nên bốc lại. Đáng ghi: nếu dòng
                # này xuất hiện đều thì không gian luật của bản đồ đó hẹp hơn
                # `LAW_NOVELTY_WINDOW`, và cửa sổ mới là thứ phải sửa.
                self.log.write(0, "LAW_REPEAT", seed=dropped,
                               map=self.map_name, attempt=i + 1)
        # Bất biến 2: sảnh trống thì ván vẫn chạy — quần thể mặc định của
        # config.POPULATION đóng vai bot, và loài người thật cắm lên trên.
        #
        # Sinh vật của người chơi phải ra đời **ở đây**, tại SEEDING, chứ không
        # phải lúc client gọi `/work` lần đầu. Bản đầu tạo chúng trong handler
        # HTTP và hỏng ba đường cùng lúc: chúng đứng chồng nhau ở ô passable đầu
        # tiên quét theo hàng (không phải chỗ ngẫu nhiên như `spawn_population`);
        # quần thể đổi giữa chừng một tick nên log không tái lập được; và loài
        # nào không kịp poll thì mất luôn những tick đầu.
        self._spawn_registered()
        # Sau `_spawn_registered`, vì danh sách loài chỉ đầy đủ khi sinh vật của
        # người chơi đã ra đời.
        self.minds.new_match()
        self._load_handbooks()

    def _load_handbooks(self) -> None:
        """Dựng khối cẩm nang cho từng loài của ván này (W-16 ở chế độ mở).

        Cẩm nang là tầng trí nhớ thứ ba: sổ tay và Sổ Luật chết theo ván, cẩm
        nang thì không. Trước N-16 nó chỉ tồn tại ở đường cục bộ, nên chế độ mở
        — nơi cùng một người chơi thật sự chơi nhiều ván liên tiếp — lại là chế
        độ **duy nhất không có trí nhớ qua ván**, đúng ngược lại.

        Khoá theo `species_id`, y như đường cục bộ. `n_matches` tăng một lần mỗi
        ván, ở đây, chứ không phải mỗi lần dựng prompt.
        """
        for species_id in sorted({c.species for c in self.creatures}):
            hb = self.handbooks.get(species_id)
            if hb is None:
                hb = (Handbook.load(species_id, self.handbook_dir)
                      if self.handbook_dir is not None
                      else Handbook(species_id=species_id))
                self.handbooks[species_id] = hb
            hb.n_matches += 1
            if self.handbook_dir is not None:
                hb.save(self.handbook_dir)
            text = hb.render()
            if text:
                self.minds.handbooks[species_id] = text
            else:
                self.minds.handbooks.pop(species_id, None)

    @staticmethod
    def _law_signature(laws: list) -> tuple:
        """"Đề bài" của một ván: bộ cặp (trigger, hệ quả), không kể mag/dur.

        Cố ý THÔ. Hai bộ luật chỉ khác cường độ là cùng một câu hỏi đối với
        người đang đi tìm, và phân biệt chúng thì cửa sổ chống trùng gần như
        không bao giờ chặn được gì — đúng lỗi mà [R-04] đã gặp một lần: khoá quá
        mịn thì "chia theo bộ luật" chỉ là chia theo seed dưới một cái tên khác.
        """
        return tuple(sorted(
            (l.trigger.kind.value, l.effect.kind.value) for l in laws
        ))

    def _spawn_registered(self) -> None:
        from genesis.creature import Creature

        # Ván mới, bảng slot mới. `slots` trả lời đúng một câu cho `genesis.tick`:
        # "con này có ai ở đầu kia dây không". Không xoá thì id của ván trước còn
        # nằm đó, và một con BOT trùng id sẽ bị coi là có model — nó chờ một câu
        # trả lời không bao giờ tới, và bỏ luôn lượt dịch trait của mình.
        self.strategist.slots.clear()
        self.strategist.pending_say.clear()
        self.strategist.shift_choice.clear()
        self.strategist.shift_why.clear()
        self.strategist.want_shift.clear()
        self.strategist._shift_asked.clear()

        for cid in sorted(self.registrations):
            reg = self.registrations[cid]
            if reg.traits is None:
                continue
            # Ba đặc điểm cho loài của NGƯỜI LẠ, bằng ĐÚNG luật của bot (W-19).
            if self.world is not None and reg.species_id not in self.world.kits:
                self.world.kits[reg.species_id] = kit_of(
                    roll_for_species(reg.species_id, self.seed))
            sample = Creature(
                id=f"{reg.species_id}:0",
                species=reg.species_id,
                traits=reg.traits,
                pos=(0, 0),
                hp=1.0,
                energy=1.0,
            )
            cells: list[tuple[int, int]] = [
                (x, y)
                for y in range(self.world.h)
                for x in range(self.world.w)
                if self.world.passable((x, y), sample)
            ] if self.world is not None else []
            if not cells:
                continue
            reg.creature_ids = []
            for i in range(max(1, reg.pop)):
                c = Creature(
                    id=f"{reg.species_id}:{i}",
                    species=reg.species_id,
                    traits=reg.traits,
                    pos=self.rng.choice(cells),
                    hp=float(config.HP_MAX),
                    energy=reg.traits.energy_max,
                )
                self.creatures.append(c)
                reg.creature_ids.append(c.id)
                self.strategist.slots[c.id] = len(self.strategist.slots)
        self.creatures.sort(key=creature_sort_key)

    def step(self) -> None:
        """Một tick sim. Chỉ hợp lệ ở RUNNING."""
        if self.phase is not Phase.RUNNING or self.world is None or self.state is None:
            return
        frame_log = _FrameCollector(self.log, on_record=self._record_event)
        run_tick(
            self.world, self.creatures, self.tick_no, self.rng, self.state,
            laws=self._laws, strategist=self.strategist, log=frame_log,
        )
        self._absorb_speech_for_clients(frame_log.events)
        self._forget_for_dead(frame_log.events)
        self._publish(self.tick_no, frame_log.events)
        self.tick_no += 1

    def _absorb_speech_for_clients(self, events: list[dict]) -> None:
        """Lời nói, dạy nhau, sổ ghi công — cùng một hàm mà đường cục bộ gọi.

        Trước N-16 hàm này tự đổ `render_heard` vào một cuốn sổ riêng của
        `routes_work` và **dừng ở đó**: phần dạy nhau (`say.teach`) bị bỏ, nên
        `Ledger` ở chế độ mở luôn rỗng và danh tiếng không bao giờ được cập
        nhật. Hậu quả là B-12 — công chảy một nấc, đo nói dối, chống farming —
        không tồn tại ở đúng chế độ có người lạ, tức đúng chế độ có động cơ để
        farm.

        Giờ nó gọi thẳng `Minds.absorb_speech`. Một bản logic, hai đường gọi.
        """
        by_id = {c.id: c for c in self.creatures}
        speak = [ev for ev in events if ev.get("kind") == "SPEAK"]
        if speak:
            self.minds.absorb_speech(self.tick_no, self.world, by_id, speak)

    def _forget_for_dead(self, events: list[dict]) -> None:
        """Sang đời mới thì sổ tay chết theo, Sổ Luật bớt chắc chắn (W-17).

        Đường cục bộ làm việc này trong `strategist.observe`, nhưng
        `RemoteClientStrategist` không có `observe` — nên chế độ mở cần móc
        riêng. Logic thật nằm ở `Minds.on_death` (rồi `lineage.forget_on_death`),
        một chỗ, cả hai đường gọi vào.
        """
        for ev in events:
            if ev.get("kind") == "DEATH":
                cid = ev.get("creature_id")
                if isinstance(cid, str):
                    self.minds.on_death(cid)

    def _publish(self, tick_no: int, events: list[dict]) -> None:
        frame = self.frame(tick_no, events)
        self.frames.append(frame)
        self._frame_raw.append(events)
        for q in list(self.subscribers):
            with contextlib.suppress(Exception):  # hàng đợi đầy: bỏ khung, đừng làm chậm ván
                q.put_nowait(frame)

    def reveal_frames(self) -> list[dict]:
        """Cùng những khung ấy, `law` điền đầy đủ (bất biến 5).

        Giữ nguyên ảnh chụp thế giới của từng khung và chỉ dựng lại phần sự
        kiện: dựng lại cả khung thì mọi khung đều mang trạng thái CUỐI ván, và
        bản phát lại thành một ảnh tĩnh lặp đi lặp lại.
        """
        pub = {l["law_id"]: l["vi"] for l in self.laws_public()}
        out = []
        for f, raw in zip(self.frames, self._frame_raw):
            g = dict(f)
            g["phase"] = str(self.phase)
            g["events"] = [_public_event(e, True, pub) for e in raw]
            out.append(g)
        return out

    def frame(self, tick_no: int, events: list[dict]) -> dict:
        """Một khung cho người xem (05 §3.8).

        Mang theo **trait hiện tại** của từng con, không phải trait khai sinh:
        hình vẽ suy từ trait (N-12 bất biến 4), mà trait dịch giữa ván. Trang xem
        tự tra bảng founder thì nó sẽ vẽ sai ngay lần dịch trait đầu tiên, và sai
        hẳn với loài do người lạ tạo ra lúc chạy.
        """
        reveal = self.phase in (Phase.REVEAL, Phase.COOLDOWN)
        pub = {l["law_id"]: l["vi"] for l in self.laws_public()}
        return {
            **envelope(self.match_id),
            "t": tick_no,
            "phase": str(self.phase),
            "w": self.world.w if self.world else 0,
            "h": self.world.h if self.world else 0,
            "creatures": [
                creature_telemetry(self, c)
                for c in sorted(self.creatures, key=creature_sort_key)
            ],
            "plants": [list(p) for p in sorted(self.world.fruits)] if self.world else [],
            "corpses": [list(p) for p in sorted(self.world.corpses)] if self.world else [],
            "terrain_delta": [],
            "map": self.world.map_name if self.world else "",
            # Địa hình 24×24 là ~3 KB; gửi mỗi tick thì nó chiếm gần hết băng
            # thông của luồng xem. Gửi ở tick 0, và `spectate` nhét thêm vào
            # khung đầu tiên của mỗi người xem mới — trang 3D tự nhớ.
            "terrain": self.terrain_rows() if tick_no == 0 else None,
            "weather": (
                self.world.weather.to_dict(diurnal=getattr(self.world, "phase", "DAY"))
                if (self.world and hasattr(self.world, "weather") and self.world.weather is not None)
                else weather_at(self.seed, tick_no).to_dict(diurnal="DAY")
            ),
            "events": [_public_event(e, reveal, pub) for e in events],
        }

    def terrain_rows(self) -> list[str] | None:
        if self.world is None:
            return None
        # `TERRAIN_CODE`, không phải một chuỗi chép tay. Bản cũ giữ `"PWBRF"`
        # cùng một tuple thứ tự song song, nên thêm một địa hình là ném
        # `ValueError: tuple.index(x): x not in tuple` ngay giữa vòng phát khung
        # — người xem mất hình, và lỗi hiện ra ở tầng trình bày chứ không ở chỗ
        # thật sự thay đổi.
        from genesis.world import TERRAIN_CODE

        return ["".join(TERRAIN_CODE[t] for t in row) for row in self.world.grid]

    # ── N-08: tick không chờ ai ──────────────────────────────────────────
    def _write(self, kind: str, **fields: Any) -> None:
        self._record_event(self.tick_no, kind, **fields)
        if self.log is not None:
            self.log.write(self.tick_no, kind, **fields)

    def on_decision(self, issued_tick: int, work_id: str, apply_fn) -> str:
        """Nhận một quyết định về muộn. Trả 'applied' | 'dropped' | 'duplicate'.

        Chịu được trễ là vì tầng chiến lược trả **goal có TTL 2–12 tick**, không
        trả nước đi: một ý đồ về muộn một hai tick vẫn còn giá trị. Nếu client
        trả nước đi thì trễ một tick là hỏng — đó là lý do thứ hai (sau tiết kiệm
        token) khiến kiến trúc hai tầng là lựa chọn đúng.
        """
        if work_id in self.applied:
            # Bất biến theo work_id (05 §3.4): gửi lại thì bỏ qua, KHÔNG phải lỗi.
            return "duplicate"
        # Ngưỡng lấy đúng theo 05 §3.4: `deadline_tick = issued + LATE_TOLERANCE`,
        # và quá hạn là `> deadline + LATE_TOLERANCE`. Con số này phải nằm ở ĐÚNG
        # MỘT chỗ — tầng HTTP quyết định hình dạng phản hồi, không quyết định
        # muộn hay không.
        k = self.tick_no - issued_tick
        if k > 2 * net_config.LATE_TOLERANCE:
            self._write("DECISION_LATE", work_id=work_id, latency_ticks=k)
            return "dropped"
        # Bất biến 3: muộn không có nghĩa là được tin — `apply_fn` vẫn phải
        # validate. Hàm này chỉ quyết định CÓ KỊP hay không.
        apply_fn()
        self.applied.add(work_id)
        self.latencies.append(k)
        self._write("THINK_LATENCY", work_id=work_id, latency_ticks=k)
        return "applied"

    def adjust_tick_rate(self) -> int:
        """Nhịp chung theo p90 độ trễ. Không ưu đãi riêng cho ai."""
        if not self.latencies:
            return self.tick_ms
        xs = sorted(self.latencies)
        p90 = xs[min(len(xs) - 1, int(0.9 * len(xs)))]
        factor = (
            net_config.TICK_RATE_UP if p90 > net_config.LATE_TOLERANCE
            else net_config.TICK_RATE_DOWN
        )
        new = int(max(net_config.TICK_MS_MIN,
                      min(net_config.TICK_MS_MAX, self.tick_ms * factor)))
        if new != self.tick_ms:
            self.tick_ms = new
            self._write("TICK_RATE", tick_ms=new, p90_latency=p90)
        return self.tick_ms

    # ── N-09: hoang dã ───────────────────────────────────────────────────
    def heartbeat(self, client_id: str) -> bool:
        reg = self.registrations.get(client_id) or self.queued.get(client_id)
        if reg is None:
            return False
        reg.last_heartbeat = self._clock()
        if reg.feral_since is not None:
            reg.feral_since = None
            self._write("NODE_DOWN", client_id=client_id, feral=False)
        return True

    def sweep_health(self) -> None:
        """Bỏ 3 nhịp -> hoang dã. Quá FERAL_GRACE tick -> gỡ loài.

        Loài KHÔNG biến mất ngay khi mất kết nối: nếu không thì ai sắp chết cũng
        rút dây. Nó rơi về tầng phản xạ của server và bị đánh dấu hoang dã.
        """
        now = self._clock()
        limit = net_config.HEARTBEAT_MS * net_config.HEARTBEAT_MISS / 1000.0
        for cid, reg in list(self.registrations.items()):
            if reg.last_heartbeat and now - reg.last_heartbeat <= limit:
                continue
            if reg.feral_since is None:
                reg.feral_since = self.tick_no
                self._write("NODE_DOWN", client_id=cid, species_id=reg.species_id,
                            feral=True)
            elif self.tick_no - reg.feral_since >= net_config.FERAL_GRACE:
                del self.registrations[cid]
                self._write("NODE_DOWN", client_id=cid, species_id=reg.species_id,
                            feral=True, removed=True)

    def reclaim(self, client_id: str, token: str) -> Registration | None:
        """Quay lại trong thời hạn thì nhận lại loài CŨ.

        Cùng `creature_ids`, cùng Sổ Luật, cùng danh tiếng. Cấp loài mới là xoá
        sạch dữ liệu của người ta vì lỗi của WiFi.
        """
        reg = self.registrations.get(client_id)
        if reg is None or reg.token != token:
            return None
        reg.feral_since = None
        reg.last_heartbeat = self._clock()
        return reg

    def is_feral(self, client_id: str) -> bool:
        reg = self.registrations.get(client_id)
        return reg is not None and reg.feral_since is not None

    async def loop(self) -> None:
        """Nhịp đồng hồ tường. Vòng lặp này KHÔNG BAO GIỜ chờ client.

        Đó là toàn bộ lý do chế độ mở chạy được sau mọi NAT: ai trả lời kịp thì
        quyết định của họ vào ván, ai không thì con vật của họ hành xử theo phản
        xạ ở tick đó. Xem [N-08]. Chờ một client là để một máy ở đâu đó quyết
        định tốc độ của cả thế giới.
        """
        while not self.stopped:
            if self.phase is Phase.RUNNING:
                # Bẫy N-08 §3: hạn chót tính bằng `monotonic`, không bằng `time`.
                # Đồng hồ hệ thống nhảy (NTP, đổi múi giờ) sẽ làm ván đứng hình
                # hoặc chạy vọt, và ta sẽ đổ lỗi cho mạng.
                deadline = self._clock() + self.tick_ms / 1000.0
                self.step()
                self.sweep_health()
                if self.tick_no % net_config.TICK_RATE_EVERY == 0:
                    self.adjust_tick_rate()
                if self.tick_no >= self.ticks_total:
                    self.advance_phase()
                    continue
                # Ngủ tới HẠN CHÓT, không ngủ đủ `tick_ms`: thời gian của `step`
                # phải nằm TRONG nhịp, nếu không ván trôi dần mỗi tick một ít.
                await asyncio.sleep(max(0.0, deadline - self._clock()))
            else:
                if self._clock() - self._phase_started >= self.phase_budget():
                    if self.phase is Phase.LOBBY:
                        self.phase = Phase.SEEDING
                        self._phase_started = self._clock()
                        await self.seed_match_async()
                        self._phase_started = self._clock()
                    else:
                        self.advance_phase()
                await asyncio.sleep(0.05)
