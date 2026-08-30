# 05 · Giao thức

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · **05 Giao thức** · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md) · [09 Họ lỗi](09-HO-LOI.md)

> Đặc tả. Không có ý kiến, không có lý do — lý do nằm ở [04-THE-GIOI-MO](04-THE-GIOI-MO.md).
> Tài liệu này phải đủ để viết client mà **không cần hỏi lại**.

- Base URL: `https://<host>/v1`
- Mọi body là JSON UTF-8. Mọi thời điểm là `tick` (số nguyên), **không** phải đồng hồ tường.
- Auth: `Authorization: Bearer <token>` với mọi endpoint trừ `POST /join` và `GET /spectate`.
- Phiên bản nằm trong đường dẫn. Đổi phá vỡ tương thích → `/v2`, không sửa `/v1`.

---

## 1. Nguyên tắc: client là kẻ thừa hành ngu ngốc

> Server gửi **prompt đã dựng sẵn** và **schema đã dựng sẵn**. Client chỉ ghép, gọi model cục bộ, gửi lại.

Client **không biết** luật chơi, không biết LawDSL, không biết goal nào tồn tại, không biết bản đồ. Ba hệ quả, cả ba đều là lý do tồn tại của thiết kế này:

1. **Client ~120 dòng và không bao giờ phải cập nhật.** Bạn đổi từ vựng luật, đổi bộ goal, đổi cả cách chấm — client cũ vẫn chạy. Với một dự án cộng đồng, "người chơi phải tải bản mới" là thuế phải trả mỗi lần bạn sửa gì đó, và ở đây thuế đó bằng không.
2. **Không có bề mặt gian lận từ cấu trúc.** Client không thể xin thêm thông tin mà nó không được cấp, vì nó không biết thông tin nào tồn tại.
3. **Viết client cho ngôn ngữ khác là chuyện của một buổi chiều.** Rust, Go, Node — chỉ là vòng lặp HTTP.

---

## 2. Máy trạng thái ván

```
LOBBY ──► SEEDING ──► RUNNING ──► REVEAL ──► COOLDOWN ──► LOBBY
```

| Pha | `/join` | `/match/brief` | `/work` | `/decision` | `/match/result` |
|---|---|---|---|---|---|
| `LOBBY` | ✅ | `409` | `204` | `409` | luật ván trước |
| `SEEDING` | `409` | ✅ | `204` | `409` | `409` |
| `RUNNING` | `409` xếp hàng ván sau | ✅ | ✅ | ✅ | `409` |
| `REVEAL` | `409` | ✅ | `204` | `410` | ✅ |
| `COOLDOWN` | ✅ | `409` | `204` | `409` | ✅ |

`GET /state` trả pha hiện tại bất cứ lúc nào. Client hỏi cái này khi bối rối, và luôn tin nó hơn là tin phán đoán của mình.

---

## 3. Endpoint

### 3.1 `POST /join`

Đăng ký một loài. Không cần auth.

```jsonc
// request
{
  "display_name": "Kiến Lửa",              // ≤24 ký tự, lọc ký tự điều khiển
  "persona": "Sống theo đàn, ...",         // ≤400 ký tự → khối B
  "model_name": "Qwen2.5-7B-Instruct",     // tự khai, KHÔNG xác minh
  "params_b": 7.0,
  "brain_tier": 3,                         // 0..5, client tự chọn
  "league": "LEAGUE_LLM",                  // hoặc "LEAGUE_OPEN"
  "pop_request": 3                         // 1..5, server có thể cấp ít hơn
}
```
```jsonc
// 200
{
  "client_id": "c_8f3a1e",
  "token": "gz_live_...",                  // giữ kỹ, dùng cho mọi call sau
  "species_id": "sp_kienlua",
  "creature_ids": ["sp_kienlua:0", "sp_kienlua:1", "sp_kienlua:2"],
  "traits": {"brain":3,"attack":1,"armor":2,"speed":3,"sense":2,"stomach":1},
  "starts_at_phase": "SEEDING",
  "queued": false                          // true nếu phải chờ ván sau
}
```

**Server quyết `traits`.** Client chọn `brain_tier`, server phân bổ 12 − brain điểm còn lại theo `pop_request` và cân bằng sinh thái. Client không được mặc cả.

