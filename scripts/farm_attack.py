#!/usr/bin/env python3
"""Agent farming: tấn công bảng ghi công của B-12, và phải ăn 0.

    python scripts/farm_attack.py --pattern ring --n 5
    python scripts/farm_attack.py --pattern flood --n 5

Phiếu B-12 §3 nói thẳng: *"Đừng chỉ đọc code rồi tin bất biến 3. **Tự viết agent
farming** và kiểm rằng nó ăn 0."* Đây là agent đó.

Hai kiểu tấn công, tương ứng hai khoá:

* `ring` — n con dạy chéo nhau thành vòng tròn về **cùng một luật**. Nếu credit
  không chảy một chiều theo thời gian thì mỗi cạnh của vòng đều ăn điểm và cả
  vòng in tiền. Đây là chiến lược tối ưu nếu khoá 1 hỏng.
* `flood` — một con dạy tất cả mọi người, mọi thứ, liên tục. Nếu mỗi cặp không
  chỉ tính một lần thì lặp lại là nhân đôi.

Ngoài ra kiểm khoá 3 (chuỗi 2 nấc) bằng một dây chuyền A→B→C→D.
"""

from __future__ import annotations

import argparse
import sys

from genesis.lawdsl import Cond, CondKind, Dur, Effect, EffectKind, Law, Mag, Trigger, TriggerKind
from genesis.provenance import Ledger, law_key

LAW = Law(
    trigger=Trigger(TriggerKind.EAT, "FRUIT_A"),
    conds=(Cond(CondKind.PHASE, "NIGHT"),),
    effect=Effect(EffectKind.POISON, Mag.MED, Dur.LONG),
)


def ring(n: int) -> dict[str, float]:
    """n con, ai cũng dạy người kế tiếp, ai cũng "biết" ở cùng một tick."""
    led = Ledger()
    key = law_key(LAW)
    ids = [f"F:{i}" for i in range(n)]
    for cid in ids:
        led.learn(cid, key, tick=0)                     # tất cả biết cùng lúc
    for i, cid in enumerate(ids):                        # dạy vòng tròn
        nxt = ids[(i + 1) % n]
        led.learn(nxt, key, tick=1, taught_by=cid)
    for cid in ids:                                      # rồi ai cũng ghi sổ
        led.award(cid, key, tick=2)
    return led.citations


def flood(n: int) -> dict[str, float]:
    """Một con dạy tất cả, lặp 50 lần. Chỉ người CHƯA biết mới được tính."""
    led = Ledger()
    key = law_key(LAW)
    led.learn("F:0", key, tick=0)
    victims = [f"V:{i}" for i in range(n)]
    led.learn(victims[0], key, tick=0)                   # người này đã tự biết rồi
    for _ in range(50):
        for v in victims:
            led.learn(v, key, tick=1, taught_by="F:0")
            led.award(v, key, tick=2)
    return led.citations


def chain(depth: int = 4) -> dict[str, float]:
    """A→B→C→D. Khoá 3, nguyên văn phiếu: "A→B→C thì A nhận từ B, **không**
    nhận từ C." Nghĩa là công chỉ chảy MỘT nấc: mỗi lần ai đó ghi sổ, chỉ người
    dạy TRỰC TIẾP được tính. Chia cho cả nấc hai thì mỗi tầng của tháp đa cấp
    vẫn có lãi, chỉ nhỏ hơn — và thế thì lập tháp vẫn là chiến lược đúng."""
    led = Ledger()
    key = law_key(LAW)
    ids = [chr(ord("A") + i) for i in range(depth)]
    led.learn(ids[0], key, tick=0)
    for i in range(1, depth):
        led.learn(ids[i], key, tick=i, taught_by=ids[i - 1])
        led.award(ids[i], key, tick=i)
    return led.citations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", choices=["ring", "flood", "chain", "all"], default="all")
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args(argv)

    fail = 0
    if a.pattern in ("ring", "all"):
        c = ring(a.n)
        total = sum(c.values())
        print(f"ring(n={a.n}):  tổng citation = {total}  {c}")
        if total != 0:
            print("  ✗ VÒNG TRÒN DẠY CHÉO ĂN ĐIỂM — khoá 1 hỏng", file=sys.stderr)
            fail = 1
    if a.pattern in ("flood", "all"):
        c = flood(a.n)
        print(f"flood(n={a.n}): tổng citation = {sum(c.values())}  {c}")
        # dạy 50 lần cho n người, một người đã biết sẵn -> đúng (n-1) điểm
        if sum(c.values()) != a.n - 1:
            print(f"  ✗ mong đợi {a.n - 1}, nhận {sum(c.values())} — khoá 2 hỏng", file=sys.stderr)
            fail = 1
    if a.pattern in ("chain", "all"):
        c = chain()
        print(f"chain(A→B→C→D): {c}")
        if c != {"A": 1.0, "B": 1.0, "C": 1.0}:
            print(f"  ✗ mong đợi mỗi người đúng 1.0 từ học trò TRỰC TIẾP, nhận {c}",
                  file=sys.stderr)
            fail = 1
    print("KHÔNG FARM ĐƯỢC" if not fail else "CÓ ĐƯỜNG FARM")
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
