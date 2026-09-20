# Kế Hoạch Nâng Cấp Toàn Diện Dự Án Genesis Zero (Comprehensive System Upgrade Plan)

> **Mã kế hoạch**: `UPGRADE-2026-09-19`  
> **Phiên bản mục tiêu**: `v1.1.0`  
> **Trạng thái**: Sẵn sàng thực thi (Approved Blueprint)  
> **Tài liệu tham chiếu**: `ORIGINAL_REQUEST.md` (2026-09-19T15:27:10Z), Survey Reports 17-1, 17-2, 17-3  

---

## 1. Executive Summary & Goals

Genesis Zero là hệ thống sandbox mô phỏng sinh thái tiến hóa đa tác nhân kết hợp suy diễn định luật vật lý ngẫu nhiên (LawDSL v5), hỗ trợ các mô hình LLM độc lập và trình hiển thị 3D WebGL (Three.js diorama). Sau đợt kiểm tra và đo lường toàn diện (empirical profiling và static auditing) trên 124 file mã nguồn và 1.866 bài test, dự án đạt độ bao phủ code 93% và độ ổn định cao. Tuy nhiên, hệ thống còn tồn tại các nút thắt hiệu năng nghiêm trọng trong vòng lặp mô phỏng, nợ kỹ thuật về kiểu dữ liệu (typing), thiếu hụt giải pháp container hóa chuẩn hóa, và hạ tầng CI/CD chưa hỗ trợ ma trận đa nền tảng.

### 1.1 Mục Tiêu Chiến Lược
1. **Tối ưu hóa hiệu năng (Simulation Throughput)**: Tăng tốc độ mô phỏng từ **1.8x đến 2.5x** (đạt > 650 ticks/giây trong chế độ headless), cắt giảm tối thiểu 60% số lệnh gọi khoảng cách `world.dist()` và triệt tiêu 100% chi phí so sánh dataclass lặp lại.
2. **Hiện đại hóa kiến trúc & Typing**: Chuẩn hóa `Strategist` lifecycle protocol, loại bỏ triệt để runtime duck-typing introspection (`getattr`), chuẩn hóa `mypy` không còn đường dẫn tuyệt đối cục bộ, và triển khai chấm điểm Sổ Luật hoàn toàn trên bộ nhớ (Zero-I/O in-memory referee scoring).
3. **Hiện đại hóa CI/CD & Containerization**: Thiết lập ma trận kiểm thử GitHub Actions 7 giai đoạn (hỗ trợ Linux, Windows, macOS trên Python 3.11 & 3.12), bổ sung GitLab CI, đóng gói Docker đa tầng (multi-stage) bảo mật với non-root user `genesis` và healthcheck định kỳ, kèm file điều phối `docker-compose.yml`.
4. **Đồng bộ hóa tài liệu & kiểm chuẩn**: Chuẩn hóa kiểm kê 1.866 test cases trong `README.md` (loại bỏ lỗi thoát `count_tests.py`), bổ sung sơ đồ kiến trúc thành phần và vòng đời 6 pha trong `docs/ARCHITECTURE.md`, tài liệu triển khai `docs/DEPLOYMENT.md`, và nhật ký phiên bản `CHANGELOG.md`.

### 1.2 Các Ràng Buộc Bất Biến (Strict Invariants)
- **B-02 (Seed Determinism)**: Mọi thay đổi thuật toán tối ưu phải bảo toàn tính tất định 100% với cùng seed và map đầu vào (khớp tuyệt đối `tests/test_determinism.py`).
- **B-05 (Hidden Law Confidentiality)**: Tuyệt đối không để lộ danh tính luật ẩn ra các luồng telemetry public trước pha `Phase.REVEAL`.
- **B-10 (Referee Isolation)**: Mô-đun chấm điểm `genesis/score.py` và `genesis/victory.py` tuyệt đối không được import `genesis/world.py` hoặc `genesis/tick.py` (được bảo vệ bởi AST check trong `tests/test_score.py::test_khong_import_sim`).

---

## 2. Điểm Nghẽn Kỹ Thuật & Nợ Kiến Trúc (Bottlenecks & Technical Debt)

### 2.1 Điểm Nghẽn Hiệu Năng Vòng Lặp Mô Phỏng (Empirical Profiling Analysis)
Kết quả cProfile từ ván đấu chuẩn 400 tick headless (`python -m genesis.run --seed 42 --ticks 400 --no-render`):

