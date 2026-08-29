# 03 · Thế Giới Luật Ẩn (v5)

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · **03 Luật ẩn** · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md)

> **Đây là bản vá, không phải bản viết lại.** v4 đúng ở tầng sandbox và sai ở tầng mục tiêu.
> Tài liệu này giữ nguyên §1–§4 và §8–§10 của v4, thay §5.4 (điểm số) và §7 (thí nghiệm),
> chèn thêm bốn mốc mới. Đọc v4 trước; đọc bản này để biết chỗ nào đổi.
>
> **Một câu tóm tắt:** thế giới vẫn thế, nhưng vật lý của nó được bốc thăm mỗi ván
> và không ai biết trước. Mục tiêu không còn là *sống lâu* — mà là *phát hiện ra luật*.
> Vì tôi sinh ra luật nên tôi biết luật, nên lần đầu tiên trong dự án này **có đáp án để chấm**.

---

## 0. Vì sao phải viết bản này

### 0.1 Chỗ chết của v4

v4 chấm bằng sinh tồn. Sinh tồn **không chấm được** — không phải vì khó đo, mà vì đo xong không dùng được vào việc gì. Bốn lý do, độc lập nhau, mỗi cái đủ để giết:

**(a) Không có đáp án.** Không tồn tại "nước đi đúng" ở tick 137. Không có gì để so. Bạn chỉ có một con số cuối ván và không có cách nào biết con số đó *đáng lẽ* phải là bao nhiêu.

**(b) Không quy được trách nhiệm (credit assignment).** Con L1 sống 400 tick. Nhờ đâu? Nhờ quyết định ở tick 12, hay nhờ tick 300 nó tình cờ ở xa con L2? Một ván có ~130 lần gọi LLM và **một** tín hiệu ở cuối. Tỉ lệ tín hiệu/quyết định là 1/130. Không gradient nào sống nổi qua cái tỉ lệ đó.

**(c) Không dừng (non-stationary).** Điểm của bạn phụ thuộc vào hành vi của 14 con khác, mà chúng cũng đang đổi. Cùng một chính sách cho hai điểm khác nhau ở hai ván. Đó không phải là nhiễu — đó là hàm mục tiêu **tự di chuyển** dưới chân bạn.

**(d) Bị nhiễu bởi cơ thể.** L1 sống lâu hơn L5 vì `energy_max` 80 và `damage` 13, hay vì Gemma-2-9B nghĩ giỏi hơn Qwen-1.5B? v4 §11 rủi ro 4 đã gọi tên confound này và không giải được. **Nó không giải được trong khung sinh tồn.** Muốn tách hai yếu tố, v4 phải chạy vòng hoán vị founder vector — gấp đôi giờ máy để đổi một *quan sát* thành một *kết luận yếu*.

Cộng lại: v4 là một **đồ chơi đẹp**, không phải một **môi trường huấn luyện**. Nó tạo ra video hay và không tạo ra dữ liệu.

### 0.2 Một câu thay đổi mọi thứ

> Mỗi ván, thế giới bốc thăm 2–3 **luật ẩn**. Sinh vật phải làm thí nghiệm để tìm ra, phát biểu luật ra bằng một ký pháp hình thức, và bị chấm bằng **luật đó có khớp với luật thật không, và khớp sau bao nhiêu tick**.

Bốn cái chết ở §0.1 lành ngay:

| Bệnh | Thuốc |
|---|---|
| (a) Không có đáp án | Tôi sinh luật bằng seed → tôi giữ đáp án. Chấm như chấm toán. |
| (b) Không quy được trách nhiệm | Mỗi luật là một tín hiệu riêng, có mốc thời gian riêng (`t_discover`). Một ván cho 2–3 tín hiệu **có nhãn thời điểm**, cộng ~20 câu hỏi tiên đoán. Tỉ lệ tín hiệu/quyết định lên ~1/6. |
| (c) Không dừng | Luật là **cố định trong ván** và độc lập với đối thủ. Điểm khám phá không phụ thuộc 14 con kia. Đối kháng vẫn còn, nhưng nó không còn nằm trong hàm mục tiêu chính. |
| (d) Nhiễu bởi cơ thể | Cơ thể ảnh hưởng *chi phí thí nghiệm*, không ảnh hưởng *đáp án*. Và §10 cho bạn một phép đo trực tiếp để tách hai thứ. |

### 0.3 Cái gì giữ, cái gì đổi, cái gì chết

| | v4 | v5 |
|---|---|---|
| Lưới, địa hình, thức ăn, xác | **giữ nguyên** | + nước uống được, 4 loại quả, chu kỳ ngày/đêm, gió, lửa |
| Trait 6 chiều, tổng 12 | **giữ nguyên** | `brain` đổi nghĩa: từ "nhiều token" thành "dung lượng nhận thức" |
| Chiến đấu, độc, xác thối | **giữ nguyên** | không đổi một dòng |
| Mỗi cá thể một slot KV | **giữ nguyên** | không đổi một dòng |
| Tầng phản xạ | **giữ nguyên** | thêm nhánh `EXPERIMENT` |
| Prompt 4 khối, prefix cache | giữ khung | thành 5 khối, prefix dài hơn ~230 token |
| Nói / danh tiếng | giữ | + `TEACH` (dạy luật), + nói dối đo được |
| **Điểm số = sinh tồn** | | **chết.** Sinh tồn thành ràng buộc, không phải mục tiêu |
| **Q1 = so loài bằng sinh tồn** | | **chết.** Q1 thành: so bằng tốc độ và độ chính xác quy nạp |
| Chế độ mở M6 | giữ | luật ẩn làm nó **hay hơn**: người lạ cắm máy vào để đua tìm luật |

**Không có bước nào của v4 bị vứt.** M0 và M1 chạy y nguyên. Bạn đang đứng ở đâu thì đi tiếp từ đó.

### 0.4 Mâu thuẫn với v4 §Bước 14 — và cách gỡ

v4 viết, đúng ở thời điểm đó:

> *"LLM không học qua các lần gọi. Không nói luật thì chúng không suy ra luật — chúng bịa luật từ prior."*

Bản v5 dựa hoàn toàn vào việc chúng **suy ra luật được**. Hai điều này chỉ mâu thuẫn nếu bạn để nguyên phần còn lại. Gỡ bằng ba việc:

**1. Tách hai loại luật.** Đây là phân biệt quan trọng nhất của cả tài liệu.

| | **Luật nền** | **Luật ẩn** |
|---|---|---|
| Là gì | Kinh tế năng lượng, di chuyển, chiến đấu, tầm nhìn, chết, hồi sinh | 2–3 quan hệ nhân quả bốc thăm mỗi ván |
| Bất biến giữa các ván | có | **không** |
| Nói cho model biết | **nói hết**, định tính, ở khối A | **giấu tuyệt đối** |
| Vì sao xử lý vậy | Suy ra từ số 0 thì tốn cả ván và đo nhầm thứ | Suy ra được **là chính bài thi** |

Nguyên tắc v4 vẫn sống nguyên vẹn, chỉ hẹp phạm vi lại: *nói cơ chế nền, giấu đối thủ, giấu luật ẩn.*

**2. Đưa dấu vết trải nghiệm vào context.** v4 nói đúng rằng không có gradient giữa các lần gọi. Nên v5 không dựa vào cái đó. Quy nạp xảy ra **trong context, trong một ván**, từ một sổ tay sự kiện mà server dựng sẵn (§7). Đây là in-context induction — thứ model làm được, và thứ đáng đo.

**3. Cắt đứt prior.** v4 lo model bịa luật từ prior phim tài liệu. Lo đúng. Nên bề mặt (màu quả, hình dạng) bị **hoán vị ngẫu nhiên mỗi ván** (§2.6), và có hẳn một nhánh thí nghiệm đo lượng prior rò rỉ (§10.2). Ván này quả đỏ độc, ván sau quả đỏ bổ nhất. Prior không những vô dụng — nó thành **cái bẫy**, và ai bám vào nó thì chết nhanh hơn.

---

## 1. Kiến trúc khái niệm

### 1.1 Ba tầng

```
┌─ TẦNG 1 — VẬT LÝ NỀN ────────────────────────────────┐
│  Bất biến mọi ván. Nói cho agent biết ở khối A.       │
│  upkeep, damage, sight, chết, hồi sinh, ăn, đánh.     │
│  = toàn bộ v4 M0+M1.                                   │
├─ TẦNG 2 — LUẬT ẨN ───────────────────────────────────┤
│  Bốc thăm bằng seed. 2–3 luật/ván. Agent KHÔNG biết.  │
│  Chèn vào vòng tick như một hook sau mỗi sự kiện.     │
│  = §2, §3.                                             │
├─ TẦNG 3 — NIỀM TIN ──────────────────────────────────┤
│  Sổ Luật của từng cá thể. Là thứ được chấm.           │
│  Riêng tư trừ khi chủ nó quyết định dạy cho kẻ khác.  │
│  = §4, §6.                                             │
└────────────────────────────────────────────────────────┘
```

Tầng 2 là thứ duy nhất mới trong sim. Tầng 3 không sống trong sim — nó sống trong `Creature.codex` và chỉ được chấm **sau ván**, offline.

**Bất biến kiến trúc:** tầng 3 không bao giờ được đọc bởi tầng 1 hay tầng 2. Sổ Luật không cho sức mạnh gì cả. Ghi đúng luật vào sổ **không** tự động làm bạn sống lâu hơn — bạn phải *hành động* theo nó. Khoảng cách giữa hai thứ đó (§9, `exploit_lag`) là một trong những chỉ số thú vị nhất bản này sinh ra.

### 1.2 Vòng đời một ván

```
seed ──► LawGen ──► [L1, L2, L3]  ─── giấu ───►  ván 400 tick
           │                                          │
           │                                          ├─ agent thí nghiệm, chết, quan sát
           │                                          ├─ agent ghi/sửa Sổ Luật
           │                                          └─ agent dạy hoặc giấu
           │                                          ▼
           └──────────► Verifier ◄──── codex cuối + mốc thời gian + log
                            │
                            ├─ match score (bảng chân trị, §5.1)
                            ├─ t_discover  (§5.5)
                            ├─ pred_acc    (§5.4 tầng 2)
                            ├─ exploit_lag (§5.4 tầng 3)
                            └─ điểm xã hội (§6)
                            ▼
                    REVEAL — công bố luật thật cho người xem và cho log
```

**`REVEAL` không phải trang trí.** Nó là (a) khoảnh khắc hay nhất để xem, (b) nguồn dữ liệu SFT hậu nghiệm ở §11.6 — biết đáp án rồi thì mọi ván thua vẫn sinh ra được một chuỗi suy luận mẫu.

### 1.3 Bốn quyết định mà agent phải cân

Đây là toàn bộ chiều sâu của trò chơi, và cả bốn đều **đo được**:

| Quyết định | Đánh đổi | Chỉ số |
|---|---|---|
| **Thí nghiệm hay không** | Biết thêm ↔ có thể chết | `experiments_per_discovery`, `death_by_experiment` |
| **Thí nghiệm hay hóng** | Tự trả giá ↔ chờ kẻ khác trả giá hộ (rẻ hơn, nhưng chậm và thụ động) | `obs_ratio` = số quan sát gián tiếp / trực tiếp |
| **Ghi hay chờ chắc** | Ghi sớm được điểm tốc độ ↔ ghi sai chiếm mất ô sổ | `conf` vs đúng/sai → Brier score |
| **Dạy hay giấu** | Được citation + đồng minh sống sót ↔ mất độc quyền | `share_rate`, `hoard_payoff`, `deception_rate` |