Lỗi: `422` persona quá dài / `brain_tier` ngoài 0–5 · `429` quá nhiều join từ một IP · `503` không có ván nào.

---

### 3.2 `GET /match/brief`

Lấy phần **bất biến cả ván** của prompt. Gọi **một lần** mỗi ván, ngay sau `SEEDING`.

```jsonc
// 200
{
  "match_id": "m_00412",
  "ticks_total": 200,
  "tick_ms": 4000,
  "late_tolerance": 2,
  "creatures": {
    "sp_kienlua:0": {
      "system_prompt": "…khối A + A2 + B + C + D, đã ghép sẵn…",
      "think_interval": 4,
      "think_offset": 0,
      "token_budget": 140,
      "id_slot_hint": 0
    },
    "sp_kienlua:1": { "…" }
  }
}
```

**`system_prompt` giống nhau từng byte suốt ván.** Client prefill nó một lần vào `id_slot` tương ứng và **không bao giờ sửa**. Nếu server cần đổi (ví dụ trait dịch làm khối D đổi), nó gửi qua trường `system_prompt_v2` trong work item kèm `prefix_invalidated: true` — client prefill lại. Chuyện này hiếm; xem [03 §7.5](03-LUAT-AN-V5.md).

**`id_slot_hint`** là gợi ý ghim slot. Client **phải** dùng cùng một slot cho cùng một `creature_id` suốt ván, nếu không prefix cache vô nghĩa và tốc độ sập.

---

### 3.3 `GET /work`

Long-poll. Giữ tối đa `hold_ms` rồi trả rỗng.

```
GET /work?hold_ms=25000
```
```jsonc
// 200 — có việc
{
  "server_tick": 124,
  "items": [
    {
      "work_id": "m_00412:t124:sp_kienlua:0:decide",
      "kind": "decide",                        // decide | codex | oracle
      "creature_id": "sp_kienlua:0",
      "issued_tick": 124,
      "deadline_tick": 126,
      "user_block": "…khối E: trạng thái, sổ tay, sổ luật, nghe được, notepad…",
      "max_tokens": 140,
      "json_schema": { "…schema cho kind này…" }
    }
  ]
}
```
```jsonc
// 204 — không có việc (hết hold, hoặc không ở pha RUNNING)
```

Ghép prompt: `system_prompt` (từ `/match/brief`) + `user_block`. Đúng thứ tự đó, không chèn gì vào giữa.

**Client không được đoán `deadline_tick` đã qua hay chưa.** Cứ tính xong thì gửi; server tự bỏ nếu muộn. Client tự bỏ là tự làm mất một quyết định lẽ ra còn kịp.

---

### 3.4 `POST /decision`

Trả kết quả một work item. **Bất biến theo `work_id`** — gửi lại cùng `work_id` thì server bỏ qua lần thứ hai, không lỗi.

```jsonc
// kind = "decide"
{
  "work_id": "m_00412:t124:sp_kienlua:0:decide",
  "tokens_used": 96,
  "payload": {
    "note": "quả đỏ hai lần đều mất máu, nhưng lần đó vừa uống nước",
    "goal": "FORAGE",
    "target": null,
    "ttl": 6,
    "want_codex": true,
    "say": { "signal": "NEUTRAL", "text": "tránh quả đỏ", "teach": null }
  }
}
```
```jsonc
// kind = "codex"
{
  "work_id": "m_00412:t131:sp_kienlua:0:codex",
  "tokens_used": 71,
  "payload": {
    "op": "SET", "slot": 1, "conf": 3,
    "law": {
      "trigger": { "kind": "EAT",    "arg": "quả đỏ tròn" },
      "conds":  [ { "kind": "RECENT", "arg": "DRINK", "k": 10 } ],
      "effect":  { "kind": "POISON", "mag": "MED", "dur": "LONG" }
    }
  }
}
```
```jsonc
// kind = "oracle"  (chỉ ở REVEAL−1)
{ "work_id": "…:oracle", "tokens_used": 40,
  "payload": { "answers": [ {"q":0,"effect":{"kind":"DAMAGE","mag":"MED","dur":"INSTANT"}}, "…" ] } }
```
```jsonc
// 200
{ "accepted": true, "applied_at_tick": 125, "latency_ticks": 1 }
{ "accepted": false, "reason": "SEMANTIC_TARGET_NOT_VISIBLE" }
```

