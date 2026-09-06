# Báo Cáo Bàn Giao Khảo Sát — R2: Trình Khởi Chạy & Cài Đặt 1-Chạm (Handoff Report)

## 1. Observation (Quan Sát Thực Tế)

1. **Mã nguồn và cấu hình hiện có**:
   - `Makefile:1-74`: Chứa các mục tiêu `test`, `run`, `serve`, `demo`, `preflight`, `hostile`, `lock`, `lint`, `site`, `clean`. Tất cả phụ thuộc vào môi trường shell POSIX và lệnh Linux (`pkill`, `rm -rf`, `sleep`, `grep`).
   - `pyproject.toml:15-27`: Khai báo `dependencies = ["rich>=13", "httpx>=0.27", "fastapi>=0.115", "uvicorn>=0.27", "pydantic>=2"]` và các extras (`dev`, `analysis`, `train`, `viz`). Phần `[tool.pytest.ini_options]` (dòng 37-48) **không có** `pythonpath = ["."]`.
   - `requirements.txt:10-14`: Chứa `rich>=13`, `httpx>=0.27`, `fastapi>=0.115`, `uvicorn>=0.27`, `pydantic>=2`. Không có `numpy`.
   - `scripts/preflight.py:48-65`: `check_deps()` liệt kê `need = ["httpx", "fastapi", "uvicorn", "numpy", "rich", "pydantic"]`. `numpy` được coi là bắt buộc dù không có trong `requirements.txt`.
   - `scripts/serve_L2.ps1:1-43` & `scripts/serve_L2.sh:1-35`: Script khởi động `llama-server` cho macOS/Linux và Windows.
   - `scripts/fake_model_server.py:1-131`: Giả lập `llama-server` trên cổng 8099 với cheat-seed.
   - `genesis/llm_client.py:80-155`: Hàm `ask()` gọi thẳng `{base_url}/completion` với các trường `prompt`, `id_slot`, `cache_prompt`, `json_schema`, `n_predict`, `temperature`.
   - `genesis/reflex.py:1-305`: Tầng phản xạ thuần túy, chạy độc lập không phụ thuộc LLM.
   - Không tìm thấy các tập tin: `run.sh`, `setup.sh`, `run.ps1`, `run.bat`, `setup.bat`, `launch.py` ở thư mục gốc.

2. **Kết quả chạy thử nghiệm**:
   - Chạy `pytest`: Ném lỗi `ModuleNotFoundError: No module named 'net'` / `'scripts'` / `'net_config'` (19 lỗi collection).
   - Chạy `python -m pytest`: Hoàn thành `646 passed, 1 skipped in 130.58s`.
   - Chạy `python scripts/preflight.py`: Báo `Python 3.11.8 (OK)`, `Thư viện bắt buộc 6 gói (OK)` (do môi trường hiện tại đã có `numpy`), `Model server (OK)` nếu llama-server đang chạy trên 8080, cảnh báo cổng 8000 chưa mở.
   - Chạy `make demo`: Chạy fake model server + ván seed 9 + chấm điểm, thoát với mã 0.
   - Chạy `python -m genesis.run --seed 42 --ticks 50 --no-render`: Hoàn thành trong < 1s ở chế độ reflex.

---

## 2. Logic Chain (Chuỗi Lập Luận)

1. **Từ Quan sát 1 (Thiếu script khởi chạy cấp cao)**:
   - Người dùng mới khi clone repository về không có script 1-chạm nào để tạo môi trường ảo `.venv`, cài đặt dependencies, chạy preflight và khởi động game.
   - Người dùng phải tự đọc tài liệu và gõ thủ công 4-6 lệnh dòng lệnh. Điều này không đáp ứng tiêu chí "Zero-friction setup & launcher < 3 phút".

2. **Từ Quan sát 1 & 2 (Lệch pha dependencies & Pytest discovery)**:
   - `scripts/preflight.py` đòi hỏi `numpy` trong nhóm `need`, nhưng `requirements.txt` không có `numpy`. Nếu người dùng cài đúng `pip install -r requirements.txt`, preflight sẽ báo lỗi đỏ.
   - Thiếu `pythonpath = ["."]` trong `pyproject.toml` khiến lệnh `pytest` trần không nhận diện được các package `net`, `scripts`, `net_config` trừ khi cài đặt ở chế độ editable `pip install -e .` hoặc chạy qua `python -m pytest`.

3. **Từ Quan sát 1 (Ràng buộc backend LLM vào llama.cpp)**:
   - `genesis/llm_client.py` chỉ xây dựng payload cho endpoint `/completion` độc quyền của llama.cpp (`id_slot`, `cache_prompt: true`, `json_schema`).
   - Các công cụ phổ biến của người dùng hiện nay như **Ollama** (`/api/chat` với `format: json_schema`) và **vLLM** (`/v1/chat/completions` với `guided_json`) không thể kết nối trực tiếp được nếu không có adapter chuyển đổi định dạng.

4. **Từ Quan sát 1 & 2 (Chế độ Offline & Fallback)**:
   - Genesis Zero có sẵn bộ điều khiển phản xạ `reflex.py` và mock server `fake_model_server.py` hoạt động hoàn hảo và tức thì.
   - Tuy nhiên, hiện tại nếu người dùng chạy `--llm all` mà không có LLM server đang mở, hệ thống sẽ cố gắng kết nối, liên tục nhận lỗi mạng HTTP, ghi log cảnh báo và ngắt mạch sau 3 lần thất bại, thay vì tự động thông báo và chuyển sang chế độ Offline một cách êm ái ngay từ đầu.