| Hạng | Hàm / Vị trí | Lượt gọi | Tổng thời gian (s) | Thời gian tích lũy (s) | Nguyên nhân gốc rễ |
|:---:|---|:---:|:---:|:---:|---|
| **1** | `world.py:267(dist)` | **795.822** | **0.534** | **0.832** | Khoảng cách Chebyshev hình xuyến bị gọi lặp lại 3 lần trong vòng lặp quét bán kính (1, 2, 3) tại `lawhook.py:build_ctx` và quét tầm nhìn $O(N^2)$. |
| **2** | `world.py:293(passable)` | **195.912** | **0.254** | **0.536** | Kiểm tra ô đi được gọi liên tục khi tìm đường, kích hoạt so sánh dataclass trên mọi bước. |
| **3** | `<string>:2(__eq__)` | **191.551** | **0.090** | **0.090** | `Traits.__eq__` so sánh 6 thuộc tính của dataclass mỗi khi `world.passable` kiểm tra cache `cached[0] == traits`. |
| **4** | `builtins.getattr` | **1.068.034** | **0.102** | **0.131** | Truy cập thuộc tính `creature.kit` (248.996 lần) và duck-typing thăm dò phương thức `strat` trong `tick.py`. |
| **5** | `lawhook.py:33(build_ctx)` | **7.701** | **0.136** | **0.610** | Tạo context đánh giá LawDSL; lặp độc lập 3 pass cho 3 bán kính $r \in \{1, 2, 3\}$. |
| **6** | `world.py:404` & `433` | **796** | **0.075** | **0.075** | Quét toàn bộ lưới $24 \times 24$ (576 ô $\times$ 2 = 1.152 truy vấn/tick, 460.800 truy vấn/ván) trong `spawn_algae` và `spawn_plants` dù địa hình tĩnh. |
| **7** | `random.py:seed` (`creature_rng`) | **16.320** | **0.090** | **0.094** | Mã hóa chuỗi MD5, chuyển sang chuỗi hex rồi ép ngược lại `int(h[:16], 16)` trên mỗi sinh vật mỗi tick. |

### 2.2 Nợ Kiến Trúc & An Toàn Kiểu Dữ Liệu
1. **Strategist Protocol Duck-Typing**: `genesis/strategy/base.py` chỉ định nghĩa phương thức `decide()`, trong khi vòng lặp 6 pha trong `genesis/tick.py` sử dụng hàng loạt lệnh `getattr(strat, "begin_tick", None)`, `getattr(strat, "take_says", None)`, `getattr(strat, "take_shift", None)`, `getattr(strat, "observe", None)` gây chậm chạp và thiếu cảnh báo tĩnh từ `mypy`.
2. **I/O Round-Trip Khi Kết Thúc Ván**: `net/match.py:compute_victory()` buộc phải flush toàn bộ sự kiện ra file JSONL rồi gọi `genesis.victory.from_files()`, mở lại file và parse JSON lần hai, gây trễ và tiềm ẩn lỗi xung đột khóa file trên Windows (`WinError 32`).
3. **Đường Dẫn Tuyệt Đối Cục Bộ Trong `pyproject.toml`**: Dòng 138 cấu hình `mypy_path` chứa `"E:/tool/mcp/terra_forge"`. Đường dẫn ổ đĩa Windows này không tồn tại trên môi trường Linux/macOS hoặc máy phát triển khác.
4. **Lệnh `lock` Sai Lệch Trong `Makefile`**: Mục `lock:` chạy `uv pip compile pyproject.toml -o requirements.lock` (thiếu `--all-extras --universal`), nếu vô tình kích hoạt sẽ làm mất toàn bộ gói phụ thuộc nhóm dev/viz/train và các marker nền tảng.
5. **Thiếu Target Kiểm Tra Kiểu Trong `Makefile`**: `Makefile` chỉ có `make lint` (chạy ruff) mà chưa có `make typecheck` (chạy mypy).

### 2.3 Khiếm Khuyết CI/CD, Container Hóa & Tài Liệu
1. **Thiếu Ma Trận Kiểm Thử Đa Nền Tảng**: Workflow `.github/workflows/test.yml` hiện tại chỉ chạy trên `ubuntu-latest` với Python 3.11 duy nhất. Windows và macOS không được tự động kiểm thử dù dự án có các script chuyên dụng (`run.ps1`, `run.bat`, xử lý UTF-8 console streams).
2. **Chưa Có Container Hóa Chuẩn Hóa**: Dự án chưa có `Dockerfile`, `.dockerignore`, hoặc `docker-compose.yml`. Việc triển khai máy chủ phụ thuộc vào cài đặt thủ công hoặc systemd VPS. Các probe `/v1/healthz` và `/v1/readyz` chưa được tận dụng làm container healthcheck.
3. **Lệch Số Lượng Test Giữa Mã Nguồn Và Tài Liệu**: Pytest hiện thu thập **1.866 test cases** trên 122 files, trong khi `README.md` ghi nhận 1.833 tests, khiến script kiểm tra `python scripts/count_tests.py` báo lỗi (exit code 1).
4. **Thiếu Sơ Đồ Kiến Trúc & Nhật Ký Phát Hành**: Thiếu sơ đồ trực quan kết nối giữa Simulation, Server, Client, WebGL Spectator và Procedural Assets; thiếu file `CHANGELOG.md` chuẩn Keep a Changelog.

---

## 3. Các Giải Pháp Nâng Cấp Cụ Thể (Concrete Upgrade Solutions)

### 3.1 Nhóm 1: Tối Ưu Hóa Hiệu Năng & Mô Phỏng (Performance & Simulation)

#### Giải Pháp 1.1: Quét Khoảng Cách Đơn Vòng (Single-Pass Monotonic Distance Loop)
- **Vị trí**: `genesis/lawhook.py:build_ctx`
- **Hiện trạng**: Lặp 3 lần qua danh sách sinh vật cho các bán kính $r \in (1, 2, 3)$, tính `world.dist(c.pos, o.pos)` độc lập 3 lần.
- **Giải pháp**: Tính `d = world.dist(c.pos, o.pos)` duy nhất 1 lần cho mỗi sinh vật khác. Do khoảng cách Chebyshev có tính đơn điệu ($d \le 1 \implies d \le 2 \implies d \le 3$), cộng dồn trực tiếp cho tất cả bán kính $r \ge d$ trong khoảng $d \in [1, 3]$:
  ```python
  counts = {
      "SAME_SP": {1: 0, 2: 0, 3: 0},
      "OTHER_SP": {1: 0, 2: 0, 3: 0},
      "ANY": {1: 0, 2: 0, 3: 0},
  }
  for o in creatures:
      if o is c or not o.alive:
          continue
      d = world.dist(c.pos, o.pos)
      if d > 3:
          continue
      key = "SAME_SP" if o.species == c.species else "OTHER_SP"
      for r in range(max(1, d), 4):
          counts[key][r] += 1
          counts["ANY"][r] += 1
  ```