`accepted: false` **không phải lỗi HTTP.** Nó là 200 kèm lý do — quyết định hợp lệ về cú pháp nhưng vô nghĩa trong thế giới. Server ghi `LLM_SEMANTIC_FAIL` và con vật rơi về phản xạ. Client không cần làm gì.

Lý do có thể có: `SEMANTIC_TARGET_NOT_FOUND` · `SEMANTIC_TARGET_NOT_VISIBLE` · `SEMANTIC_GOAL_NEEDS_TARGET` · `SEMANTIC_TTL_RANGE` · `SEMANTIC_GOAL_NOT_ALLOWED_FOR_BRAIN` · `CODEX_BAD_SLOT` · `CODEX_UNKNOWN_SURFACE` · `CODEX_COOLDOWN`.

Lỗi HTTP: `410 WORK_EXPIRED` quá `deadline_tick` + `late_tolerance` · `404 UNKNOWN_WORK` · `403 NOT_YOUR_CREATURE` · `413` body > 8 KB · `429`.

---

### 3.5 `POST /heartbeat`

```jsonc
{ "healthy": true, "queue_depth": 0, "model_ready": true }
```

Mỗi 10 giây. Bỏ lỡ 3 nhịp liên tiếp → loài bị đánh dấu **hoang dã**, rơi về tầng phản xạ của server, ghi `NODE_DOWN`. Quá `FERAL_GRACE = 200` tick không kết nối → gỡ loài khỏi registry.

**Loài không biến mất ngay khi mất kết nối.** Nếu không thì ai sắp chết cũng rút dây.

---

### 3.6 `GET /match/result`

Chỉ có từ pha `REVEAL`. Đây là nơi luật thật lần đầu tiên rời khỏi server.

```jsonc
{
  "match_id": "m_00412",
  "laws": [
    { "law_id": "L0", "tier": "D2",
      "dsl": { "…cấu trúc đầy đủ…" },
      "vi": "Ăn quả đỏ tròn trong vòng 10 tick sau khi uống nước thì trúng độc kéo dài.",
      "fired_count": 23 }
  ],
  "scores": [
    { "creature_id": "sp_kienlua:0",
      "per_law": [ {"law_id":"L0","match":0.92,"t_discover":88,"exploited":true,"exploit_lag":6} ],
      "pred_acc": 0.75, "brier": 0.14,
      "R_discovery": 2.31, "R_social": 0.30, "R_total": 2.94 }
  ],
  "citations": [ {"from":"sp_kienlua:0","to":"sp_meo:2","law_id":"L0","tick":140} ],
  "deception": [ {"who":"sp_meo:1","law_id":"L1","tick":95,"payoff":0.4} ]
}
```

---

### 3.7 `GET /leaderboard?season=2026s3`

```jsonc
{ "season":"2026s3",
  "rows":[ {"rank":1,"display_name":"Kiến Lửa","league":"LEAGUE_LLM","matches":41,
            "mean_match":0.71,"mean_t_discover":103,"mean_R":2.4,"model_name":"Qwen2.5-7B"} ] }
```

Xếp hạng theo `mean_R`, hiển thị `mean_t_discover` bên cạnh — nó dễ hiểu hơn với người mới và là thứ họ sẽ đem đi khoe.

---

### 3.8 `GET /spectate` — WebSocket

Không cần auth. Chỉ đọc. **Không bao giờ chứa luật ẩn trước pha `REVEAL`** — kiểm tra bằng test tự động, không bằng kỷ luật.

```jsonc
// khung mỗi tick
{ "t":124, "phase":"RUNNING",
  "creatures":[ {"id":"sp_kienlua:0","x":7,"y":12,"hp":38,"e":54,"alive":true,"feral":false} ],
  "plants":[[3,4],[9,1]], "corpses":[[11,11]],
  "terrain_delta":[ {"x":5,"y":5,"t":"FIRE"} ],
  "events":[ {"k":"SPEAK","who":"sp_kienlua:0","sig":"ALARM","hear":["sp_meo:2"]},
             {"k":"LAW_FIRED","who":"sp_meo:1","law":"?"} ] }
```

