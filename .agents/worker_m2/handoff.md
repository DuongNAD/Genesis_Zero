# Báo Cáo Bàn Giao Milestone 2 — Trình Khởi Chạy 1-Chạm & Đa Backend LLM (Handoff Report)

## 1. Observation (Quan Sát Thực Tế)

1. **Hiện trạng ban đầu trước khi thực hiện M2**:
   - Thiếu các tập tin khởi chạy nhanh ở thư mục gốc: `run.sh`, `run.ps1`, `run.bat`, `scripts/launch.py`.
   - `genesis/llm_client.py:80-155`: Hàm `ask()` chỉ gọi endpoint `/completion` độc quyền của llama.cpp, không hỗ trợ Ollama (`/api/chat`) hay vLLM (`/v1/chat/completions`).
   - `requirements.txt`: Thiếu `numpy>=1.26`, trong khi `scripts/preflight.py` yêu cầu `numpy` trong danh sách `need`.
   - `scripts/preflight.py`: Không có cờ `--fix` để tự động tạo thư mục và cài đặt dependencies bị thiếu.
   - `tests/e2e/conftest.py`: Fixture `test_client` thiếu gọi hàm `reset()` từ `net.ratelimit`, gây nguy cơ dính giới hạn tốc độ khi chạy tuần tự hàng trăm test.
   - Tài liệu `README.md`, `docs/HUONG-DAN.md`, `docs/CHAY-TREN-WINDOWS.md` hướng dẫn gõ tay nhiều bước thay vì lệnh 1-chạm.

2. **Kết quả triển khai & kiểm tra thực tế**:
   - `run.sh`: Tạo mới với quyền thực thi `chmod +x`, tự động phát hiện Python >= 3.11, tạo `.venv`, cài đặt requirements và khởi chạy `scripts/launch.py "$@"`.
   - `run.ps1` & `run.bat`: Tạo mới cho môi trường Windows PowerShell và Command Prompt.
   - `scripts/launch.py`: Tạo mới bộ điều phối đa năng với giao diện Rich TUI, tự động quét các cổng 11434 (Ollama), 8080 (llama.cpp), 8000 (vLLM), 8099 (Mock), hỗ trợ fallback tức thì sang chế độ Phản Xạ Bản Năng (Reflex) offline nếu không có LLM.
   - `genesis/llm_client.py`: Mở rộng hàm `ask()` và bổ sung `detect_backend()` hỗ trợ đầy đủ:
     - Ollama: `/api/chat` (messages, `format: json_schema`, `options`)
     - vLLM: `/v1/chat/completions` (messages, `response_format: {"type": "json_object"}`)
     - llama.cpp: `/completion` (prompt, `id_slot`, `cache_prompt: true`, `json_schema`)
     - Mock: `fake_model_server`
     - Reflex: Offline fallback tức thì không gọi HTTP.
   - `scripts/preflight.py`: Bổ sung `auto_fix()` và cờ `--fix` tự động tạo `runs/` và cài đặt dependencies thiếu.
   - `requirements.txt`: Đã thêm `numpy>=1.26` đồng bộ 100% với preflight.
   - `tests/e2e/conftest.py`: Thêm `from net.ratelimit import reset; reset()` và dọn dẹp các import không dùng.
   - `README.md`, `docs/HUONG-DAN.md`, `docs/CHAY-TREN-WINDOWS.md`: Đã cập nhật hướng dẫn khởi chạy 1-chạm `./run.sh` và `.\run.ps1` lên đầu phần Quickstart (< 60 giây).

3. **Kết quả chạy kiểm thử & linter**:
   - `pytest tests/e2e -v`: **196 passed** in 0.90s (100% pass across all 4 tiers).
   - `pytest --ignore=tests/e2e`: **682 passed**, 1 skipped in 229.31s.
   - `python scripts/preflight.py --fix`: Thoát mã 0, tất cả thư viện bắt buộc đều OK.
   - `python scripts/launch.py --help`: Thoát mã 0, hiển thị đầy đủ options.
   - `ruff check scripts/launch.py scripts/preflight.py genesis/llm_client.py tests/e2e/conftest.py`: **All checks passed!** (0 lỗi).

---

## 2. Logic Chain (Chuỗi Lập Luận)