5. **Từ Quan sát 1 (Hỗ trợ nền tảng Windows)**:
   - Người dùng Windows không thể dùng `Makefile` (`make run`, `make demo`, `make serve`).
   - Mặc dù mã nguồn Python thuần túy hoàn toàn tương thích Windows, việc thiếu `run.ps1` và `run.bat` khiến trải nghiệm trên Windows bị gián đoạn.

---

## 3. Caveats (Các Điểm Giới Hạn / Chưa Khảo Sát Sâu)

1. **Chưa đo đạc benchmark throughput trên GPU NVIDIA CUDA thật**: Quá trình kiểm tra diễn ra trên môi trường máy Mac (Apple Silicon). Các thông số về VRAM và tốc độ xử lý GPU trên Windows/Linux CUDA được tham chiếu từ tài liệu đo lường có sẵn trong `docs/CHAY-TREN-WINDOWS.md`.
2. **Chưa can thiệp sửa mã nguồn**: Theo nguyên tắc của vai trò Explorer (Read-only Investigation), không có bất kỳ file mã nguồn chính nào của dự án bị chỉnh sửa trong lượt này. Tất cả đề xuất đã được chuyển thành thiết kế chi tiết trong `analysis.md`.

---

## 4. Conclusion (Kết Luận & Giải Pháp)

Để đáp ứng 100% yêu cầu R2 (1-Command Setup & Launcher) với tiêu chuẩn chất lượng cao nhất:

1. **Xây dựng bộ ba Script Khởi Chạy 1-Chạm**:
   - `run.sh` (macOS / Linux)
   - `run.ps1` (Windows PowerShell)
   - `run.bat` (Windows Command Prompt)
   - `launch.py` (Bộ điều phối Python cross-platform với giao diện Rich TUI).
2. **Tự động hóa hoàn toàn quy trình Onboarding (< 3 phút)**:
   - Tự động phát hiện Python >= 3.11, khởi tạo `.venv` nếu chưa có.
   - Tự động cài đặt dependencies (`pip install -e .` hoặc `requirements.txt`).
   - Tự động chạy Preflight chẩn đoán và tự sửa lỗi nhẹ (`preflight.py --fix`).
3. **Mở rộng hỗ trợ Đa Backend LLM**:
   - Xây dựng LLM Adapter đa backend trong `genesis/llm_client.py`: hỗ trợ **Ollama** (`/api/chat`), **vLLM** (`/v1/chat/completions`), **llama.cpp** (`/completion`), **Mock** (`fake_model_server`), và **Reflex** (Offline).
   - Tự động quét các cổng 8080, 11434, 8000, 8099 khi khởi chạy. Nếu không có LLM, tự động fallback sang chế độ Offline Reflex kèm thông báo rõ ràng.
4. **Chuẩn hóa cấu hình Dependencies & Pytest**:
   - Thêm `pythonpath = ["."]` vào `pyproject.toml`.
   - Đồng bộ danh sách `need` trong `preflight.py` với `requirements.txt`.
5. **Cập nhật tài liệu Quickstart**:
   - Đưa lệnh `./run.sh` và `.\run.ps1` lên đầu `README.md`, `docs/HUONG-DAN.md`, và `docs/CHAY-TREN-WINDOWS.md`.

---

## 5. Verification Method (Phương Pháp Kiểm Tra & Nghiệm Thu Độc Lập)

Người nhận bàn giao (Builder Agent / Reviewer) có thể kiểm chứng toàn bộ các kết luận trên bằng các lệnh sau:

1. **Kiểm tra sự vắng mặt của các launcher script**:
   ```bash
   ls run.sh run.ps1 run.bat launch.py setup.sh 2>&1
   # Kỳ vọng: No such file or directory
   ```
2. **Kiểm tra lỗi collection của pytest khi chạy trần**:
   ```bash
   pytest
   # Kỳ vọng: 19 errors during collection (ModuleNotFoundError: No module named 'net')
   ```
3. **Kiểm tra sự thành công của toàn bộ test suite khi chạy qua module**:
   ```bash
   python -m pytest
   # Kỳ vọng: 646 passed, 1 skipped in ~130s
   ```
4. **Kiểm tra xung đột `numpy` giữa `preflight.py` và `requirements.txt`**:
   ```bash
   grep -n "need = " scripts/preflight.py
   grep -n "numpy" requirements.txt
   # Kỳ vọng: scripts/preflight.py có numpy, requirements.txt không có numpy
   ```
5. **Kiểm tra API format của LLM Client**:
   ```bash
   grep -n "/completion" genesis/llm_client.py
   # Kỳ vọng: Endpoint chỉ hỗ trợ /completion của llama.cpp, không hỗ trợ /api/chat hay /v1/chat/completions
   ```
6. **Kiểm tra tính năng chạy mô phỏng tức thì (Reflex & Demo)**:
   ```bash
   python -m genesis.run --seed 42 --ticks 50 --no-render
   make demo
   # Kỳ vọng: Chạy thành công và in ra điểm số Sổ Luật
   ```