- **Xử lý ngoại lệ biên (Edge Case)**: Trong trường hợp hai sinh vật trùng vị trí ($d=0$, ví dụ lúc vừa sinh hoặc đang giải quyết va chạm), việc sử dụng `range(max(1, d), 4)` đảm bảo an toàn tuyệt đối, tránh truy cập `counts[key][0]` gây lỗi `KeyError: 0` (vì từ điển chỉ khởi tạo cho bán kính $r \in \{1, 2, 3\}$).
- **Hiệu quả dự kiến**: Giảm ngay **66.7%** số lệnh gọi `world.dist()` trong `build_ctx` (tiết kiệm ~15.000 phép tính khoảng cách/ván 400 tick) mà vẫn bảo toàn 100% tính toàn vẹn biên.

#### Giải Pháp 1.2: Tối Ưu Kiểm Tra Đi Được Bằng Con Trỏ Định Danh (Identity Passability Cache)
- **Vị trí**: `genesis/world.py:passable`
- **Hiện trạng**: `world.passable()` truy cập cache bộ đệm trên sinh vật `creature._cached_passable = (traits, kit, passable_terrains)` nhưng thực hiện so sánh giá trị dataclass `cached[0] == traits` và `cached[1] == kit` trên **191.551 lượt gọi**. Do `traits` là một dataclass gồm 6 trường số nguyên, phép so sánh `==` kích hoạt 191.551 lần gọi hàm `Traits.__eq__`, gây tiêu tốn CPU đáng kể trong profiling.
- **Giải pháp**:
  - Tuân thủ nghiêm ngặt **Bất biến W-18 §2**: `world.passable` là **ĐƯỜNG DUY NHẤT** trả lời câu hỏi "ai đi được đâu", không tạo bảng tra cứu thứ hai bên ngoài để tránh phân mảnh khái niệm và lỗi lệch trạng thái (passability drift).
  - Khả năng vượt địa hình phụ thuộc vào cả `traits` và bộ kit đặc thù (`kit`, ví dụ `DAO_HANG` cho phép đi xuyên đá/hang ngầm, `LUONG_CU` cho phép bơi nước nông).
  - Vì `traits` là đối tượng bất biến (chỉ được thay thế bằng instance mới khi tiến hóa `maybe_shift` hoặc tái sinh `rebirth`), và `kit` cũng là đối tượng cố định theo loài/cá thể, ta thay thế phép so sánh giá trị (`==`) bằng kiểm tra định danh con trỏ bộ nhớ (`is`):
    ```python
    cached = getattr(creature, "_cached_passable", None)
    species = getattr(creature, "species", "")
    kit = getattr(creature, "kit", None) or self.kits.get(species)
    traits = getattr(creature, "traits", None)
    if cached is not None and cached[0] is traits and cached[1] is kit:
        return terrain in cached[2]
    ```
  - Khi `traits` hoặc `kit` thay đổi con trỏ tham chiếu (hoặc lần đầu truy vấn), hàm sẽ tính toán lại tập `passable_terrains` theo đúng quy tắc sinh học và lưu bộ ba `(traits, kit, passable_terrains)` vào `creature._cached_passable`.
- **Hiệu quả dự kiến**: Triệt tiêu hoàn toàn **100%** (191.551 lần gọi) overhead so sánh `Traits.__eq__` với độ phức tạp $O(1)$ pointer comparison, tiết kiệm ~0.09s CPU/ván mà vẫn bảo toàn tính năng của `DAO_HANG`, `LUONG_CU` và bất biến W-18.


#### Giải Pháp 1.3: Danh Sách Ô Tĩnh Tiền Tính Toán (Precomputed Static Tile Pools)
- **Vị trí**: `genesis/world.py`
- **Hiện trạng**: `spawn_algae` và `spawn_plants` duyệt toàn bộ mảng 2D $24 \times 24$ (576 ô) trên mỗi tick để lọc ô nước hoặc ô đồng bằng.
- **Giải pháp**:
  - Trong `World.__init__()`, sau khi khởi tạo địa hình, tiền tính toán danh sách ô bất biến:
    ```python
    self.plain_tiles: tuple[tuple[int, int], ...] = tuple(
        (x, y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] == Terrain.PLAIN
    )
    self.water_tiles: tuple[tuple[int, int], ...] = tuple(
        (x, y) for y in range(self.h) for x in range(self.w)
        if self.grid[y][x] in (Terrain.WATER, Terrain.DEEP)
    )
    ```
  - Cập nhật `spawn_algae`: Lọc trực tiếp từ `self.water_tiles` với điều kiện `p not in self.algae`.
  - Cập nhật `spawn_plants`: Lọc trực tiếp từ `self.plain_tiles` với điều kiện `p not in self.fruits`.
- **Hiệu quả dự kiến**: Cắt giảm 460.800 phép so sánh enum và duyệt ma trận 2D mỗi ván.

