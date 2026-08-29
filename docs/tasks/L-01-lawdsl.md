# L-01 · LawDSL — kiểu, JSON, GBNF

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | W-13 |
| **Chặn** | L-02, L-03, L-04, L-07, B-02, B-08 |
| **File** | `genesis/lawdsl.py` |
| **Ước lượng** | ~200 dòng · 3 giờ |
| **Giao cho model rẻ?** | ✅ cơ học thuần; round-trip test ghim chặt tính đúng |
| **Tài liệu gốc** | [03 §2.2 §2.3](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Một ký pháp dùng chung cho **ba** nơi: bộ sinh luật, bộ chấm, và agent phát biểu. Ba chỗ, **một** định nghĩa. Đây cũng là quyết định an ninh — vì `teach` mang cấu trúc chứ không mang văn bản, kênh dạy nhau không có bề mặt tiêm lệnh ([04 §7.4](../04-THE-GIOI-MO.md)).

## 2. Đầu vào đã có
Từ vựng đầy đủ ở [03 §2.3](../03-LUAT-AN-V5.md): 11 trigger, 10 cond, 12 effect.

## 3. Việc phải làm
1. Enum cho mọi `kind`. Frozen dataclass cho `Trigger`, `Cond`, `Effect`, `Law`.
2. `to_json` / `from_json`, round-trip chính xác.
3. **Sinh GBNF tự động từ chính định nghĩa** — không viết grammar bằng tay.
4. `to_vietnamese(law, surface_map) -> str` cho REVEAL và log.
5. `vocab_for_brain(brain) -> Vocab` — cắt từ vựng theo [03 §8](../03-LUAT-AN-V5.md).

## 4. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class Trigger: kind: TriggerKind; arg: str | None = None; k: int | None = None
@dataclass(frozen=True)
class Cond:    kind: CondKind;    arg: str | None = None; k: int | None = None; op: str | None = None; n: int | None = None
@dataclass(frozen=True)
class Effect:  kind: EffectKind;  mag: Mag | None = None; dur: Dur | None = None; r: int | None = None; arg: str | None = None
@dataclass(frozen=True)
class Law:     trigger: Trigger; conds: tuple[Cond, ...]; effect: Effect
    def tier(self) -> str: ...            # D1..D4

def to_json(law: Law) -> dict: ...
def from_json(d: dict) -> Law: ...
def to_gbnf(vocab: "Vocab") -> str: ...   # SINH TỰ ĐỘNG từ enum
def to_vietnamese(law: Law, sm: SurfaceMap) -> str: ...
def vocab_for_brain(brain: int) -> "Vocab": ...
```
**Bất biến 1:** `conds` là `tuple`, tối đa 2, và **so sánh không phụ thuộc thứ tự** — `AND` giao hoán. Chuẩn hoá bằng cách sắp theo `(kind.value, arg or "")` lúc dựng.
**Bất biến 2:** GBNF sinh từ enum. Grammar viết tay sẽ lệch khỏi dataclass sau ba lần sửa, và triệu chứng là "model tự dưng ghi sổ sai cú pháp".
**Bất biến 3 — an ninh:** `to_vietnamese` là **hàm thuần của giá trị enum**. Không nội suy chuỗi do client cung cấp vào nó, không bao giờ, kể cả tên loài. Vi phạm là mở lại toàn bộ cửa tiêm lệnh mà DSL vừa đóng ([04 §7.4](../04-THE-GIOI-MO.md)).
**Bất biến 4:** `Law` viết theo **bề mặt** khi đến từ agent, theo **lớp** khi ở trong engine. Chuyển đổi đúng một chỗ, qua `SurfaceMap`.

## 5. Bẫy
`Mag` và `Dur` là **rổ**, không phải số: `SMALL/MED/BIG`, `INSTANT/SHORT/LONG`. Nếu bạn để chúng là int thì `match()` ở L-06 sẽ so số chính xác và mọi agent đều trượt — agent không có cách nào đo con số thật.

## 6. Nghiệm thu
```bash
python - <<'PY'
import random, json
from genesis.lawdsl import *
rng = random.Random(0)
for _ in range(1000):
    law = random_law(rng)
    assert from_json(to_json(law)) == law
# ba ví dụ ở 03 §2.4 phải viết được
l1 = Law(Trigger(TriggerKind.EAT,"FRUIT_A"), (Cond(CondKind.RECENT,"DRINK",k=10),),
         Effect(EffectKind.POISON, Mag.MED, Dur.LONG));            assert l1.tier()=="D2"
l2 = Law(Trigger(TriggerKind.STEP_ON,"FIRE"), (Cond(CondKind.PHASE,"NIGHT"),),
         Effect(EffectKind.SPREAD, arg="FIRE"));                   assert l2.tier() in ("D2","D4")
l3 = Law(Trigger(TriggerKind.ADJACENT,"ANY",n=1), (), Effect(EffectKind.HEAL, Mag.SMALL, Dur.LONG)); assert l3.tier()=="D1"
# AND giao hoán
a=Law(Trigger(TriggerKind.EAT,"FRUIT_A"),(Cond(CondKind.PHASE,"NIGHT"),Cond(CondKind.HP,"LOW")),Effect(EffectKind.DAMAGE,Mag.MED,Dur.INSTANT))
b=Law(Trigger(TriggerKind.EAT,"FRUIT_A"),(Cond(CondKind.HP,"LOW"),Cond(CondKind.PHASE,"NIGHT")),Effect(EffectKind.DAMAGE,Mag.MED,Dur.INSTANT))
assert a==b, "AND phải giao hoán"
# vocab cắt theo brain
assert len(vocab_for_brain(0).conds)==0 and len(vocab_for_brain(5).conds)>=10
print("OK")
PY
# GBNF sinh ra phải parse được bằng chính from_json
python scripts/check_gbnf.py --brain 5
```

## 7. Prompt giao việc
```
BỐI CẢNH
Python 3.11, chỉ thư viện chuẩn. Đọc trước: docs/03-LUAT-AN-V5.md §2.2 và §2.3 (bảng từ vựng
đầy đủ: 11 trigger, 10 cond, 12 effect) và §8 (bảng cắt từ vựng theo brain).
Đừng đọc tài liệu khác.

VIỆC
genesis/lawdsl.py:
1. StrEnum: TriggerKind, CondKind, EffectKind, Mag(SMALL/MED/BIG), Dur(INSTANT/SHORT/LONG).
   Giá trị lấy ĐÚNG từ bảng ở §2.3.
2. frozen dataclass Trigger, Cond, Effect, Law (conds là tuple, tối đa 2).
   Law.__post_init__ SẮP XẾP conds theo (kind.value, arg or "") -> AND giao hoán.
   Law.tier() -> "D1".."D4" theo quy tắc: 0 cond = D1; 1 cond = D2; 2 cond = D3;
   effect thuộc {SPREAD, SPAWN, TELEPORT} hoặc trigger ADJACENT = D4.
3. to_json(law)->dict, from_json(dict)->Law. Round-trip chính xác.
4. to_gbnf(vocab)->str: SINH TỰ ĐỘNG bằng cách duyệt các enum trong vocab. KHÔNG viết
   grammar bằng tay, KHÔNG hardcode tên nhánh.
5. vocab_for_brain(brain)->Vocab theo bảng §8.
6. random_law(rng, vocab=None)->Law dùng rng truyền vào.
7. to_vietnamese(law, surface_map)->str: HÀM THUẦN CỦA GIÁ TRỊ ENUM. Bảng tra cứng
   enum -> cụm tiếng Việt. TUYỆT ĐỐI không nội suy chuỗi từ bên ngoài vào ngoài
   surface_map.surface_of(cls).
8. tests/test_lawdsl.py: round-trip 1000 luật ngẫu nhiên; AND giao hoán; ba ví dụ ở §2.4;
   vocab_for_brain(0).conds rỗng và vocab_for_brain(5).conds >= 10.

RÀNG BUỘC
- Chỉ thư viện chuẩn. Không thêm phụ thuộc.
- Mag và Dur là ROO (enum), KHÔNG phải số nguyên.
- Không tạo file nào khác ngoài genesis/lawdsl.py và tests/test_lawdsl.py.
- Không sửa file khác trong genesis/.
- Không dùng random ở module-level; mọi ngẫu nhiên nhận rng: random.Random qua tham số.

NGHIỆM THU: pytest tests/test_lawdsl.py -q

TRẢ VỀ: chỉ diff.
```