Cột giữa là cái làm nó vui. Cột phải là cái làm nó train được. **Bản v5 thắng vì hai cột này không đánh nhau.**

---

## 2. Ngôn ngữ luật — LawDSL

### 2.1 Vì sao phải là ngôn ngữ hình thức

Agent có thể phát biểu luật bằng tiếng Việt: *"tôi nghĩ quả đỏ độc khi vừa uống nước xong"*. Chấm câu đó cần một model làm giám khảo. Model giám khảo thì **nhiễu, đắt, và bị chơi**. Với RLVR, giám khảo mềm là con đường ngắn nhất tới reward hacking.

Nên: agent phát biểu luật bằng **cùng một ký pháp mà bộ sinh luật dùng**, ép bằng GBNF/json_schema. Chấm thành so sánh hai cấu trúc — xác định, miễn phí, không chơi được.

> **Cho agent biết ký pháp có phải là mớm bài không?** Không. Đó là đưa cho nhà khoa học bộ ký hiệu, không phải đưa đáp án. Không gian giả thuyết ~4,4 triệu luật (§2.4); biết cú pháp không giúp bạn hơn gì việc biết "định luật vật lý viết bằng phương trình vi phân".

### 2.2 Văn phạm

```
LAW      := WHEN <Trigger> [AND <Cond>]{0,2} THEN <Effect>
```

Một luật là **một** mệnh đề. Không lồng, không OR, không phủ định ở mức luật. Ba lý do: dễ chấm, dễ kiểm tra khả giải, và vì luật tự nhiên thật sự trông như thế.

### 2.3 Từ vựng

**Trigger — sự kiện châm ngòi** (11 loại):

| Kind | Tham số | Nghĩa |
|---|---|---|
| `EAT` | `FRUIT_A..D`, `CORPSE` | ăn một thứ |
| `DRINK` | — | uống ở ô `WATER` |
| `ATTACK` | `SAME_SP`, `OTHER_SP`, `ANY` | mình tấn công |
| `HIT_BY` | như trên | bị tấn công |
| `STEP_ON` | `PLAIN/WATER/BUSH/ROCK/FIRE` | bước vào ô |
| `ADJACENT` | (lớp, n=1..3) | có n con cạnh mình, liên tiếp ≥2 tick |
| `SPEAK` | `ALARM/AGGR/SUBM/NEUTRAL` | mình phát tín hiệu |
| `REST` | k=2..5 | đứng yên k tick liền |
| `DEATH_NEAR` | r=1..3 | có con chết trong bán kính r |
| `PHASE_ENTER` | `DAY/NIGHT` | thời khắc chuyển pha |
| `LOW_ENERGY` | — | energy tụt dưới 25% |

**Cond — điều kiện kèm** (10 loại, 0–2 cái):

| Kind | Tham số | Nghĩa |
|---|---|---|
| `PHASE` | `DAY/NIGHT` | đang ban ngày/đêm |
| `TERRAIN` | 5 loại | đang đứng trên |
| `HP` | `LOW/MID/HIGH` | dải máu (<33% / 33–66% / >66%) |
| `ENERGY` | như trên | dải năng lượng |
| `RECENT` | (Trigger, k=3..15) | trong k tick qua đã làm việc đó |
| `COUNT` | (lớp, r=1..3, ≥/≤, n) | đếm sinh vật quanh mình |
| `AGE` | `YOUNG/OLD` (< / ≥ 100 tick) | tuổi |
| `WIND` | `WITH/AGAINST` | hướng đi so với gió |
| `SUBJECT` | `ARMOR≥3`, `SPEED≥3`, `BRAIN≤1`, `SAME_SP` | luật chỉ tác động lên ai (D3+) |
| `ALONE` | r=2 | không có sinh vật nào trong bán kính 2 |

**Effect — hệ quả** (12 loại × 3 độ lớn × 3 thời hạn):

| Kind | Tham số | Ghi chú |
|---|---|---|
| `DAMAGE` / `HEAL` | mag, dur | mag ∈ {SMALL 1–5, MED 6–15, BIG 16–30} |
| `ENERGY_GAIN` / `ENERGY_DRAIN` | mag, dur | |
| `POISON` | mag, dur | sát thương lặp |
| `STUN` / `BLIND` | dur | dur ∈ {INSTANT 0, SHORT 1–3, LONG 4–10} |
| `SPEED_UP` / `SPEED_DOWN` | mag, dur | |
| `ARMOR_UP` / `ARMOR_DOWN` | mag, dur | |
| `REVEAL` | r, dur | lộ vị trí cho mọi kẻ trong r |
| `SPAWN` | (Item, r) | mọc thứ gì đó gần đó |
| `SPREAD` | (Terrain, dir) | địa hình lan (lửa, rêu…) |
| `TELEPORT` | r | dịch ngẫu nhiên trong r |

**Bất biến chấm điểm:** khi so hai luật, `DAMAGE(11)` và `DAMAGE(12)` **là một** — chỉ so tới mức *rổ* (`MED`). Agent không có cách nào đo con số chính xác nên không được đòi hỏi nó. Rổ hoá là điều kiện công bằng, không phải nới lỏng.

### 2.4 Ba ví dụ của bạn, viết bằng DSL

| Tiếng Việt | LawDSL | Hạng |
|---|---|---|
| Quả đỏ độc nếu ăn sau khi uống nước | `WHEN EAT(FRUIT_A) AND RECENT(DRINK, 10) THEN POISON(MED, LONG)` | D2 |
| Lửa lan theo gió nhưng chỉ ban đêm | `WHEN STEP_ON(FIRE) AND PHASE(NIGHT) THEN SPREAD(FIRE, WIND)` | D4 |
| Hai con đứng cạnh nhau thì cả hai hồi máu | `WHEN ADJACENT(ANY, 1) THEN HEAL(SMALL, LONG)` | D1 |

Ba ví dụ của bạn nằm gọn trong văn phạm mà không phải bẻ gì cả. Đó là kiểm tra tốt nhất cho một DSL.

### 2.5 Kích thước không gian giả thuyết

```
trigger cụ thể   ≈ 48
cond 0 cái       = 1
cond 1 cái       ≈ 55
cond 2 cái       ≈ C(55,2) = 1 485
tổng phần cond   ≈ 1 541
effect cụ thể    ≈ 60
──────────────────────────────────
|H| ≈ 48 × 1541 × 60 ≈ 4 440 000
```

Đoán bừa với 3 ô sổ: **p ≈ 7 × 10⁻⁷**. Kể cả tính điểm từng phần rộng rãi, đoán bừa vẫn cho kỳ vọng gần 0. Không gian con D1 (không điều kiện) chỉ có ~2 880 phần tử — về lý thuyết vét được — nhưng §4.3 (không phản hồi) và §4.1 (sổ có giới hạn ô) làm việc vét cạn trở nên vô nghĩa: vét mà không ai chấm cho biết đúng sai thì bạn chẳng thu được gì.

### 2.6 Chống rò prior — hoán vị bề mặt

**Đây là chỗ dễ hỏng nhất của toàn bộ thiết kế.** Nếu quả độc luôn màu đỏ thì bạn không đo quy nạp — bạn đo **model có nhớ rằng đỏ = nguy hiểm hay không**. Model to sẽ thắng, vì nó thuộc bài hơn, và bạn sẽ tưởng nó suy luận giỏi hơn. Đó chính xác là sai lầm mà cả dự án này tồn tại để tránh.

**Luật:** mỗi ván, ánh xạ *bề mặt → lớp* được bốc thăm lại.

```python
# mỗi ván, hoán vị độc lập với luật
surface = rng.shuffle([("đỏ","tròn"), ("xanh","dài"), ("vàng","gai"), ("tím","dẹt")])
FRUIT_A .. FRUIT_D  ←  surface[0..3]
```

Agent thấy "quả đỏ tròn", engine thấy `FRUIT_A`. Ván sau, "quả đỏ tròn" là `FRUIT_C`. Sổ Luật ghi theo **bề mặt** (vì đó là thứ agent quan sát được), verifier dịch sang lớp trước khi so.

Áp dụng hoán vị cho: màu/hình quả, âm sắc của 4 tín hiệu `say`, tên 5 loài (ở nhánh `NEUTRAL_NAME`), và chiều gió.

**Không** hoán vị: vật lý nền (lửa vẫn nóng, nước vẫn ướt). Hoán vị cái đó thì khối A nói dối, và bạn phá luôn tầng 1.

### 2.7 Tách train/test theo **cấu trúc**, không theo tham số

Nếu bạn train trên luật ngẫu nhiên rồi test trên luật ngẫu nhiên khác cùng phân phối, bạn đang đo nội suy trong một không gian model đã thấy hết. Muốn biết nó **quy nạp** hay **thuộc lòng**, phải giữ lại nguyên cụm cấu trúc:

| Tập | Giữ lại |
|---|---|
| `TRAIN` | mọi thứ trừ dưới đây |
| `TEST_EFFECT` | 3 loại effect chưa từng xuất hiện lúc train (`REVEAL`, `SPREAD`, `TELEPORT`) |
| `TEST_SHAPE` | mọi luật 2 điều kiện (train chỉ thấy 0–1 điều kiện) |
| `TEST_COND` | 2 loại cond chưa thấy (`WIND`, `SUBJECT`) |

Khoảng cách `TRAIN` – `TEST_SHAPE` là con số bạn sẽ đem đi khoe. Nó trả lời được câu **"nó học tìm luật, hay học thuộc bộ luật?"** — và không có nó thì mọi kết quả huấn luyện đều đáng ngờ.

---

## 3. Bộ sinh luật — LawGen

### 3.1 Quy trình

```
def generate(seed, tier_plan, world_cfg) -> list[Law]:
    1. bốc trigger  (theo tier)
    2. bốc 0–2 cond (theo tier)
    3. bốc effect + rổ mag/dur
    4. GATE A — quan sát được?      (§3.2)
    5. GATE B — khả giải?           (§3.3)
    6. GATE C — định danh được?     (§3.4)
    7. GATE D — không xung đột với luật đã bốc, không xung đột luật nền
    trượt bất kỳ gate nào → bốc lại (tối đa 200 lần rồi hạ tier)
```

### 3.2 Gate A — quan sát được (observability)

**Bất biến cứng:** mọi ký hiệu trong luật phải nằm trong luồng quan sát của cá thể có `sense` thấp nhất.

```
features(law) ⊆ observable(min_sense)
```

Ví dụ trượt: `WHEN ATTACK(x) AND COUNT(OTHER_SP, r=3, ≥, 2) THEN ...` — con `sense=1` có `sight_radius=3`, nhưng nếu đối tượng nấp trong `BUSH` thì nó không đếm được. Luật đòi hỏi thông tin mà giác quan không cấp là **luật không công bằng**, và nó biến điểm khám phá thành xổ số.

Viết gate này thành một hàm thuần và **test nó trước khi viết LawGen**. Nó là thứ dễ quên nhất và đắt nhất khi phát hiện muộn.

### 3.3 Gate B — khả giải (solvability)

Bốc được luật đẹp mà cả ván nó không kích hoạt lần nào thì vô nghĩa.

