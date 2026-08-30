"""Genesis Zero — tests/test_domain: ba tầng nước · cạn · trời (W-18 chặng A)."""

from __future__ import annotations

import collections
import random

import pytest

from genesis import config
from genesis.creature import Creature
from genesis.domain import Domain, can_enter, can_touch, domain_of
from genesis.tick import build_match
from genesis.traits import founder_traits
from genesis.world import CARDINAL_OFFSETS, SEEDED_TERRAINS, Terrain, World

MAPS = ("DONG_CO", "RUNG_RAM", "QUAN_DAO", "HOANG_MAC", "HEM_NUI")


def _make(sp: str) -> Creature:
    return Creature(id=f"{sp}:0", species=sp, traits=founder_traits(sp),
                    pos=(0, 0), hp=1.0, energy=1.0)


# ── "sư tử không trèo được cây, khỉ thì được" ───────────────────────────────

def test_treo_cay_doc_TRAIT_khong_doc_TEN_LOAI():
    """Không hard-code loài nào. Ngưỡng đọc thẳng từ vector trait.

    Hệ quả quan trọng hơn cả ca này: một dòng dõi **học được cách trèo** bằng
    cách dịch trait sang `speed` (B-13). Bản sắc tầng thì cố định, còn đường đi
    trong tầng thì kiếm được — nửa hay của tiến hoá mà không dính nửa dở (hội tụ).
    """
    khi = _make("L5")      # speed 5
    su_tu = _make("L2")    # speed 1, attack 4
    assert can_enter(Domain.CAN, Terrain.TREE, khi.traits) is True
    assert can_enter(Domain.CAN, Terrain.TREE, su_tu.traits) is False

    # và nó thật sự chia đàn làm hai nhóm CÓ THẬT với FOUNDERS hiện tại
    treo = {sp for sp in config.FOUNDERS
            if can_enter(Domain.CAN, Terrain.TREE, founder_traits(sp))}
    assert treo and treo != set(config.FOUNDERS), (
        f"ngưỡng CLIMB_SPEED={config.CLIMB_SPEED} không chia được đàn: {treo}")


def test_lua_doc_ARMOR():
    lua = {sp for sp in config.FOUNDERS
           if can_enter(Domain.CAN, Terrain.FIRE, founder_traits(sp))}
    assert lua and lua != set(config.FOUNDERS), lua


def test_nuoc_sau_chan_moi_sinh_vat_can():
    for sp in config.FOUNDERS:
        assert can_enter(Domain.CAN, Terrain.DEEP, founder_traits(sp)) is False


def test_ca_khong_len_bo_duoc():
    for t in (Terrain.PLAIN, Terrain.BUSH, Terrain.ROCK, Terrain.TREE, Terrain.FIRE):
        assert can_enter(Domain.NUOC, t, None) is False
    for t in (Terrain.WATER, Terrain.DEEP):
        assert can_enter(Domain.NUOC, t, None) is True


# ── trời: bay khắp nơi, nhưng phải hạ xuống mới chạm ────────────────────────

def test_troi_bay_khap_noi_nhung_khong_cham_khap_noi():
    """W-18 bất biến 3 — và nếu thiếu nó thì tầng trời trội tuyệt đối.

    Làm chim là *đi lại tự do đổi lấy tiếp xúc kém*, không phải "mạnh hơn ở mọi
    mặt". Bỏ ràng buộc này thì hai tầng kia thành trang trí.
    """
    for t in Terrain:
        assert can_enter(Domain.TROI, t, None) is True
    assert can_touch(Domain.TROI, Terrain.ROCK, None) is False
    assert can_touch(Domain.TROI, Terrain.PLAIN, None) is True
    assert can_touch(Domain.TROI, Terrain.WATER, None) is True
    # Chim ĐẬU CÀNH được — đó là chỗ tầng TRỜI gặp tầng CẠN biết trèo.
    assert can_touch(Domain.TROI, Terrain.TREE, None) is True
    # Nhưng KHÔNG kiếm ăn được ngoài khơi. Nên cá ở nước sâu an toàn trước chim,
    # còn cá vào nước nông thì không — mà nước nông vốn đã là chỗ duy nhất tầng
    # CẠN với tầng NƯỚC gặp nhau. Cả ba tầng dồn về một vành đai hẹp.
    assert can_touch(Domain.TROI, Terrain.DEEP, None) is False


def test_tang_cua_loai_la_mac_dinh_la_CAN():
    """Người chơi qua mạng đăng ký loài lúc chạy — không được ném."""
    assert domain_of("khong_co_trong_config") is Domain.CAN


# ── bản đồ: bờ nước là bất biến, không phải may mắn ─────────────────────────

