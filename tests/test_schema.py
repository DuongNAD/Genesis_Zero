"""Genesis Zero — tests cho schema_for (B-01)."""

from __future__ import annotations

import json

import pytest

from genesis import config
from genesis.strategist import schema_for
from genesis.traits import Traits, founder_traits


def test_decide_schema_invariants() -> None:
    """Kiểm tra toàn bộ 4 bất biến của schema decide."""
    l5 = founder_traits("L5")  # brain 0, budget 32 < 60
    l1 = founder_traits("L1")  # brain 4, budget 176 >= 60

    s5 = schema_for(l5, "decide")
    s1 = schema_for(l1, "decide")

    # Bất biến 1: note đứng TRƯỚC goal
    assert list(s1["properties"]).index("note") < list(s1["properties"]).index("goal")

    # Bất biến 2: token_budget < 60 -> BỎ HẲN note khỏi properties và required
    assert "note" not in s5["properties"]
    assert "note" not in s5["required"]
    assert s5["required"] == ["goal", "ttl"]
    assert "note" in s1["properties"]
    assert "note" in s1["required"]
    assert s1["required"] == ["note", "goal", "ttl"]

    # Bất biến 3: enum của goal cắt theo config.GOALS_BY_BRAIN — VÀ theo việc
    # con đó có đang thấy ai không. Không thấy ai thì HUNT/FOLLOW không phát
    # biểu được; để chúng trong enum là mời model chọn một câu trả lời không thể
    # hợp lệ, rồi đốt một lượt nghĩ vào nó (đo thật: 16/20 lời gọi trượt).
    s1t = schema_for(founder_traits("L1"), "decide", targets=["L2:0"])
    s5t = schema_for(founder_traits("L5"), "decide", targets=["L2:0"])
    assert set(s5t["properties"]["goal"]["enum"]) == set(config.GOALS_BY_BRAIN[0])
    assert set(s1t["properties"]["goal"]["enum"]) == set(config.GOALS_BY_BRAIN[4])
    assert "GUARD" not in s5t["properties"]["goal"]["enum"]
    assert "GUARD" in s1t["properties"]["goal"]["enum"]
    assert s1t["properties"]["target"]["enum"] == ["L2:0"]

    for g in config.GOALS_NEEDING_TARGET:
        assert g not in s1["properties"]["goal"]["enum"], (
            f"{g} cần mục tiêu mà con này không thấy ai"
        )
    # Không thấy ai thì BỎ HẲN trường `target`, chứ không để `enum: []`.
    # Enum rỗng dịch ra một luật GBNF không khớp được gì: model lỡ mở khoá
    # `"target"` là kẹt, nhả khoảng trắng tới hết `n_predict`, và ra một JSON
    # hỏng trông y hệt ca "bị cắt" — rất dễ chẩn đoán nhầm sang ngân sách token.
    assert "target" not in s1["properties"]

    def _empty_enums(node) -> list:
        found = []
        if isinstance(node, dict):
            if node.get("enum") == []:
                found.append(node)
            for v in node.values():
                found += _empty_enums(v)
        elif isinstance(node, list):
            for v in node:
                found += _empty_enums(v)
        return found

    for kind in ("decide", "codex", "oracle", "shift"):
        for tg in ([], ["L2:0"]):
            sch = schema_for(founder_traits("L1"), kind, targets=tg)
            assert not _empty_enums(sch), f"{kind}/{tg}: có enum rỗng trong schema"

    # Bất biến 4: want_codex có mặt ở MỌI brain
    for species in ("L1", "L2", "L3", "L4", "L5"):
        t = founder_traits(species)
        s = schema_for(t, "decide")
        assert "want_codex" in s["properties"]
        assert s["properties"]["want_codex"]["type"] == "boolean"

    # ttl và additionalProperties
    assert s1["properties"]["ttl"]["minimum"] == 2
    assert s1["properties"]["ttl"]["maximum"] == 12
    assert s1["additionalProperties"] is False
    assert s5["additionalProperties"] is False


