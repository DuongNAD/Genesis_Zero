"""Kiểm thử báo cáo tổng hợp Q1–Q7 (X-06)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from genesis.analyze import load_scores, summarize
from genesis.score import FIELDS
from scripts.x06_report import generate_report


@pytest.fixture
def sample_csv_rows() -> list[dict]:
    return [
        {
            "match_id": "m_001",
            "seed": 1,
            "creature_id": "L1:0",
            "species_id": "L1",
            "law_idx": 0,
            "tier": "D1",
            "w": 1.0,
            "match": 1.0,
            "found": "True",
            "t_discover": 40,
            "speed": 0.9,
            "R_i": 0.94,
            "exploit_lag": 0.05,
            "pred_acc": 0.875,
            "R_survive": 1.0,
        },
        {
            "match_id": "m_001",
            "seed": 1,
            "creature_id": "L1:0",
            "species_id": "L1",
            "law_idx": 1,
            "tier": "D2",
            "w": 1.5,
            "match": 0.85,
            "found": "True",
            "t_discover": 120,
            "speed": 0.7,
            "R_i": 1.05,
            "exploit_lag": 0.15,
            "pred_acc": 0.875,
            "R_survive": 1.0,
        },
        {
            "match_id": "m_001",
            "seed": 1,
            "creature_id": "L1:0",
            "species_id": "L1",
            "law_idx": 2,
            "tier": "D3",
            "w": 2.2,
            "match": 0.0,
            "found": "False",
            "t_discover": 401,
            "speed": 0.0,
            "R_i": 0.0,
            "exploit_lag": "NA",
            "pred_acc": "NA",
            "R_survive": 1.0,
        },
        {
            "match_id": "m_001",
            "seed": 1,
            "creature_id": "L5:0",
            "species_id": "L5",
            "law_idx": 0,
            "tier": "D1",
            "w": 1.0,
            "match": 0.0,
            "found": "False",
            "t_discover": 401,
            "speed": 0.0,
            "R_i": 0.0,
            "exploit_lag": "NA",
            "pred_acc": "NA",
            "R_survive": 0.8,
        },
    ]


def test_thu_muc_du_lieu_rong_khong_nem_va_noi_chua_do_duoc(tmp_path: Path):
    """Yêu cầu 1: chạy với thư mục rỗng -> tạo báo cáo hợp lệ, ghi 'chưa đo được' và không bịa số."""
    empty_data_dir = tmp_path / "empty_runs"
    empty_data_dir.mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "report_empty"

    report_file = generate_report(out_dir=out_dir, data_dir=empty_data_dir)
    assert report_file.exists()
    assert report_file.is_file()

    content = report_file.read_text(encoding="utf-8")

    # Báo cáo phải có đầy đủ các mục Q1 đến Q7
    for q_idx in range(1, 8):
        assert f"Q{q_idx}" in content, f"Thiếu mục Q{q_idx} trong báo cáo"

    # Khi không có dữ liệu, mọi câu hỏi phải nêu rõ 'chưa đo được'
    assert "chưa đo được" in content
    # Phải có hướng dẫn lệnh cần chạy
    assert "python" in content


def test_csv_nho_khop_con_so_voi_genesis_analyze_summarize(tmp_path: Path, sample_csv_rows: list[dict]):
    """Yêu cầu 2: chạy với CSV tự dựng -> các con số khớp với genesis.analyze.summarize."""
    data_dir = tmp_path / "sample_runs"
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_file = data_dir / "scores.csv"

    with csv_file.open("w", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sample_csv_rows)

    out_dir = tmp_path / "report_sample"
    report_file = generate_report(out_dir=out_dir, data_dir=data_dir)
    assert report_file.exists()

    content = report_file.read_text(encoding="utf-8")

    # Lấy thống kê chuẩn từ genesis.analyze.summarize
    loaded = load_scores([csv_file])
    expected = summarize(loaded)
    ov = expected["overall"]

    # Kiểm tra tổng mẫu và số ca tìm ra
    assert f"{ov['n_total']} mẫu" in content
    assert f"{ov['n_found']}/{ov['n_total']}" in content

    # Kiểm tra từng con số của loài L1
    l1_stat = expected["by_species"]["L1"]
    assert f"{l1_stat['mean_match']:.4f}" in content
    assert f"{l1_stat['mean_t_discover']:.4f}" in content
    assert f"{l1_stat['mean_exploit_lag']:.4f}" in content
    assert f"{l1_stat['mean_pred_acc']:.4f}" in content
    assert f"{l1_stat['mean_R_i']:.4f}" in content
    assert f"{l1_stat['mean_R_survive']:.4f}" in content

    # Kiểm tra từng con số của loài L5
    l5_stat = expected["by_species"]["L5"]
    assert f"{l5_stat['mean_match']:.4f}" in content
    assert f"{l5_stat['mean_R_survive']:.4f}" in content


def test_tat_dinh_hai_lan_chay_cung_du_lieu_cho_file_giong_het_nhau(tmp_path: Path, sample_csv_rows: list[dict]):
    """Yêu cầu 3: hai lần chạy cùng dữ liệu cho file giống hệt nhau byte-for-byte."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_file = data_dir / "scores.csv"

    with csv_file.open("w", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sample_csv_rows)

    # Thêm file x02-null.json mẫu
    x02_file = data_dir / "x02-null.json"
    x02_file.write_text(
        json.dumps({
            "seeds": 40,
            "ticks": 400,
            "by_world": {
                "LAW": {"per_species": {"L1": 0.5}, "top": "L1", "bottom": "L5", "gap": 0.1, "welch_t": 1.5, "df": 30.0},
                "FLAT": {"per_species": {"L1": 0.4}, "top": "L1", "bottom": "L5", "gap": 0.02, "welch_t": 0.3, "df": 30.0},
            },
            "shrink": 0.08,
            "verdict": "TỐT cho đường cơ sở",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    f1 = generate_report(out_dir=out1, data_dir=data_dir)
    f2 = generate_report(out_dir=out2, data_dir=data_dir)

    assert f1.read_bytes() == f2.read_bytes(), "Báo cáo xuất ra không khớp byte-for-byte giữa 2 lần chạy"
