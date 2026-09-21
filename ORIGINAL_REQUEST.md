# Original User Request

## 2026-09-20T04:52:03Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Delegate to teamwork_preview
> Requested team: Full team

Nâng cấp dự án bản đồ thế giới sinh vật 3D trở nên chân thực, đẹp mắt và hoàn thiện nhất, tham khảo các dự án mã nguồn mở để chuẩn bị cho việc đóng gói. Dự án là một bản demo chất lượng cao (Proof of Concept). Nhóm agent toàn diện (Full team) sẽ tự quyết định nền tảng (Web/Desktop) và công nghệ phù hợp nhất.

Working directory: ~/teamwork_projects/genesis_zero
Integrity mode: demo

## Requirements

### R1. Xây dựng môi trường 3D chân thực
Phát triển bản demo thế giới sinh vật 3D với mức độ chi tiết cao. Trọng tâm là chất lượng thị giác chân thực, áp dụng các kỹ thuật render hiện đại (vật liệu vật lý, ánh sáng phức tạp, bóng đổ).

### R2. Kiến trúc chuẩn mã nguồn mở và đóng gói
Thiết lập cấu trúc thư mục và mã nguồn theo chuẩn của các dự án mã nguồn mở chất lượng cao. Mã nguồn phải có tính mô-đun, dễ mở rộng và đi kèm với các tập lệnh (scripts) đóng gói/build rõ ràng để sẵn sàng phát hành.

### R3. Lựa chọn công nghệ tối ưu
Nhóm tự nghiên cứu, đánh giá và quyết định bộ công cụ/framework đồ họa tốt nhất (VD: WebGL/Three.js, Babylon.js, hoặc framework phù hợp) để đạt được mục tiêu thị giác và hiệu năng của bản demo.

## Acceptance Criteria

### Khả năng hoạt động và đóng gói
- [ ] Dự án có thể cài đặt các phụ thuộc (dependencies) và build hoặc khởi động thành công bằng kịch bản tự động (automated script) mà không văng lỗi (zero errors).
- [ ] Tồn tại các file cấu hình rõ ràng cho việc đóng gói dự án (ví dụ: kịch bản build cho production).

### Chất lượng đồ họa (Đánh giá bằng Code Analysis)
- [ ] Kịch bản phân tích mã (code analysis script) xác nhận sự hiện diện của các cấu hình ánh sáng tiên tiến (ví dụ: bật bóng đổ - shadows, ánh sáng môi trường/định hướng).
- [ ] Mã nguồn cấu hình môi trường/sinh vật có sử dụng hệ thống vật liệu vật lý (PBR - Physically Based Rendering) hoặc các kỹ thuật shader nâng cao tương đương.

### Đánh giá kiến trúc (Agent-as-judge)
- [ ] Một Agent độc lập đánh giá cấu trúc dự án và xác nhận mã nguồn được chia tách thành các mô-đun logic hợp lý (tách biệt giữa assets, rendering logic, và entity/creature logic).

## 2026-09-20T18:01:54Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Đội ngũ đầy đủ (Full Team: chuyên gia kiến trúc, lập trình, adversarial review và kiểm thử độc lập)

Nghiên cứu, nâng cấp toàn diện và tối ưu hóa hệ sinh thái Genesis Zero: cải tiến trí tuệ sinh vật LLM trong việc khám phá luật ẩn, tối đa hóa thông lượng vòng lặp mô phỏng, nâng tầm đồ họa 3D WebGL Three.js đạt chuẩn mực thị giác chân thực, và củng cố độ ổn định hạ tầng mạng đa điểm theo chuẩn mực nghiên cứu & production.

Working directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: development

## Requirements

### R1. Trí Tuệ Sinh Vật & Cơ Chế Khám Phá Định Luật Ẩn (LLM & Agent Cognition)
Nâng cấp khả năng tư duy và chiến lược sinh tồn của sinh vật, cho phép hình thành giả thuyết khoa học và suy luận chính xác các định luật vật lý ngẫu nhiên ẩn giấu của thế giới. Cung cấp bộ công cụ đo lường và benchmark A/B định lượng so sánh hiệu quả giữa các mô hình trí tuệ (Frontier LLM, Local LLM, Reflex Strategist) với đầy đủ cơ chế bảo vệ bí mật luật ẩn (bất biến B-05 và B-10).

