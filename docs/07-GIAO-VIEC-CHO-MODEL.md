# 07 · Giao việc cho model rẻ

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · **07 Giao việc** · [08 Từ điển](08-TU-DIEN.md) · [09 Họ lỗi](09-HO-LOI.md)

> Bạn có một worker model nhanh và rẻ (Gemini Flash qua `mcp-agy`, hoặc tương đương).
> Tài liệu này nói **việc nào giao được, việc nào không, và giao thế nào để nhận về thứ dùng được.**

*(Tên model: `mcp-agy` nhận tham số `model`, ví dụ `gemini-3.7-flash-high`. Chạy `agy models` để lấy danh sách id hợp lệ — sai id thì nó lặng lẽ rơi về model mặc định và bạn sẽ tưởng model dở. Tham số `effort` để trống khi id đã mang sẵn hậu tố `-high`, CLI từ chối khi có cả hai.)*

---

## 1. Một tiêu chí, không phải một danh sách

Danh sách sẽ lạc hậu. Tiêu chí thì không:

> **Giao được khi bài kiểm tra nghiệm thu ghim chặt được tính đúng.**
> Giữ lại khi "trông đúng" và "đúng" là hai chuyện khác nhau mà test không phân biệt nổi.

Ví dụ hai đầu:

| | Giao được | Giữ lại |
|---|---|---|
| Việc | `to_json` / `from_json` cho LawDSL | `match()` |
| Test | round-trip 1000 luật ngẫu nhiên — sai là đỏ ngay | 8 ca viết tay — **pass hết mà vẫn có thể sai** ở ca thứ 9 bạn chưa nghĩ ra |
| Hỏng thì sao | thấy ngay, sửa 5 phút | mọi kết luận của cả dự án sai, **và không ai biết** |

Câu hỏi trước khi giao: *"nếu nó viết sai một cách tinh vi, tôi có phát hiện ra không?"* Không → tự viết.

## 2. Bảng phân loại

### ✅ Giao được — làm ngay, đừng tự viết

| Loại việc | Phiếu |
|---|---|
| Khung kho, `pyproject`, `Makefile`, cấu hình pytest | S-01, S-03 |
| Ghi/đọc JSONL, công cụ dòng lệnh xem log | S-04 |
| Serialize / deserialize / sinh GBNF từ dataclass | L-01 |
| Diễn giải cấu trúc ra tiếng Việt | L-07 |
| JSON Schema từ đặc tả có sẵn | B-01 |
| HTTP client async, timeout, thử lại, circuit breaker | B-03 |
| Xác thực ngữ nghĩa theo danh sách quy tắc đã viết sẵn | B-04 |
| Replay từ log | B-06 |
| Ba đường may mạng (interface, registry, id/log) | N-01, N-02, N-03 |
| Endpoint FastAPI theo đặc tả [05](05-GIAO-THUC.md) | N-05, N-06 |
| Client agent | N-10 |
| Trang xem live, bảng xếp hạng | N-12 |
| `analyze.py`, biểu đồ matplotlib | X-05 |
| Render pygame theo bảng ánh xạ trait đã có | X-07 |
| Viết test từ mục "Nghiệm thu" đã có sẵn của bất kỳ phiếu nào | mọi phiếu |

### ⚠️ Giao khung, tự làm lõi

| Việc | Giao | Giữ |
|---|---|---|
| S-02 | script build, cờ dòng lệnh | tự chạy, tự đọc lỗi CUDA |
| W-06, X-07 | bố cục, màu, vòng vẽ | quyết định hiển thị gì |
| W-13 | 4 loại quả, chu kỳ ngày/đêm, gió | **hoán vị bề mặt** ([03 §2.6](03-LUAT-AN-V5.md)) — sai chỗ này là hỏng phép đo |
| L-03 | vòng bốc thăm, ràng buộc kiểu | `observable()` — Gate A |
| L-04 | dựng `Situation`, tiện ích | **tỉ lệ phân tầng 40/40/20** và trải đều theo chiều cond |
| B-02 | ghép chuỗi, cắt theo brain | **nội dung khối A2** — từng câu một |
| B-07 | vòng đệm, định dạng cột | **quy tắc chọn khi tràn** và kiểm rò rỉ đáp án |
| B-10 | đọc JSONL, xuất CSV | **công thức điểm** |
| N-04, N-07 | khung FastAPI, máy trạng thái | ranh giới tin cậy: cái gì client được gửi |
| N-11 | tunnel, systemd, rate limit | quyết định phơi cái gì ra internet |

### ❌ Không giao — tự viết từng dòng

