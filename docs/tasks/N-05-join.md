# N-05 · `/join` — cấp loài, token, persona

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-04 · **Chặn** N-10 |
| **File** | `net/routes_join.py` · ~110 dòng · 2 giờ |
| **Giao cho model rẻ?** | ✅ đặc tả ở [05 §3.1](../05-GIAO-THUC.md) đã đầy đủ |
| **Tài liệu gốc** | [05 §3.1](../05-GIAO-THUC.md), [04 §7.1](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
Cửa vào. Và là chỗ hiện thực **chống gian lận bằng ngân sách, không bằng xác minh**.

## 2. Chữ ký và bất biến
Request/response chính xác ở [05 §3.1](../05-GIAO-THUC.md).

**Bất biến 1 — không xác minh model.** Client khai 70B để xin `brain=5`? Cho luôn. Tổng trait vẫn 12, nên `brain` cao nghĩa là giáp mỏng, chậm, mắt kém. Khai láo không lợi gì. **Ngân sách tự thực thi.**
**Bất biến 2 — server quyết `traits`.** Client chọn `brain_tier`; server phân bổ `12 − brain` điểm còn lại. Client không được mặc cả.
**Bất biến 3 — persona chỉ vào prompt của chính client đó.** Hại thì tự hại. Cap 400 ký tự, strip ký tự điều khiển.
**Bất biến 4 — `display_name` thì kẻ khác đọc được.** Cap 24 ký tự, strip newline, lọc lúc join ([04 §7.4](../04-THE-GIOI-MO.md)).
**Bất biến 5 — hai giải.** `LEAGUE_LLM` (tự khai, danh dự) và `LEAGUE_OPEN` (bất cứ thứ gì). Bảng xếp hạng riêng.

## 3. Nghiệm thu
```bash
pytest tests/test_join.py -q
# ca: brain_tier 5 -> traits tổng vẫn 12 và các trait khác đều thấp
#     persona 500 ký tự -> 422 · display_name có "\n" -> bị strip
#     join lúc RUNNING -> queued true · 6 lần join/giờ từ một IP -> 429
curl -s -XPOST localhost:8000/v1/join -d '{"display_name":"Kiến Lửa","persona":"x",
  "model_name":"fake-999B","params_b":999,"brain_tier":5,"league":"LEAGUE_LLM","pop_request":2}' \
  | jq -e '.traits | to_entries | map(.value) | add == 12'
```

## 4. Prompt giao việc
```
BỐI CẢNH: FastAPI + Python 3.11. Đọc trước: docs/05-GIAO-THUC.md §3.1 (request/response
CHÍNH XÁC) và docs/tasks/N-05-join.md §2. Đã có: net/server.py với app và MatchRunner,
genesis/registry.py (SpeciesRegistry, SpeciesSpec), genesis/traits.py.
VIỆC: net/routes_join.py với POST /v1/join khớp CHÍNH XÁC hình dạng ở 05 §3.1.
- allocate_traits(brain_tier, rng) -> Traits: brain = brain_tier, phân bổ 12-brain điểm
  còn lại cho 5 trait kia sao cho mỗi trait <= 5. KHÔNG xác minh model_name/params_b.
- sinh client_id, token (secrets.token_urlsafe), species_id từ display_name đã slug hoá.
- sanitize: persona <= 400 ký tự (quá -> 422), display_name <= 24 ký tự, cả hai strip
  ký tự điều khiển và newline.
- rate limit 5 join/giờ mỗi IP -> 429 kèm Retry-After.
- pha RUNNING/SEEDING/REVEAL -> trả queued: true và xếp vào ván sau.
tests/test_join.py theo 5 ca ở §3.
RÀNG BUỘC: KHÔNG viết logic xác minh model. Không tạo/sửa file khác ngoài
net/routes_join.py và tests/test_join.py. Hằng số vào net_config.py.
NGHIỆM THU: pytest tests/test_join.py -q
TRẢ VỀ: chỉ diff.
```
