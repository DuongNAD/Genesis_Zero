"""Genesis Zero — strategist: tầng chiến lược và các hiện thực ra quyết định."""

from __future__ import annotations

import asyncio
import collections
import queue
import random
import time
from typing import TYPE_CHECKING, Any, Iterable, Protocol, runtime_checkable

import httpx

from genesis import config, law_config, law_config
from genesis.codex import Codex
from genesis.fieldnotes import FieldNotes, Note
from genesis.lawdsl import Dur, Mag, vocab_for_brain
from genesis.lineage import forget_on_death
from genesis.minds import Minds
from genesis.llm_client import CircuitBreaker, ask
from genesis.lawdsl import Law, to_json
from genesis.prompt import PromptCache, _PHASE_VN, _TERRAIN_VN, prompt_hash, user_block
from genesis.provenance import Ledger, law_key
from genesis import speech
from genesis.reflex import ActiveGoal, Goal, choose_goal
from genesis.traits import Traits
from genesis.reveal import law_from_surface_dict
from genesis.validate import (ARG_DOMAIN, Verdict, validate_codex,
                              validate_decide, validate_hunch, validate_shift)
from genesis.world import phase_at

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.world import World


def legal_args(sm=None) -> list[str]:
    """Mọi giá trị `arg` hợp lệ trong LawDSL, gộp lại thành một enum.

    JSON Schema không nói gọn được "arg phụ thuộc kind", nên ta chặn ở mức thô:
    một enum của TẤT CẢ giá trị hợp lệ. Nó không ngăn được cặp kind/arg vô nghĩa
    — `validate_codex` lo phần đó — nhưng nó ngăn được thứ nguy hiểm hơn: **một
    chuỗi model tự bịa ra**.

    Vì sao cần: model thật đầu tiên phát biểu đúng luật rồi **dịch bề mặt sang
    tiếng Trung** — `"arg": "紫扁果"` thay vì `"quả tím dẹt"` (Qwen là model
    Trung Quốc). `validate_codex` từ chối với `CODEX_UNKNOWN_SURFACE`, và nếu
    không nhìn vào `raw` thì ta sẽ kết luận nhầm rằng nó **không suy ra được
    luật** — trong khi nó suy ra đúng và chỉ viết sai thứ tiếng.
    """
    from genesis.lawdsl import CondKind, TriggerKind

    args = ["CORPSE", "SAME_SP", "OTHER_SP", "ANY",
            "PLAIN", "WATER", "BUSH", "ROCK", "FIRE",
            "DAY", "NIGHT", "LOW", "MID", "HIGH", "YOUNG", "OLD",
            "WITH", "AGAINST", "ALARM", "AGGR", "SUBM", "NEUTRAL"]
    args += [t.value for t in TriggerKind]      # cond RECENT nhận tên hành động
    args += [c.value for c in CondKind]
    if sm is not None:
        args += list(sm.cls_to_surface.values())
    return sorted(set(args))


# Kind nhận BỀ MẶT (đổi mỗi ván) chứ không phải một enum cố định.
SURFACE_KINDS = frozenset({"EAT", "SPAWN"})


def _arg_options(kind: str, sm=None) -> list[str] | None:
    """Các giá trị `arg` hợp lệ của một kind.

    `None` = để mở (không nêu enum); `[]` = kind này KHÔNG nhận arg.
    Nguồn sự thật là `validate.ARG_DOMAIN` — **cùng một bảng** mà bộ xác thực
    dùng để bắt bẻ. Hai bảng riêng thì sẽ có ngày lệch nhau, và triệu chứng là
    model bị từ chối vì một thứ schema vừa bảo nó được phép viết.
    """
    if kind in SURFACE_KINDS:
        return None if sm is None else sorted(sm.cls_to_surface.values()) + ["CORPSE"]
    d = ARG_DOMAIN.get(kind)
    return None if d is None else list(d)


# Dùng cho test: các kind mà `ARG_DOMAIN` khai miền RỖNG = không nhận arg.
ARGLESS_KINDS_FOR_TEST = frozenset(k for k, v in ARG_DOMAIN.items() if not v)


