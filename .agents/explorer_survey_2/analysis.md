# Báo Cáo Khảo Sát Chi Tiết — R2: Bộ Cài Đặt và Trình Khởi Chạy 1-Chạm (One-Command Setup & Launcher)

**Người thực hiện**: Explorer 2 (Survey Phase)  
**Ngày hoàn thành**: 2026-09-02  
**Mục tiêu**: Khảo sát toàn diện hiện trạng, phát hiện các điểm nghẽn, và thiết kế giải pháp cho bộ cài đặt và trình khởi chạy 1-chạm tự động hóa hoàn toàn (Zero-Friction Setup & Launcher), chạy đa nền tảng (macOS, Linux, Windows), tự động cấu hình venv, dependencies, preflight auto-fix, phát hiện/tích hợp đa backend LLM (Ollama, llama.cpp, vLLM, mock) và tự động fallback về reflex controller với thời gian khởi động dưới 3 phút.

---

## 1. Tóm Tắt Hiện Trạng & Điểm Cốt Lõi (Executive Summary)

Genesis Zero hiện tại là một sandbox mô phỏng sinh vật 2D/3D kết hợp suy luận LLM với test suite rất tốt (**646 tests passed**), kiến trúc 6 pha tất định và cơ chế chấm điểm Sổ Luật độc đáo. Tuy nhiên, về mặt **trải nghiệm người dùng và quy trình khởi chạy (DevEx & Onboarding UX)**, dự án đang tồn tại các rào cản đáng kể:

1. **Thiếu hoàn toàn script khởi chạy 1-chạm (1-command launcher)**: Người dùng mới phải tự gõ thủ công 4–6 lệnh riêng biệt (tạo venv, kích hoạt venv, pip install, preflight, chạy llama-server nếu có, chạy genesis.run hoặc uvicorn).
2. **Bất đối xứng giữa các hệ điều hành**: Môi trường POSIX có `Makefile` (`make run`, `make serve`, `make demo`), nhưng Windows không có Makefile tương đương ngoài tài liệu hướng dẫn thủ công trong `docs/CHAY-TREN-WINDOWS.md` và script `scripts/serve_L2.ps1`. Chưa có `run.sh`, `run.ps1`, `run.bat` ở thư mục gốc.
3. **Lệch pha định nghĩa dependencies**: `scripts/preflight.py` (dòng 49) bắt buộc kiểm tra `numpy` trong nhóm thư viện bắt buộc (`need`), nhưng `pyproject.toml` và `requirements.txt` lại xếp `numpy` vào nhóm mở rộng `analysis`. Người dùng cài theo `requirements.txt` sẽ bị preflight báo lỗi (`HỎNG`).
4. **Lỗi phát hiện module khi chạy `pytest` trực tiếp**: `pyproject.toml` thiếu `pythonpath = ["."]` trong `[tool.pytest.ini_options]`, khiến lệnh `pytest` trần ném `ModuleNotFoundError: No module named 'net'/'scripts'/'net_config'`.
5. **Backend LLM bị gắn cứng với `llama-server`**: `genesis/llm_client.py` và `client/genesis_client.py` chỉ hỗ trợ định dạng payload riêng của `llama.cpp` (`/completion`, `id_slot`, `json_schema`, `n_predict`). Chưa có adapter kết nối với **Ollama** (`/api/chat` hoặc `/api/generate`) hay **vLLM** (`/v1/chat/completions`).
6. **Preflight thiếu cơ chế tự sửa lỗi (Auto-Remediation)**: `scripts/preflight.py` chỉ in ra chuỗi gợi ý lệnh sửa chứ không có cờ `--fix` để tự động khắc phục.
7. **Thiếu cơ chế tự động nhận diện chế độ Offline vs LLM**: Nếu người dùng chạy mà không có LLM server bật sẵn, hệ thống sẽ gặp lỗi kết nối HTTP và kích hoạt circuit breaker thay vì tự động thông báo rõ ràng và chuyển mượt mà sang chế độ phản xạ (reflex) hoặc mock server ngay từ lúc bắt đầu.

---

