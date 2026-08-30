"""Genesis Zero — tests/test_features: ba đặc điểm bốc thăm mỗi loài (W-19)."""

from __future__ import annotations

import collections
import random

from genesis import config
from genesis.domain import Domain, can_enter
from genesis.features import (BY_KEY, FEATURES, N_FEATURES, describe, kit_of,
                              roll, roll_for_species)
from genesis.tick import build_match
from genesis.world import Terrain


def test_boc_ba_dac_diem_khong_trung_nhau():
    for seed in range(50):
        fs = roll(random.Random(seed))
        assert len(fs) == N_FEATURES
        assert len({f.key for f in fs}) == N_FEATURES


def test_TAT_DINH_theo_loai_va_seed():
    """Bốc lại mỗi lần chạy thì ba đường gãy cùng lúc: bộ đệm hình 3D khoá theo
    chuỗi mô tả, `--replay` dựng lại ván cũ, và bộ chấm so hai ván với nhau."""
    a = roll_for_species("L1", 21)
    b = roll_for_species("L1", 21)
    assert [f.key for f in a] == [f.key for f in b]
    assert roll_for_species("L1", 22) != a or roll_for_species("L2", 21) != a


def test_thu_tu_tra_ve_CO_DINH():
    """Trả theo `key` chứ không theo thứ tự bốc: cùng ba đặc điểm phải cho cùng
    MỘT chuỗi mô tả, nếu không thì một sinh vật sinh ra hai hình 3D khác nhau."""
    for seed in range(30):
        fs = roll(random.Random(seed))
        assert [f.key for f in fs] == sorted(f.key for f in fs)


def test_phan_phoi_deu():
    c = collections.Counter()
    for seed in range(300):
        for f in roll(random.Random(seed)):
            c[f.key] += 1
    tot = sum(c.values())
    share = [c[f.key] / tot for f in FEATURES]
    assert min(share) > 0.5 / len(FEATURES), c
    assert max(share) < 2.0 / len(FEATURES), c


# ── mặt cơ chế ──────────────────────────────────────────────────────────────

def test_he_so_NHAN_chu_khong_cong():
    """Hai đặc điểm cùng giảm sát thương thì tích vẫn > 0. Cộng trừ thì đủ hai
    cái là bất tử — và đủ hai cái giảm upkeep là con vật KIẾM ĐƯỢC năng lượng
    bằng cách đứng yên."""
    k = kit_of((BY_KEY["VAY_CUNG"], BY_KEY["VO_SO"], BY_KEY["LONG_DAI"]))
    assert 0.0 < k.dmg_taken_mult < 1.0
    assert 0.0 < k.upkeep_mult < 1.0


def test_dao_hang_mo_khoa_ca_DA_lan_HANG():
    """Hang nằm lọt giữa đá, nên vào được hang nghĩa là xuyên qua được đá.

    Thiếu `ROCK` thì hang thành ô không ai tới được — một chỗ trốn mà chính chủ
    cũng không vào nổi.
    """
    k = kit_of((BY_KEY["DAO_HANG"],))
    assert Terrain.CAVE in k.extra_terrain
    assert Terrain.ROCK in k.extra_terrain
    assert can_enter(Domain.CAN, Terrain.CAVE, None, k) is True
    assert can_enter(Domain.CAN, Terrain.CAVE, None, None) is False


def test_treo_gioi_ha_nguong_nhung_khong_xoa_nguong():
    """Đặc điểm HẠ ngưỡng, không bỏ ngưỡng: một con speed 0 vẫn không lên cây."""
    from genesis.traits import Traits

    k = kit_of((BY_KEY["TREO_GIOI"],))
    vua = Traits(brain=5, attack=4, armor=0, speed=1, sense=1, stomach=1)
    kiet = Traits(brain=5, attack=5, armor=1, speed=0, sense=1, stomach=0)
    assert can_enter(Domain.CAN, Terrain.TREE, vua, k) is True
    assert can_enter(Domain.CAN, Terrain.TREE, vua, None) is False
    assert can_enter(Domain.CAN, Terrain.TREE, kiet, k) is False


def test_ca_co_dac_diem_van_khong_len_bo():
    """Tầng đứng TRƯỚC đặc điểm. Cá mang `DAO_HANG` vẫn là cá."""
    k = kit_of((BY_KEY["DAO_HANG"], BY_KEY["CANH_LUOT"]))
    for t in (Terrain.PLAIN, Terrain.BUSH, Terrain.TREE):
        assert can_enter(Domain.NUOC, t, None, k) is False