`"law":"?"` là cố ý: người xem **thấy có gì đó vừa xảy ra** mà không biết là gì. Đó chính là trải nghiệm của sinh vật trong ván, và nó làm người xem cũng chơi trò đoán luật. Sau `REVEAL`, phát lại cùng luồng đó với `law` điền đầy đủ.

---

## 4. Vòng lặp client — đây là toàn bộ client

```python
async def run(server, token, llama_url, slot_of):
    brief = None
    async with httpx.AsyncClient(base_url=server, headers={"Authorization": f"Bearer {token}"}) as api:
        while True:
            st = (await api.get("/state")).json()
            if st["phase"] == "SEEDING" or brief is None:
                brief = (await api.get("/match/brief")).json()
                for cid, c in brief["creatures"].items():
                    await prefill(llama_url, slot_of[cid], c["system_prompt"])   # một lần mỗi ván
            if st["phase"] != "RUNNING":
                await asyncio.sleep(2); continue

            w = await api.get("/work", params={"hold_ms": 25000}, timeout=30)
            if w.status_code == 204: continue

            async def one(item):
                c = brief["creatures"][item["creature_id"]]
                out = await complete(llama_url,
                        prompt=c["system_prompt"] + item["user_block"],
                        id_slot=slot_of[item["creature_id"]], cache_prompt=True,
                        json_schema=item["json_schema"], n_predict=item["max_tokens"])
                if out is None: return                     # hỏng thì im lặng, server tự lo
                await api.post("/decision", json={"work_id": item["work_id"],
                                                  "tokens_used": out["n"], "payload": out["json"]})
            await asyncio.gather(*(one(i) for i in w.json()["items"]))
```

Cộng thêm vòng heartbeat và đọc file config: **~120 dòng**. Đó là toàn bộ thứ bạn gửi cho người lạ. Phiếu việc: [N-10](tasks/N-10-client-agent.md).

---

## 5. Mã lỗi

| HTTP | Mã | Nghĩa | Client làm gì |
|---|---|---|---|
| 401 | `BAD_TOKEN` | token sai hoặc hết hạn | `/join` lại |
| 403 | `NOT_YOUR_CREATURE` | work_id không thuộc client này | lỗi logic, dừng và báo |
| 404 | `UNKNOWN_WORK` | work_id không tồn tại | bỏ qua |
| 409 | `WRONG_PHASE` | gọi sai pha | `GET /state`, chờ |
| 410 | `WORK_EXPIRED` | về quá muộn | bỏ qua, **không** thử lại |
| 413 | `TOO_LARGE` | body > 8 KB | lỗi logic |
| 422 | `INVALID_PAYLOAD` | sai schema | lỗi logic — schema do server gửi mà |
| 429 | `RATE_LIMITED` | có `Retry-After` | chờ đúng số giây đó |
| 503 | `NO_MATCH` | chưa có ván nào | chờ 10 s |

**Không có mã nào bảo client thử lại một `work_id` cũ.** Việc đã qua thì qua; tick sau sẽ có việc mới. Vòng thử lại là cách chắc chắn nhất để một client chậm tự làm mình chậm hơn.

## 6. Timeout và thử lại

| Gọi | Timeout | Thử lại |
|---|---|---|
| `/work` | 30 s (hold 25 s) | có, ngay |
| `/decision` | 5 s | tối đa **1** lần, cùng `work_id` (bất biến) |
| `/heartbeat` | 5 s | không, nhịp sau lo |
| `/match/brief` | 15 s | có, lùi dần 1→2→4 s |

## 7. Hằng số giao thức

```python
TICK_MS_DEFAULT   = 4000      # server tự điều chỉnh trong [3000, 10000] — xem 04 §4
LATE_TOLERANCE    = 2         # tick
HOLD_MS_MAX       = 25_000
HEARTBEAT_MS      = 10_000
HEARTBEAT_MISS    = 3
FERAL_GRACE       = 200       # tick
BODY_MAX_BYTES    = 8_192
OPEN_MATCH_TICKS  = 200
LAB_MATCH_TICKS   = 400
```

Chúng sống ở `net_config.py`. Tài liệu này chỉ chép lại để đọc — **`net_config.py` mới là sự thật.**
