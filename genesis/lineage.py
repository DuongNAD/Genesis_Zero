"""Genesis Zero — lineage: chết là truyền lại, không phải ngủ dậy (W-17).

## Cái đang hỏng

`adapt.reset_body` kéo mọi con về vector khai sinh mỗi lần chết. Đo trên một ván
200 tick (seed 55): **64 lượt chết, 83 lần dịch trait, và 63/83 lần dịch — 76% —
bị xoá vì con đó chết sau đó.** Con `L5:4` dịch trait 12 lần rồi mất sạch. Cơ
chế thích nghi của [W-12](../docs/tasks/W-12-thich-nghi.md) chạy đúng và không
tích luỹ được gì: thích nghi, chết, về nguyên trạng, thích nghi lại.

## Cái thay vào

Con chết thì **không quay lại**; **một đời sau ra đời** ở chỗ xác. Cùng
`creature_id` — định danh ấy là DÒNG DÕI, không phải cá thể — nên khe prefix
cache, khoá Sổ Luật, sổ ghi công và đường replay đều giữ nguyên.

| | qua đời sau | vì sao |
|---|---|---|
| Sổ Luật | ✅ | thứ ngươi đã **viết ra** |
| Sổ tay hiện trường | ❌ | trải nghiệm thô không truyền được |
| Vector trait **đã dịch** | ✅ kèm đột biến | thích nghi cuối cùng có ý nghĩa |
| Điểm thích nghi | ❌ | đời sau phải tự kiếm |

Chỗ quan trọng nhất là dòng đầu và dòng hai **đi ngược nhau**: chỉ thứ đã ghi
vào Sổ Luật mới sống qua cái chết. Hiện Sổ Luật chỉ là tiện nghi — ghi hay không
thì trí nhớ vẫn nguyên. Từ đây, **không ghi là mất thật**. Đó đúng là cái nút mà
Qwen-7B bỏ quên suốt ván (0% mục sổ nói về uống nước, trong khi uống chiếm 26%
hành động).

## Không phải chấm sinh tồn dưới tên khác

Sống lâu **không** cho điểm; nó chỉ cho nhiều đời hơn, mà đời chỉ đáng giá nếu
có viết được gì. `t_discover` vẫn đếm từ ĐẦU VÁN chứ không từ lúc sinh, và điểm
vẫn tính theo (loài × luật) chứ không cộng dồn theo cá thể — xem
[B-10](../docs/tasks/B-10-score.md). Đây là cái cửa sau mà bản v4 đã chết vì nó,
nên nó có một bài test riêng.
"""

from __future__ import annotations

import random

from genesis import config
from genesis.creature import Creature
from genesis.traits import Traits

# Đột biến lệch theo NHÓM nguyên nhân chết — ba nhóm, không theo trigger cụ thể.
#
# Chọn lọc thật cần hàng nghìn đời; ở đây có 64 cái chết mỗi ván nên ta nén lại
# một bước Lamarck. Hệ quả: nhìn hình dáng một dòng dõi là đọc được thứ đang
# giết nó — bụng to dần qua các đời nghĩa là thế giới này đang đói (đo được:
# 61% số ca chết là chết đói).
#
# **Rào rò rỉ:** lệch theo NHÓM (đói/đánh/độc), tuyệt đối không theo trigger của
# luật ẩn. Ba nhóm thì quá thô để làm đáp án, đủ rõ để làm manh mối — và người
# chơi vốn đã được phép quan sát kẻ khác ([03 §4](../docs/03-LUAT-AN-V5.md)).
CAUSE_BIAS: dict[str, tuple[str, ...]] = {
    "starve": ("stomach",),
    "combat": ("armor", "attack"),
    "poison": ("sense",),
}