def test_world_gan_kit_cho_moi_loai():
    w, cs, st, rng = build_match(21)
    for sp in {c.species for c in cs}:
        assert sp in w.kits
        assert len(w.kits[sp].features) == N_FEATURES


def test_loai_la_khong_co_kit_thi_khong_nem():
    """Người chơi qua mạng đăng ký loài giữa ván — `passable` không được gãy."""
    from genesis.creature import Creature
    from genesis.traits import founder_traits

    w, cs, st, rng = build_match(21)
    la = Creature(id="ZZ:0", species="ZZ", traits=founder_traits("L1"),
                  pos=(0, 0), hp=1.0, energy=1.0)
    assert w.passable((0, 0), la) in (True, False)


# ── mặt ngoại hình ──────────────────────────────────────────────────────────

def test_moi_dac_diem_co_ca_HAI_mat():
    """Đặc điểm là cầu nối giữa cơ chế và ngoại hình — thiếu một mặt là hỏng ý.

    Thiếu `look`: hình 3D không phản ánh được nó, và kênh quan sát gián tiếp mất
    một chiều. Thiếu `note`: không ai biết nó đổi gì trong vòng tick.
    """
    for f in FEATURES:
        assert f.look and len(f.look) > 30, f.key
        assert f.note and len(f.note) > 10, f.key
        assert f.vn, f.key
        # `look` phải tả HÌNH KHỐI, không tả công dụng — Meshy dựng được cái
        # nhìn thấy, không dựng được cái suy ra.
        assert not any(w in f.look for w in ("giúp", "để có thể", "nhờ đó")), f.key


def test_mo_ta_ghep_du_ba_dac_diem():
    fs = roll_for_species("L1", 21)
    txt = describe(fs)
    for f in fs:
        assert f.look.rstrip(".").split(",")[0] in txt


def test_prompt_meshy_mang_ca_TANG_lan_DAC_DIEM():
    from genesis.mesh_prompts import creature_prompt
    from genesis.traits import founder_traits

    fs = (BY_KEY["LUONG_CU"], BY_KEY["LONG_DAI"], BY_KEY["RANG_NANH"])
    ca = creature_prompt(founder_traits("L1"), "NUOC", fs)
    chim = creature_prompt(founder_traits("L1"), "TROI", fs)
    assert "vây" in ca and "không có chân" in ca
    assert "cánh" in chim and "biết bay" in chim.lower()
    assert "màng bơi" in ca and "lông dài" in ca and "nanh" in ca


def test_prompt_khong_co_dac_diem_thi_van_chay():
    """Ván trước W-19 không truyền `features` — không được ném."""
    from genesis.mesh_prompts import creature_prompt
    from genesis.traits import founder_traits

    assert creature_prompt(founder_traits("L1"))


# ── hàng rào của tầng viết lại ──────────────────────────────────────────────

def test_viet_lai_khong_duoc_danh_roi_bo_phan():
    from genesis.genai import verify_rewrite

    goc = "Sinh vật bốn chân, có đuôi dài, chân có màng bơi giữa các ngón."
    assert verify_rewrite(goc, "Con vật bốn chi, đuôi dài, các ngón có màng.")[0]
    assert not verify_rewrite(goc, "Con vật bốn chân với chiếc đuôi dài.")[0]


def test_viet_lai_khong_duoc_mang_chu_so():
    """Mô tả HÌNH không được mang chỉ số — nó là kênh quan sát, không phải bảng."""
    from genesis.genai import verify_rewrite

    ok, why = verify_rewrite("Sinh vật bốn chân.", "Con vật bốn chân, giáp 3.")
    assert not ok and "chữ số" in why


def test_dong_nghia_bon_chan_bon_chi():
    """Hồi quy: bộ kiểm bản đầu bắt oan ngay lần chạy thật đầu tiên vì Gemini
    viết 'bốn chi' còn bản gốc viết 'bốn chân'."""
    from genesis.genai import verify_rewrite

    assert verify_rewrite("Sinh vật bốn chân, có đuôi.",
                          "Con vật đứng vững trên bốn chi, có chiếc đuôi dài.")[0]


def test_khong_co_khoa_thi_tra_ve_ban_GOC_khong_nem():
    """Hết khoá, mất mạng, model trả rác — tất cả rơi về bản gốc.

    Bản gốc đã đúng sẵn; cái ta mua ở tầng viết lại là văn phong, không phải sự
    thật. Trả tiền cho văn phong bằng một ván gãy thì quá đắt.
    """
    import os

    from genesis.genai import rewrite

    old = {k: os.environ.pop(k, None) for k in ("GEMINI_API_KEYS", "GEMINI_API_KEY")}
    try:
        txt, src = rewrite("Sinh vật bốn chân.")
        assert txt == "Sinh vật bốn chân." and src == "goc"
    finally:
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v


