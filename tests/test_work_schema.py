"""Genesis Zero — schema phát qua mạng phải giống hệt đường cục bộ (N-06)."""

from __future__ import annotations

from genesis.strategist import schema_for
from genesis.tick import build_match


def test_duong_mang_va_duong_cuc_bo_dung_cung_mot_schema():
    """Client qua mạng KHÔNG được chơi một trò khác client cục bộ.

    `routes_work.generate_work_items` từng dựng `schema_for(c.traits, kind)` —
    không `targets`, không `sm`. Hậu quả:

    - thiếu `targets`: `target` không enum và không bắt buộc, đúng hai lỗ đã đo
      ở B-01 (16/20 và 8/35 lời gọi trượt).
    - thiếu `sm`: enum `arg` **không chứa bề mặt nào**, nên luật về ăn quả là
      bất khả về cấu trúc — chế độ mở không phát biểu nổi luật ăn quả.
    """
    world, creatures, _, _ = build_match(55)
    c = creatures[0]
    seen = [o.id for o in creatures[1:3]]

    day_du = schema_for(c.traits, "codex", targets=seen, sm=world.surface_map)
    thieu = schema_for(c.traits, "codex")
    assert day_du != thieu, "thiếu sm mà schema không đổi -> bài test này vô nghĩa"

    def args(node):
        out = set()
        for b in node.get("oneOf", [node]):
            out |= set(b["properties"].get("arg", {}).get("enum", []))
        return out

    surfaces = set(world.surface_map.cls_to_surface.values())
    trigger = day_du["properties"]["law"]["properties"]["trigger"]
    assert surfaces <= args(trigger), "enum arg thiếu bề mặt -> không ai nói được về quả"
    assert not (surfaces & args(thieu["properties"]["law"]["properties"]["trigger"]))


def test_decide_qua_mang_co_enum_target():
    world, creatures, _, _ = build_match(55)
    c = creatures[0]
    seen = [o.id for o in creatures[1:3]]
    s = schema_for(c.traits, "decide", targets=seen, sm=world.surface_map)
    assert s["properties"]["target"]["enum"] == sorted(seen)
    assert "target" in s["required"], "thấy ai thì phải BẮT BUỘC nêu tên"


def test_routes_work_truyen_ca_hai():
    """Khoá bằng mã nguồn: gọi `schema_for` ở đường mạng phải có cả hai tham số.

    Kiểm thẳng vào nguồn vì hai đường dựng schema ở hai chỗ khác nhau — đường
    mạng theo pha, đường cục bộ theo đàn — nên không có bất biến kiểu nào bắt
    được việc chúng lệch nhau ngoài việc đọc.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "net" / "routes_work.py").read_text()
    i = src.index("js = schema_for(")
    goi = src[i:i + 200]
    assert "targets=" in goi, "đường mạng quên targets"
    assert "sm=" in goi, "đường mạng quên sm"


def test_nguoi_choi_qua_mang_NGHE_DUOC():
    """`heard` phải có thật ở đường mạng, không phải tuple rỗng cứng.

    Trước đó `routes_work` truyền thẳng `heard=()`: **người chơi qua mạng không
    bao giờ nghe thấy ai**. Cả tầng xã hội (B-11 nói, B-12 dạy) không tồn tại ở
    chế độ mở — mà chế độ mở chính là chỗ câu hỏi Q2 của dự án ("giao tiếp đáng
    giá bao nhiêu?") phải được đo.

    Đọc từ `runner.minds`, cùng chỗ mà `LlmStrategist` đọc (N-16).
    """
    from net.match import MatchRunner

    r = MatchRunner(seed=1, ticks=5, tick_ms=1, log_dir=None)
    r._seed_match()
    ids = [c.id for c in r.creatures]
    speaker, near, far = ids[0], ids[1], ids[2]

    r._absorb_speech_for_clients([{
        "kind": "SPEAK", "creature_id": speaker,
        "signal": "ALARM", "text": "coi chừng nước", "teach": None,
        "hear_full": [near], "hear_signal": [far],
    }])
    heard = r.minds.heard
    assert heard[near], "người nghe gần phải nghe ĐỦ CÂU"
    assert heard[far], "người nghe xa phải nghe ÍT NHẤT tín hiệu"
    # người ở xa nghe được ÍT hơn người ở gần
    assert len(heard[far][0]) < len(heard[near][0])
    assert speaker not in heard, "người nói không tự nghe mình"


def test_van_mo_ghi_prompt_hash():
    """Không có `prompt_hash` thì log ván MỞ không dựng lại được mẫu huấn luyện.

    `rollout.samples_from` đối chiếu `prompt_hash` và **bỏ mọi mẫu không khớp**
    — mà ván mở chính là chỗ dữ liệu thật sẽ đến từ đó. Thiếu trường này nghĩa
    là toàn bộ dữ liệu quý nhất của dự án không dùng để huấn luyện được.
    """
    import dataclasses

    from net.routes_work import WorkRecord

    names = {f.name for f in dataclasses.fields(WorkRecord)}
    assert "prompt_hash" in names