@pytest.mark.parametrize("map_name", MAPS)
def test_moi_vung_nuoc_sau_deu_con_vien_NUOC_NONG(map_name):
    """Bờ nước là ô DUY NHẤT mà tầng NƯỚC và tầng CẠN đứng cạnh nhau được.

    Mất bờ thì ba tầng thành ba ván chạy song song, và ta vừa chia một ván thành
    ba ván nhỏ hơn và nghèo hơn (W-18 §7). Bất biến này được giữ bằng **cấu
    trúc**: `erode_cores` chỉ biến một ô thành DEEP khi bốn phía là nước, nên
    vành ngoài của mọi vùng nước không bao giờ thành DEEP.
    """
    for seed in range(1, 13):
        w, _, _, _ = build_match(seed, map_name=map_name)
        deep = [(x, y) for y in range(w.h) for x in range(w.w)
                if w.grid[y][x] == Terrain.DEEP]
        if not deep:
            continue
        assert any(
            w.grid[w.wrap(x + dx, y + dy)[1]][w.wrap(x + dx, y + dy)[0]] == Terrain.WATER
            for x, y in deep for dx, dy in CARDINAL_OFFSETS
        ), f"{map_name} seed {seed}: vùng nước sâu không có bờ"


def test_ao_ho_bien_sinh_ra_tu_CACH_XEP_khong_tu_enum_moi():
    """Ba kiểu nước của đề bài, không thêm loại địa hình nào.

    `QUAN_DAO` (10 hạt nước) phải ra biển thật — nhiều DEEP; `HOANG_MAC` (1 hạt)
    gần như chỉ có ao, không đủ lớn để có lõi sâu.
    """
    deep = {}
    for name in ("QUAN_DAO", "HOANG_MAC"):
        tot = 0
        for seed in range(1, 9):
            w, _, _, _ = build_match(seed, map_name=name)
            tot += sum(1 for row in w.grid for t in row if t == Terrain.DEEP)
        deep[name] = tot
    assert deep["QUAN_DAO"] > 4 * max(1, deep["HOANG_MAC"]), deep


def test_sa_mac_khong_co_cay_rung_ram_thi_nhieu():
    tree = {}
    for name in ("RUNG_RAM", "HOANG_MAC"):
        w, _, _, _ = build_match(7, map_name=name)
        tree[name] = sum(1 for row in w.grid for t in row if t == Terrain.TREE)
    assert tree["HOANG_MAC"] == 0, tree
    assert tree["RUNG_RAM"] > 20, tree


# ── canh chừng: đừng để mọc lại bảng thứ hai ────────────────────────────────

def test_khong_co_bang_dia_hinh_chep_tay_thu_hai():
    """Bài canh chừng. Trong ĐÚNG một lượt sửa, W-18 đã đâm vào bốn bản chép tay
    của cùng khái niệm "danh sách địa hình": bộ dựng lưới thứ hai ở `maps.py`,
    chuỗi `"PWBRF"` ở `net/match.py`, bảng mô tả 3D ở `mesh_prompts.py`, và
    tuple thứ tự gieo hạt. Mỗi cái hỏng một kiểu khác nhau, và không cái nào báo.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for rel in ("net/match.py", "genesis/maps.py"):
        src = (root / rel).read_text(encoding="utf-8")
        # Bỏ dòng chú thích trước khi soi: chính chú thích giải thích lỗi cũ có
        # nhắc tới chuỗi ấy, và một bài canh chừng bắt nhầm lời kể về con bọ
        # thay vì con bọ là một bài canh chừng vô dụng.
        code = "\n".join(ln for ln in src.splitlines()
                          if not ln.lstrip().startswith("#"))
        assert '"PWBRF"' not in code, f"{rel}: mã địa hình chép tay"

    from genesis.mesh_prompts import _TERRAIN
    from genesis.world import TERRAIN_CODE

    assert set(TERRAIN_CODE) == set(Terrain), "TERRAIN_CODE thiếu địa hình"
    assert len(set(TERRAIN_CODE.values())) == len(Terrain), "mã trùng nhau"
    assert set(_TERRAIN) == set(Terrain), "mesh_prompts thiếu địa hình"
    assert set(SEEDED_TERRAINS) <= set(Terrain)


def test_passable_la_duong_DUY_NHAT():
    """Bất biến 2: `reflex` không được tự quyết ai đi được đâu."""
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "genesis" / "reflex.py").read_text(
        encoding="utf-8")
    for line in src.splitlines():
        if "world.passable(" in line:
            assert "who" in line or ", c)" in line, (
                f"gọi passable mà không nói CON NÀO: {line.strip()}")