def test_khong_co_khoa_nao_trong_kho():
    """Bài canh chừng. `.env` bị gitignore; không khoá nào được lọt vào file theo dõi.

    Khớp theo **hình dạng khoá thật**, không theo tiền tố: khoá Google là
    `AIzaSy` cộng 33 ký tự nữa. Bản đầu chỉ tìm tiền tố và đỏ ngay lần chạy đầu
    — nó bắt chính **ba file đang NÓI VỀ** khoá (phiếu việc, nhật ký, và bản
    thân bài kiểm này). Một hàng rào bắt lời kể về con bọ thay vì con bọ thì
    người sửa sau sẽ tắt nó đi, và lúc ấy nó tệ hơn không có.
    """
    import re
    import subprocess

    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    hinh_dang_khoa = re.compile(r"AIzaSy[A-Za-z0-9_\-]{33}|AQ\.Ab8RN6[A-Za-z0-9_\-]{20,}")
    tracked = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                             text=True).stdout.split()
    for rel in tracked:
        f = root / rel
        if not f.is_file() or f.stat().st_size > 400_000:
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        m = hinh_dang_khoa.search(txt)
        assert m is None, f"{rel} chứa khoá API thật (…{m.group(0)[-6:]})"


def test_luong_cu_THAT_SU_xuong_nuoc_duoc():
    """Hồi quy: `LUONG_CU` từng là đặc điểm thuần TRANG TRÍ.

    `kit_of` gom `domains` vào `extra_domains`, nhưng `can_enter` chỉ đọc
    `extra_terrain` — nên con vật được tả là có chân màng và da trơn ẩm bóng
    trong prompt 3D mà **không xuống nước được một ô nào**. Hình nói dối, đúng
    thứ W-19 dựng lên để chặn.

    Nó lọt vì bài kiểm cũ chỉ soi `extra_terrain`; chỉ tới lúc in `look` và
    `effect` cạnh nhau trong `creature_design.py` mới lộ ra: L1 mang "lưỡng cư"
    mà cột cơ chế không nhắc gì tới nước.
    """
    k = kit_of((BY_KEY["LUONG_CU"],))
    assert Domain.NUOC in k.extra_domains
    assert can_enter(Domain.CAN, Terrain.DEEP, None, k) is True, \
        "lưỡng cư phải xuống được nước sâu"
    assert can_enter(Domain.CAN, Terrain.DEEP, None, None) is False


def test_moi_dac_diem_deu_DOI_MOT_THU_GI_DO():
    """Bài canh chừng cho bất biến trung tâm của W-19: hai mặt phải khớp.

    Một đặc điểm có `look` mà không đổi gì trong vòng tick là một lời hứa suông
    với người nhìn hình. `RAU_CAM_UNG` là ngoại lệ DUY NHẤT được phép — nó mô tả
    một giác quan mà vòng tick chưa mô hình hoá, và nó được nêu tên ở đây để lần
    sau ai thêm đặc điểm rỗng thì phải sửa chính dòng này.
    """
    # Hai ngoại lệ, và cả hai được NÊU TÊN chứ không giấu:
    #
    # · `RAU_CAM_UNG` — tả một giác quan vòng tick chưa mô hình hoá.
    # · `MAT_DEM` — cơ chế ĐÃ dựng (đêm rút ngắn tầm nhìn) nhưng
    #   `NIGHT_SIGHT_PENALTY = 0` nên nó đang tắt: bật lên thì M1 vỡ, và số đo
    #   nằm ngay trong `config.py`. Nó sẽ tự hết ngoại lệ khi hằng số ấy > 0.
    #
    # Nêu tên để lần sau ai thêm một đặc điểm rỗng thì phải sửa chính dòng này —
    # một danh sách ngoại lệ phải khó nới ra, nếu không nó thành cái thùng rác.
    chua_noi_co_che = {"RAU_CAM_UNG", "MAT_DEM"}
    for f in FEATURES:
        if f.key in chua_noi_co_che:
            continue
        k = kit_of((f,))
        doi = (k.extra_terrain or k.extra_domains or k.climb_bonus or k.thorns
               or k.night_sight
               or abs(k.upkeep_mult - 1) > 1e-9 or abs(k.damage_mult - 1) > 1e-9
               or abs(k.dmg_taken_mult - 1) > 1e-9)
        assert doi, f"{f.key} có `look` mà không đổi gì trong vòng tick"


