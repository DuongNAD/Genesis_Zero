// Genesis Zero — watch.js: Canvas 2D render va giao tiep truc tiep qua WebSocket
(function() {
  const canvas = document.getElementById('sim-canvas');
  const ctx = canvas.getContext('2d');

  const phaseBadge = document.getElementById('phase-badge');
  const tickVal = document.getElementById('tick-val');
  const aliveVal = document.getElementById('alive-val');
  const plantsVal = document.getElementById('plants-val');
  const corpsesVal = document.getElementById('corpses-val');
  const eventLog = document.getElementById('event-log');

  // Kích thước lưới đến từ khung, không chép cứng: thế giới đổi cỡ thì trang
  // này đổi theo, không phải sửa hai chỗ.
  let GRID_W = 24, GRID_H = 24;
  let CELL_PX = canvas.width / GRID_W;

  // KHÔNG có bảng trait ở đây. Khung mang theo `tr` — trait HIỆN TẠI của từng
  // con — vì trait dịch giữa ván và vì loài do người lạ tạo ra lúc chạy thì
  // trang này không thể biết trước. Bản đầu chép cứng bảng founder vào JS và
  // vẽ sai ngay lần dịch trait đầu tiên.
  const TR = { brain: 0, attack: 1, armor: 2, speed: 3, sense: 4, stomach: 5 };

  function hashStr(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }

  let latestFrame = null;
  let latestTerrain = null;   // khung tick 0 mang dia hinh; giu lai cho ca van
  const speakFlashes = []; // { speakerId, hearerIds, startTime }

  function addEventLog(ev) {
    const entry = document.createElement('div');
    entry.className = `event-entry ${ev.k || ''}`;
    if (ev.k === 'SPEAK') {
      entry.textContent = `[SPEAK] ${ev.who} (${ev.sig}) -> [${(ev.hear || []).join(', ')}]`;
    } else if (ev.k === 'LAW_FIRED') {
      entry.textContent = `[LUẬT] ${ev.who}: ${ev.law}`;
    } else if (ev.k === 'EAT') {
      entry.textContent = `[ĂN] ${ev.who} tại (${ev.pos ? ev.pos.join(',') : ''})`;
    } else if (ev.k === 'ATTACK') {
      entry.textContent = `[ĐÁNH] ${ev.who} -> ${ev.target}`;
    } else if (ev.k === 'DEATH') {
      entry.textContent = `[CHẾT] ${ev.who} (${ev.cause})`;
    } else {
      entry.textContent = `[${ev.k}] ${ev.who || ''}`;
    }
    eventLog.insertBefore(entry, eventLog.firstChild);
    while (eventLog.childNodes.length > 50) {
      eventLog.removeChild(eventLog.lastChild);
    }
  }

  function connectWs() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || 'localhost:8000';
    const ws = new WebSocket(`${proto}//${host}/v1/spectate`);

    ws.onmessage = function(event) {
      try {
        const frame = JSON.parse(event.data);
        if (frame.terrain) latestTerrain = frame.terrain;
        latestFrame = frame;
        updateUI(frame);

        if (frame.events && Array.isArray(frame.events)) {
          const now = performance.now();
          frame.events.forEach(ev => {
            addEventLog(ev);
            if (ev.k === 'SPEAK') {
              speakFlashes.push({
                speakerId: ev.who,
                hearerIds: ev.hear || [],
                startTime: now,
              });
            }
          });
        }
      } catch (err) {
        // parsing error
      }
    };

    ws.onclose = function() {
      setTimeout(connectWs, 1000);
    };
  }

  function updateUI(frame) {
    if (!frame) return;
    if (frame.w) { GRID_W = frame.w; GRID_H = frame.h; CELL_PX = canvas.width / GRID_W; }
    phaseBadge.textContent = frame.phase;
    phaseBadge.className = `badge-phase ${frame.phase}`;
    tickVal.textContent = frame.t;

    const aliveCount = (frame.creatures || []).filter(c => c.alive).length;
    const totalCount = (frame.creatures || []).length;
    aliveVal.textContent = `${aliveCount}/${totalCount}`;
    plantsVal.textContent = (frame.plants || []).length;
    corpsesVal.textContent = (frame.corpses || []).length;
  }

  function toroidalDist(x1, y1, x2, y2) {
    let dx = Math.abs(x1 - x2);
    let dy = Math.abs(y1 - y2);
    dx = Math.min(dx, GRID_W - dx);
    dy = Math.min(dy, GRID_H - dy);
    return Math.max(dx, dy);
  }

  function drawWorld() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Ve nen luoi dia hinh — tu KHUNG, khong phai o caro gia.
    // Ban dau ve mot ban co xanh cho MOI ban do, nen nam ban do cua W-15 trong
    // giong het nhau tren trang xem.
    const TER = { P: '#3f6212', W: '#1d4ed8', B: '#14532d', R: '#57534e', F: '#ea580c' };
    const rows = latestTerrain;
    for (let y = 0; y < GRID_H; y++) {
      for (let x = 0; x < GRID_W; x++) {
        const ch = rows && rows[y] ? rows[y][x] : null;
        ctx.fillStyle = ch ? TER[ch] || TER.P
                           : ((x + y) % 2 === 0 ? '#263d1e' : '#22381b');
        ctx.fillRect(x * CELL_PX, y * CELL_PX, CELL_PX, CELL_PX);
        ctx.strokeStyle = '#1b2c15';
        ctx.lineWidth = 0.5;
        ctx.strokeRect(x * CELL_PX, y * CELL_PX, CELL_PX, CELL_PX);
      }
    }

    if (!latestFrame) {
      requestAnimationFrame(drawWorld);
      return;
    }

    // 2. Ve qua (plants)
    if (latestFrame.plants) {
      for (let i = 0; i < latestFrame.plants.length; i++) {
        const p = latestFrame.plants[i];
        const cx = p[0] * CELL_PX + CELL_PX / 2;
        const cy = p[1] * CELL_PX + CELL_PX / 2;
        ctx.fillStyle = '#22c55e';
        ctx.beginPath();
        ctx.arc(cx, cy, CELL_PX * 0.22, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#15803d';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }

    // 3. Ve xac (corpses)
    if (latestFrame.corpses) {
      for (let i = 0; i < latestFrame.corpses.length; i++) {
        const c = latestFrame.corpses[i];
        const cx = c[0] * CELL_PX + CELL_PX / 2;
        const cy = c[1] * CELL_PX + CELL_PX / 2;
        const arm = CELL_PX * 0.25;
        ctx.strokeStyle = '#991b1b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx - arm, cy - arm);
        ctx.lineTo(cx + arm, cy + arm);
        ctx.moveTo(cx + arm, cy - arm);
        ctx.lineTo(cx - arm, cy + arm);
        ctx.stroke();
      }
    }

    const creatures = latestFrame.creatures || [];
    const creatureMap = new Map();
    creatures.forEach(c => creatureMap.set(c.id, c));

    // 4. Ve do thi ai nghe duoc ai (Bat bien 3)
    const now = performance.now();
    for (let i = speakFlashes.length - 1; i >= 0; i--) {
      if (now - speakFlashes[i].startTime > 300) {
        speakFlashes.splice(i, 1);
      }
    }

    // Đồ thị "ai nghe được ai" vẽ từ tầm nghe của NGƯỜI NGHE (`sense` của nó),
    // đúng như `genesis/speech.hearers`. Còn lúc nhấp nháy thì dùng danh sách
    // người nghe DO SERVER GỬI: chỉ server mới biết ai thật sự nghe được.
    const aliveCreatures = creatures.filter(c => c.alive);
    for (let i = 0; i < aliveCreatures.length; i++) {
      for (let j = i + 1; j < aliveCreatures.length; j++) {
        const cA = aliveCreatures[i];
        const cB = aliveCreatures[j];
        const dist = toroidalDist(cA.x, cA.y, cB.x, cB.y);
        const sightA = 2 + (cA.tr ? cA.tr[TR.sense] : 2);
        const sightB = 2 + (cB.tr ? cB.tr[TR.sense] : 2);
        if (dist > sightA && dist > sightB) continue;

        const x1 = cA.x * CELL_PX + CELL_PX / 2;
        const y1 = cA.y * CELL_PX + CELL_PX / 2;
        const x2 = cB.x * CELL_PX + CELL_PX / 2;
        const y2 = cB.y * CELL_PX + CELL_PX / 2;

        let flashProgress = -1;
        for (let f = 0; f < speakFlashes.length; f++) {
          const flash = speakFlashes[f];
          if ((flash.speakerId === cA.id && flash.hearerIds.indexOf(cB.id) >= 0) ||
              (flash.speakerId === cB.id && flash.hearerIds.indexOf(cA.id) >= 0)) {
            flashProgress = (now - flash.startTime) / 300;
            break;
          }
        }

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        if (flashProgress >= 0) {
          ctx.strokeStyle = `rgba(56, 189, 248, ${Math.max(0, 1 - flashProgress)})`;
          ctx.lineWidth = 2.5;
        } else {
          ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)';
          ctx.lineWidth = 0.75;
        }
        ctx.stroke();
      }
    }

    // 5. Ve sinh vat bang primitive suy tu vector trait (02 §5)
    for (let i = 0; i < creatures.length; i++) {
      const c = creatures[i];
      drawCreature(c);
    }

    requestAnimationFrame(drawWorld);
  }

  function drawCreature(c) {
    const sp = c.id.split(':')[0];
    const t = c.tr || [2, 2, 2, 2, 2, 2];
    const traits = {
      brain: t[TR.brain], attack: t[TR.attack], armor: t[TR.armor],
      speed: t[TR.speed], sense: t[TR.sense], stomach: t[TR.stomach],
    };
    const cx = c.x * CELL_PX + CELL_PX / 2;
    const cy = c.y * CELL_PX + CELL_PX / 2;

    ctx.save();
    if (!c.alive) {
      ctx.globalAlpha = 0.25;
    }

    // Mau sac: hue = hash(species_id) % 360, lech ±10 theo id ca the
    const baseHue = hashStr(sp) % 360;
    const shiftHue = ((hashStr(c.id) % 21) - 10);
    const hue = (baseHue + shiftHue + 360) % 360;

    // Độ sáng theo energy / energy_max. `e_max` đến từ khung: công thức của nó
    // là chuyện của sim, và chép nó sang JS là hẹn ngày hai bên lệch nhau.
    const eMax = c.e_max || 1;
    const eRatio = Math.max(0.1, Math.min(1.0, (c.e || 0) / eMax));
    const lightness = 25 + Math.round(50 * eRatio);

    const fillColor = `hsl(${hue}, 70%, ${lightness}%)`;
    const strokeColor = `hsl(${hue}, 90%, 20%)`;

    // Anh xa cac trait vao hinh hoc:
    // stomach -> be ngang than
    const bodyW = 8 + traits.stomach * 2;
    // speed -> do dai than va so chan
    const bodyH = 10 + traits.speed * 2;
    // brain -> kich thuoc dau
    const headR = 3 + traits.brain * 1.2;
    // sense -> kich thuoc va do tach mat
    const eyeR = 1 + traits.sense * 0.6;
    const eyeSpread = 2 + traits.sense * 1.0;
    // armor -> do day vien va gai lung
    const armorLineWidth = 1 + traits.armor * 0.7;
    // attack -> nanh / vuot
    const fangLen = 2 + traits.attack * 1.5;

    // Ve chan (speed)
    const legCount = 2 + Math.min(4, traits.speed);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([]);
    for (let k = 0; k < legCount; k++) {
      const legY = cy - bodyH / 2 + (k + 0.5) * (bodyH / legCount);
      ctx.beginPath();
      ctx.moveTo(cx - bodyW / 2 - 3, legY);
      ctx.lineTo(cx + bodyW / 2 + 3, legY);
      ctx.stroke();
    }

    // Ve than
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = armorLineWidth;
    if (c.feral) {
      ctx.setLineDash([3, 3]);
    } else {
      ctx.setLineDash([]);
    }

    ctx.beginPath();
    ctx.ellipse(cx, cy, bodyW / 2, bodyH / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Ve giap doc song lung (armor)
    if (traits.armor > 0) {
      ctx.fillStyle = strokeColor;
      ctx.setLineDash([]);
      for (let a = 0; a < traits.armor; a++) {
        const plateY = cy - bodyH / 3 + a * (bodyH / (traits.armor + 1));
        ctx.beginPath();
        ctx.arc(cx, plateY, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Ve dau (brain)
    const headY = cy - bodyH / 2 - headR / 2;
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, headY, headR, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Ve mat (sense)
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(cx - eyeSpread, headY - 1, eyeR, 0, Math.PI * 2);
    ctx.arc(cx + eyeSpread, headY - 1, eyeR, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(cx - eyeSpread, headY - 1, eyeR * 0.5, 0, Math.PI * 2);
    ctx.arc(cx + eyeSpread, headY - 1, eyeR * 0.5, 0, Math.PI * 2);
    ctx.fill();

    // Ve nanh/vuot (attack)
    if (traits.attack > 0) {
      ctx.strokeStyle = '#f8fafc';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(cx - 2, headY - headR);
      ctx.lineTo(cx - 3, headY - headR - fangLen);
      ctx.moveTo(cx + 2, headY - headR);
      ctx.lineTo(cx + 3, headY - headR - fangLen);
      ctx.stroke();
    }

    ctx.restore();
  }

  connectWs();
  requestAnimationFrame(drawWorld);
})();
