"""Kiểm thử nhiều bản đồ (W-15)."""

from __future__ import annotations

import random
import statistics

import pytest

from genesis import config
from genesis.maps import DEFAULT_MAP, MAPS, generate_terrain, terrain_mix
from genesis.tick import build_match, tick
from genesis.world import Terrain


def test_ban_do_mac_dinh_KHONG_doi_the_gioi_cu():
    """Mọi số đo cân bằng của W-12 dựa trên bộ sinh cũ. Bản đồ mới không được
    đụng vào nó — nếu không, mọi con số trong tài liệu thành sai mà không ai biết."""
    a = build_match(7)[0]
    b = build_match(7, map_name=None)[0]
    assert a.grid == b.grid
    assert a.map_name == DEFAULT_MAP


def test_moi_ban_do_that_su_khac_nhau():
    mixes = {}
    for name, spec in MAPS.items():
        ms = [terrain_mix(generate_terrain(spec, config.GRID_W, config.GRID_H,
                                           random.Random(s))) for s in range(12)]
        mixes[name] = {k: statistics.fmean(m[k] for m in ms) for k in ms[0]}

    # Hai bản đồ bất kỳ phải lệch nhau ít nhất 5 điểm phần trăm ở một loại ô nào đó
    names = sorted(mixes)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            diff = max(abs(mixes[a][k] - mixes[b][k]) for k in mixes[a])
            assert diff > 0.05, f"{a} và {b} gần như giống nhau ({diff:.3f})"

    # và mỗi bản đồ phải đúng với cái tên của nó
    assert mixes["HOANG_MAC"]["WATER"] < mixes["DONG_CO"]["WATER"] / 2, "sa mạc mà nhiều nước"
    assert mixes["QUAN_DAO"]["WATER"] > mixes["DONG_CO"]["WATER"] * 2, "quần đảo mà ít nước"
    assert mixes["RUNG_RAM"]["BUSH"] > mixes["DONG_CO"]["BUSH"] * 2, "rừng mà ít bụi"
    assert mixes["HEM_NUI"]["ROCK"] > mixes["DONG_CO"]["ROCK"] * 2, "hẻm núi mà ít đá"


def test_khong_ban_do_nao_sinh_lua():
    """`FIRE_BASE_SPREAD = False`: lửa chỉ xuất hiện qua luật SPREAD (W-13).
    Sinh sẵn ô lửa trơ vừa vô nghĩa vừa ăn mất ô PLAIN."""
    for name, spec in MAPS.items():
        for seed in range(6):
            g = generate_terrain(spec, config.GRID_W, config.GRID_H, random.Random(seed))
            assert terrain_mix(g)[Terrain.FIRE.value] == 0.0, name


def test_ban_do_nao_cung_di_lai_duoc():
    """Một bản đồ bịt kín là một bản đồ không chơi được — và nó sẽ hỏng lặng lẽ:
    `spawn_population` ném, hoặc tệ hơn, sinh vật kẹt cả ván."""
    for name in MAPS:
        for seed in (1, 2, 3):
            world, creatures, _, _ = build_match(seed, map_name=name)
            passable = sum(1 for y in range(world.h) for x in range(world.w)
                           if world.passable((x, y)))
            assert passable > world.w * world.h * 0.4, f"{name} bịt quá kín"
            # Quần thể CO THEO bản đồ (W-18 chặng B): `HOANG_MAC` chỉ có ~19
            # ô nước nên nó nuôi 1 con cá thay vì 3. Bất biến là "không vượt quá
            # cấu hình", không phải "bằng đúng cấu hình".
            assert 0 < len(creatures) <= sum(config.POPULATION.values())
            # Và bất biến QUAN TRỌNG hơn: mọi con ra đời ở ô mà CHÍNH NÓ đi
            # được. Bản cũ hỏi `passable` không truyền con vật nên nó thả cá lên
            # đồng cỏ — con cá ấy không đi nổi một bước, không ăn được gì, chết
            # ở đúng chỗ nó sinh ra.
            for c in creatures:
                assert world.passable(c.pos, c), (
                    f"{name}: {c.id} ({c.species}) ra đời ở ô nó không vào được")


def test_ban_do_van_tat_dinh():
    for name in MAPS:
        assert build_match(5, map_name=name)[0].grid == build_match(5, map_name=name)[0].grid


def test_ban_do_doi_do_kho_va_ta_ghi_so_do_ra():
    """Không ép mọi bản đồ về cùng một con số — nhưng phải BIẾT chúng khác nhau
    thế nào, và số đo phải nằm trong tài liệu chứ không trong đầu ai đó."""
    src = __import__("pathlib").Path("genesis/maps.py").read_text(encoding="utf-8")
    for name in MAPS:
        assert name in src.split("Cân bằng đo được")[1], f"{name} thiếu trong bảng cân bằng"
    assert "M1 là tính chất của ĐỒNG CỎ" in src