#### Giải Pháp 1.4: Rút Gọn Sinh Seed Ngẫu Nhiên Nhanh Trong `creature_rng`
- **Vị trí**: `genesis/tick.py:creature_rng`
- **Hiện trạng**: Thực hiện băm MD5, sinh chuỗi hex 32 ký tự, cắt lát `h[:16]` và gọi `int(..., 16)`.
- **Giải pháp**: Sử dụng `int.from_bytes(digest[:8], "big")` trực tiếp từ chuỗi byte thô của MD5:
  ```python
  def creature_rng(match_seed: int, tick_no: int, creature_id: str) -> random.Random:
      raw = hashlib.md5(f"{match_seed}:{tick_no}:{creature_id}".encode()).digest()
      return random.Random(int.from_bytes(raw[:8], "big"))
  ```
- **Hiệu quả dự kiến**: Bảo toàn 100% tính ngẫu nhiên tương đương nhưng loại bỏ hoàn toàn cấp phát chuỗi hex trung gian trên 16.320 lượt gọi.

#### Giải Pháp 1.5: Tối Ưu Hóa Đánh Giá Hàng Xóm Tham Lam (Greedy Pathfinding)
- **Vị trí**: `genesis/reflex.py:_greedy_path_towards` (tầng phản xạ bản năng lõi)
- **Hiện trạng**: Trong `_greedy_path_towards` tại `genesis/reflex.py`, thuật toán tính khoảng cách Chebyshev tới đích 2 lần cho mỗi ô lân cận (lần 1 tìm khoảng cách tối thiểu `min_d`, lần 2 duyệt lại để lọc các ô đạt khoảng cách bằng `min_d`).
- **Giải pháp**: Tính danh sách tuple `(distance, pos)` một lần duy nhất cho các ô lân cận hợp lệ, sau đó tìm trực tiếp phần tử có khoảng cách nhỏ nhất kết hợp hàm bẻ hòa vị trí (coordinate tie-breaker) theo thứ tự ưu tiên chuẩn của hệ thống.
- **Hiệu quả dự kiến**: Giảm 50% số phép tính khoảng cách trong quá trình tìm đường của mọi sinh vật chạy reflex.

---

### 3.2 Nhóm 2: Hiện Đại Hóa Kiến Trúc & An Toàn Kiểu Dữ Liệu (Architecture & Typing)

#### Giải Pháp 2.1: Chấm Điểm Trọng Tài Thuần Trên Bộ Nhớ (Zero-I/O In-Memory Referee)
- **Vị trí**: `genesis/score.py`, `genesis/victory.py`, `net/match.py`
- **Giải pháp**:
  - Trong `genesis/score.py`: Tách logic tính toán khỏi đọc file bằng cách bổ sung hàm:
    ```python
    def score_records(records: list[dict[str, Any]], truth: dict[str, Any]) -> list[dict[str, Any]]:
        """Tính điểm thuần trên bộ nhớ từ danh sách bản ghi telemetry và ground truth."""
    ```
    Giữ nguyên `score_match(log: Path, truth: Path)` làm wrapper đọc file để đảm bảo backward compatibility.
  - Trong `genesis/victory.py`: Bổ sung `from_records(records: list[dict], truth: dict) -> Victory`.
  - Trong `net/match.py`: Lưu trữ danh sách bản ghi sự kiện `self._event_records: list[dict]`. Trong `compute_victory()`, gọi trực tiếp `from_records(self._event_records, truth_dict)` trên bộ nhớ mà không cần đọc lại từ ổ đĩa. Vẫn giữ lệnh flush ra file để phục vụ lưu trữ ván đấu.
- **Hiệu quả dự kiến**: Triệt tiêu độ trễ đọc đĩa (tiết kiệm 50-100ms khi kết thúc trận) và loại bỏ hoàn toàn nguy cơ tranh chấp file lock trên Windows (`PermissionError: [WinError 32]`).

#### Giải Pháp 2.2: Chuẩn Hóa Vòng Đời `Strategist` Protocol, Tương Thích Duck-Typing & `BaseStrategist`
- **Vị trí**: `genesis/strategy/base.py`, `genesis/tick.py`
- **Hiện trạng**:
  - `genesis/strategy/base.py` hiện tại chỉ có phương thức `decide()`. Vòng lặp mô phỏng 6 pha trong `genesis/tick.py` sử dụng `getattr(strat, "begin_tick", None)`, `getattr(strat, "take_says", None)`, `getattr(strat, "take_shift", None)`, `getattr(strat, "observe", None)`.
  - Trong các bài test adversarial hiện có (ví dụ `DuckTypedPacer` / `DuckStrategist` trong `tests/test_challenger_m3_adversarial.py`), các agent kiểm thử duck-typed chỉ triển khai duy nhất phương thức `decide()`, và có assertion bắt buộc: `assert isinstance(pacer, Strategist)`.
  - Nếu biến các phương thức vòng đời thành bắt buộc trong `@runtime_checkable class Strategist(Protocol)`, toàn bộ các bài test duck-typed sẽ gãy ngay lập tức khi kiểm tra `isinstance(agent, Strategist)`.
  - Chữ ký kiểu trả về của `take_shift`: Trong `tick.py` và `genesis/adapt.py:maybe_shift`, tham số `choice` nhận `tuple[str, str] | None` (cặp `(frm, to)` tên trait cần dịch chuyển, ví dụ `("bra", "arm")`), do đó kiểu trả về chuẩn phải là `tuple[str, str] | None` (thay vì `str | None`).
