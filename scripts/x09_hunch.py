"""X-09 — Linh cảm có rút ngắn `t_discover` không? (B-14)

    python scripts/x09_hunch.py --seeds 5 --ticks 200 --llm-url http://127.0.0.1:8080

Cùng model, cùng trọng số, cùng seed, cùng luật. Khác đúng hai thứ: một khối
prompt và một cuốn sổ nháp. Đó là điều làm mệnh đề này **đo được** — và rẻ hơn
R-03 vài bậc độ lớn.

## Mệnh đề đang kiểm

Sổ Luật gánh hai việc: ghi giả thuyết VÀ nộp bài. Ô sổ thì ít (brain 0 có đúng
một), ghi thì tốn `CLAIM_COOLDOWN = 25`. Nên *thử một khả năng* trả giá y hệt
*tuyên bố đã biết* — và đo được là điều đó bóp nghẹt cả hai đầu:

* `L5:1` **tìm ra luật ở tick 99 rồi phải xoá ở tick 148** để lấy chỗ ghi thứ khác.
* Model viết **24/45 mục về ăn quả**; L1 viết 9 mục thì **cả 9 về ăn quả**.

Nếu linh cảm gỡ được nút ấy thì hai con số phải nhúc nhích: `t_discover` ngắn
lại, và **chủ đề** của các mục Sổ Luật tản ra khỏi chỗ quả.

## Và nó được phép trả lời KHÔNG

Cột `chủ đề` in ra ở dưới đáng đọc kỹ hơn cả cột `match`. Nếu có linh cảm mà
model vẫn chỉ nghi về ăn quả thì nút thắt **không phải** chi phí ghi sổ — nó là
chỗ model không bao giờ nhìn tới, và B-14 không cứu được. Đó vẫn là một kết quả,
và nó chỉ đúng chỗ tiếp theo phải đào.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import statistics
import sys

from genesis.lawdsl import to_json
from genesis.lawgen import generate_cached
from genesis.logio import LogWriter
from genesis.score import score_match
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick


def one_match(seed: int, ticks: int, url: str, out: Path, with_hunch: bool,
              ids: list[str], transport=None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    tag = "co" if with_hunch else "khong"
    log_p, truth_p = out / f"{tag}-{seed}.jsonl", out / f"{tag}-{seed}.truth.json"

    laws = generate_cached(seed, arm="STANDARD")
    world, creatures, state, rng = build_match(seed, laws=laws)
    with LogWriter(log_p, f"hu_{tag}_{seed}") as log:
        log.write(0, "RUN_START", seed=seed, ticks=ticks, arm="STANDARD",
                  n_laws=len(laws))
        strat = LlmStrategist(url, ids, log=log, transport=transport)
        # Đúng MỘT dòng khác nhau giữa hai nhánh. Mọi thứ còn lại — seed, luật,
        # hoán vị bề mặt, thứ tự duyệt — giống hệt.
        strat.minds.hunch_enabled = with_hunch
        for t in range(ticks):
            tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=strat)
        log.write(ticks, "RUN_END", ticks=ticks)

    truth_p.write_text(json.dumps({
        "seed": seed, "arm": "STANDARD", "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }, ensure_ascii=False), encoding="utf-8")

    rows = score_match(log_p, truth_p)
    found = [r for r in rows if str(r.get("found")).lower() in ("true", "1")]

    # Chủ đề của những gì nó GHI VÀO SỔ — cột đáng đọc nhất của cả thí nghiệm.
    log_rows = [json.loads(x) for x in log_p.read_text(encoding="utf-8").splitlines() if x.strip()]
    subj = collections.Counter(
        r["law"]["trigger"]["kind"]
        for r in log_rows
        if r.get("kind") == "CODEX_OP" and r.get("ok") and r.get("law")
    )
    n_hunch = sum(1 for r in log_rows if r.get("kind") == "HUNCH_OP" and r.get("ok"))
    subj_h = collections.Counter(
        r["law"]["trigger"]["kind"]
        for r in log_rows
        if r.get("kind") == "HUNCH_OP" and r.get("ok") and r.get("law")
    )

    # BẢNG ĐẾM cuối ván — cột đáng đọc nhất khi `match` kẹt ở 0 cho cả hai nhánh.
    #
    # `match` chỉ trả lời "có tìm ra luật không". Nếu cả hai nhánh cùng 0 thì nó
    # không phân biệt được "linh cảm vô dụng" với "chưa gì cứu nổi ở mức này" —
    # và câu thứ hai mới đúng với Qwen-7B hôm nay. Ba cột dưới đây trả lời một
    # câu KHÁC và trả lời được ngay cả khi match = 0: *cơ chế có chạy không, và
    # con vật có thu được bằng chứng phủ định không.*
    thu = dung = 0
    bac_bo = 0          # linh cảm thử >= 5 lần mà đúng 0 — bằng chứng PHỦ ĐỊNH
    xac_nhan = 0        # thử >= 5 lần và đúng >= 80%
    o_da_dung = 0
    for hb in strat.minds.hunches.values():
        for h in hb.entries():
            if h is None:
                continue
            o_da_dung += 1
            thu += h.tried
            dung += h.hit
            if h.tried >= 5:
                if h.hit == 0:
                    bac_bo += 1
                elif h.hit >= 0.8 * h.tried:
                    xac_nhan += 1
    return {
        "seed": seed, "hunch": with_hunch,
        "n_found": len(found),
        "best_match": max((float(r["match"]) for r in rows), default=0.0),
        "mean_t_discover": statistics.fmean(int(r["t_discover"]) for r in found)
        if found else None,
        "n_codex": int(sum(subj.values())),
        "chu_de_so": dict(subj.most_common(4)),
        "n_hunch": n_hunch,
        "chu_de_linh_cam": dict(subj_h.most_common(4)),
        "o_linh_cam_da_dung": o_da_dung,
        "tong_thu": thu, "tong_dung": dung,
        "so_linh_cam_bi_BAC_BO": bac_bo,
        "so_linh_cam_duoc_XAC_NHAN": xac_nhan,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--llm-url", default="http://127.0.0.1:8080")
    ap.add_argument("--ids", default="L1:0,L1:1,L2:0,L5:0")
    ap.add_argument("--out", type=Path, default=Path("runs/hunch"))
    a = ap.parse_args(argv)

    ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    rows = []
    for seed in range(1, a.seeds + 1):
        for hu in (False, True):
            r = one_match(seed, a.ticks, a.llm_url, a.out, hu, ids)
            rows.append(r)
            print(f"  seed {seed} · linh cảm {'CÓ ' if hu else 'KHÔNG'} · "
                  f"tìm ra {r['n_found']} · match cao nhất {r['best_match']:.2f} · "
                  f"t_discover {r['mean_t_discover']} · "
                  f"ghi sổ {r['n_codex']} {r['chu_de_so']}"
                  + (f" · linh cảm {r['n_hunch']} ô, thử {r['tong_thu']} đúng "
                     f"{r['tong_dung']}, bác bỏ {r['so_linh_cam_bi_BAC_BO']} "
                     f"xác nhận {r['so_linh_cam_duoc_XAC_NHAN']} {r['chu_de_linh_cam']}"
                     if hu else ""),
                  flush=True)

    (a.out / "x09.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    print()
    for hu in (False, True):
        sub = [r for r in rows if r["hunch"] is hu]
        ts = [r["mean_t_discover"] for r in sub if r["mean_t_discover"] is not None]
        subj: collections.Counter = collections.Counter()
        for r in sub:
            subj.update(r["chu_de_so"])
        print(f"{'CÓ ' if hu else 'KHÔNG'} linh cảm: tìm ra "
              f"{sum(r['n_found'] for r in sub)} luật · "
              f"match cao nhất {max((r['best_match'] for r in sub), default=0.0):.3f} · "
              f"t_discover trung bình {statistics.fmean(ts) if ts else 'NA'} · "
              f"chủ đề sổ {dict(subj.most_common(4))}")
    co = [r for r in rows if r["hunch"]]
    print(f"\nCƠ CHẾ CÓ CHẠY KHÔNG: {sum(r['o_linh_cam_da_dung'] for r in co)} ô đã dùng · "
          f"{sum(r['tong_thu'] for r in co)} lượt thử · "
          f"{sum(r['so_linh_cam_bi_BAC_BO'] for r in co)} linh cảm BỊ BÁC BỎ · "
          f"{sum(r['so_linh_cam_duoc_XAC_NHAN'] for r in co)} được XÁC NHẬN")
    print("  (bác bỏ = thử >= 5 lần, đúng 0 — đó là bằng chứng phủ định, thứ sổ\n"
          "   tay 6 dòng không giữ nổi. Bằng 0 nghĩa là cơ chế chưa chạy tới nơi,\n"
          "   và mọi kết luận về `match` bên dưới đều chưa có căn cứ.)")
    print(
        "\nĐọc kết quả — cột CHỦ ĐỀ trước cột match:\n"
        "  · `t_discover` ngắn lại VÀ chủ đề tản ra khỏi chỗ quả -> nút thắt đúng\n"
        "    là chi phí ghi sổ, và B-14 gỡ được nó.\n"
        "  · match nhích lên mà chủ đề KHÔNG đổi -> coi chừng: nhiều khả năng\n"
        "    bảng đếm đang rò thông tin chứ không phải model nghĩ khá hơn. Kiểm\n"
        "    lại bất biến 3 của B-14 (chỉ so EffectKind, không so mag/dur).\n"
        "  · không đổi gì -> nút thắt không nằm ở giá ghi sổ. Model không nhìn ra\n"
        "    khỏi chỗ quả, và chỗ phải đào tiếp là prompt hoặc model, không phải\n"
        "    thêm một cuốn sổ nữa.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
