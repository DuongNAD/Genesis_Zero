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
from dataclasses import dataclass, field
from enum import StrEnum
import random
import time
from typing import Any

import json
from pathlib import Path

import net_config
from genesis import config, law_config
from dataclasses import astuple
from genesis.creature import Creature, creature_sort_key
from genesis.lawdsl import to_json, to_vietnamese
from genesis.logio import LogWriter
from genesis.lawgen import generate_cached
from genesis.strategist import RemoteClientStrategist
from genesis.tick import build_match, tick as run_tick


class _FrameCollector:
    """Ống chữ Y: sự kiện đi vào log THẬT và đồng thời gom lại cho người xem.

    Không phải một bộ bọc thay `runner.log`: `run_tick` nhận nó cho đúng một
    tick rồi bỏ, nên không có trạng thái nào sống lâu hơn một tick và log thật
    không bao giờ đổi hình dạng.
    """

    def __init__(self, inner) -> None:
        self.inner = inner
        self.events: list[dict] = []

    def write(self, t: int, kind: str, **fields) -> None:
        self.events.append({"kind": kind, **fields})
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

        self.log = None
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
        self.world = None
        self.creatures: list[Creature] = []
        self.state = None
        self.rng = random.Random(0)
        self._laws: list = []          # RIÊNG TƯ. Xem bất biến 5.
        self.seed = 0
        self.map_name = net_config.MAP_ROTATION[0]
        self.victory = None          # điền ở REVEAL, xem `_close_log`
        self.stopped = False

    # ── ranh giới tin cậy ────────────────────────────────────────────────
    def compute_victory(self) -> None:
        """Ba bảng danh hiệu, tính MỘT lần khi ván kết thúc (W-14)."""
        from genesis.victory import from_files

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
        if self.log is None or self.log_dir is None:
            return
        self.log.write(self.tick_no, "RUN_END", ticks=self.tick_no)
        self.log.close()
        self.log = None
        if self.world is not None and self._laws:
            (self.log_dir / f"{self.match_id}.truth.json").write_text(
                json.dumps({
                    "seed": self.seed, "arm": "STANDARD",
                    "laws": [to_json(l) for l in self._laws],
                    "surface_map": self.world.surface_map.cls_to_surface,
                }, ensure_ascii=False),
                encoding="utf-8",
            )

    def _seed_match(self) -> None:
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
        self.world, self.creatures, self.state, self.rng = build_match(
            self.seed, map_name=self.map_name
        )
        # Bản đồ đi vào khoá đệm: sa mạc và quần đảo cho hai thế giới khác nhau,
        # nên cổng khả giải phải chạy theo cặp (bản đồ, seed) — trộn chung một
        # khoá là dùng lại một bộ luật đã được duyệt cho một thế giới khác.
        self._laws = generate_cached(self.seed, arm=f"STANDARD@{self.map_name}")
        self.tick_no = 0
        self.frames.clear()
        self._frame_raw.clear()
        self.decisions.clear()
        self.applied.clear()
        self.latencies.clear()
        if self.log_dir is not None:
            self.log = LogWriter(self.log_dir / f"{self.match_id}.jsonl", self.match_id)
            self.log.write(0, "RUN_START", seed=self.seed, ticks=self.ticks_total,
                           arm="STANDARD", n_laws=len(self._laws))
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

    def _spawn_registered(self) -> None:
        from genesis.creature import Creature

        cells = [
            (x, y)
            for y in range(self.world.h)
            for x in range(self.world.w)
            if self.world.passable((x, y))
        ]
        for cid in sorted(self.registrations):
            reg = self.registrations[cid]
            if reg.traits is None:
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
        self.creatures.sort(key=creature_sort_key)

    def step(self) -> None:
        """Một tick sim. Chỉ hợp lệ ở RUNNING."""
        if self.phase is not Phase.RUNNING or self.world is None:
            return
        frame_log = _FrameCollector(self.log)
        run_tick(
            self.world, self.creatures, self.tick_no, self.rng, self.state,
            laws=self._laws, strategist=self.strategist, log=frame_log,
        )
        self._absorb_speech_for_clients(frame_log.events)
        self._forget_for_dead(frame_log.events)
        self._publish(self.tick_no, frame_log.events)
        self.tick_no += 1

    def _absorb_speech_for_clients(self, events: list[dict]) -> None:
        """Đổ lời nghe được vào hàng của từng cá thể (B-11).

        Vòng tick đã tính sẵn AI nghe được gì (`hear_full` / `hear_signal`) —
        đây chỉ là đổ sang chỗ `routes_work` đọc. Trước đó đường mạng truyền
        thẳng `heard=()`, tức **người chơi qua mạng không bao giờ nghe thấy
        ai**: cả tầng xã hội không tồn tại ở chế độ mở, và câu hỏi Q2 của dự án
        ("giao tiếp đáng giá bao nhiêu?") không đo được ở đúng chế độ sinh ra
        để hỏi nó.

        CHƯA có phần dạy nhau (`teach`) và sổ ghi công — xem
        `docs/tasks/N-16-ngang-bang-mang.md`.
        """
        from genesis import law_config, speech
        from net import routes_work

        mid = self.match_id
        for ev in events:
            if ev.get("kind") != "SPEAK":
                continue
            say = speech.Say(ev.get("signal"), ev.get("text"), ev.get("teach"))
            for ids, full in ((ev.get("hear_full") or (), True),
                              (ev.get("hear_signal") or (), False)):
                for hid in ids:
                    q = routes_work._heard.setdefault((mid, hid), [])
                    q.append(speech.render_heard(ev["creature_id"], say, full=full))
                    del q[:-law_config.HEARD_MAX]

    def _forget_for_dead(self, events: list[dict]) -> None:
        """Sang đời mới thì sổ tay chết theo, Sổ Luật bớt chắc chắn (W-17).

        Đường cục bộ làm việc này trong `strategist.observe`, nhưng ở chế độ mở
        sổ tay và Sổ Luật nằm ở `net.routes_work`, và `RemoteClientStrategist`
        không có `observe`. Thiếu móc này thì **người chơi qua mạng chơi một trò
        khác người chơi cục bộ**: sinh vật của họ giữ nguyên sổ tay thô qua mọi
        đời, đúng ngược lại thiết kế.

        Đây là lần thứ ba cùng một họ lỗi trong dự án — hai đường chạy, một
        đường bị bỏ quên. Hai lần trước: `schema_for` thiếu `targets` lẫn `sm`,
        và `founder_traits` không biết loài đăng ký lúc chạy. Nên logic thật
        nằm trong `lineage.forget_on_death`, một chỗ, cả hai đường gọi vào.

        Nhập trong hàm để khỏi vòng phụ thuộc: `routes_work` đã nhập `net.match`.
        """
        from genesis.lineage import forget_on_death
        from net import routes_work

        mid = self.match_id
        for ev in events:
            if ev.get("kind") != "DEATH":
                continue
            key = (mid, ev.get("creature_id"))
            if key in routes_work._notes or key in routes_work._codices:
                forget_on_death(routes_work._notes.get(key),
                                routes_work._codices.get(key))

    def _publish(self, tick_no: int, events: list[dict]) -> None:
        frame = self.frame(tick_no, events)
        self.frames.append(frame)
        self._frame_raw.append(events)
        for q in list(self.subscribers):
            try:
                q.put_nowait(frame)
            except Exception:      # hàng đợi đầy: bỏ khung, đừng làm chậm ván
                pass

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
        feral_species = {
            r.species_id for cid, r in self.registrations.items() if self.is_feral(cid)
        }
        return {
            "t": tick_no,
            "phase": str(self.phase),
            "w": self.world.w if self.world else 0,
            "h": self.world.h if self.world else 0,
            "creatures": [
                {
                    "id": c.id, "x": c.pos[0], "y": c.pos[1],
                    "hp": round(c.hp, 1), "e": round(c.energy, 1),
                    "e_max": round(c.traits.energy_max, 1),
                    "alive": c.alive, "feral": c.species in feral_species,
                    "tr": list(astuple(c.traits)),
                }
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
            "events": [_public_event(e, reveal, pub) for e in events],
        }

    def terrain_rows(self) -> list[str] | None:
        if self.world is None:
            return None
        return ["".join("PWBRF"[
            ("PLAIN", "WATER", "BUSH", "ROCK", "FIRE").index(str(t))
        ] for t in row) for row in self.world.grid]

    # ── N-08: tick không chờ ai ──────────────────────────────────────────
    def _write(self, kind: str, **fields: Any) -> None:
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
                    self.advance_phase()
                await asyncio.sleep(0.05)
