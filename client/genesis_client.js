#!/usr/bin/env node
// Genesis Zero — client Node.js (N-10c).
//
//   node client/genesis_client.js --server http://localhost:8000 \
//        --model-url http://localhost:8080 --name "Quạ Khoang"
//
// Tài liệu của dự án khẳng định: *"viết client cho ngôn ngữ khác là chuyện của
// một buổi chiều"* (docs/05 §1). File này tồn tại để câu đó **được kiểm chứng**
// chứ không chỉ được nói. Nó không dùng thư viện ngoài nào — `fetch` có sẵn từ
// Node 18 — và nó không biết một chữ nào về luật chơi: server gửi
// `system_prompt`, `user_block` và `json_schema` đã dựng sẵn.
//
// Nếu bạn thấy mình muốn thêm một bảng goal hay một tên EffectKind vào đây thì
// thiết kế đã sai chỗ khác, không phải ở đây.

const HEARTBEAT_MS = 10_000;

function argOf(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const SERVER = (argOf("server", "http://localhost:8000")).replace(/\/$/, "");
const MODEL_URL = (argOf("model-url", "http://localhost:8080")).replace(/\/$/, "");
const NAME = argOf("name", "Quạ Khoang");
const PERSONA = argOf("persona", "Nhặt nhạnh, bắt chước, kể lại cho đồng loại.");
const BRAIN_TIER = Number(argOf("brain-tier", "3"));
const POP = Number(argOf("pop", "2"));
const ROUNDS = Number(argOf("rounds", "0")) || Infinity;

const log = (...a) => console.log(new Date().toISOString(), ...a);

async function askModel(slot, system, user, maxTokens, schema) {
  // Endpoint gốc `/completion` — chỉ nó nhận `id_slot`, và không có `id_slot`
  // thì prefix cache vô nghĩa. Cùng creature_id phải giữ CÙNG một slot suốt ván.
  const url = MODEL_URL.endsWith("/completion") ? MODEL_URL : `${MODEL_URL}/completion`;
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        prompt: system + user,     // thứ tự này, không chèn gì vào giữa
        id_slot: slot,
        cache_prompt: true,
        json_schema: schema,
        n_predict: maxTokens,
        temperature: 0.7,
      }),
    });
    if (!r.ok) { log("model trả HTTP", r.status); return null; }
    const data = await r.json();
    if (typeof data.content !== "string") { log("phản hồi model thiếu 'content'"); return null; }
    return { json: JSON.parse(data.content), n: data.tokens_predicted ?? 0 };
  } catch (e) {
    log("lỗi khi gọi model:", e.message);   // JSON cụt hoặc mạng hỏng -> bỏ lượt
    return null;
  }
}

async function main() {
  const join = await (await fetch(`${SERVER}/v1/join`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      display_name: NAME, persona: PERSONA, model_name: "node-client",
      params_b: 0, brain_tier: BRAIN_TIER, league: "LEAGUE_OPEN", pop_request: POP,
    }),
  })).json();
  if (!join.token) { log("join hỏng:", JSON.stringify(join)); process.exit(1); }
  const H = { authorization: `Bearer ${join.token}`, "content-type": "application/json" };
  log("đã vào:", join.species_id, JSON.stringify(join.creature_ids));

  setInterval(() => {
    fetch(`${SERVER}/v1/heartbeat`, {
      method: "POST", headers: H,
      body: JSON.stringify({ healthy: true, queue_depth: 0, model_ready: true }),
    }).catch(() => {});          // mất một nhịp không phải lý do để thoát
  }, HEARTBEAT_MS).unref();

  let matchId = null, prompts = {}, slots = {}, rounds = 0;
  while (rounds < ROUNDS) {
    const st = await (await fetch(`${SERVER}/v1/state`)).json();

    // Ván mới -> lấy brief MỘT LẦN. `system_prompt` sau đó là bất khả xâm phạm:
    // sửa một byte là prefix cache của chính máy này vô nghĩa.
    if (st.match_id !== matchId && ["SEEDING", "RUNNING"].includes(st.phase)) {
      const b = await fetch(`${SERVER}/v1/match/brief`, { headers: H });
      if (b.ok) {
        const d = await b.json();
        matchId = d.match_id; prompts = {}; slots = {};
        for (const [cid, info] of Object.entries(d.creatures)) {
          prompts[cid] = info.system_prompt;
          slots[cid] = info.id_slot_hint;
        }
        log(`brief ván ${matchId}: ${Object.keys(prompts).length} cá thể`);
      }
    }

    if (st.phase !== "RUNNING" || !Object.keys(prompts).length) {
      await new Promise((r) => setTimeout(r, 500));
      continue;
    }

    const w = await fetch(`${SERVER}/v1/work?hold_ms=25000`, { headers: H });
    if (w.status !== 200) continue;
    const items = (await w.json()).items ?? [];
    if (!items.length) continue;

    await Promise.all(items.map(async (it) => {
      const r = await askModel(slots[it.creature_id] ?? 0, prompts[it.creature_id] ?? "",
                               it.user_block, it.max_tokens, it.json_schema);
      if (!r) return;            // model hỏng -> KHÔNG gửi decision
      // Không tự đoán `deadline_tick` đã qua chưa: cứ tính xong thì gửi, server
      // tự bỏ nếu muộn. Tự bỏ là tự làm mất một quyết định lẽ ra còn kịp.
      await fetch(`${SERVER}/v1/decision`, {
        method: "POST", headers: H,
        body: JSON.stringify({ work_id: it.work_id, tokens_used: r.n, payload: r.json }),
      }).catch((e) => log("gửi quyết định hỏng:", e.message));
    }));
    rounds += 1;
  }
}

main().catch((e) => { log("thoát vì:", e); process.exit(1); });
