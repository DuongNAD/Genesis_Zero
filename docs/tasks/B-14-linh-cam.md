# B-14 · Linh cảm — chỗ để ĐOÁN mà không phải TIN

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-07, B-08, L-02 · **Chặn** X-09 |
| **File** | `genesis/hunch.py` (~120 dòng) · sửa `law_config`, `prompt`, `strategist`, `tick`, `validate`, `routes_*` |
| **Ước lượng** | ~350 dòng · 3 giờ |
| **Giao cho model rẻ?** | ❌ tự viết — nó đụng vòng tick, và ranh giới "được biết cái gì" là cả thiết kế |
| **Tài liệu gốc** | [03 §5](../03-LUAT-AN-V5.md) Sổ Luật · [B-08](B-08-codex.md) CLAIM hai pha · [W-16](W-16-cam-nang.md) ba tầng trí nhớ |

## 1. Mục tiêu

Sổ Luật đang gánh **hai việc khác nhau** và đó là lý do nó hỏng ở đuôi.

Nó vừa là chỗ **ghi giả thuyết**, vừa là chỗ **nộp bài**. Nhưng ô sổ thì ít
(`CODEX_SIZE_BY_BRAIN` cho brain 0 đúng **một** ô), ghi thì tốn năng lượng và
tốn `CLAIM_COOLDOWN = 25`. Nên một con muốn *thử nghĩ ra một khả năng* phải trả
giá y hệt như khi nó *tuyên bố đã biết*. Hai hành vi rất khác nhau, một bảng giá.

Đã đo được hậu quả, và nó nằm ngay trong [01-STATUS](../01-STATUS.md):

> `L5:1` **tìm ra luật ở tick 99 rồi phải xoá ở tick 148** để ghi thứ khác —
> brain 0 có đúng một ô sổ. Cột `ever_stated` và cột `found` trả lời hai câu
> khác nhau, và ca này thuộc loại thứ hai: *tìm ra rồi đánh mất*.

Và mặt kia của cùng đồng xu: model viết **24/45 mục là `EAT -> HEAL`**, L1 viết
9 mục thì **cả 9 về ăn quả**. Nó không bao giờ nhìn ra khỏi chỗ quả. Một phần vì
model, nhưng một phần vì **thử một hướng khác quá đắt**: đoán sai một lần là mất
ô sổ, mất 25 tick chờ, và mất luôn thứ đang có trong ô ấy.

**Linh cảm là chỗ rẻ để sai.** Một linh cảm là một luật *hình dạng đầy đủ* mà
con vật ghi ra để **theo dõi**, không phải để tin. Nó không chiếm ô Sổ Luật,
không được chấm điểm, và thế giới **tự đếm hộ** nó đúng bao nhiêu lần trên bao
nhiêu lần thử.

Nó làm cho một câu trong `handbook.SEED_LESSONS` thành cơ chế thật thay vì lời
khuyên suông:

> *"Chuyện không xảy ra cũng là bằng chứng. Hãy nhớ cả những lần không có gì."*

Sổ tay 6 dòng của brain 0 **không thể** nhớ nổi những lần không có gì. Linh cảm
thì nhớ hộ — nhưng chỉ nhớ về đúng cái giả thuyết mà chính nó đã nêu ra.

## 2. Ba tầng trí nhớ thành bốn

| Tầng | Nội dung | Sống bao lâu | Được chấm? |
|---|---|---|---|
| Sổ tay ([B-07](B-07-so-tay.md)) | *"t382 TÔI ăn quả đỏ → mất máu"* | trong ván, chết theo đời | không |
| **Linh cảm** (đây) | *"KHI ăn quả đỏ THÌ mất máu — đúng 7/9"* | trong ván, chết theo đời | **không** |
| Sổ Luật ([B-08](B-08-codex.md)) | *"KHI ăn quả đỏ THÌ nhiễm độc (vừa, ngắn)"* | trong ván, `conf` giảm qua đời | **có** |
| Cẩm nang ([W-16](W-16-cam-nang.md)) | *"thử một thứ một lúc"* | qua nhiều ván | không |

Linh cảm nằm đúng khoảng trống giữa **quan sát thô** và **tuyên bố**. Sổ tay ghi
*cái đã thấy*; Sổ Luật tuyên bố *cái tin là đúng*; linh cảm giữ *cái đang thử*.

## 3. Bất biến

