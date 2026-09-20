"""Genesis Zero — genesis/strategy/law_schema.py
Xây dựng JSON Schema và ngữ pháp LawDSL phục vụ việc giải mã có ràng buộc (constrained decoding) của LLM.
"""

from __future__ import annotations

from typing import Any

from genesis import config, law_config, speech
from genesis.lawdsl import Dur, Mag, vocab_for_brain
from genesis.traits import Traits
from genesis.validate import ARG_DOMAIN


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
        return None if sm is None else [*sorted(sm.cls_to_surface.values()), "CORPSE"]
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
                    opts = [*sorted(sm.cls_to_surface.values()), "CORPSE"]
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
            required = [*required, "target"]
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


__all__ = [
    "ARGLESS_KINDS_FOR_TEST",
    "SURFACE_KINDS",
    "_arg_options",
    "_effect_schema",
    "_kind_arg_schema",
    "legal_args",
    "schema_for",
]
