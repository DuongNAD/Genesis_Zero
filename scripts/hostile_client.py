#!/usr/bin/env python3
"""Client thù địch: gửi những thứ một client tử tế không bao giờ gửi (N-07, N-11).

    python scripts/hostile_client.py --server http://localhost:8000

Chạy nó **TRƯỚC** khi phơi server ra internet, không phải sau. Mỗi ca dưới đây
tương ứng một dòng trong bảng lỗi của [docs/05 §3.4](../docs/05-GIAO-THUC.md);
ca nào server trả sai mã là một cánh cửa còn mở.

Đây không phải công cụ tấn công người khác: nó chỉ chạy vào server **của chính
bạn**, và nó tồn tại để bạn tìm ra lỗ trước khi người lạ tìm ra.
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

# Ký tự điều khiển THẬT để nhét vào input. `CTRL_ONLY` là tập để KIỂM — tách ra
# vì bản đầu kiểm bằng cả chuỗi có kèm `[31m`, nên nó soi cả chữ `m` và số `3`
# và báo động giả trên một `species_id` hoàn toàn sạch.
CTRL = "\x00\x07\r\n\x1b"
CTRL_ONLY = frozenset(CTRL)


def _case(name: str, got: int, want: tuple[int, ...]) -> bool:
    ok = got in want
    print(f"  {'✓' if ok else '✗'} {name:<46} {got} (mong đợi {'/'.join(map(str, want))})")
    return ok


def run(base: str, client=None) -> int:
    """`client` cho phép chạy ngay trong tiến trình (test) mà không mở cổng.

    Nhận một client đã dựng sẵn chứ không nhận `transport`: `ASGITransport` của
    httpx là bất đồng bộ, nên `httpx.Client` không bọc nó được — và `TestClient`
    của starlette thì bọc sẵn.
    """
    fails = 0
    own = client is None
    c = client or httpx.Client(base_url=base.rstrip("/"), timeout=20.0)
    try:
        print("── không auth ──")
        fails += not _case("GET /v1/work không token", c.get("/v1/work").status_code, (401, 403))
        fails += not _case("POST /v1/decision không token",
                           c.post("/v1/decision", json={}).status_code, (401, 403, 422))
        fails += not _case("POST /v1/heartbeat token bịa",
                           c.post("/v1/heartbeat", headers={"Authorization": "Bearer bia"},
                                  json={"healthy": True}).status_code, (401, 403))

        print("── join bẩn ──")
        fails += not _case("persona 5000 ký tự", c.post("/v1/join", json={
            "display_name": "x", "persona": "x" * 5000, "brain_tier": 3,
        }).status_code, (422,))
        fails += not _case("brain_tier = 99", c.post("/v1/join", json={
            "display_name": "x", "brain_tier": 99,
        }).status_code, (422,))
        fails += not _case("brain_tier = 'ba'", c.post("/v1/join", json={
            "display_name": "x", "brain_tier": "ba",
        }).status_code, (422,))

        r = c.post("/v1/join", json={
            "display_name": f"Kẻ{CTRL}Xấu", "persona": f"tốt{CTRL}bụng",
            "brain_tier": 3, "pop_request": 2,
        })
        if r.status_code == 200:
            d = r.json()
            probe = d["species_id"] + str(d.get("display_name", ""))
            ok = not (CTRL_ONLY & set(probe))
            print(f"  {'✓' if ok else '✗'} ký tự điều khiển bị lọc khỏi định danh")
            fails += not ok
            token = d["token"]
            h = {"Authorization": f"Bearer {token}"}

            print("── decision bẩn ──")
            fails += not _case("body 200 KB", c.post("/v1/decision", headers=h, content=b"x" * 200_000,
                                                     ).status_code, (413, 422))
            fails += not _case("work_id bịa", c.post("/v1/decision", headers=h, json={
                "work_id": "khong:ton:tai", "payload": {"goal": "FORAGE", "ttl": 5},
            }).status_code, (404, 409, 410))
            fails += not _case("payload không phải dict", c.post("/v1/decision", headers=h, json={
                "work_id": "a:b:c:decide", "payload": "chuỗi",
            }).status_code, (404, 409, 410, 422))
            fails += not _case("gửi tick từ client (bị bỏ qua)", c.post(
                "/v1/decision", headers=h,
                json={"work_id": "a:b:c:decide", "tick": 99999,
                      "payload": {"goal": "FORAGE", "ttl": 5}},
            ).status_code, (404, 409, 410, 422))

            print("── trần lạm dụng ──")
            # `hold_ms=1`: không có nó thì mỗi lời gọi giữ 25 giây và 200 lượt
            # mất hơn một giờ. Bản thân điều đó là một phát hiện — xem
            # `MAX_CONCURRENT_HOLDS` ở net_config: một client có thể giữ hàng
            # trăm kết nối mở cùng lúc, kiểu slow-loris.
            codes = [c.get("/v1/work?hold_ms=1", headers=h).status_code
                     for _ in range(200)]
            fails += not _case("200 lần /work liên tiếp -> có 429", 429 if 429 in codes else codes[-1], (429,))
        else:
            print(f"  (bỏ qua phần cần token: /join trả {r.status_code})")

        print("── luật ẩn ──")
        body = c.get("/v1/state").text + c.get("/v1/match/result").text
        leaked = [w for w in ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D") if w in body]
        print(f"  {'✓' if not leaked else '✗'} không rò tên lớp quả  {leaked or ''}")
        fails += bool(leaked)

    finally:
        if own:
            c.close()

    print(f"\n{'CỬA ĐÃ ĐÓNG' if not fails else f'CÒN {fails} CỬA MỞ'}")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://localhost:8000")
    a = ap.parse_args(argv)
    return run(a.server)


if __name__ == "__main__":
    raise SystemExit(main())