def test_other_schemas_structure() -> None:
    """Kiểm tra cấu trúc của schema codex, oracle, shift."""
    l1 = founder_traits("L1")

    for k in ("codex", "oracle", "shift"):
        s = schema_for(l1, k)
        assert isinstance(s, dict)
        assert s["type"] == "object"

    # codex
    s_codex = schema_for(l1, "codex")
    assert set(s_codex["properties"]["op"]["enum"]) == {"SET", "DROP", "CONF"}
    assert s_codex["properties"]["slot"]["type"] == "integer"
    assert s_codex["properties"]["conf"]["minimum"] == 1
    assert s_codex["properties"]["conf"]["maximum"] == 5
    assert "law" in s_codex["properties"]
    assert "trigger" in s_codex["properties"]["law"]["properties"]
    assert "conds" in s_codex["properties"]["law"]["properties"]
    assert "effect" in s_codex["properties"]["law"]["properties"]

    # oracle
    s_oracle = schema_for(l1, "oracle")
    assert "answers" in s_oracle["properties"]
    assert s_oracle["properties"]["answers"]["type"] == "array"

    # shift
    s_shift = schema_for(l1, "shift")
    assert set(s_shift["properties"]["from"]["enum"]) == set(config.TRAIT_NAMES)
    assert set(s_shift["properties"]["to"]["enum"]) == set(config.TRAIT_NAMES)
    assert s_shift["properties"]["why"]["maxLength"] == 80


def test_invalid_schema_kind() -> None:
    """Gọi kind lạ phải báo lỗi."""
    l1 = founder_traits("L1")
    with pytest.raises(ValueError, match="không hợp lệ"):
        schema_for(l1, "unknown_kind")


def test_arg_cua_luat_bi_khoa_vao_enum_hop_le():
    """Model thật phát biểu ĐÚNG luật rồi **dịch bề mặt sang tiếng Trung**:
    `"arg": "紫扁果"` thay vì `"quả tím dẹt"` (Qwen là model Trung Quốc).
    `validate_codex` từ chối với `CODEX_UNKNOWN_SURFACE`, và nếu không nhìn vào
    `raw` thì ta kết luận nhầm rằng nó **không suy ra được luật**.

    Enum làm điều đó bất khả về cấu trúc: grammar không sinh ra nổi một chuỗi
    ngoài danh sách.
    """
    from genesis.strategist import ARG_DOMAIN, legal_args
    from genesis.tick import build_match

    world, _, _, _ = build_match(55)
    sm = world.surface_map
    s = schema_for(founder_traits("L1"), "codex", sm=sm)
    law = s["properties"]["law"]["properties"]

    def branches(node):
        return node.get("oneOf", [node])

    surfaces = set(sm.cls_to_surface.values())
    for part, node in (("trigger", law["trigger"]),
                       ("effect", law["effect"]),
                       ("conds", law["conds"]["items"])):
        seen_args: set[str] = set()
        for b in branches(node):
            arg = b["properties"].get("arg")
            if arg is None:
                continue
            enum = arg["enum"]
            assert enum, f"{part}: enum RỖNG -> luật GBNF không khớp được gì"
            assert "紫扁果" not in enum and "" not in enum
            seen_args |= set(enum)
        if part in ("trigger", "effect"):
            assert surfaces <= seen_args, f"{part} phải chào được mọi bề mặt"
    cond_args = {a for b in branches(law["conds"]["items"])
                 for a in b["properties"].get("arg", {}).get("enum", [])}
    assert "SAME_SP" in cond_args and "NIGHT" in cond_args

    # Không có SurfaceMap thì vẫn phải có enum (các hằng số DSL), không phải
    # chuỗi tự do — và tuyệt đối không phải enum rỗng.
    bare = legal_args(None)
    assert bare and "紫扁果" not in bare and "CORPSE" in bare


def test_hieu_ung_khong_mang_arg_thi_schema_khong_chao_arg():
    """13/15 hiệu ứng **không nhận `arg`** — luật thật để `arg=None`, nên một
    mục sổ `ARMOR_UP(TERRAIN)` không thể khớp gì và ăn `match = 0.0`.

    Model 7B viết đúng thế: ván seed 55 có 9 mục sổ được NHẬN, 5 mục thuộc loại
    này (`ARMOR_UP(TERRAIN)`, `HEAL(EAT)`, `ENERGY_GAIN(DAY)`). Cũ thì lọt vì
    enum `arg` phẳng dùng chung cho mọi kind. Mỗi mục tiêu một ô sổ và một lần
    `CLAIM_COOLDOWN`, không đổi lấy gì.
    """
    from genesis.strategist import ARGLESS_KINDS_FOR_TEST
    from genesis.tick import build_match

    world, _, _, _ = build_match(55)
    s = schema_for(founder_traits("L1"), "codex", sm=world.surface_map)
    eff = s["properties"]["law"]["properties"]["effect"]
    for b in eff.get("oneOf", [eff]):
        kinds = b["properties"]["kind"]["enum"]
        has_arg = "arg" in b["properties"]
        for k in kinds:
            if k in ARGLESS_KINDS_FOR_TEST:
                assert not has_arg, f"{k} không nhận arg mà schema vẫn chào"
            else:
                assert has_arg, f"{k} phải nhận arg"
        # `additionalProperties: False` mới làm nó BẤT KHẢ, không chỉ thừa.
        assert b["additionalProperties"] is False


