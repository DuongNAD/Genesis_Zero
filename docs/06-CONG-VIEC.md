# 06 · Bảng điều phối công việc

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · **06 Công việc** · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md)

> Trạng thái từng việc ở [01-STATUS](01-STATUS.md). Tài liệu này nói **thứ tự** và **vì sao thứ tự đó**.

## 1. Làm gì trong tuần này

| Ngày | Việc | Xong thì có gì |
|---|---|---|
| Tối 1 | [S-01](tasks/S-01-moi-truong.md), [S-03](tasks/S-03-kiem-thu.md), [S-04](tasks/S-04-log.md) | `pytest` chạy, `make run` chạy, ghi được JSONL |
| Tối 1 (song song) | [S-02](tasks/S-02-llama-server.md) | biết ngay CUDA có build được không |
| Tối 2 | [W-01](tasks/W-01-rng-config.md) → [W-03](tasks/W-03-thuc-an.md) | lưới có cỏ mọc |
| Tối 3 | [W-04](tasks/W-04-creature.md) → [W-06](tasks/W-06-render-log.md) | ✦ **M0** — nhìn được, chạy 300 tick |

**S-02 làm ngay tối đầu tiên dù chưa cần tới model.** v4 §Bước 0.2 nói đúng: nếu build CUDA hỏng thì bạn cần biết hôm nay, không phải sau ba tuần. Nó chạy nền trong lúc bạn làm S-01.

**Bài kiểm tra sau M0, chép nguyên từ v4:** ngồi xem nó chạy. Nếu đã chán thì LLM không cứu được, và bạn cần sửa thế giới trước khi đi tiếp. Đây là bài kiểm tra rẻ nhất trong cả dự án.

## 2. Đồ thị phụ thuộc

```
S-01 ─┬─ S-03
      ├─ S-04 ────────────────┐
      └─ W-01 ─ W-02 ─┬─ W-03 │
                      └─ W-04 ─ W-05 ─ W-06 ✦M0
                           │
                      W-07 ─┬─ W-08 ─ W-09 ─┬─ W-11 ─ W-12 ✦M1 ─ W-13
                            └─ W-10 ────────┘        │           │
S-02 ──────────────────────────────────────┐         │      L-01 ┼─ L-02
                                           │         │           ├─ L-03 ─┐
    N-01,N-02 ◄── khâu ngay khi tới W-09 ──┘         │           ├─ L-04 ─┼─ L-05
    N-03      ◄── khâu ngay khi tới S-04             │           │        └─ L-06 ★
                                                     │           └─ L-07
                            B-01 ─ B-02 ─┬─ B-05 ─ B-06 ✦M2
                            B-03 ────────┤            │
                            B-04 ────────┘       B-07 ─ B-08 ─┬─ B-09
                                                              └─ B-10 ✦ĐO ĐƯỢC
                                                 B-11 ─ B-12
                                                 B-13
    N-04 ─ N-05 ─ N-06 ─ N-07 ─ N-08 ─┬─ N-09 ─ N-11
                              N-10 ───┴─ N-12          ✦THẾ GIỚI MỞ
```

★ = việc mà nếu làm sai thì mọi thứ phía sau đo nhầm. Không giao cho ai, không vội.

## 3. Bốn mốc, và bài kiểm tra của từng mốc