def _effect_schema(names: list[str], sm=None) -> dict:
    """Schema khối `effect`, BẮT BUỘC đúng những trường hệ quả ấy thật sự mang.

    Nguồn là `lawdsl.EFFECT_FIELDS` — cùng bảng `random_law` dùng để sinh.

    **Vì sao bắt buộc chứ không để tuỳ.** `verify.agree` nhân điểm trên từng
    chiều mà luật THẬT có định nghĩa; thiếu một chiều thì chiều ấy ăn **0** và
    kéo cả tích về 0. Nên một mục đúng trigger, đúng điều kiện, đúng loại hệ
    quả mà quên `dur` vẫn ăn đúng **0 điểm**.

    Đo trên toàn bộ 235 mục Sổ Luật ghi được trong ngày: **chỉ 23% nêu cả `mag`
    lẫn `dur`**. 77% dữ liệu **không thể ăn điểm về mặt cấu trúc** — kể cả mục
    `WHEN DRINK THEN DAMAGE` mà Qwen-14B viết ở tick 99, **đúng nguyên văn luật
    thật**, nhưng thiếu `dur` nên `match = 0.000`.

    Đây là lần thứ sáu cùng một bài học của [B-01]: **cái gì bộ chấm hay bộ xác
    thực bắt bẻ thì schema phải đòi trước.** Để model tự đoán là bắt nó khám phá
    lại luật chơi bằng chính lượt nghĩ dành để khám phá thế giới.

    Không nới `agree` để "cho điểm phần đúng": một luật không nêu `mag`/`dur`
    khớp với MỌI cường độ, và trả điểm cho nó là trả điểm cho sự mơ hồ.
    """
    from genesis.lawdsl import EFFECT_FIELDS

    field_schema = {
        "mag": {"type": "string", "enum": [m.value for m in Mag]},
        "dur": {"type": "string", "enum": [d.value for d in Dur]},
        "r": {"type": "integer", "minimum": 1, "maximum": 3},
    }
    # Gộp các hệ quả CÙNG bộ trường vào một nhánh: 9 hệ quả mag+dur còn 1 nhánh.
    by_fields: dict[tuple[str, ...], list[str]] = {}
    for n in names:
        by_fields.setdefault(EFFECT_FIELDS.get(n, ()), []).append(n)

    branches: list[dict] = []
    for fields, kinds in by_fields.items():
        props: dict[str, Any] = {"kind": {"type": "string", "enum": kinds}}
        req = ["kind"]
        for f in fields:
            if f == "arg":
                opts = _arg_options(kinds[0], sm)
                if opts is None:
                    if sm is None:
                        continue        # không có bề mặt -> đừng đòi thứ không nêu được
                    opts = sorted(sm.cls_to_surface.values()) + ["CORPSE"]
                props["arg"] = {"type": "string", "enum": opts}
            else:
                props[f] = field_schema[f]
            req.append(f)
        branches.append({"type": "object", "properties": props,
                         "required": req, "additionalProperties": False})
    if not branches:
        return {"type": "object", "properties": {"kind": {"type": "string"}},
                "required": ["kind"]}
    return branches[0] if len(branches) == 1 else {"oneOf": branches}


def _kind_arg_schema(names: list[str], sm, extra: dict) -> dict:
    """Schema cho một khối {kind, arg, ...}, TÁCH NHÁNH theo miền `arg` của kind.

    Một enum `arg` phẳng dùng chung cho mọi kind làm `ARMOR_UP(TERRAIN)`,
    `HEAL(EAT)` và `AGE=FIRE` thành **hợp lệ về cấu trúc**. Model 7B viết đúng
    những thứ ấy: ván seed 55 có 9 mục sổ được nhận vào sổ, 5 mục thuộc loại
    này, và cả 5 ăn `match = 0.0` — chúng không thể khớp luật nào, vì luật thật
    để `arg=None`. Mỗi mục tiêu một ô sổ và một `CLAIM_COOLDOWN`, không đổi lấy
    gì.

    Tách bằng `oneOf` làm cặp kind/arg vô nghĩa thành **bất khả về cấu trúc** —
    cùng nước đi đã dẹp `SEMANTIC_TARGET_NOT_FOUND` bằng enum `target`. Đã thử
    trên llama.cpp b9430: `oneOf` dịch ra GBNF chạy đúng, model nhả
    `{"kind": "DAMAGE", "dur": "SHORT"}` — không kèm `arg`.

    Gộp các kind CÙNG miền vào một nhánh để grammar khỏi phình: 9 cond gom còn
    4 nhánh.
    """
    argless: list[str] = []
    open_: list[str] = []
    by_domain: dict[tuple[str, ...], list[str]] = {}
    for n in names:
        opts = _arg_options(n, sm)
        if opts is None:
            open_.append(n)
        elif not opts:
            argless.append(n)
        else:
            by_domain.setdefault(tuple(opts), []).append(n)

    def branch(kinds: list[str], arg_schema: dict | None) -> dict:
        props: dict[str, Any] = {"kind": {"type": "string", "enum": kinds}, **extra}
        req = ["kind"]
        if arg_schema is not None:
            props["arg"] = arg_schema
            req.append("arg")
        return {"type": "object", "properties": props, "required": req,
                "additionalProperties": False}

    branches: list[dict] = []
    if argless:
        branches.append(branch(argless, None))
    if open_:
        # Vẫn giữ enum phẳng cho nhóm để mở: nó không chặn được cặp vô nghĩa
        # nhưng chặn được thứ nguy hiểm hơn — một chuỗi model tự bịa. Model thật
        # từng viết bề mặt bằng tiếng Trung (`"紫扁果"`) và ta suýt kết luận nhầm
        # rằng nó không suy ra được luật.
        branches.append(branch(open_, {"type": "string", "enum": legal_args(sm)}))
    for dom, kinds in by_domain.items():
        branches.append(branch(kinds, {"type": "string", "enum": list(dom)}))

    if not branches:            # từ vựng rỗng — đừng trả `oneOf: []`
        return {"type": "object", "properties": {"kind": {"type": "string"}, **extra},
                "required": ["kind"]}
    # Một nhánh thì đừng bọc `oneOf`: grammar gọn hơn, ngữ nghĩa không đổi.
    return branches[0] if len(branches) == 1 else {"oneOf": branches}