def test_ban_do_la_thi_bao_loi():
    with pytest.raises(KeyError):
        build_match(1, map_name="KHONG_TON_TAI")


def test_rung_ram_lam_tam_nhin_ngan_lai(monkeypatch):
    """`RUNG_RAM` là bản đồ để hỏi "giao tiếp đáng giá bao nhiêu" — nó chỉ có
    nghĩa nếu bụi rậm thật sự chặn được tầm nhìn."""
    from genesis.world import visible

    # TẮT thừa kế (W-17) trong bài này. Bài đo một tính chất của ĐỊA HÌNH, mà
    # thừa kế làm `sense` trôi qua các đời — tức bán kính nhìn đổi giữa ván, và
    # hai bản đồ tiến hoá khác nhau. Nhiễu ấy nuốt chửng hiệu ứng cần đo: bật
    # thừa kế thì con số ra 2.485 so với 2.475, đảo dấu so với sự thật.
    # Cách ly biến là việc của bài test, không phải nới ngưỡng cho tới khi xanh.
    monkeypatch.setattr(config, "LINEAGE_ENABLED", False)

    # Đo TRUNG BÌNH mỗi con còn sống, không đo tổng: `RUNG_RAM` có
    # `plant_scale` cao hơn nên nhiều con sống hơn, và tổng sẽ cao hơn vì lý do
    # chẳng liên quan gì tới tầm nhìn. Bản đầu của bài này đo tổng và "chứng
    # minh" điều ngược lại (140 so với 115).
    seen_by_map = {}
    for name in ("DONG_CO", "RUNG_RAM"):
        num = den = 0
        for seed in range(1, 9):
            world, creatures, state, rng = build_match(seed, map_name=name)
            for t in range(60):
                tick(world, creatures, t, rng, state)
                alive = [c for c in creatures if c.alive]
                num += sum(len(visible(c, world, creatures)) for c in alive)
                den += len(alive)
        seen_by_map[name] = round(num / max(den, 1), 3)
    assert seen_by_map["RUNG_RAM"] < seen_by_map["DONG_CO"], seen_by_map


def test_cong_kha_giai_chay_tren_DUNG_ban_do():
    """Sa mạc gần như không có ô nước, nên một luật `DRINK` được duyệt trên đồng
    cỏ sẽ là câu đố **không có lời giải** ở đó — hệt một cond không quan sát được.
    Cổng khả giải chạy một ván THẬT, nên nó phải chạy trên đúng bản đồ sẽ dùng."""
    from genesis.lawgen import split_arm

    assert split_arm("STANDARD@RUNG_RAM") == ("STANDARD", "RUNG_RAM")
    assert split_arm("STANDARD") == ("STANDARD", None)

    # Bài sắc nhất: đếm THẲNG số lần một luật `DRINK` kích hoạt trên hai bản đồ.
    # (So hai bộ luật sinh ra thì yếu: cổng là bộ LỌC, nên bộ đầu tiên hợp lệ
    # trên cả hai bản đồ sẽ được nhận ở cả hai, và bài test xanh vì lý do sai.)
    from genesis.lawdsl import Dur, Effect, EffectKind, Law, Mag, Trigger, TriggerKind
    from genesis.lawgen import live_fire_counts

    drink = Law(Trigger(TriggerKind.DRINK), (),
                Effect(EffectKind.POISON, Mag.SMALL, Dur.SHORT))
    kho = sum(live_fire_counts([drink], s, 200, "HOANG_MAC")[0] for s in range(1, 6))
    nuoc = sum(live_fire_counts([drink], s, 200, "QUAN_DAO")[0] for s in range(1, 6))
    assert kho * 3 < nuoc, (
        f"luật DRINK kích hoạt {kho} lần ở sa mạc và {nuoc} ở quần đảo — "
        f"bản đồ không đi vào cổng thì hai số này phải bằng nhau"
    )


def test_khoa_dem_tach_theo_ban_do(tmp_path):
    from genesis.lawgen import generate_cached

    generate_cached(12, arm="STANDARD@HOANG_MAC", cache_dir=tmp_path)
    generate_cached(12, arm="STANDARD@RUNG_RAM", cache_dir=tmp_path)
    names = {p.name for p in tmp_path.glob("*.json")}
    assert names == {"STANDARD@HOANG_MAC-12.json", "STANDARD@RUNG_RAM-12.json"}


def test_server_xoay_ban_do_theo_van():
    """Xoay theo `match_no`, không bốc ngẫu nhiên: "ván sau là bản đồ nào" nên
    đoán được, để người chơi biết mình đang chờ gì."""
    import net_config
    from net.match import MatchRunner, Phase

    r = MatchRunner(seed=1, ticks=4, tick_ms=1, log_dir=None)
    seen = []
    for _ in range(len(net_config.MAP_ROTATION)):
        while r.phase is not Phase.SEEDING:
            r.advance_phase()
        seen.append(r.map_name)
        r.advance_phase()
    assert seen == list(net_config.MAP_ROTATION)