def inherit(parent: Traits, cause: str | None, rng: random.Random) -> Traits:
    """Vector của đời sau: lệch ĐÚNG MỘT điểm về phía nguyên nhân chết.

    Lấy một điểm từ trait cao nhất (không phải trait đích), dồn vào trait đích.
    Tổng luôn giữ `config.TRAIT_SUM`, mọi trait luôn trong
    `[config.TRAIT_MIN, config.TRAIT_MAX]`.

    Nguyên nhân lạ hoặc không dịch được thì trả về **nguyên vector bố mẹ** —
    đột biến là món quà, không phải thuế; không bao giờ làm hỏng một cơ thể chỉ
    vì không biết nên lệch đi đâu.
    """
    targets = CAUSE_BIAS.get(cause or "", ())
    if not targets:
        return parent

    vals = {n: getattr(parent, n) for n in config.TRAIT_NAMES}

    # Đích: trait THẤP NHẤT trong nhóm còn chỗ tăng. Thấp nhất chứ không ngẫu
    # nhiên, để cùng bố mẹ + cùng nguyên nhân luôn cho cùng kết quả — ván phải
    # tái lập được từ seed.
    can = [t for t in targets if vals[t] < config.TRAIT_MAX]
    if not can:
        return parent
    to = min(can, key=lambda t: (vals[t], config.TRAIT_NAMES.index(t)))

    # Nguồn: trait CAO NHẤT còn chỗ giảm, không phải đích — và **không bao giờ
    # là `brain`**.
    #
    # `brain` là trait cao nhất ở ba trong năm loài dựng sẵn, nên để nó làm nguồn
    # thì mỗi cái chết là một khoản thuế đánh vào đầu óc: L1 (brain 4) tụt về
    # brain 0 sau bốn lần chết, mà một ván có 64 lượt chết. Đó đúng là con lỗi
    # vừa vá ở `founder_traits` cho người chơi qua mạng, chỉ chậm hơn và lần này
    # là "cố ý".
    #
    # Nó phá đúng thứ dự án sinh ra để đo: brain quyết định từ vựng Sổ Luật
    # (`ADJACENT`/`PHASE_ENTER` chỉ có từ brain 4), số ô sổ và ngân sách token.
    # Cạn brain thì mệnh đề "model to hơn thành loài đỉnh" không còn gì để đo.
    #
    # Ranh giới đúng: **thân xác trôi theo thứ giết nó; đầu óc thì không.**
    # `brain` là phần người chơi đặt cược và là trục đang được nghiên cứu.
    # (Chủ sở hữu vẫn tự dịch brain được qua `adapt.maybe_shift` — đó là lựa
    # chọn của chính nó, không phải thuế.)
    # Và **không lấy từ chính nhóm đích**: L1 khai sinh có `attack=3, armor=1`,
    # nên lấy trait cao nhất sẽ lấy đúng `attack` để dồn sang `armor` — nhóm
    # chiến đấu xáo trong nội bộ và **không lớn lên**. Đo trên chính bài test:
    # sau ba đời chết vì đánh nhau, `attack+armor` vẫn đúng 4. Thích nghi với
    # một mối đe doạ nghĩa là **trả bằng thứ khác**, không phải kê lại đồ đạc.
    donors = [n for n in config.TRAIT_NAMES
              if n != "brain" and n not in targets and vals[n] > config.TRAIT_MIN]
    if not donors:
        return parent
    frm = max(donors, key=lambda n: (vals[n], -config.TRAIT_NAMES.index(n)))

    vals[frm] -= 1
    vals[to] += 1
    return Traits(**vals)


def rebirth(c: Creature, cause: str | None, rng: random.Random) -> Traits:
    """Dựng đời sau tại chỗ. Trả về vector CŨ (của bố mẹ) để ghi log.

    KHÔNG chạm Sổ Luật và KHÔNG chạm sổ tay: cả hai sống ngoài `Creature`.
    Người gọi lo phần trí nhớ — xem `strategist.observe`. Ranh giới ấy là thứ
    giữ cho bộ mô phỏng không biết gì về tầng LLM.
    """
    truoc = c.traits
    c.traits = inherit(truoc, cause, rng)
    c.generation += 1
    c.adapt_points = 0
    c.shift_log.clear()
    # KHÔNG chạm `eat_count`/`win_count`. Chúng là bộ đếm TÍCH LUỸ mà
    # `adapt.award_adapt` lấy dư (`eat_count % ADAPT_ON_EAT`) để phát điểm; xoá
    # chúng mỗi lần chết là xoá phần dở dang, và với 64 lượt chết một ván thì
    # **không ai đủ điểm để dịch trait lần nào** — đo được: bài
    # `test_huong_dich_do_llm_chon` chuyển từ xanh sang "không ai dịch trait".
    #
    # Chỉ `adapt_points` (đồng tiền chưa tiêu của THÂN XÁC này) về 0: đời sau
    # phải tự kiếm lấy lần dịch của mình.
    return truoc


def forget_on_death(notes, codex) -> int:
    """Trí nhớ khi sang đời mới: sổ tay XOÁ SẠCH, Sổ Luật giữ nhưng bớt chắc chắn.

    Một chỗ duy nhất, vì có HAI đường chạy gọi nó: `strategist.observe` (ván cục
    bộ) và `net.match` (chế độ mở). Hai bản sao sẽ có ngày lệch nhau, và triệu
    chứng là người chơi qua mạng quên khác người chơi cục bộ — đúng kiểu lỗi vừa
    bắt được ở `schema_for`, nơi đường mạng thiếu `targets` lẫn `sm` suốt.

    Trả số mục Sổ Luật bị xoá vì cạn tin cậy.
    """
    if notes is not None:
        notes.clear()
    if codex is None:
        return 0
    return codex.decay_confidence(config.CODEX_CONF_DECAY_PER_GEN)