- **Giải pháp**:
  - Giữ các phương thức lifecycle là **tùy chọn (optional)** trên `Strategist(Protocol)`: Chỉ duy nhất `decide()` là phương thức trừu tượng bắt buộc trên Protocol để bảo toàn tính tương thích ngược tuyệt đối với `DuckStrategist` và các agent nhẹ:
    ```python
    @runtime_checkable
    class Strategist(Protocol):
        """Giao diện chiến lược chung cho mọi nguồn quyết định.
        
        Chỉ duy nhất `decide` là bắt buộc để hỗ trợ duck-typing trong test suite.
        Các phương thức vòng đời (lifecycle) là tuỳ chọn.
        """
        def decide(
            self,
            c: Creature,
            world: World,
            seen: list[Creature],
            rng: random.Random | None = None,
            tick_no: int = 0,
            current: ActiveGoal | None = None,
        ) -> ActiveGoal | None:
            ...

        # Các phương thức lifecycle tuỳ chọn (optional Protocol methods):
        # begin_tick(self, creatures: list[Creature], world: World, tick_no: int) -> None
        # take_says(self) -> dict[str, Say]
        # take_shift(self, c: Creature) -> tuple[str, str] | None
        # observe(self, tick_no: int, world: World, creatures: list[Creature],
        #         events: dict[str, list[dict]], state: Any) -> None
    ```
  - Cung cấp lớp nền tảng chuẩn hóa `class BaseStrategist` triển khai sẵn no-op default implementations cho toàn bộ lifecycle:
    ```python
    class BaseStrategist:
        """Lớp cơ sở cung cấp no-op default implementations cho toàn bộ lifecycle."""
        def begin_tick(self, creatures: list[Creature], world: World, tick_no: int) -> None:
            pass

        def decide(
            self,
            c: Creature,
            world: World,
            seen: list[Creature],
            rng: random.Random | None = None,
            tick_no: int = 0,
            current: ActiveGoal | None = None,
        ) -> ActiveGoal | None:
            return None

        def take_says(self) -> dict[str, Say]:
            return {}

        def take_shift(self, c: Creature) -> tuple[str, str] | None:
            return None

        def observe(
            self,
            tick_no: int,
            world: World,
            creatures: list[Creature],
            events: dict[str, list[dict]],
            state: Any,
        ) -> None:
            pass
    ```
  - Trong `genesis/tick.py`: Vòng lặp tick tiếp tục thăm dò phương thức với fallback an toàn `getattr(strat, "begin_tick", None)`, đảm bảo tương thích 100% với mọi đối tượng duck-typed mà không làm gãy runtime hoặc assertion `isinstance(agent, Strategist)`.

#### Giải Pháp 2.3: Chuẩn Hóa Cấu Hình `mypy_path`, Pytest `pythonpath` & `make typecheck`
- **Vị trí**: `pyproject.toml`, `Makefile`
- **Giải pháp**:
  - Trong `pyproject.toml`:
    - Xóa bỏ đường dẫn cục bộ `"E:/tool/mcp/terra_forge"` khỏi `mypy_path`. Cấu hình thành danh sách tương đối:
      ```toml
      mypy_path = [".", "client", "assets/flora/generators", "archive/legacy_blender_map_20260903"]
      ```
    - Bổ sung `pythonpath = ["."]` dưới mục `[tool.pytest.ini_options]` để pytest tự động nạp root module mà không cần can thiệp `sys.path`:
      ```toml
      [tool.pytest.ini_options]
      pythonpath = ["."]
      testpaths = ["tests"]
      ```
  - Trong `Makefile`: Bổ sung target `typecheck`:
    ```makefile
    .PHONY: typecheck
    typecheck:
    	@command -v mypy >/dev/null 2>&1 || { echo "mypy chưa được cài đặt: pip install mypy"; exit 1; }
    	mypy genesis net client
    ```
  - Cập nhật dòng lệnh `lock` trong `Makefile`:
    ```makefile
    lock:
    	uv pip compile pyproject.toml --all-extras --universal -o requirements.lock
    ```

---

### 3.3 Nhóm 3: Hiện Đại Hóa CI/CD & Đóng Gói Container (CI/CD & Containerization)

#### Giải Pháp 3.1: Ma Trận Kiểm Thử Tự Động 7 Giai Đoạn Trên GitHub Actions (`.github/workflows/ci.yml`)
Thay thế workflow cũ bằng đường ống đa tầng hiện đại:
1. **Stage 1: Quality Gate**: Chạy trên `ubuntu-latest`, cài nhanh qua `uv`, kiểm tra:
   - `ruff check genesis net tests scripts client tools` (gating nghiêm ngặt: 0 lỗi).
   - *Lưu ý về định dạng*: **KHÔNG** thiết lập rào cản chặn (gate) trên `ruff format --check` vì dự án có các quy chuẩn định dạng đặc thù theo ngữ cảnh (văn xuôi tiếng Việt trong docstrings, căn lề cấu trúc bảng/schema có chủ ý). Format check chỉ chạy mang tính thông tin tham khảo.
   - `mypy genesis net client`
   - `python tools/build_site.py` (biên dịch tài liệu tĩnh)
   - `python scripts/count_tests.py` (khớp số lượng test với README)