## 2. Khảo Sát Chi Tiết Từng Thành Phần

### 2.1. Cấu hình Dependencies & Môi trường Python

| Tập tin | Nội dung hiện tại | Nhận xét & Vấn đề |
|---|---|---|
| `pyproject.toml` | Core: `rich>=13`, `httpx>=0.27`, `fastapi>=0.115`, `uvicorn>=0.27`, `pydantic>=2`<br>Extras: `dev`, `analysis` (`numpy`, `matplotlib`), `train` (`torch`, `peft`, `transformers`), `viz` (`pygame`) | Khai báo chuẩn PEP 621. Tuy nhiên, phần `[tool.pytest.ini_options]` thiếu `pythonpath = ["."]`. |
| `requirements.txt` | 5 gói core: `rich`, `httpx`, `fastapi`, `uvicorn`, `pydantic` | Khớp với core `pyproject.toml`. Không chứa `numpy`. |
| `requirements.lock` | 20 gói ghim chính xác phiên bản ngày 2026-08-30 | Tốt cho việc tái hiện kết quả khoa học. |
| `.env.example` | `GEMINI_API_KEYS=`, `MESHY_API_KEY=` | Dùng cho `genesis/genai.py` (viết lại prompt 3D cho Meshy). |
| `client/pyproject.toml` | Package riêng cho client: `httpx>=0.27` | Độc lập, nhẹ, tốt cho client từ xa. |

#### Quan sát & Kiểm chứng:
- **Lỗi 1 (Dependency Conflict)**:
  - `scripts/preflight.py:49`: `need = ["httpx", "fastapi", "uvicorn", "numpy", "rich", "pydantic"]`
  - `requirements.txt:10-14`: chỉ có `rich`, `httpx`, `fastapi`, `uvicorn`, `pydantic`.
  - Hậu quả: Nếu người dùng làm đúng theo README `pip install -r requirements.txt` rồi chạy `make preflight`, preflight sẽ báo:  
    `✗ Thư viện bắt buộc  numpy`  
    `→ pip install numpy`
- **Lỗi 2 (Pytest Import Failure)**:
  - Chạy `pytest` trực tiếp: Báo 19 lỗi `ModuleNotFoundError: No module named 'net'` / `'scripts'` / `'net_config'`.
  - Chạy `python -m pytest`: Pass 646 tests vì Python tự thêm thư mục hiện tại vào `sys.path`.
  - Khắc phục: Cần thêm `pythonpath = ["."]` vào `[tool.pytest.ini_options]` trong `pyproject.toml`.

---

### 2.2. Bộ Kiểm Tra Tiền Khởi Chạy (`scripts/preflight.py`)

`scripts/preflight.py` có cấu trúc rất sáng sủa, kiểm tra theo nguyên tắc: *"Mỗi mục hỏng in kèm LỆNH SỬA"*.
Các bài kiểm tra hiện có:
1. `check_python()`: Yêu cầu Python >= 3.11.
2. `check_deps()`: Kiểm tra thư viện bắt buộc và tuỳ chọn qua `importlib.util.find_spec`.
3. `check_import()`: Thử chạy `from genesis.tick import build_match; build_match(1)`.
4. `check_web()`: Kiểm tra sự tồn tại của `web/watch.html`, `web/watch3d.html`, `web/vendor/three.min.js`, `web/vendor/GLTFLoader.js`.
5. `check_disk()`: Kiểm tra dung lượng đĩa trống (< 2GB báo HỎNG, < 10GB báo CẢNH BÁO).
6. `check_llm(url)`: Gửi yêu cầu kiểm tra `json_schema` với enum bịa `XYZZY` tới `{url}/completion`.
7. `check_server()`: Kiểm tra cổng 8000 (`127.0.0.1:8000`).
8. `check_tunnel()`: Kiểm tra cài đặt và authtoken của `ngrok`.
9. `check_tests(full)`: Chạy pytest nếu có cờ `--full`.

