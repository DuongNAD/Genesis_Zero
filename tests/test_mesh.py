"""Kiểm thử mesh 3D từ vector trait và cache (N-13).

Tám ca kiểm thử theo yêu cầu:
1. mesh_key KHÔNG đổi khi client_id/species_id/display_name đổi mà trait giữ nguyên;
2. mesh_key ĐỔI khi dịch một điểm từ trait này sang trait khác;
3. body_prompt chứa nguyên văn kết quả của genesis.prompt.body_line(traits),
   và KHÔNG chứa display_name/persona nào được truyền vào ở bất kỳ đâu;
4. ensure_mesh lúc cache rỗng trả None trong dưới 50 ms (đo bằng time.perf_counter);
5. ensure_mesh lúc cache có trả đúng url và KHÔNG gọi transport lần nào;
6. quota vượt -> ensure_mesh trả None, không ném;
7. generate_mesh gặp HTTP 500 -> trả None, không ném;
8. mesh KHÔNG chạm sim: đọc genesis/world.py, genesis/logio.py, genesis/tick.py
   bằng ast/đọc file và khẳng định chuỗi "mesh" không xuất hiện.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import time
from pathlib import Path

import httpx
import pytest

from genesis.prompt import body_line
from genesis.traits import Traits
from net.mesh import MeshCache, body_prompt, ensure_mesh, generate_mesh, mesh_key


def test_1_mesh_key_khong_doi_khi_metadata_doi():
    """1. mesh_key KHÔNG đổi khi client_id/species_id/display_name đổi mà trait giữ nguyên."""
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    k1 = mesh_key(tr)
    k2 = mesh_key(tr)
    assert k1 == k2

    # Danh sách CHO PHÉP, không phải danh sách cấm — cấm thì mỗi tên mới lại
    # lọt qua. Cả ba đều là thứ SERVER bốc thăm tất định theo `(loài, seed)`:
    # `domain` là tầng (W-18), `features` là ba đặc điểm (W-19). Không cái nào
    # do client gõ ra được, và đó mới là điều bất biến này bảo vệ.
    #
    # Vì sao chúng PHẢI có mặt: sau W-18/W-19 ngoại hình không còn là hàm của
    # riêng vector trait. Khoá chỉ-theo-trait làm một con cá dùng chung mesh với
    # một con bốn chân cùng chỉ số — tức là hình 3D nói dối, đúng thứ W-19 dựng
    # lên để chặn.
    sig = inspect.signature(mesh_key)
    cho_phep = {"traits", "domain", "features"}
    cam = {"client_id", "species_id", "display_name", "persona", "name", "token"}
    assert set(sig.parameters) <= cho_phep, set(sig.parameters) - cho_phep
    assert not (set(sig.parameters) & cam)

    # Hai đối tượng Traits có cùng giá trị luôn sinh cùng một khoá
    tr_clone = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    assert mesh_key(tr) == mesh_key(tr_clone)


def test_2_mesh_key_doi_khi_dich_mot_diem():
    """2. mesh_key ĐỔI khi dịch một điểm từ trait này sang trait khác."""
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    k_orig = mesh_key(tr)

    tr_shift1 = tr.shift("brain", "attack")
    k_shift1 = mesh_key(tr_shift1)
    assert k_shift1 != k_orig

    tr_shift2 = tr.shift("speed", "armor")
    k_shift2 = mesh_key(tr_shift2)
    assert k_shift2 != k_orig
    assert k_shift1 != k_shift2


def test_3_body_prompt_chua_body_line_va_khong_chua_metadata():
    """3. body_prompt chứa nguyên văn kết quả của genesis.prompt.body_line(traits),
    và KHÔNG chứa display_name/persona nào được truyền vào ở bất kỳ đâu.
    """
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    expected_line = body_line(tr)
    prompt = body_prompt(tr)

    assert expected_line in prompt

    sig = inspect.signature(body_prompt)
    cho_phep = {"traits", "domain", "features"}
    cam = {"client_id", "species_id", "display_name", "persona", "name", "token"}
    assert set(sig.parameters) <= cho_phep, set(sig.parameters) - cho_phep
    assert not (set(sig.parameters) & cam)

    # Thử với nhiều vector trait khác nhau
    tr2 = Traits(brain=0, attack=2, armor=0, speed=5, sense=3, stomach=2)
    assert body_line(tr2) in body_prompt(tr2)


@pytest.mark.asyncio
async def test_4_ensure_mesh_cache_rong_tra_none_duoi_50ms(tmp_path: Path):
    """4. ensure_mesh lúc cache rỗng trả None trong dưới 50 ms (đo bằng time.perf_counter)."""
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=10, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    # Transport giả lập mất nhiều thời gian nếu bị gọi nhầm đồng bộ
    async def slow_handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.3)
        return httpx.Response(200, json={"model_url": "https://assets.meshy.ai/model.glb"})

    transport = httpx.MockTransport(slow_handler)

    t0 = time.perf_counter()
    result = await ensure_mesh(tr, cache, "client_1", transport=transport)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert result is None
    assert elapsed_ms < 50.0, f"ensure_mesh mất {elapsed_ms:.2f} ms (vượt trần 50 ms)"


@pytest.mark.asyncio
async def test_5_ensure_mesh_cache_hit_tra_url_khong_goi_transport(tmp_path: Path):
    """5. ensure_mesh lúc cache có trả đúng url và KHÔNG gọi transport lần nào."""
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=10, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    key = mesh_key(tr)
    expected_url = "https://assets.meshy.ai/cached_model_123.glb"
    cache.put(key, expected_url)

    called: list[httpx.Request] = []

    def bomb_handler(request: httpx.Request) -> httpx.Response:
        called.append(request)
        raise AssertionError("Transport KHÔNG được gọi khi cache hit!")

    transport = httpx.MockTransport(bomb_handler)

    result = await ensure_mesh(tr, cache, "client_1", transport=transport)
    assert result == expected_url
    assert len(called) == 0


@pytest.mark.asyncio
async def test_6_quota_vuot_ensure_mesh_tra_none_khong_nem(tmp_path: Path):
    """6. quota vượt -> ensure_mesh trả None, không ném."""
    # per_client = 2, global = 3
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=2, global_per_day=3)
    tr1 = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    tr2 = tr1.shift("brain", "attack")
    tr3 = tr2.shift("brain", "attack")
    tr4 = tr3.shift("speed", "armor")

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"model_url": "https://assets.meshy.ai/model.glb"})

    transport = httpx.MockTransport(mock_handler)

    # Client 1 gọi lần 1 -> cho phép
    assert await ensure_mesh(tr1, cache, "client_1", transport=transport) is None
    # Client 1 gọi lần 2 -> cho phép
    assert await ensure_mesh(tr2, cache, "client_1", transport=transport) is None
    # Client 1 gọi lần 3 -> VƯỢT QUOTA client (tối đa 2) -> trả None, không ném
    assert await ensure_mesh(tr3, cache, "client_1", transport=transport) is None

    # Client 2 gọi lần 1 (toàn cục lần 3) -> cho phép
    assert await ensure_mesh(tr3, cache, "client_2", transport=transport) is None
    # Client 3 gọi lần 1 (toàn cục lần 4) -> VƯỢT QUOTA toàn cục (tối đa 3) -> trả None, không ném
    assert await ensure_mesh(tr4, cache, "client_3", transport=transport) is None

    # Cache hit KHÔNG tính vào quota: client 1 vẫn lấy được mesh đã có trong cache
    cache.put(mesh_key(tr4), "https://assets.meshy.ai/already_cached.glb")
    hit_result = await ensure_mesh(tr4, cache, "client_1", transport=transport)
    assert hit_result == "https://assets.meshy.ai/already_cached.glb"


@pytest.mark.asyncio
async def test_7_generate_mesh_http_500_tra_none_khong_nem(tmp_path: Path):
    """7. generate_mesh gặp HTTP 500 -> trả None, không ném."""
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=10, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Meshy 500 Internal Server Error")

    transport = httpx.MockTransport(error_handler)
    result = await generate_mesh(tr, cache, transport=transport)
    assert result is None


def test_8_mesh_khong_cham_sim():
    """8. mesh KHÔNG chạm sim: đọc genesis/world.py, genesis/logio.py, genesis/tick.py
    bằng ast/đọc file và khẳng định chuỗi "mesh" không xuất hiện.
    """
    repo_root = Path(__file__).resolve().parent.parent
    sim_files = [
        repo_root / "genesis" / "world.py",
        repo_root / "genesis" / "logio.py",
        repo_root / "genesis" / "tick.py",
    ]

    for fpath in sim_files:
        assert fpath.exists(), f"Không tìm thấy file {fpath}"
        content = fpath.read_text(encoding="utf-8")

        # Kiểm tra chuỗi "mesh" (không phân biệt hoa thường)
        assert "mesh" not in content.lower(), (
            f"Phát hiện chuỗi 'mesh' xuất hiện trong {fpath.name}!"
        )

        # Kiểm tra AST để đảm bảo không có định danh/import liên quan đến mesh
        tree = ast.parse(content, filename=str(fpath))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Name, ast.Attribute)):
                name = getattr(node, "id", None) or getattr(node, "attr", None)
                if name:
                    assert "mesh" not in name.lower(), (
                        f"Phát hiện AST identifier {name!r} chứa 'mesh' trong {fpath.name}!"
                    )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert "mesh" not in node.module.lower(), (
                        f"Phát hiện import từ module chứa 'mesh' trong {fpath.name}!"
                    )
                for alias in node.names:
                    assert "mesh" not in alias.name.lower(), (
                        f"Phát hiện import tên {alias.name!r} chứa 'mesh' trong {fpath.name}!"
                    )


@pytest.mark.asyncio
async def test_9_quota_dem_luot_sinh_khong_dem_luot_hoi(tmp_path: Path):
    """Quota phải đếm LƯỢT SINH, không đếm lượt hỏi.

    Bản đầu tiêu quota trước rồi mới xét in-flight: hỏi ba lần về CÙNG một vector
    trait ăn ba suất trong khi chỉ sinh một mesh. Ở luồng thật `/join` gọi mỗi lần
    vào và trang xem thì poll, nên một người chơi có một cơ thể đốt sạch quota
    ngày mà không tạo thêm được cái mesh nào.
    """
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=3, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    async def never(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.01)
        return httpx.Response(200, json={"model_url": "u"})

    transport = httpx.MockTransport(never)
    for _ in range(3):
        assert await ensure_mesh(tr, cache, "c1", transport=transport) is None
    assert cache.allow("c1", time.time(), record=False), (
        "ba lần hỏi về cùng một cơ thể đã ăn hết quota — quota đang đếm nhầm thứ"
    )


@pytest.mark.asyncio
async def test_10_quota_song_qua_khoi_dong_lai(tmp_path: Path):
    """Đếm trong RAM thôi thì trần chi phí toàn cục biến mất mỗi lần deploy."""
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)
    transport = httpx.MockTransport(
        lambda r: httpx.Response(200, json={"model_url": "u"})
    )
    c1 = MeshCache(cache_dir=tmp_path, per_client_per_day=1, global_per_day=100)
    assert await ensure_mesh(tr, c1, "c1", transport=transport) is None
    assert not c1.allow("c1", time.time(), record=False)

    c2 = MeshCache(cache_dir=tmp_path, per_client_per_day=1, global_per_day=100)
    assert not c2.allow("c1", time.time(), record=False), "quota reset sau khởi động lại"


def test_11_khong_dung_bien_toan_cuc_cap_module():
    """Trạng thái sinh nền phải gắn với cache, không phải với module."""
    import net.mesh as m
    assert not hasattr(m, "_in_flight"), "biến toàn cục cấp module rò trạng thái giữa các test"


def test_mesh_key_PHAI_doi_khi_tang_hoac_dac_diem_doi():
    """Hồi quy W-19: khoá đệm chỉ-theo-trait làm hình 3D NÓI DỐI.

    Sau W-18/W-19 ngoại hình là hàm của (trait, tầng, ba đặc điểm). Khoá cũ chỉ
    băm sáu trait, nên hai con cùng chỉ số nhưng khác đặc điểm — thậm chí khác
    TẦNG — dùng chung một mesh: con cá nhận thân bốn chân, con lưỡng cư mất chân
    màng.

    Đó là W-19 hỏng theo chiều ngược lại. Phiếu ấy dựng lên để hình dáng không
    nói dối về cơ chế; một khoá đệm quá thô làm nó nói dối mà không ai thấy, vì
    đệm trúng thì trông y như đệm đúng.
    """
    from genesis.features import roll_for_species
    from genesis.traits import founder_traits

    tr = founder_traits("L1")
    goc = mesh_key(tr, "CAN", roll_for_species("L1", 21))
    assert goc != mesh_key(tr, "NUOC", roll_for_species("L1", 21)), "khác TẦNG mà cùng khoá"
    assert goc != mesh_key(tr, "CAN", roll_for_species("L2", 21)), "khác ĐẶC ĐIỂM mà cùng khoá"
    # và vẫn tất định
    assert goc == mesh_key(tr, "CAN", roll_for_species("L1", 21))


def test_mo_ta_3D_mang_dung_tang_cua_con_vat():
    """Cá phải được tả là có VÂY, không phải bốn chân."""
    from genesis.features import roll_for_species
    from genesis.traits import founder_traits

    ca = body_prompt(founder_traits("W1"), "NUOC", roll_for_species("W1", 21))
    chim = body_prompt(founder_traits("A1"), "TROI", roll_for_species("A1", 21))
    assert "vây" in ca and "không có chân" in ca, ca[:120]
    assert "cánh" in chim, chim[:120]


@pytest.mark.asyncio
async def test_generate_mesh_missing_task_id(tmp_path: Path):
    """Initial call returns JSON without task_id or model_url -> returns None."""
    from net.mesh import MeshCache, generate_mesh

    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=3, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={"foo": "bar"}))
    res = await generate_mesh(tr, cache, transport=transport)
    assert res is None


@pytest.mark.asyncio
async def test_generate_mesh_poll_http_error(tmp_path: Path, monkeypatch):
    """Poll returns non-200 HTTP error -> returns None."""
    import net_config
    from net.mesh import MeshCache, generate_mesh

    monkeypatch.setattr(net_config, "MESHY_POLL_INTERVAL", 0.001)
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=3, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"result": "task_abc"})
        return httpx.Response(500, text="Poll error")

    transport = httpx.MockTransport(handler)
    res = await generate_mesh(tr, cache, transport=transport)
    assert res is None
    assert calls >= 2


@pytest.mark.asyncio
async def test_generate_mesh_poll_success_missing_model_url(tmp_path: Path, monkeypatch):
    """Task succeeded but model_url is missing -> returns None."""
    import net_config
    from net.mesh import MeshCache, generate_mesh

    monkeypatch.setattr(net_config, "MESHY_POLL_INTERVAL", 0.001)
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=3, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"result": "task_xyz"})
        return httpx.Response(200, json={"status": "SUCCEEDED"})

    transport = httpx.MockTransport(handler)
    res = await generate_mesh(tr, cache, transport=transport)
    assert res is None
    assert calls >= 2


@pytest.mark.asyncio
async def test_generate_mesh_poll_failed_status(tmp_path: Path, monkeypatch):
    """Task status is FAILED -> returns None."""
    import net_config
    from net.mesh import MeshCache, generate_mesh

    monkeypatch.setattr(net_config, "MESHY_POLL_INTERVAL", 0.001)
    cache = MeshCache(cache_dir=tmp_path, per_client_per_day=3, global_per_day=100)
    tr = Traits(brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1)

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"result": "task_failed"})
        return httpx.Response(200, json={"status": "FAILED", "task_error": "out of memory"})

    transport = httpx.MockTransport(handler)
    res = await generate_mesh(tr, cache, transport=transport)
    assert res is None
    assert calls >= 2

