# B-01 · Schema quyết định và GBNF

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** W-12 · **Chặn** B-02, B-04, B-05 |
| **File** | `genesis/strategist.py` · ~60 dòng · 45 phút |
| **Giao cho model rẻ?** | ✅ đặc tả đã đầy đủ, test ghim chặt |
| **Tài liệu gốc** | v4 Bước 13, [03 §4.2](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Hợp đồng giữa sim và model. Thứ tự trường trong schema là **quyết định kỹ thuật, không phải trang trí**.

## 2. Việc phải làm
1. Schema `decide` theo §3. 2. Schema `codex` và `oracle` (dùng GBNF từ [L-01](L-01-lawdsl.md)). 3. Cắt trường theo `token_budget` và `brain`.

## 3. Chữ ký và bất biến
```json
{"type":"object","properties":{
  "note":{"type":"string","maxLength":90},
  "goal":{"type":"string","enum":["FORAGE","HUNT","FLEE","FOLLOW","REST","WANDER","GUARD"]},
  "target":{"type":"string"},
  "ttl":{"type":"integer","minimum":2,"maximum":12},
  "want_codex":{"type":"boolean"}},
 "required":["note","goal","ttl"],"additionalProperties":false}
```
**Bất biến 1:** `note` đứng **trước** `goal`. Model sinh token tuần tự — `note` ra trước thì những token lập luận đó nằm trong context lúc model chọn `goal`, và nó ảnh hưởng thật. Đảo lại thì `note` chỉ là lời biện minh viết sau.
**Bất biến 2:** `token_budget < 60` (tức L5) → **bỏ hẳn `note`** khỏi schema. Con đó không có ngân sách để diễn đạt suy nghĩ, và điều đó đúng với thiết kế.
**Bất biến 3:** `enum` của `goal` cắt theo `config.GOALS_BY_BRAIN`. Con `brain 0` không **có** khái niệm `GUARD` — nó không phải là con dùng sai `GUARD`.
**Bất biến 4:** `want_codex` chỉ tốn 1–2 token, có mặt ở **mọi** brain. Đó là pha 1 của CLAIM hai pha.

## 4. Nghiệm thu
```bash
python - <<'PY'
from genesis.strategist import schema_for
from genesis.traits import Traits; from genesis import config
L5 = Traits(*config.FOUNDERS["L5"]); L1 = Traits(*config.FOUNDERS["L1"])
s5, s1 = schema_for(L5,"decide"), schema_for(L1,"decide")
assert "note" not in s5["properties"] and "note" in s1["properties"]
assert list(s1["properties"]).index("note") < list(s1["properties"]).index("goal")
assert set(s5["properties"]["goal"]["enum"]) == {"FORAGE","FLEE","WANDER","HUNT"}
assert "GUARD" in s1["properties"]["goal"]["enum"]
assert all("want_codex" in schema_for(t,"decide")["properties"] for t in (L1,L5))
print("OK")
PY
```

## 5. Prompt giao việc
```
BỐI CẢNH: Python 3.11. Đọc trước: docs/tasks/B-01-schema.md §3 và genesis/config.py
(GOALS_BY_BRAIN). Đã có genesis/traits.py với Traits.token_budget và .brain.
VIỆC: genesis/strategist.py -> schema_for(traits, kind) trả JSON Schema dict cho
kind in {"decide","codex","oracle"}. Áp dụng đủ 4 bất biến ở §3. Thêm tests/test_schema.py
kiểm cả 4 bất biến đó.
RÀNG BUỘC: chỉ thư viện chuẩn; không tạo file khác; không sửa file khác trong genesis/;
không hardcode danh sách goal — lấy từ config.GOALS_BY_BRAIN.
NGHIỆM THU: pytest tests/test_schema.py -q
TRẢ VỀ: chỉ diff.
```


## ✦ Bài học từ model thật: **mọi ràng buộc của bộ xác thực đều phải có trong schema**

Bốn lần, bốn chỗ khác nhau, cùng một hình dạng — và mỗi lần chỉ lộ ra khi có một
model **thật** đi vào đúng nhánh đó:

| Ràng buộc | `validate_*` nói | Schema nói (trước khi sửa) | Giá phải trả |
|---|---|---|---|
| `target` phải là kẻ đang NHÌN THẤY | `SEMANTIC_TARGET_NOT_FOUND` | `{"type": "string"}` | **16/20 lời gọi** trượt |
| `HUNT`/`FOLLOW` phải có `target` | `SEMANTIC_GOAL_NEEDS_TARGET` | `target` không bắt buộc | 8/35 trượt |
| `arg` phải là một bề mặt CÓ THẬT | `CODEX_UNKNOWN_SURFACE` | `{"type": "string"}` | model **dịch sang tiếng Trung** (`紫扁果`) và mất lượt |
| `slot` phải trong `[0, codex_size)` | `CODEX_BAD_SLOT` | chỉ có `minimum: 0` | con một-ô chọn `slot: 1` |
| `arg` phải thuộc miền của `kind` | *(chưa có)* → `CODEX_ARG_KIND_MISMATCH` | enum phẳng, mọi arg hợp lệ cho mọi kind | luật vô nghĩa **chiếm một ô sổ** |

Mỗi dòng là một lượt nghĩ bị đốt vào một câu trả lời **không thể hợp lệ**. Tệ hơn:
ca thứ ba trông y hệt "model không suy ra được luật" — nó suy ra **đúng**, chỉ
viết sai thứ tiếng, và nếu không mở `raw` ra đọc thì ta đã kết luận nhầm về năng
lực của model.

Quy tắc rút ra, và nó rẻ: **cái gì `validate_*` từ chối được thì schema phải nói
trước.** Grammar của llama-server ràng buộc thật (đã kiểm bằng một enum chỉ nhận
một chuỗi bịa), nên mọi thứ đưa được vào `enum`/`minimum`/`maximum`/`required`
đều trở thành **bất khả về cấu trúc** thay vì một lỗi phải học bằng cách trượt.

**Chỗ quy tắc ấy DỪNG lại, và vì sao.** Dòng cuối bảng đi ngược chiều: nó là một
ràng buộc schema **không nói được**. JSON Schema không diễn đạt gọn được "arg phụ
thuộc kind" (phải `oneOf` mười lăm nhánh), nên enum ở đó là **phẳng** — mọi giá
trị hợp lệ cho mọi `kind`. Nó chặn được thứ nguy hiểm nhất, một chuỗi model bịa
ra, nhưng không chặn được `TERRAIN = "DAY"`. Qwen-7B ghi đúng một luật như thế ở
lượt 8, và nó **chiếm một ô sổ** trong khi `to_vietnamese` render thành *"đang
đứng trên ?"*. Cái gì schema không nói được thì bộ xác thực phải nói:
`ARG_DOMAIN` trong `genesis/validate.py`.

`tests/test_schema.py::test_moi_rang_buoc_cua_bo_xac_thuc_deu_co_trong_schema`
và `tests/test_validate.py::test_arg_phai_thuoc_mien_cua_kind` ghim năm ca này.

## 5. Lần thứ năm — và lần này bài học được đóng thành cơ chế

Qwen2.5-7B, seed 55 và 26. Sổ Luật **có** được ghi: 21 mục, 20 mục được nhận.
`match` vẫn **0.00** trên cả 90 dòng chấm.

Không phải model yếu. Đọc chính các mục nó ghi:

```
ARMOR_UP(TERRAIN)     HEAL(EAT)     ENERGY_GAIN(DAY)     ENERGY_DRAIN(quả xanh dài)
```

13/15 hiệu ứng **không mang `arg`** — `lawdsl.random_law` cho chúng `mag`/`dur`/`r`,
và luật thật để `arg=None`. Một mục ghi `ARMOR_UP(TERRAIN)` **không thể khớp luật
nào**, dù suy luận đằng sau nó có đúng hay không. Ở seed 26, **8/9 mục được nhận**
đều mang `effect.arg`: tám ô sổ và tám lần `CLAIM_COOLDOWN` đổi lấy 0 điểm.

Hai chỗ hỏng, cùng một gốc:

1. **`ARG_DOMAIN` không có mục nào cho 15 hiệu ứng**, mà `arg_fits_kind` viết
   `arg in domain if domain else True` — tuple rỗng là falsy, nên "chưa nêu miền"
   và "không nhận arg" sập vào làm một. Mọi hiệu ứng lọt.
2. **Schema chào một enum `arg` phẳng** dùng chung cho mọi kind. `legal_args` gộp
   40 giá trị lại để chặn model tự bịa chuỗi (nó từng viết bề mặt bằng tiếng
   Trung) — nhưng cái giá là model được phép rút bất kỳ giá trị nào cho bất kỳ ô
   nào, và nó làm đúng thế.

Sửa: `_kind_arg_schema` tách `oneOf` theo miền `arg` của từng kind, **đọc thẳng
từ `validate.ARG_DOMAIN`** — schema và bộ xác thực dùng chung một bảng. Đây là
điểm khác biệt so với bốn lần trước: bài học không còn là một điều phải nhớ mà là
một ràng buộc của cấu trúc. Thêm một miền vào bảng thì cả hai phía biết ngay.

Đo:

| | trước | sau |
|---|---|---|
| nhánh cho `effect` | 1 (enum phẳng 40 giá trị) | 3 (13 kind không arg / SPAWN / SPREAD) |
| nhánh cho `cond` | 1 | 8 |
| 6 lần hỏi model thật | `AGE=FIRE`, `EAT=FIRE`, `ARMOR_UP(TERRAIN)` | **6/6 hợp lệ, 0 bị từ chối** |
| 4000 luật thật qua validator | — | **0 bị từ chối oan** |
| 300 luật thật qua schema | — | **0 luật schema không diễn đạt nổi** |

`oneOf` đã thử trên llama.cpp b9430: GBNF dịch đúng, model nhả
`{"kind": "DAMAGE", "dur": "SHORT"}` — không kèm `arg`.

> Bốn lần trước bài học là "nhớ đồng bộ schema với validator". Lần này nó là
> "**đừng có hai bảng**". Bài học nào còn phải nhớ thì sẽ có ngày quên.