def schema_for(traits: Traits, kind: str, targets: list[str] | None = None,
               sm=None, hunch: bool = False) -> dict:
    """Trả về JSON Schema dict cho kind in {'decide', 'codex', 'oracle', 'shift', 'hunch'}.

    `hunch=False` là mặc định và nó có nghĩa đen: schema `decide` **không có**
    trường `want_hunch`, nên một ván không bật linh cảm sinh ra đúng cùng một
    grammar như trước B-14. Đổi grammar là đổi phân phối đầu ra của model, và
    một nhánh đối chứng dùng grammar khác nhánh thí nghiệm thì không đối chứng
    được gì.

    `targets` là danh sách id mà con này ĐANG NHÌN THẤY. Đưa nó vào schema dưới
    dạng `enum` làm cho một mục tiêu không nhìn thấy trở nên **bất khả về cấu
    trúc** — grammar không sinh ra nổi.

    Đo ở lần chạy model thật đầu tiên (Qwen2.5-1.5B, seed 9): không có enum thì
    **16/20 lời gọi** trượt xác thực ngữ nghĩa, gần hết là
    `SEMANTIC_TARGET_NOT_FOUND` — model chọn `HUNT` rồi đặt tên một con nó không
    hề thấy. Đó không chỉ là model yếu: prompt liệt kê ai đang thấy nhưng schema
    thì cho phép viết bất cứ chuỗi nào, và ta đã để ngỏ đúng cái cửa mà cả kiến
    trúc "server gửi schema" sinh ra để đóng.
    """

    if kind == "decide":
        props: dict[str, Any] = {}
        has_note = traits.token_budget >= 60
        if has_note:
            props["note"] = {"type": "string", "maxLength": 90}
        props["goal"] = {
            "type": "string",
            # Bỏ các goal cần mục tiêu khi không thấy ai: để lại thì model chọn
            # chúng rồi trượt xác thực, và ta đốt một lượt nghĩ vào một câu trả
            # lời không thể hợp lệ.
            "enum": [
                g for g in config.GOALS_BY_BRAIN[traits.brain]
                if targets or g not in config.GOALS_NEEDING_TARGET
            ],
        }
        if targets:
            props["target"] = {"type": "string", "enum": sorted(targets)}
        # Không thấy ai thì BỎ HẲN trường `target`. Đừng để lại nó với `enum: []`:
        # một enum rỗng dịch ra một luật GBNF **không khớp được gì**, nên nếu
        # model lỡ mở khoá `"target"` thì nó kẹt — không có ký tự hợp lệ nào để
        # đi tiếp, và nó nhả khoảng trắng cho tới hết `n_predict`. Đầu ra là
        # `{"goal": "GUARD", "ttl": 10, "target":  }` — JSON hỏng, 65 token, và
        # trông y hệt một ca "bị cắt" nên rất dễ chẩn đoán nhầm sang ngân sách.
        props["ttl"] = {"type": "integer", "minimum": 2, "maximum": 12}
        props["want_codex"] = {"type": "boolean"}
        if hunch:
            props["want_hunch"] = {"type": "boolean"}
        if has_note:
            # Nói tốn token của chính mình. Con 32-token (L5) không có chỗ cho
            # một câu nói, và đó là một sự thật của thế giới chứ không phải một
            # thiếu sót: loài ít não thì câm, và im lặng là một chiến lược.
            props["say"] = {
                "type": "object",
                "properties": {
                    "signal": {"type": "string",
                               "enum": ["ALARM", "AGGR", "SUBM", "NEUTRAL"]},
                    "text": {"type": "string", "maxLength": speech.TEXT_MAX},
                    "teach": {"type": "integer", "minimum": 0},
                },
                "required": ["signal"],
                "additionalProperties": False,
            }

        required = ["note", "goal", "ttl"] if has_note else ["goal", "ttl"]
        if targets:
            # Thấy ai thì BẮT BUỘC nêu tên. Không bắt buộc thì model chọn `HUNT`
            # rồi bỏ trống `target` — đo thật: 8/35 lời gọi trượt đúng vì thế,
            # sau khi enum đã dẹp xong ca "nêu tên kẻ không nhìn thấy".
            # JSON Schema không nói được "bắt buộc NẾU goal là HUNT", nên đòi
            # luôn: với goal không cần mục tiêu thì trường thừa là vô hại.
            required = required + ["target"]
        return {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False,
        }

    vocab = vocab_for_brain(traits.brain)

    if kind == "codex":
        int_ = {"type": "integer"}
        trigger_schema = _kind_arg_schema(
            [t.value for t in vocab.triggers], sm, {"k": int_, "n": int_, "r": int_})
        cond_schema = _kind_arg_schema(
            [c.value for c in vocab.conds], sm,
            {"k": int_, "op": {"type": "string", "enum": [">=", "<="]}, "n": int_, "r": int_})
        effect_schema = _effect_schema([e.value for e in vocab.effects], sm)
        return {
            "type": "object",
            "properties": {
                "op": {"type": "string", "enum": ["SET", "DROP", "CONF"]},
                # Trần ô sổ PHẢI ở trong schema. `validate_codex` từ chối slot
                # ngoài phạm vi bằng `CODEX_BAD_SLOT`, và không nói trước thì
                # model đoán — đo thật với Qwen-7B: nó chọn `slot: 1` trên một
                # con có đúng MỘT ô, và mất cả lượt ghi sổ.
                #
                # Đây là lần thứ tư cùng một bài học: **mọi ràng buộc mà bộ xác
                # thực bắt bẻ đều phải có mặt trong schema**, nếu không model
                # đốt lượt đi khám phá lại chúng. Ba lần trước: `target` không
                # enum, `target` không bắt buộc, `arg` của luật không enum.
                "slot": {"type": "integer", "minimum": 0,
                         "maximum": max(0, law_config.CODEX_SIZE_BY_BRAIN[traits.brain] - 1)},
                "conf": {"type": "integer", "minimum": 1, "maximum": 5},
                "law": {
                    "type": "object",
                    "properties": {
                        "trigger": trigger_schema,
                        "conds": {
                            "type": "array",
                            "items": cond_schema,
                            "maxItems": vocab.max_conds,
                        },
                        "effect": effect_schema,
                    },
                    "required": ["trigger", "conds", "effect"],
                },
            },
            "required": ["op", "slot"],
            "additionalProperties": False,
        }

    if kind == "hunch":
        int_ = {"type": "integer"}
        trigger_schema = _kind_arg_schema(
            [t.value for t in vocab.triggers], sm, {"k": int_, "n": int_, "r": int_})
        cond_schema = _kind_arg_schema(
            [c.value for c in vocab.conds], sm,
            {"k": int_, "op": {"type": "string", "enum": [">=", "<="]}, "n": int_, "r": int_})
        effect_schema = _effect_schema([e.value for e in vocab.effects], sm)
        return {
            "type": "object",
            "properties": {
                # Không có `CONF`: một linh cảm không mang độ tin. Cả điểm của
                # nó là ngươi CHƯA tin — bảng đếm mới là thứ nói nó đáng tin đến
                # đâu, và bảng đếm do thế giới ghi chứ không do ngươi khai.
                "op": {"type": "string", "enum": ["SET", "DROP"]},
                "slot": {"type": "integer", "minimum": 0,
                         "maximum": max(0, law_config.HUNCH_BY_BRAIN[traits.brain] - 1)},
                "law": {
                    "type": "object",
                    "properties": {
                        "trigger": trigger_schema,
                        "conds": {
                            "type": "array",
                            "items": cond_schema,
                            "maxItems": vocab.max_conds,
                        },
                        "effect": effect_schema,
                    },
                    "required": ["trigger", "conds", "effect"],
                },
            },
            "required": ["op", "slot"],
            "additionalProperties": False,
        }

    if kind == "oracle":
        effect_props = {
            "kind": {"type": "string", "enum": [e.value for e in vocab.effects]},
            "mag": {"type": "string", "enum": [m.value for m in Mag]},
            "dur": {"type": "string", "enum": [d.value for d in Dur]},
            "r": {"type": "integer"},
            "arg": {"type": "string"},
            "dir": {"type": "string"},
        }
        return {
            "type": "object",
            "properties": {
                "answers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "q": {"type": "integer"},
                            "effect": {
                                "type": "object",
                                "properties": effect_props,
                                "required": ["kind"],
                            },
                        },
                        "required": ["q", "effect"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["answers"],
            "additionalProperties": False,
        }

    if kind == "shift":
        return {
            "type": "object",
            "properties": {
                "from": {"type": "string", "enum": list(config.TRAIT_NAMES)},
                "to": {"type": "string", "enum": list(config.TRAIT_NAMES)},
                "why": {"type": "string", "maxLength": 80},
            },
            "required": ["from", "to"],
            "additionalProperties": False,
        }

    raise ValueError(f"Loại schema không hợp lệ: {kind!r}")


def payload_to_goal(payload: dict | None) -> ActiveGoal | None:
    """Đổi payload 'decide' đã hợp lệ thành ActiveGoal.

    Dùng chung cho tầng LLM sống (B-05) và replay (B-06) — hai đường phải đi
    qua đúng một hàm, nếu không replay sẽ "khớp" trên một phép biến đổi khác.
    """
    if not isinstance(payload, dict):
        return None
    try:
        goal = Goal(payload["goal"])
        ttl = int(payload["ttl"])
    except (KeyError, ValueError, TypeError):
        return None
    target = payload.get("target") or None
    return ActiveGoal(goal=goal, target=target, ttl=ttl)


@runtime_checkable
class Strategist(Protocol):
    """Giao diện chiến lược chung cho mọi nguồn quyết định."""

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        """Ý đồ mới cho sinh vật c, hoặc None để giữ ý đồ cũ.

        Được gọi **mỗi tick cho mỗi con còn sống**, không phải chỉ khi ý đồ cũ
        hết hạn. Tầng LLM cần thế: quyết định của nó về tới lúc nào thì đè lúc
        ấy (B-05 bất biến 1), chứ không chờ hết `ttl`. Tầng nào không muốn đè
        thì trả `None` — `current` chính là để nó biết mà trả `None`.
        """
        ...


class ReflexStrategist:
    """Tầng chiến lược mặc định: gọi tầng phản xạ bản năng choose_goal."""

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        if current is not None and current.ttl > 0:
            return None
        if rng is None:
            rng = random.Random(0)
        return choose_goal(c, world, seen, rng)


class RemoteClientStrategist:
    """Đọc quyết định từ hàng đợi do client từ xa gửi về.

    Nếu hàng đợi trống hoặc chưa có quyết định cho sinh vật c, trả None
    để vòng tick tiếp tục bằng phản xạ / giữ goal cũ.
    """

    def __init__(self, queue_dict: dict[str, Any] | None = None) -> None:
        self.queue: dict[str, Any] = queue_dict if queue_dict is not None else {}
        # Trí nhớ và tầng xã hội. `MatchRunner` gán bản của nó đè lên; bản mặc
        # định ở đây chỉ để lớp này đứng một mình được trong test.
        self.minds = Minds()
        # ── ngang bằng với `LlmStrategist` (N-16) ────────────────────────
        # Vòng tick hỏi ba thứ này bằng `getattr`, nên thiếu chúng thì đường
        # mạng **im lặng** chơi một trò khác: không nói được câu nào, và hướng
        # dịch trait rơi về giàn giáo if-else của W-12 thay vì do model của
        # người chơi chọn. Không lỗi, không log, chỉ khác.
        self.pending_say: dict[str, speech.Say] = {}
        self.shift_choice: dict[str, tuple[str, str]] = {}
        self.shift_why: dict[str, str | None] = {}
        self.want_shift: set[str] = set()
        # `creature_id -> adapt_points lúc đã hỏi`. Cùng lý do với bản cục bộ:
        # không có bảng này thì một câu trả lời sai làm con vật hỏi lại **mãi
        # mãi**, và mọi lượt nghĩ của nó từ đó đổ vào một câu hỏi nó liên tục
        # trả lời sai.
        self._shift_asked: dict[str, int] = {}
        # `slots` là cách `genesis.tick` hỏi "con này có model không". Rỗng lúc
        # dựng; `MatchRunner._spawn_registered` điền id của sinh vật do người
        # chơi thật điều khiển. Bot của server KHÔNG có mặt ở đây — chúng không
        # có ai để hỏi hướng dịch, nên chúng phải rơi về W-12.
        self.slots: dict[str, int] = {}

    def take_says(self) -> dict[str, "speech.Say"]:
        """Lấy VÀ xoá hàng chờ nói. Một câu nói là của MỘT tick."""
        out, self.pending_say = self.pending_say, {}
        return out

    def take_shift(self, c) -> tuple[str, str] | None:
        """Hướng dịch trait do model của người chơi chọn (B-13 ở chế độ mở).

        Giống bản cục bộ từng chữ, và đó là chủ ý: hai bản khác nhau ở đây nghĩa
        là hai chế độ thưởng cho hai chiến lược khác nhau, mà `brain` — thứ
        quyết định dung lượng Sổ Luật — lại chính là trait đáng tranh nhất.
        """
        got = self.shift_choice.pop(c.id, None)
        if got is not None:
            self._shift_asked.pop(c.id, None)
            return got
        if self._shift_asked.get(c.id) == c.adapt_points:
            return None          # đã hỏi ở đúng mức điểm này và hỏng: bỏ lượt
        self._shift_asked[c.id] = c.adapt_points
        self.want_shift.add(c.id)
        return None

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        if c.id not in self.queue:
            return None

        val = self.queue[c.id]
        if isinstance(val, ActiveGoal):
            del self.queue[c.id]
            return val
        if isinstance(val, list):
            if val:
                return val.pop(0)
            return None
        if isinstance(val, collections.deque):
            if val:
                return val.popleft()
            return None
        if isinstance(val, queue.Queue):
            try:
                return val.get_nowait()
            except queue.Empty:
                return None
        if val is not None:
            del self.queue[c.id]
            return val
        return None


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
    "hunch": (
        "\n\n[LINH CẢM]\nĐây KHÔNG phải Sổ Luật và nó không được chấm điểm. Hãy nêu "
        "một điều ngươi NGHI, chưa cần tin. Từ giờ mỗi lần chuyện ấy đáng lẽ xảy "
        "ra, ngươi sẽ được cho biết nó có xảy ra thật không — kể cả những lần "
        "không có gì. Nghi sai không mất gì; nghi thứ ngươi đã chắc thì phí ô."
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
    if kind == "shift":
        base = max(48, traits.token_budget // 2)
    else:
        base = traits.token_budget
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
    def notes(self) -> dict[str, "FieldNotes"]:
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
        """Dùng chung cho gọi thật và cho replay — replay so hash của CHÍNH nó."""
        system = self.cache.get(
            c, self.personas.get(c.species, ""), world.surface_map, tick_no, self.log,
            handbook=self.handbooks.get(c.species, ""),
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
        """`_ensure_slots` nhưng tự mở client — cho đường gọi ngoài `think`.

        `oracle_run` là đường thứ tư gọi model và nó từng bỏ cả ba bài học của
        `think` (chỗ hợp lệ, cổng chặn, hạn chờ theo đo). Cho nó mượn đúng cơ
        chế thay vì để nó viết bản thứ hai.
        """
        if self._n_slots is not None:
            return self._n_slots
        async with httpx.AsyncClient(timeout=30.0, transport=transport) as c:
            return await self._ensure_slots(c)

    async def _ensure_slots(self, client: httpx.AsyncClient) -> int:
        """Số chỗ song song của server, dò một lần rồi nhớ.

        **Vì sao cần.** `asyncio.gather` bắn cả đàn cùng lúc — 15 con — nhưng
        llama-server chạy `-np 4` chỉ có bốn chỗ. Mười một lời gọi còn lại nằm
        xếp hàng TRONG server, mà `timeout` của httpx đếm từ lúc gửi. Đo ở ván
        seed 55: **21 lần trượt, mọi lần đúng 20003–20005 ms** — không phải model
        chậm mà là hạn chờ đếm cả thời gian xếp hàng. Trung vị lời gọi thành
        công là 10.6 s, tức nửa đàn nằm ngay mép hạn.

        Hậu quả không dừng ở việc mất lượt: `id_slot` cũng được phát 0..14 trong
        khi server chỉ có chỗ 0..3, nên **prefix cache hỏng** — thứ đã đo được
        756/757 token tái dùng ở B-03 thì trong ván thật gần như không chạy.
        Lấy `% n` để mỗi con luôn về đúng một chỗ cố định: chia sẻ chỗ thì tái
        dùng kém đi, nhưng kém một cách tất định, và `id_slot` luôn hợp lệ.
        """
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
            # Xin ghi sổ nhưng chưa hết nguội thì ĐỪNG gọi: `Codex.apply` sẽ trả
            # `CODEX_COOLDOWN` và cả lượt nghĩ đó mất trắng. Đo với model giả luôn
            # xin ghi: 397/582 lời gọi ghi sổ bị nguội từ chối, tức hai phần ba
            # ngân sách suy nghĩ đổ vào một câu trả lời đã biết trước là hỏng.
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
                # SAU `codex`: một kết luận đáng giá hơn một giả thuyết khi cả
                # hai cùng chờ, và Sổ Luật mới là thứ được chấm.
                kind = "hunch"
            else:
                kind = "decide"
            jobs.append((c, kind, system, user, prompt_hash(system, user),
                         [o.id for o in visible(c, world, creatures)]))

        # Hạn chờ phải theo SỐ ĐỢT, không phải một hằng số.
        #
        # Đo trên máy này (Qwen-7B q4, Metal, 8 chỗ): một lời gọi 3.5 s, nhưng
        # **15 lời gọi song song mất 32 s** — cả đàn là một đợt, và đợt ấy dài
        # hơn hạn 20 s. Hậu quả không phải "chậm" mà là **mất im lặng**: ở ván
        # seed 55, 42% lượt nghĩ bị huỷ đúng ở mốc 20003 ms, và một ván mất gần
        # nửa số lượt nghĩ thì không đo được năng lực quy nạp của model nữa.
        #
        # Nhân hạn theo số đợt: đàn to hơn hoặc máy ít chỗ hơn thì chờ lâu hơn,
        # nhưng KHÔNG ai bị bỏ rơi. Ván chạy chậm là một sự thật đọc được; ván
        # mất 42% lượt nghĩ là một con số sai không ai nhìn thấy.
        n_slots = self._n_slots or law_config.LLM_PARALLEL_FALLBACK
        waves = max(1, -(-len(jobs) // max(1, n_slots)))
        # Hằng số 45 s là số của MỘT model. Qwen-7B sinh ~14 tok/s nên một đợt
        # đầy mất 20 s; Qwen-14B sinh 5–6 tok/s nên đúng đợt ấy mất **81 s** —
        # và cả ván 14B trượt 20/41 lời gọi, đúng mốc 45004 ms, rồi ghi Sổ Luật
        # **0 lần**. Đọc vội thì thành "14B cũng không quy nạp được", trong khi
        # nó gần như chưa được nghĩ lần nào.
        #
        # Nên hạn chờ phải ĐO, không phải đặt. `_call_ms` là thời gian một đợt
        # quan sát được, cập nhật dần; nhân 3 để chừa cho phương sai.
        timeout = max(self.timeout, 3.0 * (self._call_ms or 0.0) / 1000.0) * waves
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            n = await self._ensure_slots(client)
            # Semaphore dựng MỚI mỗi lượt, không nhớ lại.
            #
            # `begin_tick` gọi `asyncio.run` mỗi tick, mà `asyncio.run` dựng một
            # vòng lặp sự kiện MỚI mỗi lần. `Semaphore` gắn vào vòng lặp nó chờ
            # lần đầu, nên dùng lại ở tick sau là `RuntimeError: bound to a
            # different event loop`.
            #
            # Nó nằm im rất lâu: `acquire()` chỉ chạm tới vòng lặp khi phải CHỜ,
            # nên chừng nào số con nghĩ cùng lượt còn <= số chỗ thì không ai
            # thấy gì. Lệch pha `think_interval` giữ hầu hết lượt dưới ngưỡng —
            # ba ván 7B chạy trọn 200 tick không sao. Nó nổ đúng ở ca semaphore
            # sinh ra để phục vụ: cả đàn cùng nghĩ một lượt. Chế độ mở có 15+
            # con, nên đó là ca thường chứ không phải ca hiếm.
            gate = asyncio.Semaphore(n)

            async def _one(c, kind, system, user, tg):
                # Xếp hàng TRƯỚC khi gửi, không phải trong server. `timeout` của
                # httpx đếm từ lúc gửi, nên chờ trong server bị tính vào hạn.
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
            # Chỉ học từ đợt CÓ KẾT QUẢ: một đợt trượt sạch chỉ nói lên hạn chờ
            # cũ quá ngắn, lấy nó làm mốc là tự khoá mình ở giá trị sai.
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

        # Bất biến 3: tính tiền theo token THỰC SINH. Tính theo max_tokens thì
        # con nghĩ ngắn phải trả tiền cho con nghĩ dài, và ngân sách token theo
        # brain (`token_budget`) mất hết ý nghĩa kinh tế.
        tokens = int(r["n"])
        cost = round(tokens / config.TOKENS_PER_ENERGY, 4)
        c.energy -= cost
        self.stats["call"] += 1
        self._write(
            tick_no, "LLM_CALL", c,
            prompt_hash=phash, raw=r["raw"],
            tokens_used=tokens, cost_think=cost, ms=elapsed_ms,
            # Ghi cả nhịp: `think_interval` đổi giữa ván khi brain dịch, nên
            # "khoảng cách giữa hai lời gọi luôn bằng 3" là điều KHÔNG đúng.
            # Bất biến thật là t % think_interval == offset, và muốn kiểm nó từ
            # log thì log phải mang theo hai số đó.
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
            # Lời nói gặp hành động: mọi người từng nghe con này nói giờ thấy nó
            # ĐỊNH LÀM GÌ. Kêu ALARM rồi đi HUNT là nói một đằng làm một nẻo.
            for rep in self.reputation.values():
                rep.observe_goal(c.id, goal.goal.value, tick_no)
        note = r["json"].get("note")
        if isinstance(note, str) and note.strip():
            # Ghi chú do MODEL viết, và nó đi thẳng vào khối E ở lượt sau — cùng
            # đường với `say.text`, nên cùng phải qua `sanitize_text`.
            #
            # Không qua thì đây là một đường **tự sát**: model chỉ cần viết chữ
            # "HP" vào ghi chú là `_check_no_leak` ném `PromptLeak` và **ván gãy**.
            # Xảy ra thật ở ván model thật đầu tiên, lượt 87. Tệ hơn ca lời nói
            # của B-11 vì nó không cần kẻ thù nào cả — con vật tự giết ván của
            # mình bằng chính ghi chú của mình.
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
        """Lấy VÀ xoá hàng chờ nói. Vòng tick gọi đúng một lần mỗi tick.

        Trả rồi xoá chứ không để lại: một câu nói là của MỘT tick. Giữ lại thì
        con vật lặp đi lặp lại cùng một câu suốt cả `ttl` của goal.
        """
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
            # `learn` trước, `award` sau: `award` cần mốc "biết lúc nào" của cả
            # hai phía để khoá 1 (credit chảy một chiều) so được.
            self.ledger.learn(c.id, key, tick_no)
            self.ledger.award(c.id, key, tick_no)
        self.stats["codex_ok" if verdict.ok else "codex_bad"] += 1
        self._write(
            tick_no, "CODEX_OP", c,
            ok=verdict.ok, reason=verdict.reason,
            op=payload.get("op"), slot=payload.get("slot"), conf=payload.get("conf"),
            # Ghi luật bằng LỚP, không bằng bề mặt: bộ chấm so với luật thật, mà
            # luật thật viết bằng lớp. Ghi bề mặt thì mỗi ván một cách viết khác
            # và không so được ván này với ván kia.
            law=to_json(law) if law is not None else None,
        )

    def _absorb_hunch(self, c, world, tick_no, phash, r, elapsed_ms) -> None:
        """Ghi một linh cảm (B-14). Không `Ledger`, không điểm, không danh tiếng.

        Cố ý thiếu ba thứ mà `_absorb_codex` có, và mỗi thứ thiếu là một bất biến:
        không `ledger.award` (linh cảm không phải tri thức, không có công để
        chia), không `CODEX_OP` (bộ chấm không được nhìn thấy nó), và chi phí chỉ
        là token — không `COST_CLAIM`, vì nêu một nghi vấn phải rẻ hơn hẳn tuyên
        bố một kết luận, nếu không thì cơ chế này không mua được gì.
        """
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
        # `HUNCH_OP` chứ không `CODEX_OP`: `score.py` gom theo `kind`, nên trộn
        # tên là để linh cảm chảy thẳng vào bộ chấm — vi phạm bất biến 1 của
        # B-14 bằng đúng một chữ.
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
        # Bất biến 1: tầng phản xạ vẫn chạy. Model chưa trả lời, trả lời hỏng,
        # hay ngắt mạch — con vật vẫn phải sống tiếp chứ không đứng đực ra.
        if current is not None and current.ttl > 0:
            return None
        if rng is None:
            rng = random.Random(0)
        return choose_goal(c, world, seen, rng)

    def _absorb_speech(self, tick_no, world, by_id, speak_events) -> None:
        self.minds.absorb_speech(tick_no, world, by_id, speak_events)

    def _absorb_shift(self, c, tick_no, phash, r, elapsed_ms) -> None:
        """Hướng dịch trait do chính LLM của con đó chọn (B-13).

        Mỗi quyết định nâng cấp trở thành **dữ liệu quan sát được**, và ở v5
        hướng dịch ưa thích là chữ ký hành vi rõ nhất của một model — rõ hơn cả
        tỉ lệ sống, vì nó là một lựa chọn chứ không phải một kết quả.

        Sai thì **bỏ lượt, ghi log, KHÔNG thử lại**: thử lại là cho con nghĩ
        nhiều lần về cùng một việc, tức là một ưu đãi vô hình cho con hay sai.
        """
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
        events: dict[str, list[dict]],
        state: Any = None,
    ) -> None:
        """Ghi sổ tay từ sự kiện có thật của tick vừa rồi (B-07 §nạp).

        Hai điều dễ làm hỏng: (1) ghi tên hệ quả thì đề bài tự giải; (2) chỉ ghi
        việc của chính mình thì tầng xã hội (B-11/B-12) không có gì để quan sát.
        Nên: hệ quả dịch sang cảm giác, và cái gì trong tầm nhìn thì ghi là THẤY.
        """
        from genesis.lawhook import build_ctx

        by_id = {c.id: c for c in creatures}
        sm = world.surface_map

        # Sang đời mới thì sổ tay chết theo, Sổ Luật bớt chắc chắn (W-17).
        # Làm TRƯỚC khi ghi sổ tay của tick này: con vừa chết ở tick này thì đời
        # sau không được thừa hưởng dòng ghi về cái chết ấy.
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
        outcome: dict[str, str] = {}
        for ev in events.get("law", ()):
            phrase = _OUTCOME_VN.get(ev.get("effect", ""), "có gì đó vừa xảy ra")
            cid = ev["creature_id"]
            # Hai luật cùng hệ quả trong một tick thì cảm giác chỉ có MỘT. Lặp lại
            # nó là nói cho agent biết có hai luật — một mẩu đáp án miễn phí.
            parts = outcome.setdefault(cid, [])
            if phrase not in parts:
                parts.append(phrase)

        acted: list[tuple[str, str]] = []
        for ev in events.get("eat", ()):
            cls = ev.get("fruit_class")
            what = sm.surface_of(cls) if cls in sm.cls_to_surface else "thứ gì đó"
            acted.append((ev["creature_id"], f"ăn {what}"))
        for ev in events.get("drink", ()):
            acted.append((ev["creature_id"], "uống nước"))
        for ev in events.get("attack", ()):
            acted.append((ev["creature_id"], "trúng đòn"))
        did_something = {a for a, _ in acted}
        for ev in events.get("move", ()):
            cid = ev["creature_id"]
            if cid in did_something or (cid not in outcome and cid not in self.slots):
                continue
            c = by_id.get(cid)
            if c is None:
                continue
            wx, wy = world.wrap(*c.pos)
            terr = _TERRAIN_VN.get(world.grid[wy][wx], "đất trống")
            acted.append((cid, f"bước vào {terr}" if ev["moved"] else "đứng yên"))

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
                # Ngữ cảnh lấy từ NGƯỜI QUAN SÁT, không phải người hành động:
                # cắt theo brain của người đọc, và nó cũng chỉ biết hoàn cảnh của
                # chính mình. Ghi ngữ cảnh nội tâm của kẻ khác là rò (B-07 bất biến 3).
                self.notes_of(obs).record(Note(
                    t=tick_no, who=who, action=action, outcome=out,
                    ctx=ctx_to_pairs(ctx_of(obs), obs.traits.brain),
                ))