**Cách đo:** chạy 200 rollout Monte-Carlo với **chính sách tham chiếu tò mò** — random walk có xác suất thực hiện mỗi hành động châm ngòi. Không cần LLM, chạy vài giây.

| Đại lượng | Ngưỡng nhận |
|---|---|
| `t_first_fire` — tick trung vị luật kích hoạt lần đầu | ≤ 0.25 · T |
| `n_fire` — số lần kích hoạt trong T tick | ≥ 5 |
| `p_never` — tỉ lệ rollout luật không kích hoạt lần nào | ≤ 5% |

Trượt thì **tự sửa trước khi bốc lại**: tăng mật độ item liên quan, nới `RECENT(k)`, hạ `n` trong `COUNT`. Chỉ bốc lại khi sửa không cứu được.

> **Bẫy:** đừng dùng chính sách tham chiếu là chính con reflex ở v4 bước 9. Reflex có thiên lệch (đói mới đi ăn), nên nó ước lượng thấp cho luật liên quan tới ăn và ước lượng cao cho luật liên quan tới đánh. Dùng random tò mò, có thiên lệch nhưng **đồng đều**.

### 3.4 Gate C — định danh được (identifiability)

Gate tinh vi nhất, và bỏ nó thì bạn sẽ chấm oan agent hàng loạt.

Xét `WHEN EAT(FRUIT_A) AND PHASE(NIGHT) THEN DAMAGE(MED)`. Nếu trong ván đó quả A chỉ mọc ban đêm, thì **không tồn tại bằng chứng nào** phân biệt luật thật với `WHEN EAT(FRUIT_A) THEN DAMAGE(MED)`. Agent viết cái thứ hai là suy luận đúng đắn nhất có thể từ dữ liệu nó có — mà bạn lại trừ điểm.

**Yêu cầu:** phải tồn tại đủ **trường hợp gần trượt** (trigger xảy ra mà điều kiện sai) để điều kiện suy ra được.

```
n_near_miss ≥ 3   với mỗi cond trong luật
```

Đo cùng lúc với Gate B trên chính 200 rollout đó — miễn phí.

> **Vì sao không sửa ở chỗ chấm điểm mà sửa ở chỗ sinh luật?** Vì chấm phải chấm theo *sự thật*, không theo *bằng chứng agent tình cờ có*. Nếu bạn nới điểm cho luật không định danh được thì hai agent gặp bằng chứng khác nhau bị chấm bằng hai thước khác nhau — và điểm hết so sánh được. Sửa ở đầu vào: chỉ phát ra những đề bài **giải được**.

### 3.5 Bao nhiêu luật một ván

| Ván | Cấu hình | Dùng cho |
|---|---|---|
| `SOLO_LAB` | 1 luật D1 hoặc D2, không có loài khác | huấn luyện RL giai đoạn đầu (§11.5) |
| `STANDARD` | 1×D1 + 1×D2 + 1×(D3 hoặc D4) | mặc định, mọi thí nghiệm |
| `HARSH` | 2×D2 + 1×D3, + 1 **luật giả** (§3.6) | thử độ bền |

Quá 3 luật thì ngân sách chú ý của model vỡ và điểm biến thành nhiễu. Dưới 2 thì phương sai mỗi ván quá lớn.

### 3.6 Luật giả — mồi nhử

Ở `HARSH`, chèn thêm một quan hệ **tương quan mà không nhân quả**: ví dụ quả B luôn mọc gần ô `ROCK`, nhưng ROCK không gây ra gì cả. Agent nào ghi `WHEN STEP_ON(ROCK) THEN ...` là đã nhầm tương quan với nhân quả.

Đây là bài kiểm tra khoa học thật sự, và nó **miễn phí** — chỉ là một thiên lệch trong bộ sinh bản đồ. Chỉ số: `spurious_claim_rate`.

---

## 4. Sổ Luật và hành động CLAIM

### 4.1 Sổ Luật (Codex)

```python
@dataclass
class CodexEntry:
    law: Law            # cấu trúc DSL, viết theo BỀ MẶT agent quan sát
    conf: int           # 1..5, agent tự khai
    written_at: int     # tick
    source: str         # "self" | creature_id đã dạy mình
    
codex: list[CodexEntry | None]   # độ dài cố định = codex_size
```

**Sổ có số ô cố định và ít.** Đây là cơ chế chống spam quan trọng nhất: muốn ghi giả thuyết mới khi sổ đầy thì phải **xoá một cái cũ**. Bạn buộc agent phải *chọn tin cái gì*, thay vì liệt kê mọi khả năng.

| brain | `codex_size` | `events_in_prompt` | `claim_budget` (token) |
|---|---|---|---|
| 0 | 1 | 6 | 24 |
| 1 | 1 | 8 | 44 |
| 2 | 2 | 12 | 64 |
| 3 | 3 | 16 | 84 |
| 4 | 3 | 20 | 104 |
| 5 | 4 | 24 | 124 |

> Đây là chỗ `brain` đổi nghĩa. Ở v4 nó là "nhiều token hơn" — một lợi thế thô. Ở v5 nó là **dung lượng nhận thức**: nhớ được nhiều sự kiện hơn, giữ được nhiều giả thuyết song song hơn, diễn đạt được luật phức tạp hơn. Con L5 (`brain 0`) giữ đúng **một** niềm tin về thế giới. Nó không ngu vì bạn phạt nó — nó ngu vì bộ nhớ làm việc của nó có một ô.

### 4.2 CLAIM hai pha

Con L5 có 32 token output. Không đủ để vừa ra goal vừa viết luật. Nên tách:

**Pha 1 — cờ (miễn phí, nằm trong quyết định thường):**
```json
{"note": "...", "goal": "FORAGE", "ttl": 5, "want_codex": true}
```
`want_codex` tốn 1–2 token. Con nào cũng gánh được.

**Pha 2 — gọi riêng**, chỉ khi cờ bật **và** `tick - last_claim ≥ CLAIM_COOLDOWN` (25 tick):
```json
{"op": "SET", "slot": 1,
 "law": {"trigger": {"kind":"EAT","arg":"quả đỏ tròn"},
         "conds":   [{"kind":"RECENT","arg":"DRINK","k":10}],
         "effect":  {"kind":"POISON","mag":"MED","dur":"LONG"}},
 "conf": 3}
```
`op ∈ {SET, DROP, CONF}`. Ép bằng GBNF từ chính văn phạm §2.2 — không có đường nào sinh ra luật sai cú pháp.

**Chi phí:** `COST_CLAIM = 4.0` energy + `tokens_used / 50` như mọi lần nghĩ. Ghi bừa thì đói.

### 4.3 Không phản hồi — quyết định thiết kế, không phải tiết kiệm

**Agent không bao giờ được biết luật nó ghi đúng hay sai, cho tới `REVEAL` cuối ván.**

Ba lý do, xếp theo độ quan trọng:

1. **Giết chết vét cạn.** Có phản hồi thì thuật toán tối ưu là: ghi bừa, xem đúng/sai, lặp. Đó là tấn công vào verifier chứ không phải khám phá thế giới. Không phản hồi thì thông tin **chỉ** đến từ thế giới.
2. **Đúng về mặt khoa học.** Tự nhiên không chấm bài cho bạn. Bạn kiểm tra giả thuyết bằng cách tiên đoán rồi quan sát, không bằng cách hỏi trọng tài.
3. **Buộc phải hiệu chỉnh tự tin.** Không ai xác nhận thì `conf` mà agent tự khai trở thành một phát biểu thật về niềm tin của nó — và đo được bằng Brier score (§9).

Hệ quả với RL: reward là **ở cuối tập** (terminal), không dày. Nhưng nó **có đáp án** — và một tín hiệu thưa có đáp án tốt hơn vô hạn lần một tín hiệu dày không có đáp án. Đó chính là chỗ v4 chết.

### 4.4 Bẫy

- **Đừng cho tầng phản xạ đọc codex.** Nếu reflex tự động né quả độc khi codex ghi độc, bạn đã hard-code việc khai thác và `exploit_lag` (§9) mất hết ý nghĩa. Khai thác **phải** đi qua goal do LLM chọn.
- **Đừng xoá codex khi chết.** v4 bước 12 xoá `adapt_points` khi chết nhưng giữ trí nhớ. Codex theo vế thứ hai: chết mất cơ thể, không mất hiểu biết. Xoá thì mọi ván thành 20 tick đầu lặp đi lặp lại.
- **`slot` ngoài phạm vi** là lỗi ngữ nghĩa hay gặp nhất của model nhỏ. Ghi vào `LLM_SEMANTIC_FAIL` như v4 bước 16, đừng crash.

---

## 5. Verifier — trái tim của bản này

### 5.1 Nguyên tắc: chấm bằng bảng chân trị, không bằng cú pháp

So sánh cây cú pháp là sai. Hai luật có thể viết khác nhau mà **hành xử y hệt**, và agent viết cách nào cũng phải được điểm như nhau.

> **Định nghĩa:** hai luật bằng nhau khi chúng cho cùng kết quả trên cùng tình huống.

```
match(C, L) = P_{s ~ D}[ C(s) ≡ L(s) ]     chuẩn hoá theo null
```

Không cần canonicalizer, không cần luật viết lại, không cần xử lý giao hoán của `AND`. Điểm từng phần rơi ra tự nhiên: đoán đúng trigger sai điều kiện được ~0.5, chứ không phải 0.

### 5.2 Không gian tình huống và lấy mẫu phân tầng

Một **tình huống** `s` = (sự kiện châm ngòi + đủ ngữ cảnh để mọi cond đánh giá được). Verifier chạy được cả `C` lẫn `L` trên `s` vì cả hai đều là cấu trúc DSL.

Lấy mẫu **bắt buộc phân tầng**, nếu không thì mọi thứ vỡ:

| Tầng | Tỉ lệ | Vì sao |
|---|---|---|
| `L` kích hoạt | 40% | |
| Trigger đúng, cond sai (**gần trượt**) | 40% | tầng quyết định — không có nó thì "đoán trigger, kệ cond" ăn điểm cao |
| Không liên quan | 20% | |

Trong tầng "gần trượt", trải đều theo **từng chiều cond một**: hỏng `PHASE` riêng, hỏng `RECENT` riêng, hỏng cả hai. Có vậy điểm từng phần mới phản ánh đúng "hiểu được bao nhiêu phần của luật".

`N_SITUATIONS = 400` mỗi luật. Xác định theo seed → cùng luật cho cùng bảng chấm, mọi lần chạy.

### 5.3 Công thức

```
acc  = (1/N) Σ_s  1[ C(s) ≡ L(s) ]
acc₀ = (1/N) Σ_s  1[ NULL(s) ≡ L(s) ]        # NULL = "không có luật nào"
match = clip( (acc − acc₀) / (1 − acc₀),  0, 1 )
```

Chuẩn hoá theo null là **bắt buộc**. Không có nó, một agent ghi luật vô hại kích hoạt cực hiếm sẽ ăn 0.9 điểm vì "hầu như luôn dự đoán đúng là chẳng có gì xảy ra". Với chuẩn hoá, null ăn đúng **0**.

`≡` so ở mức rổ: `(effect_kind, mag_bucket, dur_bucket)`. Sai loại effect → 0. Đúng loại, lệch một rổ
→ **0.85 điểm cho chiều đó** (rổ liền kề mới được, cách hai rổ thì 0); nhiều chiều thì **nhân** lại.