1. **Từ việc thiếu script 1-chạm & UX phức tạp**:
   - Người dùng mới trên Linux/macOS chỉ cần gõ `./run.sh`, trên Windows gõ `.\run.ps1` hoặc `run.bat`. Script tự xử lý môi trường ảo và dependencies, loại bỏ hoàn toàn các rào cản cài đặt thủ công.
2. **Từ việc mở rộng adapter trong `genesis/llm_client.py`**:
   - Người dùng sở hữu bất kỳ LLM backend cục bộ nào (Ollama, llama.cpp, vLLM) hoặc chạy demo mock đều được phục vụ tự động mà không cần can thiệp mã nguồn.
   - Nếu không có LLM backend nào đang chạy, hệ thống chuyển sang chế độ Phản Xạ Bản Năng (Reflex) với thông báo rõ ràng, giữ ván đấu luôn chạy mượt mà không bị treo do timeout.
3. **Từ việc sửa `requirements.txt` & `scripts/preflight.py`**:
   - `numpy` được khai báo rõ ràng trong `requirements.txt` giúp preflight không bị lỗi đỏ khi cài đặt môi trường mới. Cờ `--fix` cho phép người dùng hoặc script tự động sửa lỗi môi trường chỉ bằng một lệnh.
4. **Từ việc gọi `reset()` trong `conftest.py`**:
   - Mỗi test case được cấp một môi trường rate limit hoàn toàn sạch sẽ, tránh hiện tượng test chạy sau bị từ chối 429 do các test trước gọi dồn dập.

---

## 3. Caveats (Các Điểm Giới Hạn / Lưu Ý)

1. **Cổng 8000 được dùng chung giữa FastAPI server và vLLM mặc định**:
   - Khi chạy ở chế độ Web Server (`--web`), cổng 8000 được dùng cho server Genesis. Nếu vLLM cũng chạy trên cổng 8000, người dùng nên cấu hình vLLM trên cổng 8001 hoặc truyền `--llm-url` / `--port` tương ứng.
2. **GPU Inference Performance**:
   - Việc sinh token thực tế phụ thuộc vào cấu hình phần cứng của người dùng; ở chế độ Reflex (Offline), game đạt tốc độ tối đa ~200 tick/s không phụ thuộc GPU.

---

## 4. Conclusion (Kết Luận)

Milestone 2 đã hoàn thành 100% tất cả các yêu cầu kỹ thuật và trải nghiệm người dùng theo đúng hợp đồng `PROJECT.md` và `ORIGINAL_REQUEST.md`:
- Hệ thống khởi chạy 1-chạm đa nền tảng (`run.sh`, `run.ps1`, `run.bat`, `launch.py`) hoạt động trơn tru.
- Adapter đa backend LLM (Ollama, vLLM, llama.cpp, Mock, Reflex) tích hợp hoàn chỉnh và có cơ chế fallback thông minh.
- Toàn bộ 196 test E2E và 682 unit/integration test đều đạt 100% pass rate.
- Linter clean 0 lỗi.

---

## 5. Verification Method (Phương Pháp Kiểm Tra Độc Lập)

Người thẩm định hoặc auditor có thể kiểm chứng độc lập bằng các lệnh sau:

1. **Kiểm tra bộ test E2E 4 tầng**:
   ```bash
   pytest tests/e2e -v
   # Kết quả kỳ vọng: 196 passed in < 2s
   ```

2. **Kiểm tra bộ test toàn diện**:
   ```bash
   pytest --ignore=tests/e2e
   # Kết quả kỳ vọng: 682 passed, 1 skipped
   ```

3. **Kiểm tra script khởi chạy 1-chạm & chế độ offline**:
   ```bash
   ./run.sh --reflex --seed 42 --ticks 20 --no-render
   # Kết quả kỳ vọng: Thoát mã 0, in thông tin ván và bảng tổng kết
   ```

4. **Kiểm tra preflight auto-fix**:
   ```bash
   python scripts/preflight.py --fix
   # Kết quả kỳ vọng: Thoát mã 0, tất cả thư viện bắt buộc đều OK
   ```

5. **Kiểm tra linter**:
   ```bash
   ruff check scripts/launch.py scripts/preflight.py genesis/llm_client.py tests/e2e/conftest.py
   # Kết quả kỳ vọng: All checks passed!
   ```