2. **Stage 2: Security & Vulnerability Scan**: Kiểm tra lỗ hổng thư viện qua `pip-audit -r requirements.txt`.
3. **Stage 3: Fast Release Contracts**: Chạy hợp đồng nhanh `python scripts/ci_quick.py` (< 60 giây).
4. **Stage 4: Matrix Testing & Coverage**: Ma trận 6 tổ hợp:
   - Hệ điều hành: `ubuntu-latest`, `windows-latest`, `macos-latest`
   - Phiên bản Python: `3.11`, `3.12`
   - Đo lường và xuất báo cáo `pytest --cov=genesis --cov=net --cov=client --cov-report=xml`.
   - Trên Windows: thiết lập biến môi trường bắt buộc `PYTHONUTF8=1` và `PYTHONIOENCODING=utf-8`.
5. **Stage 5: E2E Smoke & Hostile Anti-Abuse**:
   - Khởi chạy simulation server, chạy `ci_smoke.py` (kiểm tra `match == 1.000`).
   - Chạy kịch bản tấn công rò rỉ luật `python scripts/hostile_client.py`.
6. **Stage 6: Multi-Stage Docker Verification**: Xây dựng Docker image và kiểm tra healthcheck qua `/v1/healthz`.
7. **Stage 7: Release & Publishing**: Tự động đóng gói bánh xe phân phối wheel/sdist khi có git tag `v*`.

#### Giải Pháp 3.2: Đường Ống Kiểm Thử Cho GitLab CI (`.gitlab-ci.yml`)
Cung cấp file `.gitlab-ci.yml` độc lập phục vụ các đội ngũ triển khai trên máy chủ GitLab tự host với các stage: `lint`, `security`, `test`, `smoke`, `build`. Stage `lint` áp dụng chính sách gating nhất quán: bắt buộc vượt qua `ruff check` (0 lỗi), không gate trên `ruff format`.

#### Giải Pháp 3.3: Dockerfile Đa Tầng Bảo Mật & Phân Quyền Thư Mục (Multi-Stage Hardened Dockerfile)
- **Base image**: `python:3.11-slim-bookworm`.
- **Builder stage**: Tận dụng `astral-sh/uv` để build virtual environment tối ưu tại `/opt/venv`.
- **Runtime stage**:
  - Sao chép `/opt/venv` từ builder và bổ sung `PATH="/opt/venv/bin:$PATH"`.
  - Cài đặt `curl` phục vụ container healthcheck.
  - Tạo nhóm và người dùng không có đặc quyền root: `groupadd -g 10001 genesis && useradd -u 10001 -g genesis genesis`.
  - **Khởi tạo và phân quyền thư mục**: Tiền tạo trước các thư mục `/app/runs` và `/app/data/mesh_cache`, đồng thời phân quyền sở hữu `chown -R genesis:genesis /app/runs /app/data/mesh_cache` trước khi chuyển sang `USER genesis` (ngăn ngừa lỗi `PermissionError` khi người dùng non-root ghi log ván đấu hoặc cache mesh 3D):
    ```dockerfile
    WORKDIR /app
    RUN mkdir -p /app/runs /app/data/mesh_cache && \
        chown -R genesis:genesis /app/runs /app/data/mesh_cache
    USER genesis
    ```
  - **Khởi chạy Uvicorn**: Bind Uvicorn đến `--host 0.0.0.0 --port 8000` để dịch vụ lắng nghe trên toàn bộ giao diện mạng và có thể truy cập được từ bên ngoài container:
    ```dockerfile
    CMD ["uvicorn", "net.server:app", "--host", "0.0.0.0", "--port", "8000"]
    ```
  - Cấu hình chỉ thị kiểm tra sức khỏe tự động:
    ```dockerfile
    HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
        CMD curl -f http://localhost:8000/v1/healthz || exit 1
    ```
- **Tập tin `.dockerignore`**: Loại trừ `.git`, `.venv`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `runs/*.jsonl`, và các file nhị phân trung gian để giữ kích thước image < 250 MB.

#### Giải Pháp 3.4: File Điều Phối Đa Dịch Vụ (`docker-compose.yml`)
- **Dịch vụ `match-server`**:
  - Chạy máy chủ mô phỏng Genesis Zero và 3D Spectator tại cổng `8000:8000`.
  - **Gắn Volumes**: Lưu trữ bền vững log ván đấu và cache địa hình 3D:
    - `./runs:/app/runs`
    - `./data/mesh_cache:/app/data/mesh_cache`
  - **Biến môi trường**: Tiêm URL trỏ tới mock LLM và thiết lập mã hóa UTF-8:
    ```yaml
    environment:
      - PYTHONUTF8=1
      - PYTHONIOENCODING=utf-8
      - GENESIS_LLM_URL=http://mock-llm:8099
    ```
  - Cấu hình phụ thuộc: `depends_on: [mock-llm]`.
- **Dịch vụ `mock-llm`** (profile `testing`): Chạy máy chủ LLM giả lập (`fake_model_server.py`) tại cổng `8099` với cheat-seed 9, cho phép chạy thử nghiệm tự động khép kín mà không cần GPU thật.


---

### 3.4 Nhóm 4: Đồng Bộ Hóa Tài Liệu & Kiểm Chuẩn (Documentation & Alignment)