> **Sửa 2026-08-29 (L-06).** Bản đầu ghi 0.5, mâu thuẫn với phiếu L-06 §6 vốn đòi ca (g)
> ra 0.80–0.90. Giữ phiếu vì nó ràng buộc **thứ tự**: "đúng hết, lệch một rổ" phải tốt hơn hẳn
> "sai hẳn điều kiện". Với 0.5 thì hai ca bằng nhau và thang đo mất trật tự. Số đo sau khi sửa:
> trùng khít 1.00 · lệch một rổ 0.85 · lệch hai chiều 0.72 · bỏ một cond 0.66 · bỏ cả hai cond 0.00
> · sai hệ quả 0.00 · sai trigger 0.00 · null 0.00 · 1000 luật ngẫu nhiên: trung bình **0.000**.

Ngưỡng "coi như đã tìm ra": `θ = 0.8`.

### 5.4 Ba tầng chấm

Ba tầng đo ba thứ khác nhau. Đừng gộp.

**Tầng 1 — Phát biểu.** `match(codex, L)` như trên. Trả lời: *nó nói đúng không?*

**Tầng 2 — Tiên đoán (oracle).** Cuối ván, hỏi agent 8 câu tình huống lấy từ chính `D` phân tầng: *"Bạn ăn quả đỏ tròn ngay sau khi uống nước, lúc ban đêm, máu đầy. Chuyện gì xảy ra?"* Agent trả lời bằng cấu trúc effect. Ground truth có sẵn.

```
pred_acc = số câu đúng / 8      (baseline null ≈ 0.4 sau phân tầng → chuẩn hoá tương tự)
```

Trả lời: *nó hiểu, hay nó vừa may?* Tầng này bắt được kiểu "đúng vì lý do sai" mà tầng 1 bỏ lọt. Chi phí: 8 lần gọi LLM ngắn mỗi ván — rẻ.

**Tầng 3 — Hành vi.** Sau khi entry đúng vào sổ ở tick `t*`, hành vi có đổi không?

```
rate_before = tần suất thực hiện trigger có hại trong [t*−60, t*]
rate_after  = tần suất trong [t*, t*+60]
exploited   = rate_after ≤ 0.5 × rate_before        (luật có hại)
            | rate_after ≥ 1.5 × rate_before        (luật có lợi)
exploit_lag = tick đầu tiên thoả điều kiện trên − t*
```

Trả lời: *biết rồi có làm không?* **Khoảng cách giữa tầng 1 và tầng 3 là phát hiện thú vị nhất mà môi trường này có thể sinh ra**, và nó chỉ tồn tại vì §4.4 cấm reflex đọc codex.

> **Bẫy mẫu nhỏ:** nếu trigger hiếm, `rate_before` có thể là 1/60. Đòi hỏi `n ≥ 4` lần xảy ra ở mỗi cửa sổ, không đủ thì ghi `exploit_lag = NA`, đừng ghi 0.

### 5.5 Điểm khám phá

Với mỗi luật thật `L_i`:

```
t_i      = tick sớm nhất có entry với match ≥ θ VÀ entry đó còn trong sổ tới cuối ván
speed_i  = clip(1 − t_i / T, 0, 1)
R_i      = w_i · match_final(L_i) · (0.4 + 0.6 · speed_i)
```

Ba chi tiết, mỗi cái vá một lỗ:

- **"còn tới cuối ván"** giết đoán mò-rồi-bỏ. Đoán trúng ở tick 30 rồi tick 40 xoá đi thì không tính.
- **Sàn 0.4** để tìm ra muộn vẫn hơn hẳn không tìm ra. Không có sàn thì agent tìm ra ở tick 380 được ~0 và bạn mất tín hiệu ở phần đuôi — đúng chỗ RL cần nó nhất lúc đầu.
- **`w_i` theo hạng:** D1 = 1.0, D2 = 1.5, D3/D4 = 2.2. Luật khó đáng nhiều điểm hơn.

**Tổng phần thưởng một ván:**

```
R = Σ R_i  +  0.5·R_pred  +  0.3·R_exploit  +  0.3·R_social  +  0.1·R_survive
```

`R_survive` = tỉ lệ tick còn sống, **hệ số 0.1**. Nó không phải mục tiêu nữa — nó là dây neo, đảm bảo hiểu biết phải dùng được. Bỏ hẳn cũng chạy; giữ nhỏ thì hành vi trông giống sinh vật hơn và video hay hơn.

### 5.6 Bảng tấn công → phòng thủ

Đây là bảng bạn phải đọc lại mỗi lần định sửa công thức điểm.

| Tấn công | Cách hack | Phòng thủ |
|---|---|---|
| Vét cạn không gian D1 | ghi lần lượt 2 880 luật | sổ ≤ 4 ô + `CLAIM_COOLDOWN` 25 tick + không phản hồi |
| Đoán mò may mắn | ghi bừa sớm, trúng một cái | yêu cầu entry tồn tại tới cuối ván |
| Nông dân null | ghi luật gần như không bao giờ kích hoạt | chuẩn hoá theo `acc₀` → đúng 0 điểm |
| Chỉ đoán trigger | bỏ qua cond, ăn điểm từng phần cao | 40% mẫu là "gần trượt", trải đều theo từng cond |
| Gọi tên prior | dựa "đỏ = độc" | hoán vị bề mặt mỗi ván (§2.6) + nhánh đối chứng (§10.2) |
| Nhồi sổ tay | viết rác vào notepad để chiếm context | cap 200 ký tự, tính vào `cost_think` |
| Vòng lặp trích dẫn | A dạy B, B dạy lại A, cả hai ăn credit | DAG provenance, credit chảy một chiều theo thứ tự thời gian, mỗi luật ăn credit **một lần** (§6.2) |
| Rải truyền đạo | dạy tất cả mọi người mọi thứ để gom credit | credit chỉ tính khi người nhận **chưa** có entry đúng, và entry của người dạy đã đúng **trước đó** |
| Dò verifier | thử nghiệm để đoán bảng chấm | verifier chạy **offline sau ván**, không có mặt trong sim, không có kênh nào chạm tới |
| Thuộc bộ luật | overfit vào phân phối luật lúc train | tách train/test theo cấu trúc (§2.7) |

### 5.7 Dùng làm reward cho RL

**Nhóm (group) cho GRPO phải cố định luật.** N rollout cùng seed thế giới, cùng bộ luật, cùng slot loài; chỉ khác nhau ở sampling. Advantage = `(R − mean_group) / (std_group + 1e-6)`.

**Đổi bộ luật giữa các nhóm, đừng đổi trong nhóm.** Trong nhóm đổi luật thì phương sai của điểm bị chi phối bởi độ khó đề, không phải bởi chất lượng chính sách — và advantage thành nhiễu. Đây là lỗi dễ mắc nhất khi mang môi trường này sang RL.

`N_GROUP = 8`. Nhỏ hơn thì ước lượng baseline quá nhiễu với reward thưa như thế này.

**Reward shaping tối thiểu.** Cám dỗ sẽ là thưởng cho "đã thí nghiệm", "đã ghi sổ". Đừng. Mọi shaping ở đây đều là một hàm mục tiêu mới mà agent sẽ tối ưu thay cho cái bạn muốn. Nếu thưa quá không học được thì hạ độ khó (`SOLO_LAB`, 1 luật D1, T=150), đừng làm dày reward.

---

## 6. Tầng xã hội: dạy, giấu, lừa

### 6.1 TEACH

Mở rộng trường `say` của v4 bước 24:

```json
"say": {
  "signal": "ALARM|AGGRESSIVE|SUBMISSIVE|NEUTRAL",
  "text":   "≤60 ký tự",
  "teach":  {"slot": 0}          // tuỳ chọn: phát nội dung ô sổ đó ra
}
```

Quy tắc nghe, kế thừa nguyên §bước 24:

| Người nghe | Nhận được |
|---|---|
| Cùng loài, trong `sight_radius` của **người nghe** | `signal` + `text` + **luật đầy đủ** |
| Khác loài, trong `sight_radius` | `signal` + `text` + luật **thiếu effect** (chỉ trigger + cond) |
| Mọi kẻ trong `2 × sight_radius` | chỉ `signal` |

Khác loài nhận thiếu effect là chi tiết cố ý: nó biến việc dạy liên loài thành **một nửa món quà** — đủ để có ích, không đủ để cho không. Và nó tạo ra thị trường: bạn có mảnh trigger, tôi có mảnh effect, đổi không?

`COST_TEACH = 5.0` energy. Dạy tốn hơn nói, vì nó dài hơn và vì phải có cái giá thật thì im lặng mới thành lựa chọn.

**Người nghe không tự động tin.** Luật nghe được vào **hàng chờ**, hiện trong prompt ở mục `nghe được`, kèm ai nói và độ tin cậy quá khứ của kẻ đó. Muốn vào sổ thì chính agent phải `SET` — tốn ô sổ, tốn energy. Chép mù thì hết ô sổ để chứa thứ mình tự tìm ra.

### 6.2 Provenance và citation

```python
@dataclass
class Provenance:
    law_id: str          # định danh của luật THẬT (verifier biết, agent không)
    discoverer: str      # creature_id ghi đúng đầu tiên
    chain: list[str]     # ai dạy ai, theo thứ tự tick
```

**Thưởng trích dẫn:** khi cá thể B có entry đúng, và truy ngược ra A đã dạy B trước đó, và A đã đúng **trước** thời điểm dạy, thì A nhận `+0.3 × R_i(B)`. B không mất gì.

Ba khoá chống farming, cả ba đều bắt buộc:
1. Credit chảy **một chiều** theo thời gian — dạy lại người đã biết không ăn gì.
2. Mỗi cặp (luật, người nhận) tính **một lần**, dù dạy bao nhiêu lần.
3. Chuỗi tính tối đa **2 nấc**. A→B→C thì A nhận từ B, không nhận từ C. Không thì mọi tháp đa cấp đều lãi.

### 6.3 Cái nút xoay: luật đơn độc và luật hợp tác

Đây là chỗ bạn *thiết kế* ra tình thế lưỡng nan thay vì hy vọng nó tự xuất hiện.

| Loại luật | Ví dụ | Khai thác được một mình? | Áp lực |
|---|---|---|---|
| **Đơn độc** | `EAT(FRUIT_C) THEN ENERGY_GAIN(BIG)` | được | **giấu** — nói ra là mất mỏ ăn |
| **Hợp tác** | `ADJACENT(ANY,1) THEN HEAL(SMALL,LONG)` | **không**, cần hai con | **dạy** — không nói thì không ai đứng cạnh |
| **Phòng thủ** | `STEP_ON(FIRE) AND PHASE(NIGHT) THEN SPREAD` | được, nhưng đồng loại chết thì mình cũng thiệt | tuỳ vào việc bạn cần đồng loại tới đâu |

**LawGen phải bốc ít nhất một luật mỗi loại ở `STANDARD`.** Nếu cả ba luật đều đơn độc thì mọi agent duy lý đều im lặng, và bạn không quan sát được gì về hợp tác. Đây là một dòng ràng buộc trong bộ sinh, và bỏ nó thì cả §6 thành trang trí.

### 6.4 Nói dối

Dạy sai là hành động hợp lệ. `teach` chỉ phát nội dung một ô sổ — nhưng không có gì buộc agent phải **tin** cái nó vừa ghi vào ô đó.