**Bất biến 1 — linh cảm KHÔNG BAO GIỜ được chấm.** `score.py`, `match()`,
`t_discover`, ba danh hiệu của [W-14](W-14-chien-thang.md): không cái nào nhìn
vào linh cảm. Một linh cảm đúng suốt ván mà không bao giờ được chép sang Sổ Luật
thì ăn **0**. Cam kết vẫn là cam kết; nếu không thì phép đo đổi từ *"ngươi có
biết không"* sang *"ngươi có từng đoán trúng không"*, và hai câu ấy khác nhau xa.

**Bất biến 2 — bảng đếm chỉ nói về giả thuyết mà CHÍNH NÓ nêu ra.** Không có
đường nào để linh cảm hé lộ rằng có một luật ở chỗ con vật chưa hỏi tới. Nó trả
lời đúng một câu: *"cái ngươi vừa nói, có xảy ra không"*. Vi phạm bất biến này
là biến linh cảm thành một oracle miễn phí, và cả phép đo mất nghĩa.

**Bất biến 3 — so ở mức `EffectKind`, KHÔNG so `mag`/`dur`.** Con vật cảm được
"máu tụt hẳn xuống", không cảm được "DAMAGE mức MED kéo dài SHORT". So tới
`mag`/`dur` là cho nó một độ chính xác nó **không quan sát được**, tức là rò
đáp án qua cửa sau. Hệ quả cố ý: linh cảm **yếu hơn hẳn** một mục Sổ Luật — nó
chỉ ra hướng, không ra bài. Đây là chỗ dễ hỏng nhất của cả phiếu, và nó hỏng
**im lặng**: `match` sẽ nhích lên và trông như model giỏi hơn.

**Bất biến 4 — dung lượng theo `brain`, và phải TỐN một lượt nghĩ.** Miễn phí
thì chiến lược đúng là đăng ký hết mọi luật có thể rồi đọc bảng đếm — đó là vét
cạn, không phải quy nạp, và `match` sẽ đo tốc độ vét chứ không đo năng lực. Nêu
một linh cảm đi qua đúng đường CLAIM hai pha của [B-08](B-08-codex.md): một cờ
`want_hunch` trong quyết định thường, rồi **một lời gọi riêng** ở tick sau.

**Bất biến 5 — chết theo đời.** Linh cảm là trạng thái *đang điều tra*, không
phải niềm tin. Nó đi cùng sổ tay ở `lineage.forget_on_death`, không đi cùng Sổ
Luật (thứ chỉ giảm `conf`).

**Bất biến 6 — TẮT mặc định.** Bật lên là **đổi luật chơi**, nên mọi con số đã
ghi trước đây không so được với con số sau đây. Nó là một **nhánh thí nghiệm**
(`--hunch`), đúng cách [W-16](W-16-cam-nang.md) được đối xử: mệnh đề *"linh cảm
rút ngắn `t_discover`"* phải được **đo**, không được giả định.

## 4. Chữ ký

```python
# genesis/law_config.py
HUNCH_BY_BRAIN  = {0: 2, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}   # > CODEX_SIZE_BY_BRAIN
HUNCH_COOLDOWN  = 10          # riêng, KHÔNG dùng chung CLAIM_COOLDOWN
HUNCH_BUDGET_BY_BRAIN = CLAIM_BUDGET_BY_BRAIN            # cùng hình dạng JSON

# genesis/hunch.py
@dataclass
class Hunch:
    law: Law
    born_at: int
    tried: int = 0            # số lần trigger + cond khớp
    hit: int = 0              # trong đó, số lần EffectKind đúng xảy ra

@dataclass
class HunchBook:
    size: int
    def entries(self) -> list[Hunch | None]: ...
    def apply(self, op: str, slot: int, law: Law | None, tick: int) -> Verdict: ...
    def resize(self, n: int) -> None: ...
    def observe(self, ev: LawEvent, happened: set[EffectKind]) -> None: ...
    def render(self, sm: SurfaceMap) -> str: ...
```

`observe` là cả cơ chế, và nó ngắn:

```python
for h in self._entries:
    if h is None or evaluate(h.law, ev) is None:
        continue                      # giả thuyết không nói gì về tick này
    h.tried += 1
    if h.law.effect.kind in happened: # BẤT BIẾN 3: chỉ so kind
        h.hit += 1
```

Móc vào pha 4 của [W-11](W-11-vong-tick.md), **sau** `collect_law_effects` và
**sau** khi đã biết `happened` của từng con — không phải trong lúc áp hệ quả,
nếu không thì con nào được duyệt trước sẽ thấy một thế giới khác con duyệt sau
(vỡ tính đồng thời).