#### Hạn chế & Cơ hội cải tiến:
1. **Thiếu chức năng Auto-Remediation (`--fix`)**: Khi thiếu thư mục (`runs/`), thiếu package bắt buộc hoặc cấu hình, preflight chỉ in text gợi ý mà không tự động cài đặt/khởi tạo cho người dùng.
2. **Hardcoded endpoint `llama.cpp`**: `check_llm` chỉ kiểm tra `/completion` với format của `llama-server`. Nếu người dùng cấu hình URL của Ollama (`http://localhost:11434`) hoặc vLLM (`http://localhost:8000`), hàm này sẽ kết luận model không trả lời hoặc grammar không ép.
3. **Thiếu khả năng tự động rà quét các cổng LLM phổ biến**: Không tự động thăm dò `8080` (llama-server), `11434` (Ollama), `8000/8001` (vLLM) để báo cho người dùng biết trên máy đang có backend nào sẵn sàng.
4. **Chưa có định dạng xuất JSON / Machine-readable**: Cần hỗ trợ cờ `--json` để launcher script hoặc các tool tự động khác có thể đọc kết quả chẩn đoán theo dạng dữ liệu có cấu trúc.

---

### 2.3. Tích Hợp Các Backend LLM & Chế Độ Offline

Hiện trạng hỗ trợ backend trong toàn bộ mã nguồn:

| Backend | Trạng thái hỗ trợ | Chi tiết triển khai | Hạn chế |
|---|---|---|---|
| **Reflex Controller** (Bản năng) | **Sẵn sàng 100%** | `genesis/reflex.py`<br>`--controller reflex` hoặc không truyền `--llm` | Hoạt động tức thì, tất định, 0 latency, không cần mạng/GPU. |
| **Fake Model Server** (Mock) | **Sẵn sàng 100%** | `scripts/fake_model_server.py`<br>Cổng mặc định 8099, hỗ trợ `--cheat-seed` | Giả lập endpoint `/completion`, sinh JSON hợp lệ theo prompt tags, phục vụ demo & test pipeline. |
| **llama.cpp** (`llama-server`) | **Sẵn sàng 100%** | `genesis/llm_client.py`<br>`scripts/serve_L2.sh`, `scripts/serve_L2.ps1` | Gọi endpoint `/completion`, truyền `id_slot`, `cache_prompt: true`, `json_schema`, `n_predict`. Tối ưu prefix cache rất cao. |
| **Ollama** | **CHƯA HỖ TRỢ** | Không có adapter trong code | Ollama dùng `/api/chat` hoặc `/api/generate` (với `format: json_schema`) hoặc `/v1/chat/completions`. Gửi payload llama.cpp sang Ollama sẽ lỗi 404/400. |
| **vLLM** | **CHƯA HỖ TRỢ** | Không có adapter trong code | vLLM dùng `/v1/chat/completions` với `guided_json` hoặc `response_format`. Không nhận `id_slot`. |
| **OpenAI-Compatible** | **CHƯA HỖ TRỢ** | Không có adapter chung | Chưa có lớp bọc chuẩn hoá cho các endpoint `/v1/chat/completions`. |
| **Google GenAI / Gemini** | **Chỉ dùng cho Meshy** | `genesis/genai.py` | Hiện chỉ dùng để viết lại mô tả hình thái 3D cho API Meshy (`mesh_export.py`), không dùng làm mind cho sinh vật trong game. |

#### Điểm cần nâng cấp cho R2:
- Cần xây dựng một **Unified LLM Backend Adapter** trong `genesis/llm_client.py` (hoặc `genesis/backends/`):
  1. `LlamaCppBackend`: Endpoint `/completion` (tối ưu slot & prefix cache).
  2. `OllamaBackend`: Endpoint `/api/chat` hoặc `/v1/chat/completions` (tự chuyển đổi JSON schema sang `format`).
  3. `VllmBackend` / `OpenAiBackend`: Endpoint `/v1/chat/completions` với `response_format: {"type": "json_object"}` hoặc `guided_json`.
  4. `MockBackend`: Tự khởi động hoặc kết nối tới `fake_model_server.py`.
  5. `ReflexBackend`: Chạy trực tiếp qua logic của `reflex.py`.