Đo được sạch sẽ:

```
deception_rate  = số lần TEACH mà nội dung có match < 0.3 với luật thật
                  VÀ người dạy đang giữ một entry khác đúng hơn về cùng luật đó
```

Mệnh đề thứ hai là thứ tách **nói dối** khỏi **nhầm lẫn**. Không có nó thì mọi model dốt đều bị ghi là kẻ lừa đảo, và chỉ số thành vô nghĩa.

```
deception_payoff = ΔR của kẻ lừa − ΔR của kẻ bị lừa, trong 60 tick sau đó
```

Bảng chéo `deception_rate × cỡ model` sẽ là biểu đồ được nhìn nhiều nhất trong toàn bộ dự án. Tôi không đoán trước kết quả.

### 6.5 Điểm xã hội

```
R_social = 0.3 · Σ citation  −  0.2 · victim_of_deception  +  0.1 · knowledge_diffusion_bonus
```

Không thưởng trực tiếp cho việc lừa. Nếu lừa có lợi thì nó có lợi **qua** `R_i` và `R_survive` — như đời thật. Thưởng thẳng cho việc lừa là bảo model đi lừa, và thế thì bạn đo lại chính hàm reward của mình.

---

## 7. Kênh quan sát: sổ tay thực địa

### 7.1 Sổ tay sự kiện

Không có ký ức sự kiện thì không có quy nạp. Đây là bổ sung **bắt buộc**, không phải tuỳ chọn.

Server dựng, cắt theo `events_in_prompt` (§4.1), định dạng cột cố định:

```
SỔ TAY (mới nhất trước):
t382 TÔI ăn quả đỏ tròn        → mất máu nhiều, kéo dài     [đêm, vừa uống nước t379]
t377 TÔI uống nước             → không thấy gì               [đêm]
t361 THẤY L5#2 ăn quả đỏ tròn  → nó mất máu                  [đêm]
t340 TÔI ăn quả đỏ tròn        → không thấy gì               [ngày]
```

Bốn cột: **thời điểm · ai · làm gì · kết quả · [ngữ cảnh]**. Ngữ cảnh trong ngoặc là thứ chứa lời giải, và nó phải có mặt — nếu không thì luật có `cond` trở thành không định danh được (§3.4) ngay ở tầng quan sát, dù bộ sinh đã kiểm.

**Chọn cái gì để ghi khi tràn:** ưu tiên (1) sự kiện có kết quả bất thường, (2) sự kiện của chính mình, (3) mới nhất. Đừng chỉ lấy N cái gần nhất — 20 lần "đi bộ, không có gì" sẽ đẩy hết bằng chứng ra khỏi context, và bạn không hiểu nổi vì sao model to cũng không tìm ra luật.

> **Bẫy tokenizer:** ngữ cảnh trong ngoặc phải **có mặt kể cả khi bình thường**. Nếu chỉ ghi `[đêm]` lúc trời tối và bỏ trống lúc ban ngày, model sẽ học rằng "có ngoặc = có chuyện" — một tương quan giả do bạn tự tạo ra ở tầng định dạng. Luôn ghi đủ cả pha ngày lẫn đêm.

### 7.2 Xem kẻ khác chết là thí nghiệm rẻ nhất

Sự kiện `THẤY` vào sổ tay khi nằm trong `sight_radius`. Hệ quả:

- `sense` cao thành **lợi thế khoa học**, không chỉ lợi thế chiến thuật. Trait `sense` vừa có thêm một lý do tồn tại.
- Sinh ra ăn theo (free-riding): để loài khác thử trước rồi hưởng. Đo bằng `obs_ratio`.
- Sinh ra thế lưỡng nan "ai đi trước". Không hard-code một dòng nào, và nó đúng là thứ v4 §M4 mong có mà không chắc có.

**Không** đưa vào sổ tay kết quả mà giác quan không thấy được: nhìn thấy con khác ăn quả thì thấy, nhưng nội tâm nó thì không. Ghi `→ nó mất máu` là được (máu là quan sát được qua hành vi/hiển thị), ghi `→ nó bị nhiễm độc 5 tick` là **rò rỉ đáp án**.

### 7.3 Notepad bền

200 ký tự tự do, agent tự viết, giữ giữa các lần gọi, hiện ở cuối prompt.

Vì sao cần khi đã có codex: codex chỉ chứa **kết luận** (luật hoàn chỉnh). Notepad chứa **quá trình** — *"nghi quả đỏ, nhưng 2 lần ăn ban ngày không sao"*. Không có chỗ chứa giả thuyết dở dang thì mọi lần gọi đều bắt đầu lại từ đầu, và bạn cắt mất chính cái năng lực đang muốn đo.

### 7.4 Ngân sách token — tính lại

| Khối | v4 | v5 |
|---|---|---|
| A cơ chế nền | 180 | 200 |
| A2 giao kèo (có luật ẩn, tìm nó) | — | **90** |
| B loài | 100 | 100 |
| C cơ thể | 60 | 60 |
| D từ vựng LawDSL (cắt theo brain) | — | **60–140** |
| **prefix cache được** | **340** | **510–590** |
| E trạng thái | 250 | 250 |
| E sổ tay | — | **90–330** (theo `events_in_prompt`) |
| E sổ luật + hàng chờ nghe được | — | **40–120** |
| E notepad | — | 50 |
| output | ≤212 | ≤212 (+ claim 24–124) |
| **cao nhất (L1/L5 brain 5)** | ~800 | **~1 550** |

`-c` 2048/slot của v4 **không còn đủ** cho brain cao. Đổi:

| Loài | brain | `-c` mỗi slot | slot | `-c` truyền vào |
|---|---|---|---|---|
| L1 | 4 | 3072 | 2 | **6144** |
| L2 | 3 | 3072 | 2 | **6144** |
| L3 | 3 | 3072 | 3 | **9216** |
| L4 | 1 | 2048 | 3 | **6144** |
| L5 | 0 | 1536 | 5 | **7680** |

Bộ nhớ đội thêm: Gemma-2-9B KV ≈ 336 KB/token → 6144 token ≈ **2.06 GB** (v4 là 1.4 GB). Mac 32GB: 5.8 + 2.06 = 7.9 GB. Thoải mái. PC 16GB: Llama 4.9 + KV 0.7 + Mistral 4.4 + KV 1.1 + sim 1.0 ≈ **12.1 / 16 GB**. Vẫn ổn, nhưng hết dư — đừng mở Chrome.

> **Bẫy `-c` của v4 vẫn nguyên đó và giờ nguy hiểm hơn.** `-c` là **tổng** chia cho mọi slot. Prompt v5 dài gần gấp đôi nên nếu tính nhầm, biểu hiện không phải là báo lỗi mà là **sổ tay bị cắt cụt âm thầm** — và bạn sẽ ngồi kết luận sai rằng model không quy nạp được, trong khi thật ra nó chưa bao giờ được nhìn thấy bằng chứng.

### 7.5 Prefix cache vẫn phải giữ

A + A2 + B + C + D **bất biến từng byte cả ván**. Sổ tay, sổ luật, notepad, trạng thái đều nằm ở khối E, ở **cuối**. Kiểm tra như v4 bước 14: in prompt hai lần liên tiếp, `diff` phần system phải sạch.

Cạm bẫy mới của v5: khối D (từ vựng DSL) phụ thuộc `brain`, mà `brain` **dịch được** giữa ván (v4 bước 26). Trait dịch → khối D đổi → cache vỡ → một lần prefill lại. Chấp nhận được (vài lần một ván), nhưng phải biết là nó xảy ra, và **không** được để `codex_size` co lại làm mất entry đang giữ. Trait tụt thì sổ giữ nguyên số ô, chỉ không ghi thêm được.

---

## 8. Prompt v5

```
┌─ SYSTEM (bất biến cả ván, prefill một lần) ─────────────┐
│ A   CƠ CHẾ NỀN     — server viết, giống mọi client       │
│ A2  GIAO KÈO       — "thế giới này có luật ẩn"           │
│ B   LOÀI           — chủ client viết, ≤400 ký tự         │
│ C   CƠ THỂ         — server sinh từ trait                │
│ D   TỪ VỰNG LUẬT   — cắt theo brain                      │
├─ USER (đổi mỗi lần gọi) ────────────────────────────────┤
│ E1  trạng thái + tầm nhìn                                │
│ E2  SỔ TAY                                               │
│ E3  SỔ LUẬT của tôi                                      │
│ E4  NGHE ĐƯỢC (luật kẻ khác dạy, chưa tin)               │
│ E5  ghi chú riêng (notepad)                              │
└──────────────────────────────────────────────────────────┘
```

**Khối A2, viết đúng thế này** (đây là bản lề của cả thiết kế, đừng viết lại cho hoa mỹ):

> Thế giới này có **2 hoặc 3 quy luật ẩn** mà không sinh vật nào được cho biết trước. Chúng đổi mỗi lần thế giới sinh ra. Chúng là quan hệ nhân quả: một việc xảy ra, trong một hoàn cảnh nào đó, dẫn tới một hệ quả.
> Cách duy nhất để biết là **thử và quan sát** — của chính bạn, hoặc của kẻ khác. Thử có thể giết bạn.
> Khi bạn tin mình đã tìm ra, hãy ghi vào Sổ Luật. **Không ai xác nhận đúng sai cho bạn.**
> Bề ngoài của sự vật ở thế giới này **không nói lên bản chất**. Màu sắc, hình dạng, âm thanh được xáo lại mỗi lần thế giới sinh ra. Điều bạn tin ở nơi khác có thể sai ở đây.

Câu cuối là câu quan trọng nhất trong toàn bộ prompt. Nó **nói thẳng ra rằng prior không dùng được**. Có nó, ta đo đúng thứ muốn đo. Thiếu nó, ta chỉ đo được model nào cứng đầu hơn.

**Khối D cắt theo brain:**

| brain | Được dùng |
|---|---|
| 0–1 | trigger 5 loại, **0 cond**, effect 6 loại → chỉ phát biểu được luật D1 |
| 2–3 | trigger 8, cond 5, ≤1 cond, effect 9 |
| 4–5 | toàn bộ từ vựng, ≤2 cond |

**Trừ một cond: `SUBJECT`.** Nó bị `law_config.IMPLEMENTED_CONDS` loại khỏi cả bộ sinh luật, JSON schema lẫn khối D — nên brain 4–5 có **9** cond chứ không phải 10. Lý do: `build_ctx` điền `SUBJECT` từ trait của **chính người quan sát** và ghim `SAME_SP: True`, tức là nó đang mô tả nhầm người; và sổ tay ([B-07](tasks/B-07-so-tay.md)) không có chiều nào nói về trait của kẻ khác. Một cond không quan sát được là một câu đố không có lời giải, và nó vốn là cond được sinh **nhiều nhất** (3/12 trên 9 seed) — tức là một phần tư số đề bài đang không giải được mà không có gì báo. Muốn mở lại: sửa `build_ctx` cho đúng đối tượng, rồi thêm chiều "kẻ đó" vào `ctx_to_pairs`.

Con L5 **về mặt cấu trúc không thể phát biểu** luật D2 trở lên. Nó không sai — nó câm về mặt khái niệm. Đó là điều bạn muốn: khi L1 tìm ra luật D3 mà L5 thì không bao giờ nổi, khác biệt đó là **thật**, chứ không phải do bạn cho L1 nhiều máu hơn.