def test_khong_lo_ten_lop_qua_enum():
    """Enum đi vào prompt qua `json_schema`. Nó được phép mang BỀ MẶT, tuyệt đối
    không được mang tên lớp."""
    from genesis.tick import build_match

    world, _, _, _ = build_match(55)
    s = json.dumps(schema_for(founder_traits("L1"), "codex", sm=world.surface_map),
                   ensure_ascii=False)
    assert "FRUIT_" not in s


def test_moi_rang_buoc_cua_bo_xac_thuc_deu_co_trong_schema():
    """Bốn lần cùng một bài học, nên viết nó ra thành một bài test.

    Mỗi ràng buộc mà `validate_*` bắt bẻ nhưng schema không nói đều là một lượt
    nghĩ bị đốt: model đoán, trượt, và ta mất một quyết định. Đã gặp:
    `target` không enum · `target` không bắt buộc · `arg` của luật không enum ·
    `slot` không có trần.
    """
    from genesis import law_config

    for sp in ("L1", "L2", "L3", "L4", "L5"):
        t = founder_traits(sp)
        size = law_config.CODEX_SIZE_BY_BRAIN[t.brain]
        slot = schema_for(t, "codex")["properties"]["slot"]
        assert slot["minimum"] == 0
        assert slot["maximum"] == size - 1, (sp, size, slot)

        d = schema_for(t, "decide", targets=["L9:0"])
        assert d["properties"]["ttl"]["minimum"] == 2
        assert d["properties"]["ttl"]["maximum"] == 12
        assert "target" in d["required"]
        assert set(d["properties"]["goal"]["enum"]) == set(config.GOALS_BY_BRAIN[t.brain])

        sh = schema_for(t, "shift")
        for f in ("from", "to"):
            assert set(sh["properties"][f]["enum"]) == set(config.TRAIT_NAMES)


def test_schema_doi_dung_truong_ma_bo_cham_can():
    """`verify.agree` nhân điểm trên từng chiều luật THẬT có; thiếu chiều nào
    thì chiều ấy ăn **0** và kéo cả tích về 0.

    Nên một mục đúng trigger, đúng điều kiện, đúng loại hệ quả mà quên `dur`
    vẫn ăn đúng **0 điểm**. Đo trên 235 mục Sổ Luật ghi được trong một ngày:
    **chỉ 23% nêu cả `mag` lẫn `dur`** — 77% dữ liệu không thể ăn điểm về mặt
    cấu trúc, kể cả mục `WHEN DRINK THEN DAMAGE` của Qwen-14B, đúng nguyên văn
    luật thật.

    Lần thứ sáu cùng bài học B-01: cái gì bộ chấm bắt bẻ thì schema phải đòi.
    """
    from genesis.lawdsl import EFFECT_FIELDS
    from genesis.tick import build_match

    world, _, _, _ = build_match(55)
    s = schema_for(founder_traits("L1"), "codex", sm=world.surface_map)
    eff = s["properties"]["law"]["properties"]["effect"]
    for b in eff.get("oneOf", [eff]):
        for kind in b["properties"]["kind"]["enum"]:
            for f in EFFECT_FIELDS[kind]:
                assert f in b["required"], f"{kind} mang {f} mà schema không đòi"
        # và không đòi thứ hệ quả ấy KHÔNG mang
        thua = set(b["required"]) - {"kind"} - set(EFFECT_FIELDS[b["properties"]["kind"]["enum"][0]])
        assert not thua, f"đòi thừa {thua}"


def test_bang_EFFECT_FIELDS_khop_voi_bo_sinh_luat():
    """Bảng và bộ sinh luật KHÔNG được lệch nhau.

    Lệch thì schema đòi một trường luật thật không có (model không nêu nổi),
    hoặc bỏ qua một trường luật thật có (mọi mục ăn 0 trong im lặng).
    """
    import random

    from genesis.lawdsl import EFFECT_FIELDS, random_law, to_json, vocab_for_brain

    v = vocab_for_brain(5)
    for seed in range(400):
        d = to_json(random_law(random.Random(seed), v))["effect"]
        want = set(EFFECT_FIELDS[d["kind"]])
        got = {f for f in ("mag", "dur", "r", "arg") if d.get(f) is not None}
        assert got == want, f"{d['kind']}: bảng nói {want}, bộ sinh cho {got}"