| Việc | Vì sao |
|---|---|
| W-01 … W-12 | v4 §10. Đây là phần tư duy. Chép code = quay lại đúng chỗ đã bế tắc với Anima Engine. |
| W-11 vòng tick | Tính đồng thời. Sai thì bug không tái lập được, và không test nào bắt. |
| L-02 cắm luật vào tick | Cùng lý do W-11, cộng thứ tự pha (`SPREAD` sửa địa hình, phải ở pha 5). |
| L-05 Gate B + C | Suy luận thống kê tinh vi. "Định danh được" là khái niệm mà model sẽ gật đầu rồi làm sai. |
| **L-06 `match()`** | ★ Hàm quan trọng nhất dự án. Sai nhẹ → số đẹp → mọi kết luận sai. |
| B-12 provenance | Chống farming. Model viết ra thứ pass test và vẫn farm được. |
| N-08 tick không chờ ai | Đồng thời + thời gian thực. |
| X-02 gác cổng, X-06 báo cáo | Diễn giải kết quả. Đây là chỗ bạn phải tự nhìn thấy sự thật. |

## 3. Quy trình giao việc

```
1. Đọc phiếu việc. Mục 8 có prompt sẵn — chỉ phiếu ✅ mới có.
2. mcp-agy: agy_start_task  với prompt đó + đường dẫn workspace
3. agy_job_status cho tới xong
4. agy_get_diff   ← ĐỌC. Không merge mù.
5. agy_run_tests  ← chạy đúng lệnh ở mục 7 của phiếu
6. Duyệt theo §4 rồi mới nhận
```

**Bước 4 và 6 không bỏ được.** Model rẻ tiết kiệm thời gian gõ, không tiết kiệm thời gian đọc. Nếu bạn không định đọc diff thì đừng giao — tự viết còn nhanh hơn là gỡ một thứ mình không hiểu.

## 4. Duyệt: sáu câu hỏi

Chạy qua đúng sáu câu này với mọi diff nhận về:

1. **Có gọi `random.xxx()` ở module-level không?** — phá tính tái lập của cả dự án. Lỗi hay gặp nhất.
2. **Có dùng `set` ở chỗ thứ tự ảnh hưởng kết quả không?** — thứ tự lặp của `set` không ổn định.
3. **Có chép hằng số vào code không?** — mọi hằng số ở `config.py` / `law_config.py` / `net_config.py`. Số 24 nằm trong `world.py` là một quả bom hẹn giờ.
4. **Có tự ý mở rộng phạm vi không?** — model thích "tiện tay làm luôn". Thêm file, thêm lớp trừu tượng, thêm phụ thuộc. Cắt hết.
5. **Test có thật sự kiểm cái cần kiểm không?** — `assert result is not None` là test giả. Đọc từng assert.
6. **Có `try/except` nuốt lỗi không?** — `except: pass` biến một lỗi thành một bí ẩn im lặng ba tuần sau.

Ba câu đầu bắt được ~80% lỗi thực tế của model rẻ trong dự án kiểu này.

## 5. Mẫu prompt

Mục 8 của mỗi phiếu ✅ có sẵn prompt. Nếu tự viết thì theo khung này:

```
BỐI CẢNH
Dự án: sim ALife 2D, Python 3.11, không phụ thuộc ngoài <rich, httpx>.
Đọc trước: docs/<tài liệu liên quan> §<mục>. Đừng đọc tài liệu khác.

VIỆC
<chép nguyên mục 2 và 4 của phiếu>

CHỮ KÝ BẮT BUỘC — không đổi tên, không đổi kiểu
<chép nguyên mục 5 của phiếu>

RÀNG BUỘC
- Mọi hằng số lấy từ config.py / law_config.py. KHÔNG viết số vào code.
- Không thêm phụ thuộc ngoài.
- Không tạo file mới ngoài danh sách ở trên.
- Không sửa file nào khác trong kho.
- Không dùng random ở module-level; nhận `rng: random.Random` qua tham số.
- Không `except: pass`.

NGHIỆM THU — code của bạn phải làm lệnh này pass
<chép nguyên mục 7 của phiếu>

TRẢ VỀ
Chỉ diff. Không giải thích. Không viết README.
```

Bốn dòng làm nên khác biệt: **"không tạo file mới"**, **"không sửa file khác"**, **"không thêm phụ thuộc"**, **"chỉ diff"**. Thiếu chúng thì bạn nhận về một cấu trúc thư mục mới và một `README.md` viết lại lịch sử dự án.

## 6. Việc mà model rẻ làm tốt hơn bạn

Đừng chỉ giao việc chán. Có ba loại nó thật sự làm tốt hơn:

| Việc | Vì sao |
|---|---|
| **Viết test từ mục "Nghiệm thu"** | Kiên nhẫn liệt kê ca biên hơn người. Giao cả những phiếu ❌ — bạn viết code, nó viết test. |
| **Chuyển đặc tả thành schema/GBNF/dataclass** | Cơ học thuần, và nó không quên trường nào. |
| **Dò lệch giữa tài liệu và code** | *"Đọc docs/05 §3.4 và net/api.py, liệt kê mọi chỗ lệch."* Rẻ, và bắt được thứ mắt người trượt qua. |

Loại thứ ba đáng chạy sau mỗi mốc. Nó là thứ giữ cho bộ tài liệu này không mục ra trong ba tháng.