---

## 9. Chỉ số và câu hỏi nghiên cứu

### 9.1 Câu hỏi

| | Câu hỏi | Đo bằng | Chạy được từ mốc |
|---|---|---|---|
| **Q1** | Model to có quy nạp nhanh và đúng hơn không? | `t_discover`, `match`, `pred_acc` theo loài | M2.5 |
| **Q2** | Giao tiếp có làm quần thể biết nhanh hơn không? | `diffusion_t50`, `t_discover` gộp quần thể; VOCAL vs SILENT | M4.5 |
| **Q3** | Khi nào thì nói dối, và có lãi không? | `deception_rate`, `deception_payoff` | M4.5 |
| **Q4** | Prior rò rỉ bao nhiêu? | Δ`t_discover` giữa nhánh thuận / nghịch / trung tính | M5.5 |
| **Q5** | Biết rồi có làm không? | `exploit_lag`, tỉ lệ `exploited` | M2.5 |
| **Q6** | Nó có biết là nó không biết không? | Brier score trên `conf` | M2.5 |
| **Q7** | Lợi thế của não to đến **từ** quy nạp, hay chỉ đi kèm? | §10 — thí nghiệm gác cổng | M5.5 |

**Q7 là câu hỏi mà bản v5 tồn tại để trả lời.** v4 không hỏi được nó.

### 9.2 Bảng chỉ số

| Chỉ số | Định nghĩa | Ghi chú |
|---|---|---|
| `t_discover(i)` | tick sớm nhất entry đúng vào sổ và ở lại | `T+1` nếu không tìm ra |
| `match(i)` | §5.3 | 0–1 |
| `pred_acc` | §5.4 tầng 2, chuẩn hoá null | |
| `exploit_lag` | §5.4 tầng 3 | `NA` khi mẫu < 4 |
| `experiments_per_discovery` | số lần chủ động thực hiện trigger trước `t_discover` | **hiệu suất khoa học** — chỉ số tôi thích nhất bảng này |
| `death_by_experiment` | số lần chết trong 3 tick sau một hành động thí nghiệm | giá phải trả cho hiểu biết |
| `obs_ratio` | quan sát gián tiếp / trực tiếp | ăn theo hay tự thân |
| `spurious_claim_rate` | tỉ lệ entry khớp luật giả (§3.6) | nhầm tương quan với nhân quả |
| `brier` | mean((conf/5 − đúng)²) | hiệu chỉnh tự tin |
| `diffusion_t50` | tick mà 50% quần thể giữ entry đúng | lan truyền tri thức |
| `share_rate` | TEACH / (số luật đang giữ đúng) | |
| `deception_rate`, `deception_payoff` | §6.4 | |
| `LLM_SEMANTIC_FAIL` | giữ nguyên v4 bước 16, thêm loại `BAD_SLOT`, `BAD_LAW_REF` | |

### 9.3 Quy mô chạy

| Nhánh | Ván | Ghi chú |
|---|---|---|
| `STANDARD` × 5 seed × 3 bộ luật | 15 | chính |
| `SILENT` (gỡ `say` + `teach`) | 15 | Q2 |
| `REFLEX` (không LLM) | 15 | sàn — phải ra `match ≈ 0` |
| `RANDOM` | 15 | sàn tuyệt đối |
| `WORLD_FLAT` (§10) | 15 | Q7 |
| Nhánh prior × 3 (§10.2) | 45 | Q4 |
| **Tổng** | **120 ván** | ~27 phút/ván → **~54 giờ máy** |

Ba đêm cuối tuần, hoặc một tuần chạy nền. Nhánh `REFLEX` và `RANDOM` không cần LLM nên nhanh hơn nhiều — thực tế gần 40 giờ.

> **`REFLEX` phải ra `match ≈ 0`.** Nếu bộ điều khiển if-else không LLM mà ăn được điểm khám phá đáng kể thì bạn đã rò rỉ đáp án ở đâu đó trong sổ tay hoặc trạng thái. Đây là bài kiểm tra rẻ nhất để bắt lỗi rò rỉ, và nó phải chạy **trước** mọi kết luận khác.

---

## 10. Thí nghiệm gác cổng — bản này đúng hay sai

### 10.1 `WORLD_FLAT` vs `WORLD_LAW`

Bạn đã chốt: *model to = loài đầu bảng, vì nó suy luận quy nạp tốt hơn nên sống dai hơn **một cách có lý do**.* Đó là một mệnh đề **kiểm chứng được**, và đây là cách kiểm.

Hai nhánh, khác nhau đúng một biến:

| | `WORLD_LAW` | `WORLD_FLAT` |
|---|---|---|
| Luật ẩn | 3 luật | **0 luật** |
| Mọi thứ khác | | y hệt, cùng seed |

**Tiên đoán nếu thiết kế đúng:**

1. Ở `FLAT`, chênh lệch sinh tồn L1 − L5 **co lại rõ rệt** so với `LAW`.
2. Ở `LAW`, chênh lệch đó **có trung gian là `t_discover`**: hồi quy `survival ~ brain + t_discover`, hệ số của `brain` phải **tụt đáng kể** khi thêm `t_discover` vào.

**Nếu (1) sai** — L1 vẫn thắng đậm y hệt trong thế giới không có gì để khám phá — thì lợi thế của nó **không** đến từ quy nạp. Nó đến từ founder vector, hoặc từ việc model to bám goal ổn định hơn. Thiết kế chưa đạt mục tiêu.

**Nếu (2) sai** — `t_discover` không giải thích được gì — thì khám phá và sinh tồn là hai thứ rời nhau, nghĩa là `R_survive` với hệ số 0.1 chưa đủ nối chúng lại. Nâng lên, hoặc sinh thêm luật có tác động sinh tồn mạnh hơn.

> **Đây là mốc gác cổng, không phải mốc báo cáo.** Chạy nó **trước** khi đổ 40 giờ máy vào Q1–Q6. Nếu không qua, mọi số liệu sau đó đều đo nhầm thứ, và bạn cần biết điều đó trong tuần đầu chứ không phải tháng sau.

### 10.2 Nhánh prior

Ba nhánh, cùng cấu trúc luật, khác ánh xạ bề mặt:

| Nhánh | Ánh xạ |
|---|---|
| `PRIOR_ALIGNED` | quả đỏ độc, lửa hại, nước lành — đúng trực giác |
| `PRIOR_INVERTED` | quả đỏ bổ nhất, nước gây hại ban đêm — ngược trực giác |
| `PRIOR_NEUTRAL` | tên và màu vô nghĩa (`quả zim`, `quả kar`) |

```
prior_leak = t_discover(INVERTED) − t_discover(ALIGNED)
```

Nếu `prior_leak` lớn → điểm ở nhánh `ALIGNED` phần lớn là **nhớ bài**, không phải suy luận. Khi đó `PRIOR_NEUTRAL` thành nhánh chuẩn để báo cáo Q1.

Đây là một phép đo mà tôi chưa thấy ai làm gọn ghẽ cho agent LLM, nó gần như miễn phí ở đây, và **nó là thứ đáng viết bài nhất trong toàn bộ dự án.**

---

## 11. Lộ trình thi công — delta trên v4

Đánh số `L*` để không đụng 36 bước của v4. Format giữ nguyên: **Mục tiêu / Viết gì / Bẫy / Xong khi.**

### M1.5 — Động cơ luật · L1–L7 · ~320 dòng · 2 cuối tuần
*Sau v4 bước 12 (chốt M1), trước bước 13. Không cần LLM.*

---

**L1 — Mở rộng sandbox nền**

- **Mục tiêu:** đủ chất liệu để luật có cái mà nói tới.
- **Viết gì:** hành động `DRINK` trên ô `WATER`; tách `PLANT` thành `FRUIT_A..D` với `(màu, hình)` bốc thăm mỗi ván; chu kỳ ngày/đêm `PHASE_LEN = 40` tick; hướng gió cố định mỗi ván, quan sát được; địa hình `FIRE` + luật lan cơ sở (tắt mặc định, chỉ bật khi có luật `SPREAD`).
- **Bẫy:** ban đêm **không được** giảm `sight_radius`. Nghe rất hợp lý và nó sẽ phá Gate A (§3.2) cho mọi luật có `PHASE(NIGHT)` — luật chỉ xảy ra lúc bạn nhìn kém nhất thì không định danh được. Nếu rất muốn có, để tới sau khi Q1 xong, và chạy lại baseline.
- **Xong khi:** chạy 400 tick không LLM, log có `DRINK`, chu kỳ ngày/đêm đúng 10 lần, 4 loại quả xuất hiện với tỉ lệ đều nhau ±10%, hai seed khác nhau cho hai ánh xạ màu khác nhau.

---

**L2 — LawDSL: kiểu dữ liệu, parser, GBNF**

- **Mục tiêu:** một ký pháp dùng chung cho bộ sinh, bộ chấm và agent. Ba chỗ, **một** định nghĩa.
- **Viết gì:** `Trigger`/`Cond`/`Effect`/`Law` dạng frozen dataclass; `to_json` / `from_json`; sinh GBNF **từ chính định nghĩa** (đừng viết tay grammar — nó sẽ lệch với code sau ba lần sửa); `to_vietnamese(law)` cho `REVEAL` và cho log.
- **Bẫy:** GBNF phải sinh tự động và có test round-trip. Grammar viết tay lệch khỏi dataclass là loại bug tốn cả buổi tối và biểu hiện thành "model tự dưng ghi sổ sai cú pháp".
- **Xong khi:** round-trip 1000 luật ngẫu nhiên `law == from_json(to_json(law))`; GBNF sinh ra parse được bằng chính `from_json`; ba ví dụ ở §2.4 viết được.

---

**L3 — LawEval: cắm luật vào vòng tick**

- **Mục tiêu:** luật thật sự tác động lên thế giới.
- **Viết gì:** `evaluate(law, event, ctx) -> Effect | None`; hook sau pha resolve của v4 bước 11, **trước** pha tính chết; `apply_effect(creature, effect, world)`.
- **Bẫy:** luật kích hoạt trong **cùng một pha đồng thời** với chiến đấu. Nếu bạn resolve tuần tự thì con đi trước ăn hiệu ứng trước và bạn mất tính đồng thời mà v4 bước 11 đã phải rất cẩn thận mới có. Thu hết `(creature, effect)` rồi mới áp dụng, đúng như intent.
- **Bẫy 2:** luật `SPREAD` sửa **địa hình**, tức là sửa thế giới chứ không sửa sinh vật. Nó phải nằm ở pha 5 (spawn/decay), không phải pha 2.
- **Xong khi:** nạp tay ba luật ở §2.4, chạy 200 tick, log có `LAW_FIRED` với đủ `law_id / creature / tick / effect`; tắt luật đi thì ván chạy y hệt v4 (`diff` sạch trên cùng seed).

---

**L4 — LawGen + Gate A**

- **Mục tiêu:** sinh luật hợp lệ từ seed.
- **Viết gì:** bốc thăm theo tier; `observable(law, min_sense) -> bool`; ràng buộc §6.3 (≥1 luật đơn độc, ≥1 luật hợp tác ở `STANDARD`).
- **Bẫy:** dùng **đúng một** `random.Random(seed)` truyền xuống, y như v4 bước 1. Bộ sinh luật gọi `random.xxx()` ở module-level là cách chắc chắn nhất để mất khả năng tái lập của cả dự án.
- **Xong khi:** `generate(seed=42)` hai lần cho kết quả giống hệt; 1000 luật sinh ra đều qua Gate A; in ra bằng tiếng Việt đọc thấy hợp lý.