### R2. Tối Ưu Hóa Thông Lượng & Hiệu Năng Vòng Lặp Mô Phỏng (Simulation Engine Throughput)
Loại bỏ các điểm nghẽn hiệu năng trong vòng lặp 6 pha của simulation engine (tối ưu hóa phép tính khoảng cách Chebyshev, kiểm tra địa hình đi được, tạo context đánh giá LawDSL và quản lý bộ nhớ). Đảm bảo tốc độ tính toán nhanh vượt bậc trong chế độ headless nhưng bảo toàn tuyệt đối 100% tính tất định (bất biến B-02 Seed Determinism).

### R3. Nâng Tầm Trải Nghiệm & Độ Chân Thực Trình Hiển Thị 3D Spectator (WebGL 3D Fidelity)
Nâng cấp trình hiển thị WebGL Three.js với vật liệu PBR cao cấp, bóng đổ mềm, hiệu ứng nước và khí quyển thời tiết chân thực, chuyển động animation sinh vật mượt mà, và hệ thống âm thanh tổng hợp Web Audio phản hồi theo sự kiện chiến đấu/sinh tồn. Đảm bảo toàn bộ kiến trúc đồ họa tuân thủ nghiêm ngặt nguyên tắc Zero-CDN (chạy 100% offline) kèm cơ chế dự phòng (fallback) tự động.

### R4. Hạ Tầng Mạng Đồng Bộ & Chuẩn Mực Triển Khai Production (Network & Code Quality)
Đảm bảo luồng truyền phát WebSocket `/v1/spectate` đồng bộ mượt mà với nhiều spectator đồng thời mà không làm giảm tốc độ của engine mô phỏng. Củng cố chất lượng toàn bộ codebase đạt chuẩn kiểm thử tĩnh nghiêm ngặt (Ruff, Mypy), tỷ lệ bao phủ test suite cao, và hỗ trợ khởi chạy 1-chạm đa nền tảng (Windows, macOS, Linux, Docker).

## Acceptance Criteria

### Tính Tất Định & Bất Biến Cốt Lõi (Invariants & Integrity)
- [ ] Tất cả các bài kiểm tra determinism (`tests/test_determinism.py`) vượt qua 100% với cùng seed và map đầu vào (bảo toàn bất biến B-02).
- [ ] Các bài kiểm thử bảo mật luật ẩn và cách ly trọng tài (`tests/test_score.py`, `tests/test_victory.py`) vượt qua 100% (bảo toàn bất biến B-05 và B-10).
- [ ] Toàn bộ test suite hiện có (1889+ tests) cùng các test mới được thực thi tự động qua pytest mà không có bất kỳ failure nào.

### Thông Lượng Mô Phỏng (Simulation Throughput)
- [ ] Tốc độ mô phỏng headless (`python -m genesis.run --seed 42 --ticks 400 --no-render`) đạt thông lượng tối thiểu >= 900 ticks/giây trên môi trường tiêu chuẩn.
- [ ] Hồ sơ profiling định lượng (cProfile) chứng minh giảm thiểu tối thiểu 50% thời gian tích lũy tại các hàm nút thắt (`dist`, `passable`, `build_ctx`).

### Đánh Giá Trí Tuệ & Khám Phá Luật (AI Benchmarking)
- [ ] Kịch bản đánh giá A/B benchmark (`scripts/b10_ab.py` hoặc suite tương đương) hoàn tất 5 seed kiểm chuẩn độc lập mà không gặp lỗi runtime, dead-lock hay rò rỉ bộ nhớ.
- [ ] Sinh vật ứng dụng cơ chế suy luận giả thuyết ghi nhận tỷ lệ phát hiện chính xác định luật ẩn cao hơn tối thiểu 20% so với baseline ngẫu nhiên.

### Đồ Họa 3D WebGL & Zero-CDN (Graphics & Modularity)
- [ ] Các kịch bản kiểm định kiến trúc và đồ họa (`python scripts/analyze_graphics_code.py` và `python scripts/verify_modular_architecture.py`) vượt qua 100% các tiêu chí đánh giá.
- [ ] Kịch bản kiểm tra offline (`python scripts/verify_zero_cdn.py`) xác nhận 0 dependency từ external CDN.

### Chuẩn Mực Mã Nguồn & Đóng Gói (Code Quality & Build)
- [ ] `uv run ruff check .` và `uv run mypy genesis/` vượt qua 100% không phát sinh lỗi hoặc cảnh báo vi phạm kiểu dữ liệu.
- [ ] Kịch bản đóng gói phân phối (`python scripts/build_dist.py`) tạo thành công wheel package và sdist sạch, cài đặt và kiểm thử hoạt động bình thường.