#### Giải Pháp 4.1: Đồng Bộ Hóa Kiểm Kê Kiểm Thử Trong `README.md`
- Chạy `python scripts/count_tests.py --update-readme` hoặc cập nhật thủ công các bảng thống kê trong `README.md`:
  - Cập nhật số lượng kiểm thử từ 1.833 lên **1.866 test cases** (1.658 unit/feature tests và 208 E2E tests trên 122 files).
  - Bổ sung huy hiệu (badges) trực quan: CI Status, Python Version (3.11 | 3.12), Code Style (Ruff), Docker Ready.
  - Bổ sung mục hướng dẫn khởi chạy Docker nhanh trong 30 giây: `docker compose up -d`.

#### Giải Pháp 4.2: Tài Liệu Kiến Trúc Toàn Diện (`docs/ARCHITECTURE.md`)
- Biên soạn `docs/ARCHITECTURE.md` với hai biểu đồ Mermaid trực quan:
  1. **System Component Topology**: Thể hiện mối quan hệ giữa Core Simulation Engine (`genesis/`), Network Server & Telemetry (`net/`), Distributed Mind Clients (`client/`), 3D Diorama Spectator (`web/`), và Procedural Artifacts (`assets/`).
  2. **6-Phase Match Tick Lifecycle**: Trình bày chi tiết luồng điều phối tuần tự qua 6 pha: Sense $\to$ Think $\to$ Act $\to$ World Physics $\to$ Rule Verification $\to$ Telemetry.

#### Giải Pháp 4.3: Nhật Ký Phiên Bản Chuẩn (`CHANGELOG.md`)
- Tạo `CHANGELOG.md` theo chuẩn Keep a Changelog và Semantic Versioning, ghi nhận các cải tiến của phiên bản `[1.1.0]` (Containerization, CI Matrix, In-Memory Scoring, Simulation Speedup) và phiên bản nền tảng `[1.0.0]`.

#### Giải Pháp 4.4: Sổ Tay Vận Hành & Triển Khai (`docs/DEPLOYMENT.md`)
- Hướng dẫn chi tiết chạy container đơn lẻ và Docker Compose.
- Cấu hình Reverse Proxy mẫu (Nginx / Caddy) hỗ trợ TLS tự động và WebSocket proxying cho endpoint `/v1/spectate`.
- Danh mục chi tiết các biến môi trường hệ thống (`PORT`, `HOST`, `PYTHONUTF8`, `GENESIS_LLM_BACKEND`, `GEMINI_API_KEYS`, `MESHY_API_KEY`).

---

## 4. Lộ Trình Triển Khai Phân Kỳ (Phased Implementation Roadmap)

Quá trình nâng cấp được chia làm 5 giai đoạn tuần tự với các cổng kiểm chuẩn độc lập:

```
[Phase 1: Khảo Sát & Kế Hoạch] (Hoàn tất)
       │
       ▼
[Phase 2: Tối Ưu Mô Phỏng & Core Refactoring] ────► [Cổng Kiểm Chuẩn 1: Determinism & Perf]
       │
       ▼
[Phase 3: Kiến Trúc, Typing & In-Memory Scoring] ──► [Cổng Kiểm Chuẩn 2: Mypy & AST Invariant]
       │
       ▼
[Phase 4: CI/CD & Đóng Gói Container] ────────────► [Cổng Kiểm Chuẩn 3: Docker Health & CI Matrix]
       │
       ▼
[Phase 5: Tài Liệu Hóa & Đồng Bộ Kiểm Kê] ────────► [Cổng Kiểm Chuẩn 4: count_tests & site.html]
       │
       ▼
[Phase 6: Kiểm Thử Độc Lập Toàn Diện] ────────────► [Bàn Giao Nghiệm Thu (Acceptance)]
```

### Chi Tiết Phân Công & Các Bước Thực Hiện:

| Giai đoạn | Nội dung công việc | File tác động chính | Tiêu chí hoàn thành (Exit Criteria) |
|---|---|---|---|
| **Phase 1** | Khảo sát tĩnh, profiling hiệu năng, lập kế hoạch nâng cấp | `upgrade_plan.md`, `DISPATCH.md` | Bản kế hoạch hoàn chỉnh, được phê duyệt. |
| **Phase 2** | Triển khai tối ưu hóa mô phỏng: đơn vòng khoảng cách (xử lý an toàn d=0), identity passability cache (is traits/kit), tile pools tĩnh, rút gọn seed RNG, greedy path trong reflex.py | `genesis/lawhook.py`, `genesis/world.py`, `genesis/creature.py`, `genesis/tick.py`, `genesis/reflex.py` | `pytest tests/test_determinism.py` pass 100%; tốc độ tăng > 1.5x; `ci_quick.py` pass. |
| **Phase 3** | Hiện đại hóa kiến trúc: In-memory scoring, Strategist protocol (optional lifecycle & duck-typing support, take_shift tuple), dọn dẹp `mypy_path` & pytest `pythonpath`, cập nhật Makefile | `genesis/score.py`, `genesis/victory.py`, `net/match.py`, `genesis/strategy/base.py`, `pyproject.toml`, `Makefile` | `mypy genesis net client` không lỗi (0 error); `test_score.py::test_khong_import_sim` pass. |
| **Phase 4** | Thiết lập CI/CD & Container: GitHub Actions (gating ruff check), GitLab CI, Dockerfile (0.0.0.0:8000, pre-create/chown runs/cache), docker-compose (mesh_cache volume, mock LLM URL) | `.github/workflows/ci.yml`, `.gitlab-ci.yml`, `Dockerfile`, `.dockerignore`, `docker-compose.yml` | File YAML hợp lệ; Docker build thành công và vượt qua healthcheck `/v1/healthz`. |
| **Phase 5** | Đồng bộ tài liệu & kiểm kê: Reconcile test count (1866), viết `ARCHITECTURE.md`, `CHANGELOG.md`, `DEPLOYMENT.md` | `README.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`, `docs/DEPLOYMENT.md`, `docs/site.html` | `python scripts/count_tests.py` exit code 0; `python tools/build_site.py` pass. |
| **Phase 6** | Thẩm định kiểm thử độc lập, rà soát hồi quy và hoàn tất nghiệm thu | Toàn bộ repo | 1.866 test cases pass (100%); linter 0 warning; smoke test `match == 1.000`. |

