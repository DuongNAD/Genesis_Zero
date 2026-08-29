.PHONY: test run serve expose preflight preflight-full demo model-check hostile lint clean site

test:
	pytest

run:
	python -m genesis.run --seed 42 --ticks 400

# Ván mở: server + trang xem live. Client chạy ở máy người chơi, xem client/README.md
serve:
	uvicorn net.server:app --host 127.0.0.1 --port 8000

# Toàn bộ đường ống mà KHÔNG cần model — model giả biết trước đáp án của seed 9,
# chỉ để chứng minh bộ chấm bắt được lời giải đúng. Đừng báo cáo số từ chế độ này.
demo:
	@python scripts/fake_model_server.py --port 8099 --cheat-seed 9 & sleep 2; \
	python -m genesis.run --seed 9 --ticks 400 --llm all --llm-url http://127.0.0.1:8099 \
	  --no-render --out runs/demo.jsonl --truth runs/demo.truth.json; \
	python -m genesis.score runs/demo.jsonl runs/demo.truth.json | head -5; \
	pkill -f fake_model_server

# Kiểm một model thật: json_schema có RÀNG BUỘC không, prefix cache có trúng không.
model-check:
	python scripts/bench_client.py --url http://127.0.0.1:8080 --n 50 --slots 4

# Một lệnh trả lời "máy này chạy được một ván thật chưa?". Mỗi mục hỏng in kèm
# lệnh sửa — bản kiểm chỉ nói "hỏng" bắt người đọc tra lại chính thứ nó vừa biết.
preflight:
	python scripts/preflight.py

preflight-full:
	python scripts/preflight.py --full

# Phơi server ra internet qua ngrok (N-11 giai đoạn 1). Cần chạy `make serve` ở
# một cửa sổ khác trước. Cổng 8000, KHÔNG phải 80 — trang ngrok gợi ý 80 và đó
# là chỗ sai đầu tiên ai cũng mắc.
NGROK_URL ?= https://<tên-miền-của-bạn>.ngrok-free.dev
expose:
	@command -v ngrok >/dev/null || { echo "cần: brew install ngrok"; exit 2; }
	@ngrok config check >/dev/null 2>&1 || { 	  echo "chưa có authtoken. Tự chạy: ngrok config add-authtoken <token>"; exit 2; }
	ngrok http 8000 --url $(NGROK_URL)

# Chạy TRƯỚC khi phơi server ra internet, không phải sau (N-11 bất biến 3).
hostile:
	python scripts/hostile_client.py --server http://127.0.0.1:8000

lint:
	@ruff check genesis tests 2>/dev/null || echo "(ruff chưa cài — bỏ qua)"

site:
	python tools/build_site.py

clean:
	rm -rf runs/*.jsonl .pytest_cache **/__pycache__ __pycache__