- **Cơ chế Fallback thông minh**: Khi khởi chạy launcher:
  - Nếu người dùng chọn LLM mode nhưng không phát hiện server nào sống: Launcher hiển thị thông báo rõ ràng, giải thích rằng hệ thống sẽ tự động dùng chế độ **Offline Reflex** (hoặc hỏi người dùng có muốn bật Mock server không) thay vì để game bị crash/nghẽn.

---

### 2.4. Trải Nghiệm Khởi Chạy (Launcher UX) & Script Hiện Hữu

#### Hiện trạng:
- `Makefile` chứa các lệnh hữu ích nhưng chỉ chạy trên POSIX:
  - `make run`: `python -m genesis.run --seed 42 --ticks 400`
  - `make serve`: `uvicorn net.server:app --host 127.0.0.1 --port 8000`
  - `make demo`: chạy fake model server + simulation + score
  - `make preflight`: `python scripts/preflight.py`
  - `make hostile`: `python scripts/hostile_client.py --server http://127.0.0.1:8000`
- `scripts/final_run.sh`: Script chạy benchmark nhiều seed và in phán quyết.
- `scripts/serve_L2.sh` / `scripts/serve_L2.ps1`: Script khởi động `llama-server`.
- **Hoàn toàn vắng bóng**:
  - `run.sh` / `setup.sh` ở thư mục gốc.
  - `run.ps1` / `run.bat` / `setup.bat` ở thư mục gốc.
  - `launch.py` hoặc module launcher tích hợp tương tác/tự động.

#### Yêu cầu thiết kế Launcher 1-Chạm (Target Experience):
Người dùng chỉ cần gõ một lệnh duy nhất:
- **macOS / Linux**: `./run.sh` (hoặc `bash run.sh`)
- **Windows**: `.\run.ps1` (hoặc `run.bat`)
- **Python trực tiếp**: `python launch.py`

Quá trình tự động thực hiện từ A đến Z trong **dưới 3 phút** (thậm chí < 30 giây nếu venv đã có):
1. **Bước 1 (Kiểm tra & Thiết lập Môi trường)**:
   - Phát hiện Python (ưu tiên `python3.11`, `python3`, `py -3.11`, `python`). Kiểm tra version >= 3.11.
   - Kiểm tra thư mục `.venv`. Nếu chưa có, tự động tạo `python -m venv .venv`.
   - Tự động kích hoạt venv trong ngữ cảnh script.
2. **Bước 2 (Cài đặt & Đồng bộ Dependencies)**:
   - Kiểm tra các package bắt buộc (`rich`, `httpx`, `fastapi`, `uvicorn`, `pydantic`).
   - Nếu thiếu, tự động chạy `pip install -e .` (hoặc `pip install -r requirements.txt`).
3. **Bước 3 (Preflight & Chẩn đoán Nhanh)**:
   - Chạy preflight nội bộ (kiểm tra import, web assets, dung lượng đĩa).
   - Tự động sửa các lỗi thông thường (tạo thư mục `runs/`, vendor static assets nếu thiếu).
4. **Bước 4 (Dò tìm Backend & Thiết lập Chế độ)**:
   - Thăm dò: llama-server (`:8080`), Ollama (`:11434`), vLLM (`:8000`), Fake server (`:8099`).
   - Nếu tìm thấy LLM -> Báo sẵn sàng kết nối LLM.
   - Nếu không có LLM -> Báo rõ ràng:  
     `⚡ [OFFLINE MODE] Không phát hiện LLM cục bộ. Tự động khởi chạy chế độ Phản Xạ Bản Năng (Reflex) siêu tốc.`
5. **Bước 5 (Trình đơn Khởi chạy & Tự động Mở Game)**:
   - Chế độ Mặc định (hoặc truyền cờ `--web`, `--demo`, `--cli`):
     - **Tùy chọn 1: Trận đấu Mô Phỏng Tức thì (Terminal Visualizer)**: Hiển thị bàn cờ sống động qua Rich live console.
     - **Tùy chọn 2: Khởi động Web Server & Mở Trình duyệt 3D**: Chạy server FastAPI cổng 8000, tự động mở trình duyệt tới `http://127.0.0.1:8000/watch/watch3d.html`.
     - **Tùy chọn 3: Chạy Toàn Bộ Đường Ống Demo (Mock LLM + Chấm Điểm)**.
     - **Tùy chọn 4: Chạy Bộ Kiểm Tra Sức Khỏe (Preflight Diagnostics)**.