---

## 5. Các Cổng Kiểm Chuẩn & Tiêu Chí Nghiệm Thu (Verification Gates)

Bất kỳ thay đổi mã nguồn nào cũng phải vượt qua 8 cổng kiểm chuẩn nghiêm ngặt trước khi được coi là hoàn tất:

### Cổng 1: Fast Release Contract Gate
- **Lệnh thực thi**: `python scripts/ci_quick.py`
- **Tiêu chuẩn đạt**: Vượt qua 100% (37 tests), thời gian thực thi < 60 giây (mục tiêu: < 3.0 giây).

### Cổng 2: Code Quality & Static Linting Gate
- **Lệnh thực thi**: `ruff check genesis net tests scripts client tools`
- **Tiêu chuẩn đạt**: 0 lỗi, 0 cảnh báo (exit code 0).
- **Chính sách định dạng**: Gating chỉ áp dụng nghiêm ngặt cho `ruff check` (0 lỗi). Tuyệt đối **không gate** trên `ruff format --check` để bảo toàn định dạng tiếng Việt trong docstrings và các cấu trúc dữ liệu đặc thù của dự án.

### Cổng 3: Static Type Integrity Gate
- **Lệnh thực thi**: `mypy genesis net client`
- **Tiêu chuẩn đạt**: `Success: no issues found in 76 source files` (exit code 0), không còn đường dẫn tuyệt đối Windows trong `pyproject.toml`.

### Cổng 4: Test Discovery & Inventory Synchronization Gate
- **Lệnh thực thi**: `python scripts/count_tests.py`
- **Tiêu chuẩn đạt**: Khớp chính xác 1.866 test cases trên 122 files giữa mã nguồn và bảng kê trong `README.md` (exit code 0).

### Cổng 5: Determinism Invariant Gate (B-02)
- **Lệnh thực thi**: `pytest tests/test_determinism.py tests/test_tick.py`
- **Tiêu chuẩn đạt**: Tất cả các bước di chuyển, biến đổi năng lượng và kết quả ván đấu tái lập chính xác 100% từng bit so với seed gốc.

### Cổng 6: Scoring Isolation Invariant Gate (B-10)
- **Lệnh thực thi**: `pytest tests/test_score.py::test_khong_import_sim`
- **Tiêu chuẩn đạt**: Xác nhận bằng kiểm tra cây cú pháp trừu tượng (AST) rằng `genesis/score.py` và `genesis/victory.py` không import `world.py` hay `tick.py`.

### Cổng 7: End-to-End Simulation & Golden Referee Gate
- **Lệnh thực thi**: `python scripts/ci_smoke.py`
- **Tiêu chuẩn đạt**: Khởi động fake model server trên cổng 8099, chạy 120 ticks mô phỏng, chấm điểm đạt kết quả hoàn hảo `match = 1.000` (exit code 0).

### Cổng 8: Full Regression Suite Gate
- **Lệnh thực thi**: `pytest -q`
- **Tiêu chuẩn đạt**: 1.679 passed, 0 failed, 0 errors, 39 skipped (các test skip có lý do hợp lệ về môi trường headless Blender hoặc kiểm thử phần cứng chuyên biệt). Tỷ lệ bao phủ code `pytest --cov` đạt $\ge 90.0\%$.

---

## 6. Kế Hoạch Ứng Phó Rủi Ro & Rollback (Contingency & Rollback Strategy)

1. **Rủi ro phá vỡ tính tất định (Determinism Regression)**:
   - *Nguyên nhân*: Thứ tự duyệt tập hợp ô hoặc thứ tự sinh số ngẫu nhiên bị thay đổi trong các hàm tối ưu hóa.
   - *Biện pháp kiểm soát*: Chạy `test_determinism.py` ngay sau từng chỉnh sửa vi mô. Mọi cấu trúc dữ liệu ứng viên ô đều sử dụng `tuple` có thứ tự cố định `(x, y)` theo thứ tự quét hàng-cột nguyên bản.
2. **Rủi ro không tương thích phiên bản Starlette/FastAPI TestClient**:
   - *Nguyên nhân*: Cảnh báo deprecation từ `httpx` đối với `Starlette.TestClient`.
   - *Biện pháp kiểm soát*: Không nâng cấp cưỡng bức các gói thư viện chưa được kiểm chứng trong lockfile; giữ nguyên cấu hình warnings đã lọc.
3. **Chiến lược Rollback**:
   - Toàn bộ các thay đổi được chia nhỏ theo từng atomic commit tương ứng với từng Phase. Nếu phát sinh lỗi không thể khắc phục tại bất kỳ cổng kiểm chuẩn nào, hoàn tác (git checkout/revert) về commit ổn định gần nhất của Phase trước đó.

---
*Kế hoạch được lập và xác nhận bởi Worker M1 — Teamwork Preview.*