---

**L5 — Không gian tình huống + lấy mẫu phân tầng**

- **Mục tiêu:** hạ tầng cho verifier. Làm trước khi cần, vì Gate B/C cũng dùng nó.
- **Viết gì:** `Situation` dataclass; `sample_situations(law, n=400, rng) -> list[Situation]` theo tỉ lệ 40/40/20 ở §5.2; trong tầng gần trượt, trải đều theo từng chiều cond.
- **Bẫy:** tình huống phải chứa **đủ trường cho mọi cond có thể**, không chỉ cond của luật thật. Nếu chỉ điền trường mà `L` cần, thì mọi luật `C` nhắc tới trường khác đều đánh giá thành `None` và ăn điểm oan bằng nhau. Điền **toàn bộ** ngữ cảnh.
- **Xong khi:** với luật 1 cond, tỉ lệ ba tầng đúng ±3%; `NULL` chấm ra `acc₀` nằm trong [0.55, 0.65].

---

**L6 — Gate B + Gate C (khả giải, định danh được)**

- **Mục tiêu:** chỉ phát ra đề bài giải được.
- **Viết gì:** chính sách tham chiếu tò mò; 200 rollout headless; đo `t_first_fire`, `n_fire`, `p_never`, `n_near_miss`; vòng tự sửa trước khi bốc lại.
- **Bẫy:** 200 rollout × 400 tick phải chạy dưới 10 giây, nếu không thì LawGen thành nút cổ chai của mọi ván. Chạy rollout **không render, không log, không LLM**. Nếu chậm thì hạ xuống 400 tick → 200 tick và ngoại suy tuyến tính `t_first_fire` — sai số chấp nhận được ở tầng gác cổng này.
- **Xong khi:** sinh 200 bộ luật `STANDARD` liên tiếp, 100% qua cả ba gate, thời gian trung bình < 10s/bộ; cố tình nạp một luật không khả giải (`ADJACENT(ANY,3)` trên bản đồ 15 con) thì bị chặn.

---

**L7 — `match()` — chấm bằng bảng chân trị**

- **Mục tiêu:** hàm quan trọng nhất của bản v5.
- **Viết gì:** `match(claimed, truth, situations) -> float` theo §5.3; so effect ở mức rổ, rổ liền kề = 0.5; chuẩn hoá null.
- **Bẫy:** đây là chỗ **bắt buộc** phải có bộ test viết tay trước khi tin. Tối thiểu tám ca: (a) trùng khít → 1.0; (b) khác cú pháp cùng hành vi → 1.0; (c) đúng trigger sai cond → 0.4–0.6; (d) đúng trigger đúng cond sai effect → ≤0.3; (e) null → 0.0; (f) luật ngẫu nhiên → ≤0.15 trung bình trên 1000 mẫu; (g) lệch một rổ độ lớn → ~0.85; (h) đúng effect sai hoàn toàn trigger → ≤0.2.
- **Xong khi:** cả tám ca đúng. **Không đi tiếp khi ca (b) hoặc (f) chưa đạt** — (b) hỏng thì bạn chấm oan người đúng, (f) hỏng thì đoán bừa có điểm và toàn bộ RL sẽ đi tối ưu vào đó.

---

### M2.5 — Sổ Luật và điểm khám phá · L8–L12 · ~280 dòng · 1 cuối tuần
*Sau v4 bước 18 (chốt M2).*

---

**L8 — Codex + CLAIM hai pha**

- **Viết gì:** `codex` độ dài `codex_size`; cờ `want_codex` trong schema quyết định; schema claim riêng + GBNF từ L2; `COST_CLAIM`, `CLAIM_COOLDOWN`.
- **Bẫy:** khi trait dịch làm `codex_size` **giảm**, đừng cắt bớt sổ. Giữ nguyên các ô đang có, chỉ chặn ghi thêm cho tới khi có chỗ.
- **Xong khi:** một con reflex-với-claim-ngẫu-nhiên chạy 400 tick, sổ luôn hợp lệ, không entry nào vượt số ô, `LLM_SEMANTIC_FAIL` phân loại đúng `BAD_SLOT`.

---

**L9 — Sổ tay sự kiện**

- **Viết gì:** vòng đệm sự kiện mỗi cá thể; ưu tiên chọn khi tràn (§7.1); định dạng cột cố định; sự kiện `THẤY` từ tầm nhìn.
- **Bẫy:** rò rỉ đáp án. Kiểm bằng `grep` trên 100 prompt sinh ra: không được xuất hiện tên loại effect nội bộ (`POISON`, `STUN`…) cho sự kiện của **con khác**, và không bao giờ được xuất hiện `law_id`.
- **Xong khi:** in prompt của một con ở tick 200 và đọc được — bạn tự đọc sổ tay đó có suy ra được luật không? Nếu **bạn** không suy ra được thì model cũng không, và lỗi nằm ở đây chứ không ở model.

---

**L10 — Prompt v5, giữ prefix cache**

- **Viết gì:** 5 khối §8; khối D cắt theo brain; `-c` mới ở §7.4.
- **Bẫy:** trait dịch → khối D đổi → cache vỡ. Chấp nhận, nhưng phải **log** `PREFIX_INVALIDATED` để bạn thấy nó xảy ra bao nhiêu lần. Nếu nhiều hơn ~5 lần/ván thì tần suất dịch trait đang quá cao và nó đang ăn hết throughput.
- **Xong khi:** gọi 2 lần liên tiếp, `diff` phần system sạch; đo `t_prefill` lần 1 vs lần 2, lần 2 phải nhanh hơn ≥3×.

---

**L11 — Prediction oracle**

- **Viết gì:** cuối ván, 8 câu hỏi/luật lấy từ `sample_situations`; schema trả lời = `Effect`; `pred_acc` chuẩn hoá null.
- **Bẫy:** hỏi bằng **bề mặt** ("quả đỏ tròn"), không bằng lớp nội bộ ("FRUIT_A"). Hỏi bằng lớp là đưa luôn đáp án của phép hoán vị §2.6.
- **Xong khi:** con `REFLEX` ra `pred_acc ≈ 0`; hỏi thẳng một agent đã được nạp sẵn luật đúng vào prompt thì ra ≥0.9. Hai đầu này kẹp lấy thang đo.

---

**L12 — Bảng điểm và log**

- **Viết gì:** `score.py` chạy offline trên JSONL; toàn bộ §5.5 + §9.2; xuất một dòng CSV mỗi (ván, cá thể, luật).
- **Bẫy:** verifier **không** được import gì từ vòng tick. Nó đọc JSONL, chấm, xong. Ranh giới đó là thứ đảm bảo sim không bao giờ chạm được vào bảng chấm — nghĩa là §5.6 dòng "dò verifier" đúng theo kiến trúc chứ không theo lời hứa.
- **Xong khi (chốt M2.5):** một ván có LLM cho ra bảng điểm đầy đủ; `REFLEX` ra `match ≈ 0` (nếu không: rò rỉ, quay lại L9); ít nhất một cá thể đạt `match ≥ 0.8` trên luật D1 trong 5 ván.

> **Đây là mốc chứng minh cả bản v5 có sống được không.** Nếu qua 5 ván × 15 con mà **không ai** tìm ra nổi một luật D1, thì hoặc sổ tay quá nghèo (L9), hoặc từ vựng quá rộng (§8 khối D), hoặc luật quá hiếm kích hoạt (L6). Sửa theo thứ tự đó.

---

### M4.5 — Xã hội · L13–L16 · ~200 dòng
*Sau v4 bước 28 (chốt M4).*

- **L13 — TEACH.** Trường `teach` trong `say`; quy tắc nghe theo loài (§6.1); hàng chờ "nghe được" trong prompt; `COST_TEACH`. **Xong khi:** truy được trong log một chuỗi `TEACH` → `SET` của người nghe → entry đúng.
- **L14 — Provenance + citation.** DAG; ba khoá chống farming §6.2. **Bẫy:** tự viết một agent farming (dạy chéo vòng tròn) và kiểm rằng nó ăn 0 credit. Đừng chỉ đọc code rồi tin. **Xong khi:** agent farming ra 0.
- **L15 — Luật hợp tác.** Ràng buộc bộ sinh §6.3; hiệu ứng cần ≥2 chủ thể. **Xong khi:** một ván có luật `ADJACENT` mà không ai dạy ai thì không ai khai thác được — xác nhận bằng log.
- **L16 — Đo nói dối.** `deception_rate` với mệnh đề kép §6.4; `deception_payoff`. **Xong khi:** dựng tay một ca lừa và chỉ số bắt đúng; dựng tay một ca nhầm lẫn thật thà và chỉ số **không** bắt.

---

### M5.5 — Gác cổng và đo · L17–L19 · ~120 dòng

- **L17 — `WORLD_FLAT`.** Cờ tắt toàn bộ tầng 2. **Xong khi:** §10.1 tiên đoán (1) và (2) đều đạt. **Không qua thì dừng và báo cáo đúng như vậy** — v4 §11 rủi ro 5 đã nói tinh thần này, và nó áp dụng ở đây gấp đôi.
- **L18 — Nhánh prior.** Ba ánh xạ bề mặt §10.2. **Xong khi:** có `prior_leak` với khoảng tin cậy trên 15 ván/nhánh.
- **L19 — Báo cáo.** `analyze.py`: đường cong khám phá (số cá thể biết luật theo tick), ma trận dạy-học, hiệu chỉnh `conf`, bảng Q1–Q7.

---

### M7 — Vòng huấn luyện · L20–L23 · ~400 dòng
*Đây là thứ mà cả bản v5 tồn tại để mở khoá. Cũng là phần tôi ít chắc chắn nhất về khối lượng.*

**Nói thẳng về quy mô trước khi bạn bắt đầu.** Eval cần ~120 ván. RL cần ~**16 000**. Ở 27 phút/ván thì đó là 7 200 giờ — bất khả thi. Nên M7 **không** phải là "bật RL lên trên ván hiện tại"; nó là dựng một chế độ chạy khác:

| | Ván eval | Ván train |
|---|---|---|
| Độ dài | 400 tick | **150 tick** |
| Loài dùng LLM | 5 | **1** (4 loài kia reflex) |
| Số luật | 3 | **1** (`SOLO_LAB` → nâng dần) |
| Render, log đầy đủ | có | **không** |
| Gọi LLM | qua mạng, 5 node | **cục bộ, gộp batch** |
| Thời gian/ván | ~27 phút | **mục tiêu 15–25 giây** |

Ước tính: 150 tick / think_interval 4 × 3 cá thể ≈ 113 lần gọi × ~150 token ≈ 17k token/ván. Model 1.5B trên một GPU, gộp batch tốt, ~2 000 tok/s → ~9 giây tính toán + prefill. Thực tế 15–25 giây. 16 000 ván ≈ **70–110 giờ một GPU**. Vài ngày, không phải vài giờ. Đó là con số thật, và nó khả thi.