---

### 2.5. Tài Liệu Hướng Dẫn & Onboarding (Docs & Quickstart)

| Tài liệu | Hiện trạng | Cần cập nhật |
|---|---|---|
| `README.md` | Giới thiệu dự án, bảng kết quả, status. Mục cài đặt đưa lệnh 3 bước (`git clone`, `pip install`, `python -m genesis.run`). | Đưa lệnh 1-chạm (`./run.sh` / `.\run.ps1`) lên đầu mục Quickstart trong 60 giây. Cập nhật bảng kiểm tra và liên kết. |
| `docs/HUONG-DAN.md` | Hướng dẫn chi tiết bằng tiếng Việt, rất đầy đủ về logic game, cắm model, xem ván. | Cập nhật mục "0. Trong 60 giây" và "2. Cắm model vào" với launcher 1-chạm và hỗ trợ Ollama/vLLM. |
| `docs/CHAY-TREN-WINDOWS.md` | Hướng dẫn cụ thể cho PowerShell, giải thích VRAM, `-c` context size. | Thêm hướng dẫn chạy `.\run.ps1` và `run.bat` 1-chạm. |

---

## 3. Ma Trận Đánh Giá: Hiện Tại vs Mục Tiêu R2

| Tiêu chí | Hiện tại | Mục tiêu R2 (1-Command Launcher) | Trạng thái Gap |
|---|---|---|---|
| **Lệnh cài đặt & chạy** | Phải gõ 4–5 lệnh thủ công | **1 lệnh duy nhất** (`./run.sh` hoặc `.\run.ps1`) | 🔴 Chưa có |
| **Tự động tạo venv** | Thủ công (`python -m venv .venv`) | **Tự động 100%** nếu chưa có `.venv` | 🔴 Chưa có |
| **Tự động cài dependencies** | Thủ công (`pip install -r ...`) | **Tự động kiểm tra & cài đặt** khi thiếu | 🔴 Chưa có |
| **Độ nhất quán Pytest/Deps** | Lỗi `numpy` trong preflight, `pytest` lỗi import | Đồng bộ `numpy` trong dependencies, thêm `pythonpath=["."]` | 🟡 Cần sửa |
| **Auto-remediation** | Chỉ in gợi ý lệnh | Tự động tạo thư mục, cài đặt gói, sửa lỗi cấu hình | 🔴 Chưa có |
| **Đa backend LLM** | Chỉ có `llama-server` và `fake_model_server` | Hỗ trợ **Ollama**, **llama.cpp**, **vLLM**, **Mock**, **Reflex** | 🟡 Thiếu adapter |
| **Fallback Offline** | Cần truyền cờ thủ công hoặc đợi timeout | Tự nhận diện và thông báo chuyển mượt sang Reflex | 🟡 Cần hoàn thiện |
| **Windows Parity** | Chỉ có hướng dẫn gõ tay + script serve | Có đầy đủ `run.ps1` và `run.bat` 1-chạm ngang hàng macOS/Linux | 🔴 Chưa có |
| **Thời gian Onboarding** | 5–10 phút cấu hình | **< 3 phút** từ lúc clone về tới lúc thấy game chạy | 🟢 Khả thi ngay |

---

## 4. Đề Xuất Thiết Kế Kiến Trúc Cho Giai Đoạn Triển Khai (Phase 2)

### 4.1. Cấu trúc tập tin đề xuất thêm mới / cập nhật:

```
Genesis_Zero/
├── run.sh                  # [MỚI] POSIX launcher (macOS / Linux)
├── run.ps1                 # [MỚI] Windows PowerShell launcher
├── run.bat                 # [MỚI] Windows CMD launcher
├── launch.py               # [MỚI] Python Launcher Engine (Cross-platform core, UI đẹp bằng Rich)
├── pyproject.toml          # [SỬA] Thêm pythonpath=["."] trong pytest, chuẩn hóa deps
├── requirements.txt        # [SỬA] Bổ sung numpy (hoặc tách rõ ràng với preflight)
├── scripts/
│   ├── preflight.py        # [SỬA] Thêm cờ --fix, sửa check numpy, hỗ trợ quét đa cổng LLM
│   ├── serve_L2.sh         # Giữ nguyên
│   └── serve_L2.ps1        # Giữ nguyên
├── genesis/
│   ├── llm_client.py       # [SỬA] Bổ sung adapter cho Ollama (/api/chat) và vLLM (/v1/chat/completions)
│   └── ...
├── README.md               # [SỬA] Cập nhật Quickstart 1-chạm
└── docs/
    ├── HUONG-DAN.md        # [SỬA] Cập nhật hướng dẫn launcher
    └── CHAY-TREN-WINDOWS.md# [SỬA] Cập nhật hướng dẫn Windows 1-chạm
```

### 4.2. Thiết kế chi tiết `launch.py` & Shell Launchers:

1. **`run.sh`**:
   - Kiểm tra `python3.11` / `python3`.
   - Nếu chưa có `.venv`, chạy `python3 -m venv .venv`.
   - Kích hoạt `.venv/bin/activate`.
   - Chạy `python launch.py "$@"`.

2. **`run.ps1`**:
   - Kiểm tra `py -3.11` / `python`.
   - Nếu chưa có `.venv`, chạy `python -m venv .venv`.
   - Gọi `.\.venv\Scripts\Activate.ps1`.
   - Chạy `python launch.py @args`.

3. **`launch.py` (Python Core Launcher)**:
   - Module hoá các bước:
     - `ensure_dependencies()`: Dùng `importlib` kiểm tra `rich`, `httpx`, `fastapi`, `uvicorn`, `pydantic`. Nếu thiếu, tự động gọi `pip install -e .`.
     - `run_preflight(auto_fix=True)`: Gọi kiểm tra môi trường và tự động xử lý các lỗi nhẹ.
     - `detect_llm_backends()`: Quét nhanh (timeout 0.3s) các cổng 8080 (llama.cpp), 11434 (Ollama), 8000 (vLLM), 8099 (fake server).
     - `select_or_prompt_mode()`: Nếu chạy ở chế độ tương tác (không truyền cờ):
       - Hiển thị menu Rich TUI đẹp mắt:
         1. 🎮 **Chạy ván nhanh (Terminal ASCII/Rich UI)**
         2. 🌐 **Khởi động Web 3D Spectator & Mở Trình duyệt**
         3. 🤖 **Chạy Thử Nghiệm Toàn Tuyến (Mock LLM Demo)**
         4. 🩺 **Kiểm Tra & Tự Động Sửa Lỗi Hệ Thống (Preflight Diagnostics)**
     - Hỗ trợ các cờ dòng lệnh:
       - `--offline` / `--reflex`: Ép chạy chế độ bản năng.
       - `--web`: Tự động khởi chạy server và mở trình duyệt xem 3D.
       - `--demo`: Chạy ván demo có mock model và chấm điểm.
       - `--llm-backend [llama|ollama|vllm]`: Chỉ định backend LLM.
       - `--fix`: Tự động sửa chữa môi trường.

---

## 5. Kết Luận & Kế Hoạch Bàn Giao

Kho mã nguồn Genesis Zero có nền tảng toán học, logic mô phỏng và bộ test rất vững chắc. Việc bổ sung bộ cài đặt và khởi chạy 1-chạm (R2) sẽ hoàn thiện mảnh ghép quan trọng nhất về tính dễ tiếp cận (zero-friction usability), giúp bất kỳ người dùng nào trên macOS, Linux hay Windows cũng có thể trải nghiệm thế giới mô phỏng thú vị này trong vòng chưa đầy 3 phút.

Báo cáo khảo sát này cung cấp đầy đủ bằng chứng quan sát, phân tích nguyên nhân và thiết kế giải pháp chi tiết sẵn sàng cho Builder triển khai ở Phase 2.
