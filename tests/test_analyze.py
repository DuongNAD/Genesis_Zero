"""Kiểm thử phân tích dữ liệu và xuất báo cáo biểu đồ (X-05)."""

from __future__ import annotations

import csv
from pathlib import Path
import pytest

from genesis.analyze import (
    chart_law_tier,
    chart_match_by_species,
    chart_tdiscover_hist,
    load_scores,
    summarize,
    write_report,
)
from genesis.score import FIELDS


@pytest.fixture
def sample_rows() -> list[dict]:
    return [
        {
            "match_id": "m_00001", "seed": 1, "creature_id": "L1:0", "species_id": "L1",
            "law_idx": 0, "tier": "D1", "w": 1.0, "match": 1.0, "t_discover": 40,
            "speed": 0.9, "R_i": 0.94, "exploit_lag": 0.05, "pred_acc": 0.875, "R_survive": 1.0,
        },
        {
            "match_id": "m_00001", "seed": 1, "creature_id": "L1:0", "species_id": "L1",
            "law_idx": 1, "tier": "D2", "w": 1.5, "match": 1.0, "t_discover": 120,
            "speed": 0.7, "R_i": 1.23, "exploit_lag": 0.15, "pred_acc": 0.875, "R_survive": 1.0,
        },
        {
            "match_id": "m_00001", "seed": 1, "creature_id": "L1:0", "species_id": "L1",
            "law_idx": 2, "tier": "D3", "w": 2.2, "match": 0.0, "t_discover": 401,
            "speed": 0.0, "R_i": 0.0, "exploit_lag": "NA", "pred_acc": "NA", "R_survive": 1.0,
        },
        {
            "match_id": "m_00001", "seed": 1, "creature_id": "L5:0", "species_id": "L5",
            "law_idx": 0, "tier": "D1", "w": 1.0, "match": 0.0, "t_discover": 401,
            "speed": 0.0, "R_i": 0.0, "exploit_lag": "NA", "pred_acc": "NA", "R_survive": 0.8,
        },
    ]


def test_tdiscover_t_plus_1_khong_vao_trung_binh(sample_rows, tmp_path):
    """Yêu cầu 1: `t_discover == T+1` vào cột 'không tìm ra', KHÔNG vào trung bình.

    `summarize` phải trả cả `n_found` lẫn `n_total`.
    """
    s = summarize(sample_rows)
    ov = s["overall"]
    assert ov["n_total"] == 4
    assert ov["n_found"] == 2
    # Chỉ tính trung bình trên 2 ca tìm ra: (40 + 120) / 2 = 80.0
    assert ov["mean_t_discover"] == pytest.approx(80.0)

    # Loài L1 tìm ra 2/3 luật -> mean t_discover = 80.0
    l1_stat = s["by_species"]["L1"]
    assert l1_stat["n_total"] == 3
    assert l1_stat["n_found"] == 2
    assert l1_stat["mean_t_discover"] == pytest.approx(80.0)

    # Loài L5 không tìm ra luật nào -> mean t_discover là None
    l5_stat = s["by_species"]["L5"]
    assert l5_stat["n_total"] == 1
    assert l5_stat["n_found"] == 0
    assert l5_stat["mean_t_discover"] is None

    # Biểu đồ histogram được vẽ và chứa cả cột chưa tìm ra
    out_hist = chart_tdiscover_hist(sample_rows, tmp_path / "hist.svg")
    assert out_hist.exists()
    content = out_hist.read_text(encoding="utf-8")
    assert "Tìm ra" in content or "t_discover" in content


def test_exploit_lag_na_loai_khoi_trung_binh(sample_rows):
    """Yêu cầu 2: hàng có `exploit_lag == 'NA'` bị loại khỏi trung bình và số ca loại được ghi lại."""
    s = summarize(sample_rows)
    ov = s["overall"]

    # 2 ca có số liệu: 0.05 và 0.15 -> trung bình = 0.10 (không bị kéo tụt bởi 2 ca NA)
    assert ov["mean_exploit_lag"] == pytest.approx(0.10)
    assert ov["n_exploit_lag_na"] == 2
    assert ov["n_exploit_lag_valid"] == 2

    # pred_acc: 2 ca có số liệu 0.875, 2 ca NA
    assert ov["mean_pred_acc"] == pytest.approx(0.875)
    assert ov["n_pred_acc_na"] == 2
    assert ov["n_pred_acc_valid"] == 2