Khối prompt mới, E6, ngay dưới Sổ Luật:

```
[LINH CẢM] — ngươi đang thử ba điều này. Chưa cái nào là kết luận.
1. KHI uống nước THÌ máu tụt          — đúng 7 / thử 9
2. KHI ăn quả zim THÌ khoẻ ra         — đúng 0 / thử 12
3. KHI có kẻ đứng cạnh THÌ liền vết   — chưa thử lần nào
```

Dòng số 2 là dòng đáng giá nhất trong ví dụ trên: **12 lần thử, 0 lần đúng.**
Đó là bằng chứng phủ định, và nó là thứ sổ tay 6 dòng không bao giờ giữ nổi.

## 5. Bẫy

**Bẫy 1 — `agree` là của bộ chấm, đừng gọi nó ở đây.** `verify.agree` trả điểm
*từng phần* trên `mag`/`dur`. Gọi nó trong vòng tick là đưa cho con vật đúng cái
thước mà cuối ván sẽ chấm nó — nó sẽ dò `mag` bằng cách xem điểm nhích lên hay
xuống. So bằng `in happened` trên `EffectKind`, và không hơn.

**Bẫy 2 — `tried` phải đếm cả lần TRIGGER KHỚP MÀ KHÔNG CÓ GÌ XẢY RA.** Bỏ qua
những lần ấy thì mọi linh cảm đều có tỉ lệ đúng 100% và bảng đếm thành vô dụng.
Đây chính là "chuyện không xảy ra cũng là bằng chứng", và nó là nửa giá trị của
cả cơ chế.

**Bẫy 3 — một hệ quả có thể đến từ luật KHÁC.** `happened` là tập hệ quả thật
sự giáng xuống con vật trong tick đó, không phải hệ quả *của luật mà nó đang
đoán*. Nên bảng đếm **có nhiễu**, và điều đó là **đúng**: đó chính là sự lẫn lộn
nhân quả mà một nhà khoa học thật phải gỡ. Đừng "sửa" nó bằng cách lọc theo
`law_id` — làm thế là nói cho con vật biết luật nào tồn tại.

**Bẫy 4 — đường mạng.** Sau [N-16](N-16-ngang-bang-mang.md) trạng thái trí nhớ
nằm ở `genesis.minds.Minds`, một bản. `HunchBook` **phải** vào đó, không được
mọc thêm một dict ở `net/routes_work.py`; `tests/test_n16_ngang_bang.py` có một
bài canh chừng đúng chuyện này và nó sẽ đỏ.

## 6. Nghiệm thu

```bash
pytest tests/test_hunch.py -q
```

Bảy ca bắt buộc:

1. Trigger khớp, hệ quả đúng kind → `hit += 1`, `tried += 1`.
2. Trigger khớp, **không có gì xảy ra** → `tried += 1`, `hit` không đổi (bẫy 2).
3. Trigger khớp, hệ quả sai kind → `tried += 1`, `hit` không đổi.
4. Trigger không khớp → cả hai không đổi.
5. `mag`/`dur` sai hoàn toàn mà `kind` đúng → vẫn tính `hit` (bất biến 3).
6. `score.py` trên một ván có linh cảm ra **đúng cùng con số** với ván không có,
   khi Sổ Luật giống nhau (bất biến 1).
7. `HunchBook` chết theo đời cùng sổ tay, Sổ Luật thì không (bất biến 5).

Rồi đo mệnh đề — đây mới là nghiệm thu thật, và nó **được phép trả lời KHÔNG**:

```bash
python scripts/x09_hunch.py --seeds 5 --ticks 200 --llm-url http://127.0.0.1:8080
# CÓ linh cảm phải rút ngắn t_discover hoặc nâng match, hoặc trả lời thẳng rằng
# nó không. Cùng model, cùng trọng số, chỉ khác một khối prompt và một cuốn sổ.
```

## 7. Cái KHÔNG làm, và vì sao

**Không có "thăng cấp" từ linh cảm sang Sổ Luật.** Nghe thì tiện, nhưng con vật
đã có sẵn chữ của luật ấy trong prompt của chính nó — nó chỉ cần chép sang. Một
lệnh `PROMOTE` thêm cơ chế mà **không thêm năng lực**, và nó xoá mất chi phí
chép lại, vốn là một phần của việc cam kết.
