# N-04 · Server FastAPI và vòng đời ván

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-01, N-02, N-03, W-11 · **Chặn** N-05…N-08 |
| **File** | `net/server.py`, `net/match.py`, `net_config.py` · ~220 dòng · 4 giờ |
| **Giao cho model rẻ?** | ⚠️ khung FastAPI và máy trạng thái giao được; **ranh giới tin cậy tự quyết** |
| **Tài liệu gốc** | [04 §3](../04-THE-GIOI-MO.md), [05 §2](../05-GIAO-THUC.md) |

## 1. Mục tiêu
Đưa sim vào một tiến trình phục vụ nhiều client. Vòng đời ván là đơn vị của cả trò chơi lẫn cộng đồng.

## 2. Chữ ký và bất biến
```python
class Phase(StrEnum): LOBBY; SEEDING; RUNNING; REVEAL; COOLDOWN

class MatchRunner:
    async def loop(self) -> None: ...        # nhịp đồng hồ tường
    def advance_phase(self) -> None: ...
```
Bảng chuyển pha và endpoint nào hợp lệ ở pha nào: [05 §2](../05-GIAO-THUC.md).

**Bất biến 1 — server là đồng hồ duy nhất.** Client không bao giờ gửi `tick`. Điểm v5 phụ thuộc **thời điểm** ghi sổ, nên client khai lùi được là gian lận được ([04 §7.2](../04-THE-GIOI-MO.md)).
**Bất biến 2 — sảnh trống thì tự lấp bằng bot.** Ván **luôn** chạy. Sảnh phải chờ đủ người là cách nhanh nhất để dự án cộng đồng chết trong tuần đầu.
**Bất biến 3 — vào giữa ván thì xếp hàng ván sau.** Luật đã bị khám phá một nửa; điểm của người vào muộn sẽ vô nghĩa.
**Bất biến 4 — `T = OPEN_MATCH_TICKS = 200` ở chế độ mở**, không phải 400. Người lạ không chờ 27 phút.
**Bất biến 5 — luật thật không rời server trước `REVEAL`.** Kiểm bằng test tự động ([N-12](N-12-xem-live.md)), không bằng kỷ luật.

## 3. Nghiệm thu
```bash
uvicorn net.server:app --port 8000 &
sleep 2
curl -s localhost:8000/v1/state | jq -e '.phase'
pytest tests/test_match_lifecycle.py -q
# ca: LOBBY -> SEEDING -> RUNNING -> REVEAL -> COOLDOWN -> LOBBY, đúng thời lượng
#     0 client người thật -> ván vẫn chạy với toàn bot
#     join lúc RUNNING -> queued: true
# ★ ca rò rỉ: quét MỌI phản hồi HTTP trong pha RUNNING, không được chứa law_id hay tên effect
pytest tests/test_no_law_leak.py -q
```
