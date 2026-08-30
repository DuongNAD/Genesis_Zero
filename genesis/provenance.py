"""Genesis Zero — provenance: hiểu biết đến từ đâu, và ai được ghi công (B-12).

Tách khỏi `teach.py` vì nó trả lời một câu hỏi khác: `teach` hỏi *ai nói gì với
ai*, còn file này hỏi *ai là người đầu tiên biết, và chuỗi truyền đi thế nào*.

Ba khoá chống farming của phiếu B-12 §2, cả ba bắt buộc, và cả ba đều nằm ở đây
chứ không nằm ở chỗ chấm điểm:

1. **Credit chảy một chiều theo thời gian.** Dạy lại người đã biết ăn 0.
2. **Mỗi cặp (luật, người nhận) tính một lần**, dù dạy bao nhiêu lần.
3. **Chuỗi tối đa 2 nấc.** A→B→C thì A nhận từ B, **không** nhận từ C. Không có
   khoá này thì mọi tháp đa cấp đều lãi, và chiến lược tối ưu là lập vòng tròn
   dạy chéo thay vì đi tìm luật.

`scripts/farm_attack.py` dựng đúng hai kiểu tấn công ấy và đòi kết quả bằng 0.
Đừng chỉ đọc code rồi tin — phiếu nói rõ: **tự viết agent farming và kiểm nó ăn 0.**
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from genesis.lawdsl import Law, to_json

# Chuỗi được GHI tới 2 nấc (để báo cáo hiểu biết đi đường nào), nhưng công chỉ
# chảy MỘT nấc. Phiếu B-12 nói đúng câu này: "A→B→C thì A nhận từ B, **không**
# nhận từ C." Bản đầu ở đây chia cho cả nấc hai và A ăn 1,5 trong dây chuyền
# A→B→C→D — tức là mỗi tầng của một tháp đa cấp vẫn có lãi, chỉ nhỏ hơn.
CHAIN_RECORD_DEPTH = 2
CREDIT_DEPTH = 1
CITATION_VALUE = 1.0


def law_key(law: Law) -> str:
    """Khoá nội dung của một phát biểu. Hai người nói y hệt nhau là cùng một khoá.

    Dùng nội dung chứ không dùng chỉ số luật thật: lúc dạy nhau, chưa ai biết
    luật thật là gì — kể cả server cũng không được dùng thông tin đó ở đây, nếu
    không chính bảng ghi công đã rò đáp án.
    """
    return json.dumps(to_json(law), sort_keys=True, ensure_ascii=False)


@dataclass
class Provenance:
    law_id: str                                  # law_key
    discoverer: str
    chain: list[str] = field(default_factory=list)


class Ledger:
    """Sổ cái: ai biết gì, biết từ ai, từ lúc nào."""

    def __init__(self) -> None:
        self.knows: dict[str, dict[str, int]] = {}          # cid -> {key: tick biết}
        self.source: dict[tuple[str, str], str] = {}        # (cid, key) -> ai dạy
        self.discoverer: dict[str, tuple[str, int]] = {}    # key -> (cid, tick)
        self.credited: set[tuple[str, str]] = set()         # (người nhận, key) đã tính
        self.citations: dict[str, float] = {}

    # ── ghi nhận ─────────────────────────────────────────────────────────
    def learn(self, cid: str, key: str, tick: int, taught_by: str | None = None) -> bool:
        """Ghi nhận `cid` biết `key`. Trả True nếu đây là lần ĐẦU nó biết."""
        seen = self.knows.setdefault(cid, {})
        if key in seen:
            return False
        seen[key] = tick
        if taught_by is not None:
            self.source[(cid, key)] = taught_by
        self.discoverer.setdefault(key, (cid, tick))
        return True

    def knew_before(self, cid: str, key: str, tick: int) -> bool:
        t = self.knows.get(cid, {}).get(key)
        return t is not None and t <= tick

    def chain_of(self, cid: str, key: str, depth: int = CHAIN_RECORD_DEPTH) -> list[str]:
        """Đi ngược chuỗi người dạy, tối đa `depth` nấc, không lặp vô hạn."""
        out: list[str] = []
        cur = cid
        seen = {cid}
        while len(out) < depth:
            src = self.source.get((cur, key))
            if src is None or src in seen:
                break
            out.append(src)
            seen.add(src)
            cur = src
        return out

    # ── ghi công ─────────────────────────────────────────────────────────
    def award(self, receiver: str, key: str, tick: int) -> dict[str, float]:
        """Người nhận vừa TỰ TAY ghi `key` vào sổ. Chia công cho chuỗi đã dạy.

        Gọi ở lúc **ghi sổ**, không ở lúc nghe: người nghe không tự động tin
        (bất biến 2), nên chỉ khi họ chịu tốn một ô sổ và một ít energy thì lời
        dạy ấy mới thật sự có giá trị.
        """
        if (receiver, key) in self.credited:
            return {}                       # khoá 2: mỗi cặp tính đúng một lần
        self.credited.add((receiver, key))

        out: dict[str, float] = {}
        # khoá 3: chỉ NGƯỜI DẠY TRỰC TIẾP được ghi công.
        for teacher in self.chain_of(receiver, key, depth=CREDIT_DEPTH):
            if teacher == receiver:
                continue
            t_learn = self.knows.get(teacher, {}).get(key)
            t_recv = self.knows.get(receiver, {}).get(key)
            # khoá 1: credit chảy một chiều theo thời gian. Người "dạy" mà biết
            # SAU người nhận thì không dạy gì cả — đó là vòng tròn dạy chéo.
            if t_learn is None or (t_recv is not None and t_learn >= t_recv):
                break
            out[teacher] = out.get(teacher, 0.0) + CITATION_VALUE
        for k, v in out.items():
            self.citations[k] = round(self.citations.get(k, 0.0) + v, 4)
        return out