def test_summarize_danh_sach_rong(tmp_path):
    """Yêu cầu 3: `summarize` trên danh sách RỖNG trả cấu trúc hợp lệ, không ném.

    Các hàm chart vẽ biểu đồ rỗng có chữ 'chưa có dữ liệu', không ném lỗi.
    """
    s = summarize([])
    assert s["total_rows"] == 0
    assert s["by_species"] == {}
    assert s["by_tier"] == {}
    assert s["overall"]["n_total"] == 0
    assert s["overall"]["n_found"] == 0
    assert s["overall"]["mean_match"] == 0.0
    assert s["overall"]["mean_t_discover"] is None
    assert s["overall"]["mean_exploit_lag"] is None
    assert s["overall"]["n_exploit_lag_na"] == 0
    assert s["overall"]["mean_pred_acc"] is None
    assert s["overall"]["n_pred_acc_na"] == 0

    p_sp = chart_match_by_species([], tmp_path / "species.svg")
    p_hist = chart_tdiscover_hist([], tmp_path / "hist.svg")
    p_tier = chart_law_tier([], tmp_path / "tier.svg")

    for p in (p_sp, p_hist, p_tier):
        assert p.exists()
        assert "chưa có dữ liệu" in p.read_text(encoding="utf-8")


def test_write_report_tao_du_file_va_nhac_thieu_mau(sample_rows, tmp_path):
    """Yêu cầu 4: `write_report` tạo đủ file và `summary.md` nhắc số ca thiếu mẫu."""
    out_dir = tmp_path / "report"
    rep = write_report(sample_rows, out_dir)

    assert rep.exists()
    assert (out_dir / "match_by_species.svg").exists()
    assert (out_dir / "tdiscover_hist.svg").exists()
    assert (out_dir / "law_tier.svg").exists()

    md_text = rep.read_text(encoding="utf-8")
    assert "Báo cáo phân tích kết quả khám phá luật" in md_text
    assert "Thống kê theo loài" in md_text
    assert "Thống kê theo tier luật" in md_text
    assert "Ghi chú thiếu mẫu" in md_text
    assert "exploit_lag == NA" in md_text
    assert "pred_acc == NA" in md_text
    assert "2 / 4" in md_text


def test_tat_dinh_hai_lan_goi_cho_file_giong_het_nhau(sample_rows, tmp_path):
    """Yêu cầu 5: hai lần gọi cùng dữ liệu cho file giống hệt nhau (tất định)."""
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    write_report(sample_rows, dir1)
    write_report(sample_rows, dir2)

    for fname in ("summary.md", "match_by_species.svg", "tdiscover_hist.svg", "law_tier.svg"):
        f1 = dir1 / fname
        f2 = dir2 / fname
        assert f1.read_bytes() == f2.read_bytes(), f"File {fname} không khớp byte giữa 2 lần chạy"


def test_load_scores_doc_csv_dung_dinh_dang(tmp_path):
    """Kiểm tra load_scores đọc đúng các trường từ file CSV của score.py."""
    csv_file = tmp_path / "scores.csv"
    rows_in = [
        {
            "match_id": "m_1", "seed": "1", "creature_id": "L1:0", "species_id": "L1",
            "law_idx": "0", "tier": "D1", "w": "1.0", "match": "0.85", "t_discover": "50",
            "speed": "0.875", "R_i": "0.80", "exploit_lag": "0.12", "pred_acc": "0.75",
            "R_survive": "0.95",
        },
        {
            "match_id": "m_1", "seed": "1", "creature_id": "L1:0", "species_id": "L1",
            "law_idx": "1", "tier": "D2", "w": "1.5", "match": "0.0", "t_discover": "401",
            "speed": "0.0", "R_i": "0.0", "exploit_lag": "NA", "pred_acc": "NA",
            "R_survive": "0.95",
        },
    ]
    with csv_file.open("w", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows_in)

    loaded = load_scores([csv_file])
    assert len(loaded) == 2
    assert loaded[0]["seed"] == 1
    assert loaded[0]["match"] == 0.85
    assert loaded[0]["t_discover"] == 50
    assert loaded[0]["exploit_lag"] == 0.12
    assert loaded[0]["pred_acc"] == 0.75

    assert loaded[1]["match"] == 0.0
    assert loaded[1]["t_discover"] == 401
    assert loaded[1]["exploit_lag"] == "NA"
    assert loaded[1]["pred_acc"] == "NA"
