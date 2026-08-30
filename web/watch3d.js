// Genesis Zero — watch3d: cảnh 3D cho ván đang chạy (N-14).
//
// Cùng một luồng WebSocket với trang 2D (`/v1/spectate`), khác cách vẽ. Ba thứ
// dựng nên cảnh, và cả ba đều đến TỪ KHUNG chứ không từ một bảng chép cứng:
//
//   * địa hình  — `frame.terrain` (server gửi một lần mỗi ván)
//   * sinh vật  — `frame.creatures[].tr`, vector trait HIỆN TẠI
//   * ai nghe được ai — `frame.events[].hear`, do server tính
//
// Bảng chép cứng trong JS là bảng sẽ lệch: trait dịch giữa ván, và loài do người
// lạ tạo ra lúc chạy thì trang này không thể biết trước.
//
// CẤM KỴ (docs/02 §5): kích thước sinh vật KHÔNG phụ thuộc cỡ model. Người chạy
// model to được hình đẹp hơn thì không sao; con vật TO HƠN thì không.
(function () {
  const TR = { brain: 0, attack: 1, armor: 2, speed: 3, sense: 4, stomach: 5 };
  const CELL = 1;
  // Mỗi loại ô một độ cao và một màu. Nước trũng, đá nhô — đó là toàn bộ "3D"
  // của địa hình, và nó đủ để nhìn ra hình dạng bản đồ từ trên cao.
  // Khung gửi địa hình dạng chuỗi một ký tự mỗi ô — 24×24 ký tự thay vì 576
  // chuỗi JSON. Bảng này là chỗ DUY NHẤT dịch ký tự sang hình.
  const TERRAIN = {
    P: { h: 0.10, c: 0x3f6212 },   // đồng cỏ
    W: { h: 0.02, c: 0x1d4ed8 },   // nước — trũng xuống
    B: { h: 0.45, c: 0x14532d },   // bụi rậm
    R: { h: 0.95, c: 0x57534e },   // đá — nhô lên
    F: { h: 0.16, c: 0xea580c },   // lửa
    D: { h: 0.00, c: 0x0c2a6b },   // nước sâu — trũng hẳn, chỉ tầng NƯỚC (W-18)
    T: { h: 1.40, c: 0x166534 },   // cây — cao nhất bản đồ, chỉ loài biết trèo
    C: { h: 0.30, c: 0x1c1917 },   // hang — trũng trong lòng đá, chỉ loài đào hang
  };

  const el = (id) => document.getElementById(id);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x06080f);
  scene.fog = new THREE.Fog(0x06080f, 26, 62);

  const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.1, 400);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  el("scene").appendChild(renderer.domElement);
  addEventListener("resize", () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  scene.add(new THREE.HemisphereLight(0xbfdbfe, 0x1c1917, 0.85));
  const sun = new THREE.DirectionalLight(0xfff7ed, 0.9);
  sun.position.set(14, 26, 10);
  scene.add(sun);

  // ── camera quỹ đạo, tự viết cho gọn (OrbitControls là file thứ ba) ──
  let yaw = 0.7, pitch = 0.95, dist = 34, dragging = false, lx = 0, ly = 0;
  let cx = 12, cz = 12;
  renderer.domElement.addEventListener("mousedown", (e) => { dragging = true; lx = e.clientX; ly = e.clientY; });
  addEventListener("mouseup", () => { dragging = false; });
  addEventListener("mousemove", (e) => {
    if (!dragging) return;
    yaw -= (e.clientX - lx) * 0.006;
    pitch = Math.max(0.18, Math.min(1.5, pitch - (e.clientY - ly) * 0.006));
    lx = e.clientX; ly = e.clientY;
  });
  renderer.domElement.addEventListener("wheel", (e) => {
    dist = Math.max(8, Math.min(90, dist + e.deltaY * 0.03));
    e.preventDefault();
  }, { passive: false });

  let showHear = true;
  addEventListener("keydown", (e) => { if (e.key === "g" || e.key === "G") showHear = !showHear; });

  // ── trạng thái cảnh ──
  const terrainGroup = new THREE.Group();
  const bodyGroup = new THREE.Group();
  const lineGroup = new THREE.Group();
  const sparkGroup = new THREE.Group();
  scene.add(terrainGroup, bodyGroup, lineGroup, sparkGroup);

  let W = 24, H = 24, latest = null, terrainKey = "";
  const bodies = new Map();          // creature_id -> THREE.Group
  const flashes = [];                // { a, b, t0 } cho đồ thị nghe
  const sparks = [];                 // { mesh, t0 } cho LAW_FIRED

  function hashStr(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) { h = ((h << 5) - h) + s.charCodeAt(i); h |= 0; }
    return Math.abs(h);
  }

  function buildTerrain(rows) {
    if (!rows || !rows.length) return;
    const key = rows.join("|");
    if (key === terrainKey) return;          // chỉ dựng lại khi bản đồ đổi
    terrainKey = key;
    while (terrainGroup.children.length) terrainGroup.remove(terrainGroup.children[0]);
    H = rows.length; W = rows[0].length;
    cx = W / 2; cz = H / 2;

    // Gom theo loại ô rồi dựng một InstancedMesh mỗi loại: 24×24 ô mà mỗi ô một
    // mesh thì trình duyệt phải vẽ 576 lần một khung, và nó sẽ giật.
    const byType = {};
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) (byType[rows[y][x]] ||= []).push([x, y]);

    const geo = new THREE.BoxGeometry(CELL, 1, CELL);
    for (const [type, cells] of Object.entries(byType)) {
      const t = TERRAIN[type] || TERRAIN.P;
      const mesh = new THREE.InstancedMesh(
        geo, new THREE.MeshLambertMaterial({ color: t.c }), cells.length);
      const m = new THREE.Matrix4();
      cells.forEach(([x, y], i) => {
        m.makeScale(1, t.h, 1);
        m.setPosition(x + 0.5, t.h / 2, y + 0.5);
        mesh.setMatrixAt(i, m);
      });
      mesh.instanceMatrix.needsUpdate = true;
      terrainGroup.add(mesh);
    }
  }

  function makeBody(c) {
    // Hình suy từ vector trait, đúng cùng ánh xạ với trang 2D và bản pygame.
    const t = c.tr || [2, 2, 2, 2, 2, 2];
    const hue = ((hashStr(c.id.split(":")[0]) % 360) + ((hashStr(c.id) % 21) - 10) + 360) % 360;
    const col = new THREE.Color().setHSL(hue / 360, 0.62, 0.55);
    const dark = new THREE.Color().setHSL(hue / 360, 0.8, 0.22);
    const g = new THREE.Group();

    const body = new THREE.Mesh(
      new THREE.SphereGeometry(0.16 + t[TR.stomach] * 0.035, 12, 10),
      new THREE.MeshLambertMaterial({ color: col }));
    body.scale.z = 1 + t[TR.speed] * 0.14;           // chân dài -> thân thuôn
    body.position.y = 0.28;
    g.add(body);

    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.07 + t[TR.brain] * 0.028, 10, 8),
      new THREE.MeshLambertMaterial({ color: col }));
    head.position.set(0, 0.42 + t[TR.brain] * 0.02, 0.18 + t[TR.speed] * 0.03);
    g.add(head);

    for (const s of [-1, 1]) {                        // mắt: sense
      const eye = new THREE.Mesh(
        new THREE.SphereGeometry(0.018 + t[TR.sense] * 0.012, 6, 6),
        new THREE.MeshBasicMaterial({ color: 0xffffff }));
      eye.position.set(s * (0.03 + t[TR.sense] * 0.012), head.position.y + 0.02,
                       head.position.z + 0.05);
      g.add(eye);
    }
    for (let i = 0; i < t[TR.armor]; i++) {            // gai lưng: armor
      const sp = new THREE.Mesh(
        new THREE.ConeGeometry(0.035, 0.09, 5),
        new THREE.MeshLambertMaterial({ color: dark }));
      sp.position.set(0, 0.44, -0.1 + i * 0.07);
      g.add(sp);
    }
    if (t[TR.attack] > 0) {                            // nanh: attack
      const f = new THREE.Mesh(
        new THREE.ConeGeometry(0.022, 0.05 + t[TR.attack] * 0.022, 5),
        new THREE.MeshLambertMaterial({ color: 0xf8fafc }));
      f.rotation.x = Math.PI / 2;
      f.position.set(0, head.position.y - 0.04, head.position.z + 0.07);
      g.add(f);
    }
    g.userData.mats = g.children.map((m) => m.material);
    return g;
  }

  function syncBodies(frame) {
    const alive = new Set();
    for (const c of frame.creatures || []) {
      alive.add(c.id);
      let g = bodies.get(c.id);
      if (!g) { g = makeBody(c); bodies.set(c.id, g); bodyGroup.add(g); }
      g.position.set(c.x + 0.5, TERRAIN.P.h, c.y + 0.5);
      const e = Math.max(0.12, Math.min(1, (c.e || 0) / (c.e_max || 1)));
      for (const m of g.userData.mats) {
        if (m.opacity !== undefined) { m.transparent = true; m.opacity = c.alive ? 1 : 0.18; }
        if (m.emissive) m.emissive.setScalar(c.alive ? e * 0.12 : 0);
      }
      g.visible = true;
    }
    for (const [id, g] of bodies) if (!alive.has(id)) g.visible = false;
  }

  function drawHearing(frame) {
    while (lineGroup.children.length) lineGroup.remove(lineGroup.children[0]);
    if (!showHear) return;
    const now = performance.now();
    const cs = (frame.creatures || []).filter((c) => c.alive);
    const pos = Object.fromEntries(cs.map((c) => [c.id, c]));
    for (let i = 0; i < cs.length; i++)
      for (let j = i + 1; j < cs.length; j++) {
        const a = cs[i], b = cs[j];
        let dx = Math.abs(a.x - b.x), dy = Math.abs(a.y - b.y);
        dx = Math.min(dx, W - dx); dy = Math.min(dy, H - dy);
        const d = Math.max(dx, dy);
        const ra = 2 + (a.tr ? a.tr[TR.sense] : 2), rb = 2 + (b.tr ? b.tr[TR.sense] : 2);
        if (d > ra && d > rb) continue;
        const fl = flashes.find((f) => now - f.t0 < 300 &&
          ((f.a === a.id && f.b.includes(b.id)) || (f.a === b.id && f.b.includes(a.id))));
        const g = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(a.x + 0.5, 0.42, a.y + 0.5),
          new THREE.Vector3(b.x + 0.5, 0.42, b.y + 0.5)]);
        lineGroup.add(new THREE.Line(g, new THREE.LineBasicMaterial({
          color: fl ? 0x38bdf8 : 0x94a3b8,
          transparent: true, opacity: fl ? 0.9 : 0.09,
        })));
      }
  }

  function addSpark(x, y) {
    // Luật kích hoạt = một tia sáng, KHÔNG kèm chữ. Trước REVEAL thì người xem
    // cũng đang đoán như chính lũ sinh vật — đó là chủ ý, không phải hạn chế.
    const m = new THREE.Mesh(
      new THREE.RingGeometry(0.2, 0.28, 20),
      new THREE.MeshBasicMaterial({ color: 0xfde047, transparent: true, side: THREE.DoubleSide }));
    m.rotation.x = -Math.PI / 2;
    m.position.set(x + 0.5, 0.5, y + 0.5);
    sparkGroup.add(m);
    sparks.push({ mesh: m, t0: performance.now() });
  }

  function logEvent(ev) {
    const d = document.createElement("div");
    d.className = "ev " + (ev.k || "");
    d.textContent =
      ev.k === "SPEAK" ? `[NÓI] ${ev.who} (${ev.sig}) → ${(ev.hear || []).length} kẻ nghe`
      : ev.k === "LAW_FIRED" ? `[LUẬT] ${ev.who}: ${ev.law}`
      : ev.k === "DEATH" ? `[CHẾT] ${ev.who} (${ev.cause})`
      : ev.k === "ATTACK" ? `[ĐÁNH] ${ev.who} → ${ev.target}`
      : `[${ev.k}] ${ev.who || ""}`;
    const log = el("log");
    log.insertBefore(d, log.firstChild);
    while (log.childNodes.length > 60) log.removeChild(log.lastChild);
  }

  function onFrame(frame) {
    latest = frame;
    buildTerrain(frame.terrain);
    el("phase").textContent = frame.phase;
    el("phase").className = "badge " + frame.phase;
    el("tick").textContent = frame.t;
    el("map").textContent = frame.map || "—";
    const cs = frame.creatures || [];
    el("alive").textContent = `${cs.filter((c) => c.alive).length}/${cs.length}`;

    syncBodies(frame);
    const now = performance.now();
    for (const ev of frame.events || []) {
      logEvent(ev);
      if (ev.k === "SPEAK") flashes.push({ a: ev.who, b: ev.hear || [], t0: now });
      if (ev.k === "LAW_FIRED" && ev.pos) addSpark(ev.pos[0], ev.pos[1]);
    }
    while (flashes.length && now - flashes[0].t0 > 300) flashes.shift();
  }

  function connect() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${location.host || "localhost:8000"}/v1/spectate`);
    ws.onmessage = (e) => { try { onFrame(JSON.parse(e.data)); } catch (_) {} };
    ws.onclose = () => setTimeout(connect, 1000);
  }

  function loop() {
    const now = performance.now();
    for (let i = sparks.length - 1; i >= 0; i--) {
      const p = (now - sparks[i].t0) / 500;
      if (p >= 1) { sparkGroup.remove(sparks[i].mesh); sparks.splice(i, 1); continue; }
      sparks[i].mesh.scale.setScalar(1 + p * 2.2);
      sparks[i].mesh.material.opacity = 1 - p;
    }
    if (latest) drawHearing(latest);

    camera.position.set(
      cx + dist * Math.cos(pitch) * Math.sin(yaw),
      dist * Math.sin(pitch),
      cz + dist * Math.cos(pitch) * Math.cos(yaw));
    camera.lookAt(cx, 0, cz);
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  }

  connect();
  loop();
})();
