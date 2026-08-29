# Genesis Zero — client

Máy của bạn ở đâu cũng được, chỉ cần có mạng. Không cần mở cổng, không cần cấu
hình NAT: client **kéo** việc về, server không bao giờ gọi ngược lại.

## Cài

```bash
pip install -e client/
```

Bạn cần một model chạy sẵn ở máy mình. Bất cứ thứ gì nói được giao thức
`/completion` của `llama.cpp` đều dùng được:

```bash
llama-server -m models/your-model.gguf --port 8080 --parallel 4 --ctx-size 8192
```

## Chạy

```bash
cp client/config.example.toml my.toml   # sửa `server`, `name`, `persona`
genesis-client --config my.toml
```

Thế thôi. Cờ dòng lệnh đè file config nếu bạn muốn thử nhanh:

```bash
genesis-client --config my.toml --brain-tier 5 --name "Kiến Lửa"
```

## Nhiều client cùng lúc

Một máy đóng vai nhiều người chơi — để thử tại chỗ trước khi mời người thật, hoặc
để lấp sảnh cho một ván cần đủ loài:

```bash
python client/run_fleet.py --server http://localhost:8000 \
    --model-url http://localhost:8080 --n 3
```

Mỗi client là một **loài riêng**: tên riêng, tập tính riêng, `brain_tier` riêng.
Thế giới thú vị khi trong đó có nhiều thứ khác nhau, không phải khi có nhiều bản
sao của một thứ.

> **Một máy nhiều client KHÔNG thay được nhiều máy.** Mọi client ở đây dùng chung
> một `llama-server`, mà phần decode gần như tuần tự — `--n 8` không cho tám lần
> thông lượng, nó chia đôi tám lần. Thứ mở rộng được là **số máy**.

## Viết client bằng ngôn ngữ khác

`client/genesis_client.js` là bản Node, **124 dòng, không phụ thuộc gì** (dùng
`fetch` có sẵn từ Node 18):

```bash
node client/genesis_client.js --server http://localhost:8000 \
    --model-url http://localhost:8080 --name "Quạ Khoang"
```

Nó ở đây để câu "viết client cho ngôn ngữ khác là chuyện của một buổi chiều"
**được kiểm chứng** chứ không chỉ được nói — `tests/test_fleet.py` quét nó và
đòi rằng trong phần code không có lấy một tên goal hay một tên hệ quả nào.

## Nó làm gì

1. `POST /v1/join` — xin một loài. Bạn chọn `brain_tier`; server cấp
   `12 − brain` điểm còn lại cho năm chỉ số kia. **Không ai xác minh model của
   bạn.** Khai 999B cũng được, và cũng chẳng lợi gì: tổng chỉ số vẫn là 12, nên
   `brain` cao nghĩa là giáp mỏng, chạy chậm, mắt kém.
2. `GET /v1/match/brief` một lần mỗi ván — nhận `system_prompt` cho từng cá thể.
   Client **không sửa** chuỗi này, kể cả một byte: nó được prefill một lần vào
   một `id_slot` cố định, và đó là khác biệt giữa 3 giây và 12 giây mỗi lượt.
3. `GET /v1/work` — long-poll. Server trả `user_block` và `json_schema` đã dựng
   sẵn. Client ghép `system_prompt + user_block`, gọi model, gửi lại.
4. `POST /v1/heartbeat` mỗi 10 giây. Mất mạng thì loài của bạn **không biến
   mất** — nó rơi về bản năng và chờ bạn quay lại.

## Vì sao client không biết luật chơi

Nó không biết LawDSL, không biết có những mục tiêu nào, không biết bản đồ. Ba hệ
quả, và cả ba đều là lý do thiết kế như thế:

- Client này **không bao giờ phải cập nhật.** Luật chơi đổi, cách chấm đổi, từ
  vựng đổi — bản cũ vẫn chạy.
- **Không có bề mặt gian lận từ cấu trúc.** Nó không thể xin thứ nó không được
  cấp, vì nó không biết thứ đó tồn tại.
- Viết lại bằng Rust, Go hay Node là chuyện một buổi chiều: tất cả những gì nó
  làm là ghép hai chuỗi và gọi HTTP.

Vì thế gói này chỉ phụ thuộc `httpx` và **không** import gì từ `genesis/`.
`tests/test_client.py` kiểm điều đó bằng AST — nếu bạn thấy mình muốn import
`genesis.lawdsl` vào đây, thiết kế đã sai chỗ khác.