def test_dem_lam_ngan_tam_nhin_va_MAT_DEM_xoa_khoan_do():
    """Hồi quy thứ hai của cùng một họ: `MAT_DEM` từng hứa suông.

    Trước W-19, ngày và đêm khác nhau đúng một chuỗi trong prompt và một trigger
    `PHASE_ENTER` — **không đổi một hành vi nào**. Nên "mắt đêm" là lợi thế chống
    lại một bất lợi không tồn tại: hình 3D tả đôi mắt to chiếm nửa khuôn mặt, và
    trong vòng tick nó chẳng để làm gì.

    Sửa bằng cách cho ĐÊM một cái giá, không phải bằng cách bỏ đặc điểm — cả chu
    kỳ ngày/đêm nhờ thế mới thành một biến số thật.
    """
    from genesis import config
    from genesis.world import visible
    from genesis.tick import build_match

    w, cs, st, rng = build_match(21)
    obs = cs[0]
    r_ngay = obs.traits.sight_radius

    assert kit_of((BY_KEY["MAT_DEM"],)).night_sight is True
    assert kit_of((BY_KEY["LONG_DAI"],)).night_sight is False

    # Kiểm cơ chế bằng cách BẬT nó lên trong phạm vi bài này, dù mặc định là tắt
    # — cơ chế phải đúng ngay cả khi hằng số đang bằng 0, nếu không thì hôm bật
    # lên ta mới phát hiện nó sai.
    cu = config.NIGHT_SIGHT_PENALTY
    try:
        config.NIGHT_SIGHT_PENALTY = 2
        w.phase = "NIGHT"
        w.kits[obs.species] = kit_of((BY_KEY["MAT_DEM"],))
        co_mat_dem = len(visible(obs, w, cs))
        w.kits[obs.species] = kit_of((BY_KEY["LONG_DAI"],))
        khong = len(visible(obs, w, cs))
        assert co_mat_dem >= khong, "mắt đêm phải nhìn được ít nhất bằng kẻ không có"

        w.phase = "DAY"
        assert len(visible(obs, w, cs)) >= khong, "ban ngày không được kém hơn đêm"
    finally:
        config.NIGHT_SIGHT_PENALTY = cu
    assert r_ngay > 0


def test_ban_ngay_khong_bi_phat():
    from genesis.world import visible
    from genesis.tick import build_match

    w, cs, st, rng = build_match(21)
    w.phase = "DAY"
    a = len(visible(cs[0], w, cs))
    w.phase = "NIGHT"
    b = len(visible(cs[0], w, cs))
    assert b <= a, "đêm không được cho nhìn XA HƠN ngày"


def test_CA_khong_chui_qua_da_duoc_du_boc_trung_DAO_HANG():
    """Hồi quy: `extra_terrain` từng áp TRƯỚC cổng tầng.

    Bốc thăm là ngẫu nhiên nên một con cá hoàn toàn có thể trúng `DAO_HANG` —
    và với thứ tự cũ thì nó **chui qua đá đặc và vào hang được**, trong khi vẫn
    không đi nổi trên cỏ. Hiện ra ngay lần đầu nhìn dữ liệu thật (`W1` seed 1
    bốc `DAO_HANG · LUONG_CU · RAU_CAM_UNG`), không phải từ đọc code.

    Đào hang và lượn là chuyện của con vật có chân. Đặc điểm mở đường đi TRONG
    tầng; muốn đổi tầng thì phải là `extra_domains`, và `LUONG_CU` là thứ duy
    nhất được phép làm việc ấy.
    """
    from genesis.traits import founder_traits

    tr = founder_traits("W1")
    for key in ("DAO_HANG", "CANH_LUOT"):
        k = kit_of((BY_KEY[key],))
        assert can_enter(Domain.NUOC, Terrain.ROCK, tr, k) is False, key
        assert can_enter(Domain.NUOC, Terrain.CAVE, tr, k) is False, key
        # nhưng loài CẠN thì vẫn được mở khoá như thiết kế
        assert can_enter(Domain.CAN, Terrain.ROCK, founder_traits("L2"), k) is True, key


def test_LUONG_CU_van_doi_duoc_tang_vi_no_la_extra_domains():
    """Ngoại lệ duy nhất, và nó đi qua `extra_domains` chứ không `extra_terrain`."""
    from genesis.traits import founder_traits

    k = kit_of((BY_KEY["LUONG_CU"],))
    assert can_enter(Domain.CAN, Terrain.DEEP, founder_traits("L1"), k) is True
