"""Genesis Zero — lựa chọn brain của người chơi qua mạng phải SỐNG QUA CÁI CHẾT."""

from __future__ import annotations

import random

import pytest
from fastapi.testclient import TestClient

from genesis import config
from genesis.adapt import reset_body
from genesis.creature import Creature
from genesis.traits import (
    clear_dynamic_founders,
    founder_traits,
    register_founder,
)
from net import server, state
from net.match import MatchRunner
from net.routes_join import allocate_traits, clear_rate_limits


@pytest.fixture(autouse=True)
def _sach():
    clear_dynamic_founders()
    clear_rate_limits()
    yield
    clear_dynamic_founders()
    clear_rate_limits()


@pytest.fixture
def client(monkeypatch):
    r = MatchRunner(seed=1, ticks=5, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def _con(species: str, traits):
    return Creature(id=f"{species}:0", species=species, traits=traits,
                    pos=(1, 1), hp=1.0, energy=1.0)


@pytest.mark.parametrize("brain", [0, 1, 2, 3, 4, 5])
def test_chet_khong_xoa_lua_chon_brain(brain):
    """Người chơi trả `brain` điểm lúc `/join`; chết rồi vẫn phải còn `brain`.

    Bản cũ: `founder_traits` chỉ tra `config.FOUNDERS` (năm loài dựng sẵn), nên
    loài đăng ký lúc chạy rơi về vector chia đều 2/2/2/2/2/2. Một người chọn
    brain 5 nhận brain 5 lúc vào rồi **tụt về 2 sau cái chết đầu tiên** — không
    lỗi, không log, mà một ván 200 tick có tới 64 lượt chết.

    Brain quyết định từ vựng Sổ Luật (`ADJACENT`/`PHASE_ENTER` chỉ có từ brain
    4), số ô sổ, và ngân sách token. Nên mất nó là mất đúng thứ người chơi bỏ
    điểm ra mua — và mệnh đề trung tâm "model to hơn thành loài đỉnh" không đo
    được nữa vì mọi loài hội tụ về cùng một vector.
    """
    sp = f"sp_thu{brain}"
    t = allocate_traits(brain, random.Random(7))
    register_founder(sp, t)
    c = _con(sp, t)
    reset_body(c)
    assert c.traits.brain == brain
    assert c.traits == t


def test_khong_dang_ky_thi_van_co_cuu_canh_nhung_khac_han():
    """Loài lạ chưa đăng ký vẫn trả vector chia đều — và nó KHÁC vector thật.

    Bài test này ghim chính khoảng cách gây ra lỗi: nếu ai đó bỏ
    `register_founder` khỏi `/v1/join`, `test_chet_khong_xoa_lua_chon_brain`
    đỏ ngay chứ không âm thầm đúng.
    """
    t = allocate_traits(5, random.Random(7))
    mac_dinh = founder_traits("sp_chua_dang_ky")
    assert mac_dinh.brain == config.TRAIT_SUM // len(config.TRAIT_NAMES)
    assert mac_dinh != t


def test_loai_dung_san_khong_bi_so_dong_de_len():
    """`config.FOUNDERS` phải THẮNG sổ động — không ai ghi đè được L1..L5."""
    that = founder_traits("L1")
    register_founder("L1", allocate_traits(0, random.Random(1)))
    assert founder_traits("L1") == that


def test_join_that_su_ghi_so(client):
    """Đi qua HTTP thật: `/v1/join` phải để lại vector trong sổ động."""
    c, _r = client
    resp = c.post("/v1/join",
                  json={"display_name": "Não To", "brain_tier": 5, "pop_request": 1})
    assert resp.status_code == 200
    body = resp.json()
    sp = body["species_id"]
    cap = body["traits"]
    ghi = founder_traits(sp)
    assert ghi.brain == 5 == cap["brain"]
    from genesis.traits import Traits

    assert ghi == Traits(**cap)