- **L20 — Chế độ headless.** Tách rollout khỏi render/log; N môi trường song song trong một tiến trình; gộp mọi lời gọi LLM cùng tick thành **một** batch.
  **Bẫy:** đây là chỗ tính đồng thời của v4 bước 11 dễ vỡ nhất. Test bất biến cũ: hoán vị thứ tự creature, kết quả không đổi. Chạy test đó trên chế độ headless, đừng giả định nó còn đúng.
  **Xong khi:** 8 môi trường song song, < 25 giây/ván, và ván headless cho log **giống hệt** ván thường trên cùng seed ở nhánh reflex.
- **L21 — Dữ liệu.** Trajectory → danh sách `(prompt, response, reward)`; reward tính bằng chính `score.py` của L12 — **một** bộ luật chấm cho cả eval lẫn train, không được có hai.
- **L22 — GRPO.** Nhóm 8 cùng luật (§5.7); advantage chuẩn hoá trong nhóm; TRL hoặc verl; LoRA trên Qwen2.5-1.5B hoặc 3B.
  **Bẫy:** đổi luật trong nhóm. Nó sẽ trông như đang chạy đúng và advantage thì thành nhiễu.
- **L23 — Tách train/test.** §2.7; eval trên `TEST_SHAPE` mỗi 200 bước.
  **Xong khi (chốt M7):** `match` trên `TRAIN` tăng, **và** `match` trên `TEST_SHAPE` cũng tăng. Chỉ tăng ở `TRAIN` = học thuộc bộ luật, không phải học tìm luật — và phải báo cáo đúng như vậy.

### 11.6 Phần thưởng phụ: mọi ván thua đều thành dữ liệu SFT

Vì verifier biết đáp án, sau `REVEAL` bạn dựng được **hồi tưởng hậu nghiệm**: cho một model mạnh xem (sổ tay thật + luật thật) và viết ra chuỗi suy luận *đáng lẽ* phải có. Cặp `(sổ tay, suy luận mẫu)` là dữ liệu SFT sạch, sinh tự động, không cần người gán nhãn.

Đây là thứ chỉ môi trường có đáp án mới cho được, và v4 không bao giờ có được. Nó đáng một mốc riêng nhưng tôi để ở đây vì nó là hệ quả, không phải mục tiêu.

---

## 12. Hằng số bổ sung — `law_config.py`

```python
"""Genesis Zero v5 — hằng số tầng luật. config.py của v4 giữ nguyên."""

# ─── Sandbox mở rộng ────────────────────────────────
PHASE_LEN        = 40      # tick mỗi pha ngày/đêm
FRUIT_KINDS      = 4       # FRUIT_A..D
FRUIT_SURFACES   = [("đỏ","tròn"), ("xanh","dài"), ("vàng","gai"), ("tím","dẹt")]
WIND_DIRS        = ["N","E","S","W"]
WATER_DRINKABLE  = True
FIRE_BASE_SPREAD = False   # chỉ lan khi có luật SPREAD

# ─── Sinh luật ──────────────────────────────────────
LAWS_PER_MATCH   = {"SOLO_LAB": 1, "STANDARD": 3, "HARSH": 4}
TIER_PLAN        = {"STANDARD": ["D1","D2","D3|D4"]}
LAW_WEIGHT       = {"D1": 1.0, "D2": 1.5, "D3": 2.2, "D4": 2.2}
DECOY_LAW        = {"STANDARD": False, "HARSH": True}
REQUIRE_SOLO_LAW = True    # ≥1 luật khai thác được một mình
REQUIRE_COOP_LAW = True    # ≥1 luật cần ≥2 cá thể

# ─── Gate khả giải / định danh ──────────────────────
SOLVE_ROLLOUTS       = 200
SOLVE_MAX_FIRST_FIRE = 0.25   # × T
SOLVE_MIN_FIRES      = 5
SOLVE_MAX_P_NEVER    = 0.05
IDENT_MIN_NEAR_MISS  = 3
LAWGEN_MAX_RETRY     = 200

# ─── Sổ Luật ────────────────────────────────────────
CODEX_SIZE_BY_BRAIN  = {0:1, 1:1, 2:2, 3:3, 4:3, 5:4}
EVENTS_BY_BRAIN      = {0:6, 1:8, 2:12, 3:16, 4:20, 5:24}
CLAIM_BUDGET_BY_BRAIN= {0:24, 1:44, 2:64, 3:84, 4:104, 5:124}
CLAIM_COOLDOWN       = 25
COST_CLAIM           = 4.0
NOTEPAD_MAX_CHARS    = 200

# ─── Chấm điểm ──────────────────────────────────────
N_SITUATIONS         = 400
SITUATION_STRATA     = {"fires": 0.4, "near_miss": 0.4, "unrelated": 0.2}
MATCH_THRESHOLD      = 0.80
ADJACENT_BUCKET_CREDIT = 0.5
SPEED_FLOOR          = 0.4
ORACLE_QUERIES       = 8
W_PRED, W_EXPLOIT, W_SOCIAL, W_SURVIVE = 0.5, 0.3, 0.3, 0.1

# ─── Xã hội ─────────────────────────────────────────
COST_TEACH           = 5.0
CITATION_SHARE       = 0.3
CITATION_MAX_HOPS    = 2
CROSS_SPECIES_TEACH  = "trigger_and_cond_only"   # giấu effect

# ─── Nhánh thí nghiệm ───────────────────────────────
ARMS = ["STANDARD","SILENT","REFLEX","RANDOM","WORLD_FLAT",
        "PRIOR_ALIGNED","PRIOR_INVERTED","PRIOR_NEUTRAL"]

# ─── Chế độ train (M7) ──────────────────────────────
TRAIN_TICKS          = 150
TRAIN_LLM_SPECIES    = 1
TRAIN_PARALLEL_ENVS  = 8
GRPO_GROUP           = 8
```

---

## 13. Cấu trúc file — thêm vào v4 §9

```
genesis/
  config.py          # v4, không đổi
  law_config.py      # MỚI — §12
  lawdsl.py          # MỚI — kiểu, parser, GBNF, to_vietnamese     (L2)
  lawgen.py          # MỚI — bốc thăm + 4 gate                      (L4, L6)
  laweval.py         # MỚI — hook vào vòng tick                     (L3)
  situations.py      # MỚI — không gian tình huống, lấy mẫu         (L5)
  verify.py          # MỚI — match(), oracle, exploit               (L7, L11)
  score.py           # MỚI — chấm offline từ JSONL                   (L12)
  codex.py           # MỚI — Sổ Luật, CLAIM, provenance             (L8, L14)
  fieldnotes.py      # MỚI — sổ tay sự kiện                          (L9)
  rollout.py         # MỚI — headless, song song, gộp batch         (L20)
  train/             # MỚI — M7
  ...                # phần còn lại y v4
```

**Ranh giới bắt buộc:** `verify.py` và `score.py` **không import** `world.py`. Chúng đọc JSONL. Đó là cách duy nhất đảm bảo vòng tick không bao giờ chạm được vào bảng chấm.

---

## 14. Rủi ro

1. **`match()` sai mà không ai biết.** Rủi ro số một. Một hàm chấm hỏng nhẹ cho ra số đẹp và mọi kết luận sau đó đều sai. Phòng: 8 ca test ở L7, cộng nhánh `RANDOM` phải ra ~0 và nhánh "nạp sẵn đáp án" phải ra ~1. Hai đầu kẹp thang đo.
2. **Không ai tìm ra luật nào.** Rất có thể ở lần chạy đầu. Chẩn đoán theo thứ tự: sổ tay có bằng chứng không (tự đọc bằng mắt) → luật kích hoạt đủ nhiều chưa (L6) → từ vựng có quá rộng không (§8 D). **Đừng** chẩn đoán bằng cách đổi model.
3. **Rò prior lớn tới mức nuốt hết tín hiệu.** Nếu `prior_leak` rất lớn thì `PRIOR_NEUTRAL` thành nhánh chuẩn duy nhất và bạn mất 2/3 số ván. Chấp nhận được — miễn là bạn phát hiện ở M5.5 chứ không phải trong lúc viết báo cáo.
4. **`WORLD_FLAT` không qua** (§10.1). Nghĩa là não to thắng vì lý do khác. Đó vẫn là một kết quả, và phải báo cáo đúng như vậy — v4 §11 rủi ro 5 đã cam kết tinh thần này.
5. **Chi phí M7 vượt dự toán.** 70–110 giờ GPU là ước tính lạc quan có điều kiện (batch tốt, môi trường không phải nút cổ chai). Nếu môi trường Python thành nút cổ chai thì con số nhân đôi. Đo `env_time / gpu_time` ở L20 trước khi cam kết.
6. **Không gian luật hẹp hơn tưởng.** 4,4 triệu nghe to, nhưng sau các gate lọc thì số luật *thật sự sinh ra được* có thể nhỏ hơn nhiều. **Đo nó:** sinh 10 000 bộ luật, đếm số luật khác nhau. Dưới ~5 000 thì rủi ro thuộc lòng là thật và phải mở rộng từ vựng.
7. **Phương sai.** v4 §11 rủi ro 3 vẫn nguyên: đừng kể chuyện dựa trên một ván. Ở v5 cám dỗ còn mạnh hơn vì mỗi ván có một kịch bản "phát hiện" rất hấp dẫn để kể.
8. **`exploit_lag` mẫu quá nhỏ.** Trigger hiếm thì cửa sổ 60 tick không đủ. Chuẩn bị sẵn tinh thần rằng chỉ số này `NA` ở nhiều ván, và **đừng** nới ngưỡng để có số đẹp.

---

## 15. Cần bạn duyệt

1. **Từ vựng §2.3** — 11 trigger / 10 cond / 12 effect. Thiếu loại nào bạn thấy nhất định phải có? Thừa loại nào?
2. **3 luật mỗi ván** ở `STANDARD` — hay 2 cho nhẹ, hay 4 cho khó?
3. **`brain` → dung lượng nhận thức** (§4.1) thay vì "nhiều token". Đây là đổi nghĩa một trait giữa dự án. Đồng ý không?
4. **L5 `brain=0` không phát biểu nổi luật có điều kiện** (§8 khối D). Cố ý — nó là nhánh đối chứng "bản năng". Hay bạn muốn mọi loài đều claim được?
5. **Không phản hồi cho tới cuối ván** (§4.3). Đây là quyết định cứng nhất của bản này. Nó làm reward thưa hơn nhiều, đổi lại giết được vét cạn. Giữ chứ?
6. **Khác loài dạy nhau thì giấu effect** (§6.1) — hay dạy đủ, hay không cho dạy khác loài?
7. **`R_survive` hệ số 0.1** (§5.5) — giữ nhỏ, bỏ hẳn, hay nâng lên? Nâng lên thì kéo v5 về phía v4 và mang lại các bệnh ở §0.1.
8. **Thứ tự: gác cổng §10.1 chạy trước Q1–Q6.** Tốn ~7 giờ máy trước khi có bất kỳ kết quả nào để khoe. Đồng ý không?
9. **M7 có nằm trong phạm vi không?** Nếu mục tiêu thật chỉ là một môi trường eval tốt (dừng ở M5.5) thì lộ trình ngắn đi ~400 dòng và vài ngày GPU, và dự án vẫn đứng vững — thậm chí một môi trường eval có verifier là thứ hiếm hơn một lần train GRPO.
10. **Nguyên tắc tự học của v4 §10** áp cho L1–L7 chứ? Chúng đúng là phần tư duy của bản v5, tương đương bước 1–12 của v4. Từ L8 trở đi là hạ tầng, dùng AI thoải mái.