| Mốc | Xong khi | Nếu không đạt |
|---|---|---|
| ✦ **M0** W-06 | 300 tick không crash · hai lần cùng seed cho JSONL `diff` sạch · **bạn thấy vui khi ngồi xem** | Sửa thế giới. Đừng đi tiếp. |
| ✦ **M1** W-12 | 400 tick × 5 seed: không con nào chết > 8 lần · không con nào **chưa từng** chết · mỗi con dịch ≥ 2 điểm trait | Tune `config.py`. Bạn sẽ sửa vài chục lần. Đây là mốc quan trọng nhất. |
| ✦ **M2** B-06 | JSON hợp lệ ≥ 99% · `LLM_SEMANTIC_FAIL` < 5% · con dùng LLM **không tệ hơn** con reflex cùng loài · `--replay` dựng lại đúng ván cũ | Nếu LLM tệ hơn reflex, báo cáo đúng như vậy — v4 §11.5 |
| ✦ **ĐO ĐƯỢC** B-10 | nhánh `REFLEX` ra `match ≈ 0` · ít nhất một cá thể đạt `match ≥ 0.8` trên luật D1 trong 5 ván | Chẩn đoán theo thứ tự: sổ tay nghèo (B-07) → luật hiếm kích hoạt (L-05) → từ vựng quá rộng (B-02). **Đừng chẩn đoán bằng cách đổi model.** |

> **Mốc "ĐO ĐƯỢC" là mốc chứng minh bản v5 có sống được không.** Nếu qua 5 ván × 15 con mà không ai tìm ra nổi một luật D1 nào thì thiết kế có vấn đề, và bạn cần biết điều đó ở tuần thứ sáu chứ không phải tháng thứ sáu.

## 4. Ba nhánh chạy song song được

Nếu bạn có nhiều thời gian hoặc nhiều tay giúp:

| Nhánh | Việc | Phụ thuộc vào nhánh khác? |
|---|---|---|
| **Chính** | S → W → L → B | — |
| **Hạ tầng** | S-02, S-03, S-04, X-05, X-07 | không, làm lúc nào cũng được |
| **Mạng** | N-01…N-03 (sớm), N-04…N-12 (sau B-06) | ba việc N đầu **phải** làm sớm |

Nhánh hạ tầng là nhánh **giao được hết cho model rẻ** ([07](07-GIAO-VIEC-CHO-MODEL.md)) trong lúc bạn tự viết nhánh chính.

## 5. Quy tắc "xong"

Một việc `✅` khi **và chỉ khi**:

1. Lệnh ở mục 7 của phiếu việc đã chạy và pass.
2. Không có `TODO` hay `pass  # sau này` trong phần code của việc đó.
3. [01-STATUS](01-STATUS.md) đã cập nhật.

Không có mục "gần xong". Một việc gần xong là một việc chưa xong, và cột trạng thái chỉ có giá trị khi nó nói thật.

## 6. Thêm việc mới

1. Chọn mã theo track ([00-INDEX](00-INDEX.md#quy-ước)).
2. Chép `tasks/_MAU.md`, điền đủ 8 mục. **Mục 7 (nghiệm thu) phải là lệnh chạy được** — nếu bạn không viết nổi lệnh nghiệm thu thì việc đó chưa được định nghĩa đủ rõ để bắt đầu.
3. Thêm một dòng vào [01-STATUS](01-STATUS.md).
4. Nếu nó chặn việc khác, sửa cột phụ thuộc của việc kia.

## 7. Nguyên tắc tự viết code — v4 §10, vẫn giữ

> **W-01 → W-12 và L-02, L-05, L-06: tự viết. Không giao cho AI.**

Đó là phần tư duy của dự án — vòng tick, resolve đồng thời, bất biến trait, và ở v5 thêm: hàm `match()` và hai gate lọc luật. Dùng AI để **giải thích khái niệm** và **review sau khi bạn viết xong**, nhưng từng dòng phải ra từ tay bạn.

Từ B-03 trở đi (HTTP client, asyncio, pygame, server FastAPI) — dùng AI thoải mái. Đó là hạ tầng.

Danh sách đầy đủ ai làm gì: [07-GIAO-VIEC-CHO-MODEL](07-GIAO-VIEC-CHO-MODEL.md).

**Bài test sau mỗi mốc, chép nguyên từ v4 §10:** đóng máy, nói to thành lời toàn bộ luồng dữ liệu từ lúc creature "nhìn thấy" đến lúc lưới cập nhật. Kẹt ở đâu thì chỗ đó chưa xong.
