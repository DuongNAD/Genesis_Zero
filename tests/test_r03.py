"""Kiểm thử chuẩn bị dữ liệu GRPO (R-03).

Bước huấn luyện chưa từng chạy trên máy này — thiếu `trl`/`peft` và GPU. Cái
kiểm được, và cái phải kiểm, là **phép biến đổi dữ liệu**: nhóm sai hay chuẩn
hoá sai thì mọi lần huấn luyện sau đó học nhầm, và không có gì báo.
"""

from __future__ import annotations

import json

import pytest

from scripts.r03_train import advantages, group_for_grpo, main, prepare


def _row(seed, cid, t, reward, resp="{}"):
    return {"seed": seed, "creature_id": cid, "t": t, "reward": reward,
            "prompt": f"P{seed}{cid}{t}", "response": resp}


def test_nhom_theo_cung_de_bai():
    """Nhóm GRPO phải là CÙNG (seed, cá thể, lượt) — cùng luật ẩn, cùng thế giới.

    So hai rollout khác seed là so hai ĐỀ BÀI khác nhau, và lợi thế đo được sẽ
    là "đề nào dễ hơn" chứ không phải "lần nào nghĩ khá hơn".
    """
    rows = [_row(1, "L1:0", 5, 1.0), _row(1, "L1:0", 5, 0.0),
            _row(2, "L1:0", 5, 9.9)]
    g = group_for_grpo(rows)
    assert list(g) == [(1, "L1:0", 5)], "nhóm lẫn seed khác"
    assert len(g[(1, "L1:0", 5)]) == 2


def test_nhom_mot_phan_tu_bi_bo():
    """Lợi thế trong nhóm một phần tử luôn bằng 0 — chỉ làm loãng gradient."""
    assert group_for_grpo([_row(1, "L1:0", 5, 1.0)]) == {}


def test_loi_the_chuan_hoa_trong_nhom():
    g = [_row(1, "a", 0, 1.0), _row(1, "a", 0, 3.0)]
    adv = advantages(g)
    assert adv[0] < 0 < adv[1]
    assert abs(sum(adv)) < 1e-9, "tổng lợi thế trong nhóm phải bằng 0"


def test_phuong_sai_khong_thi_khong_chia_cho_khong():
    g = [_row(1, "a", 0, 2.0), _row(1, "a", 0, 2.0)]
    assert advantages(g) == [0.0, 0.0]


def test_mau_khong_co_tin_hieu_bi_loai():
    rows = [_row(1, "a", 0, 2.0), _row(1, "a", 0, 2.0),
            _row(1, "b", 0, 1.0), _row(1, "b", 0, 5.0)]
    out = prepare(rows)
    assert {tuple(r["group"]) for r in out} == {(1, "b", 0)}
    assert len(out) == 2


def test_cli_dry_run_ghi_file(tmp_path, capsys):
    data = tmp_path / "train.jsonl"
    rows = [_row(1, "a", 0, 1.0), _row(1, "a", 0, 4.0)]
    data.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    out = tmp_path / "lora"
    assert main(["--data", str(data), "--out", str(out), "--dry-run"]) == 0
    lines = (out / "grpo_data.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    d = json.loads(lines[0])
    assert set(d) == {"prompt", "response", "advantage", "reward", "group"}


def test_thieu_thu_vien_thi_noi_thang_va_thoat_2(tmp_path, monkeypatch):
    """Một script huấn luyện chưa chạy bao giờ mà trông như đã chạy là thứ tệ
    nhất trong một kho nghiên cứu — nên khi thiếu thư viện, nó phải NÓI."""
    import builtins

    real_import = builtins.__import__

    def fake(name, *a, **k):
        if name in ("peft", "transformers", "torch"):
            raise ImportError(f"giả vờ thiếu {name}")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    data = tmp_path / "train.jsonl"
    data.write_text(json.dumps(_row(1, "a", 0, 1.0)) + "\n"
                    + json.dumps(_row(1, "a", 0, 4.0)) + "\n", encoding="utf-8")
    assert main(["--data", str(data), "--out", str(tmp_path / "o")]) == 2


@pytest.mark.slow
def test_vong_huan_luyen_chay_that_va_luu_adapter(tmp_path):
    """Vòng GRPO ngoại tuyến chạy thật trên một model nhỏ và lưu được adapter.

    Chậm (nạp model + vài bước trên MPS/CPU), nên nó chỉ chạy khi có sẵn model
    trong cache HuggingFace — không tải về giữa lúc chạy test.
    """
    import os

    if os.environ.get("GENESIS_SLOW_TESTS") != "1":
        pytest.skip("đặt GENESIS_SLOW_TESTS=1 để chạy bài nạp model thật")

    data = tmp_path / "train.jsonl"
    rows = [_row(1, "a", 0, 1.0, '{"goal":"REST","ttl":3}'),
            _row(1, "a", 0, 4.0, '{"goal":"FORAGE","ttl":6}')]
    data.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    out = tmp_path / "lora"
    rc = main(["--data", str(data), "--out", str(out),
               "--model", "Qwen/Qwen2.5-0.5B-Instruct", "--steps", "2"])
    assert rc == 0
    assert (out / "adapter" / "adapter_model.safetensors").exists()
