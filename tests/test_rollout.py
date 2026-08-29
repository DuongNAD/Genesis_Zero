"""Kiểm thử sinh dữ liệu huấn luyện (R-01, R-02, R-04)."""

from __future__ import annotations

import collections
import json
import logging

import httpx
import pytest

from genesis.lawgen import generate_cached
from genesis.reveal import _law_to_surface_dict
from genesis.rollout import rollout, samples_from, split_by_law_structure, write_jsonl
from genesis.tick import build_match

logging.disable(logging.WARNING)
SEED = 9


def _model(cheat: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        p = json.loads(request.content)["prompt"]
        out = ({"op": "SET", "slot": 0, "conf": 5, "law": cheat}
               if "[GHI SỔ LUẬT]" in p
               else {"goal": "FORAGE", "ttl": 4, "want_codex": True})
        return httpx.Response(200, json={"content": json.dumps(out),
                                         "tokens_predicted": 50})
    return httpx.MockTransport(handler)


@pytest.fixture
def cheat():
    world, _, _, _ = build_match(seed=SEED)
    return _law_to_surface_dict(generate_cached(SEED)[0], world.surface_map)


def test_rollout_sinh_du_log_va_truth(tmp_path, cheat):
    log, truth = rollout(SEED, 60, ["L1:0"], "http://m", tmp_path,
                         transport=_model(cheat))
    assert log.exists() and truth.exists()
    t = json.loads(truth.read_text(encoding="utf-8"))
    assert t["seed"] == SEED and t["laws"] and t["surface_map"]


def test_moi_mau_deu_qua_kiem_prompt_hash(tmp_path, cheat):
    """Log KHÔNG chứa prompt (B-06 bất biến 1), nên prompt phải dựng lại — và
    mẫu nào dựng lại không khớp `prompt_hash` thì bị LOẠI, không lặng lẽ vào tập
    train. Học trên một prompt chưa từng tồn tại là cách âm thầm nhất để hỏng
    một lần huấn luyện."""
    log, truth = rollout(SEED, 150, ["L1:0", "L1:1"], "http://m", tmp_path,
                         transport=_model(cheat))
    ss = samples_from(log, truth, transport=_model(cheat))
    assert ss, "không sinh được mẫu nào"
    assert ss[0].meta["n_mismatched_in_match"] == 0
    for s in ss:
        assert s.system and s.user and s.response
        assert s.system in (s.system + s.user)


def test_ghi_so_luat_cung_duoc_phat_lai(tmp_path, cheat):
    """Nội dung Sổ Luật nằm TRONG khối E, nên một lần ghi làm prompt mọi lượt
    sau đổi. Bản đầu của replay không phát lại thao tác ghi sổ, và ván rẽ nhánh
    ngay ở lượt gọi kế tiếp — bài test replay cũ không bắt được vì model giả của
    nó chưa bao giờ ghi sổ."""
    log, truth = rollout(SEED, 150, ["L1:0"], "http://m", tmp_path,
                         transport=_model(cheat))
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    assert any(r["kind"] == "CODEX_OP" and r["ok"] for r in rows), (
        "ván này phải CÓ ghi sổ thành công thì bài test mới có nghĩa"
    )
    ss = samples_from(log, truth, transport=_model(cheat))
    assert ss[0].meta["n_mismatched_in_match"] == 0


def test_moi_loai_loi_goi_deu_thanh_mau(tmp_path, cheat):
    log, truth = rollout(SEED, 150, ["L1:0", "L1:1"], "http://m", tmp_path,
                         transport=_model(cheat))
    kinds = collections.Counter(s.kind for s in samples_from(log, truth,
                                                             transport=_model(cheat)))
    assert kinds["decide"] > 0 and kinds["codex"] > 0


def test_reward_gan_theo_ca_the(tmp_path, cheat):
    """RLVR ở mức VÁN, không mức bước: tín hiệu kiểm chứng được chỉ có ở cuối ván."""
    log, truth = rollout(SEED, 150, ["L1:0", "L1:1"], "http://m", tmp_path,
                         transport=_model(cheat))
    ss = samples_from(log, truth, transport=_model(cheat))
    by_c = {s.creature_id: {x.reward for x in ss if x.creature_id == s.creature_id}
            for s in ss}
    for cid, rewards in by_c.items():
        assert len(rewards) == 1, f"{cid} có nhiều reward khác nhau: {rewards}"
    assert max(next(iter(v)) for v in by_c.values()) > 0.5, "model 'biết đáp án' phải ăn điểm"


def test_xuat_jsonl_du_truong(tmp_path, cheat):
    log, truth = rollout(SEED, 90, ["L1:0"], "http://m", tmp_path,
                         transport=_model(cheat))
    out = write_jsonl(samples_from(log, truth, transport=_model(cheat)),
                      tmp_path / "train.jsonl")
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        d = json.loads(line)
        assert set(d) >= {"prompt", "response", "reward", "kind"}
        assert isinstance(d["reward"], (int, float))


def test_chia_theo_cau_truc_luat_khong_phai_theo_seed():
    """Chia ngẫu nhiên theo seed là tự lừa mình. Khoá là HÌNH DẠNG luật.

    Khoá phải THÔ: đo trên 400 seed với khoá mịn (kèm cond) ra **400 khuôn khác
    nhau, không một trùng lặp** — và lúc ấy "chia theo cấu trúc" chỉ là chia theo
    seed dưới một cái tên khác.
    """
    seeds = list(range(1, 25))
    d = split_by_law_structure(seeds)
    assert set(d["train"]) & set(d["test"]) == set(), "train và test giao nhau"
    assert set(d["train"]) | set(d["test"]) == set(seeds)
    assert d["train"] and d["test"], "một phía rỗng thì không chia được gì"

    # Điều kiện làm cho phép chia có NGHĨA: mọi cặp (trigger, effect) bị giữ lại
    # phải VẮNG MẶT hoàn toàn ở tập train. Không có ràng buộc này thì "test" chỉ
    # là một mẫu ngẫu nhiên khác của cùng phân bố.
    from genesis.lawgen import generate_cached
    held = {tuple(p) for p in d["held_pairs"]}
    for s in d["train"]:
        for law in generate_cached(s):
            assert (law.trigger.kind.value, law.effect.kind.value) not in held
