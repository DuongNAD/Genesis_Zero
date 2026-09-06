// Genesis Zero — watch3d: Trình hiển thị 3D & Bản đồ thu nhỏ sinh động (Milestone 3 / R3).
//
// Bản đồ thu nhỏ dạng diorama 3D, hệ sinh thái 3 tầng (Nước, Cạn, Trời),
// hình thái sinh học thủ tục phản ánh 6 trait và 12 đặc điểm sinh học,
// bảng Sổ Luật (Law Journal) thời gian thực, hiệu ứng sóng xung kích bí ẩn,
// và lễ vinh danh 3 danh hiệu vô địch ở pha REVEAL.
//
// Bất biến bắt buộc:
//   1. 100% Không CDN, không http/https bên ngoài (Offline-first).
//   2. Kích thước sinh vật chỉ phụ thuộc vector trait (tr), tuyệt đối không phụ thuộc model parameter.
//   3. Không rò rỉ nội dung luật ẩn trước pha REVEAL (quan sát gián tiếp).
//   4. Dữ liệu thuần tuý đến từ khung telemetry qua WebSocket /v1/spectate.
(function () {
  "use strict";

  const TR = { brain: 0, attack: 1, armor: 2, speed: 3, sense: 4, stomach: 5 };
  const CELL = 1.0;

  // 8 loại ô địa hình chuẩn hoá mang vẻ đẹp tự nhiên lấy cảm hứng từ Anima-Engine
  const TERRAIN = {
    P: { h: 0.16, c: 0x4fa83b, name: "Đồng cỏ" },     // Rich vibrant meadow green
    W: { h: -0.08, c: 0x2294a8, name: "Nước nông" },   // Crystal turquoise shallow water
    B: { h: 0.32, c: 0x2d7a36, name: "Bụi rậm" },     // Shrubland foliage
    R: { h: 0.95, c: 0x64748b, name: "Vách đá" },     // Mountain rock slate
    F: { h: 0.22, c: 0xea580c, name: "Lửa cháy" },     // Volcanic molten ember
    D: { h: -0.32, c: 0x125875, name: "Nước sâu" },   // Deep ocean abyss
    T: { h: 0.28, c: 0x1e6b2c, name: "Cây cao" },     // Ancient forest floor
    C: { h: 0.42, c: 0x334155, name: "Hang đá" },     // Cavern bedrock
  };

  // 12 đặc điểm sinh học từ genesis/features.py và chú giải tiếng Việt
  const FEATURE_NAMES_VN = {
    LUONG_CU: "Lưỡng cư (Chân màng bơi)",
    DAO_HANG: "Biết đào hang (Móng vuốt bới)",
    TREO_GIOI: "Trèo giỏi (Đuôi cuốn cành)",
    CANH_LUOT: "Màng lượn (Da căng lượn đá)",
    LONG_DAI: "Lông dài (Bờm dày giữ nhiệt)",
    VAY_CUNG: "Vảy cứng (Giáp vảy ngói)",
    GAI_DOC: "Gai độc (Gai phát quang sườn)",
    VO_SO: "Vỏ sò (Mai cứng khum lưng)",
    MAT_DEM: "Mắt đêm (Đồng tử lớn phát sáng)",
    RAU_CAM_UNG: "Râu cảm ứng (Cặp râu dài)",
    RANG_NANH: "Răng nanh (Nanh kiếm bạnh hàm)",
    TUI_MA: "Túi má (Túi dự trữ phồng)",
    // Các bí danh tương đương
    CANH_BAY: "Cánh bay rộng",
    VAY_BOI: "Vây bơi ngực & đuôi",
    NOC_DOC: "Gai nọc độc",
    GIAP_CUNG: "Giáp cứng liền khối",
    DA_DOI_MAU: "Da đổi màu nguỵ trang",
    MAT_KHAM: "Mắt khảm đa hướng",
    VAP_HAM: "Vạp hàm săn mồi",
    VOI_HUT: "Vòi hút mật",
    CO_QUAN_PHAT_SANG: "Cơ quan phát quang",
    TU_BAO: "Túi bào tử",
    MANG_THO: "Mang thở nước",
  };

  const el = (id) => document.getElementById(id);

  // ── Khởi tạo Three.js Scene ──
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x06080f);
  scene.fog = new THREE.Fog(0x06080f, 32, 75);

  const camera = new THREE.PerspectiveCamera(46, innerWidth / innerHeight, 0.1, 500);
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  el("scene").appendChild(renderer.domElement);

  addEventListener("resize", () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  // ── Ánh sáng & Môi trường ──
  const hemiLight = new THREE.HemisphereLight(0xbfdbfe, 0x1e293b, 0.85);
  scene.add(hemiLight);

  const sunLight = new THREE.DirectionalLight(0xfff7ed, 1.1);
  sunLight.position.set(18, 32, 14);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.width = 1024;
  sunLight.shadow.mapSize.height = 1024;
  sunLight.shadow.camera.near = 0.5;
  sunLight.shadow.camera.far = 120;
  sunLight.shadow.camera.left = -20;
  sunLight.shadow.camera.right = 20;
  sunLight.shadow.camera.top = 20;
  sunLight.shadow.camera.bottom = -20;
  scene.add(sunLight);

  const ambientFill = new THREE.AmbientLight(0x0f172a, 0.6);
  scene.add(ambientFill);

  const dioramaGroup = new THREE.Group();
  const terrainGroup = new THREE.Group();
  const plantsGroup = new THREE.Group();
  const corpsesGroup = new THREE.Group();
  const bodyGroup = new THREE.Group();
  const lineGroup = new THREE.Group();
  const shockwaveGroup = new THREE.Group();
  const podiumGroup = new THREE.Group();
  const weatherGroup = new THREE.Group();
  scene.add(dioramaGroup, terrainGroup, plantsGroup, corpsesGroup, bodyGroup, lineGroup, shockwaveGroup, podiumGroup, weatherGroup);

  // ── Hệ Thống Hạt Thời Tiết Thủ Tục (Three.js Points) ──
  // 1. Mưa giông (Rain streaks - 800 hạt)
  const rainGeo = new THREE.BufferGeometry();
  const rainPositions = new Float32Array(800 * 3);
  for (let i = 0; i < 800; i++) {
    rainPositions[i * 3] = Math.random() * 26 - 1;
    rainPositions[i * 3 + 1] = Math.random() * 18;
    rainPositions[i * 3 + 2] = Math.random() * 26 - 1;
  }
  rainGeo.setAttribute("position", new THREE.BufferAttribute(rainPositions, 3));
  const rainMat = new THREE.PointsMaterial({
    color: 0x7dd3fc,
    size: 0.12,
    transparent: true,
    opacity: 0.75,
    depthWrite: false,
  });
  const rainParticles = new THREE.Points(rainGeo, rainMat);
  rainParticles.visible = false;
  weatherGroup.add(rainParticles);

  // 2. Bão Mặt Trời (Solar Flare Embers - 400 hạt)
  const solarGeo = new THREE.BufferGeometry();
  const solarPositions = new Float32Array(400 * 3);
  for (let i = 0; i < 400; i++) {
    solarPositions[i * 3] = Math.random() * 26 - 1;
    solarPositions[i * 3 + 1] = Math.random() * 16;
    solarPositions[i * 3 + 2] = Math.random() * 26 - 1;
  }
  solarGeo.setAttribute("position", new THREE.BufferAttribute(solarPositions, 3));
  const solarMat = new THREE.PointsMaterial({
    color: 0xf97316,
    size: 0.18,
    transparent: true,
    opacity: 0.85,
    depthWrite: false,
  });
  const solarParticles = new THREE.Points(solarGeo, solarMat);
  solarParticles.visible = false;
  weatherGroup.add(solarParticles);

  // 3. Bão Bào Tử Độc (Toxic Spores - 500 hạt)
  const sporeGeo = new THREE.BufferGeometry();
  const sporePositions = new Float32Array(500 * 3);
  for (let i = 0; i < 500; i++) {
    sporePositions[i * 3] = Math.random() * 26 - 1;
    sporePositions[i * 3 + 1] = 0.5 + Math.random() * 9;
    sporePositions[i * 3 + 2] = Math.random() * 26 - 1;
  }
  sporeGeo.setAttribute("position", new THREE.BufferAttribute(sporePositions, 3));
  const sporeMat = new THREE.PointsMaterial({
    color: 0x84cc16,
    size: 0.16,
    transparent: true,
    opacity: 0.75,
    depthWrite: false,
  });
  const sporeParticles = new THREE.Points(sporeGeo, sporeMat);
  sporeParticles.visible = false;
  weatherGroup.add(sporeParticles);

  // 4. Nghịch Từ Trường (Magnetic Shift Pulses - 300 hạt)
  const magneticGeo = new THREE.BufferGeometry();
  const magneticPositions = new Float32Array(300 * 3);
  for (let i = 0; i < 300; i++) {
    magneticPositions[i * 3] = 12 + (Math.random() - 0.5) * 16;
    magneticPositions[i * 3 + 1] = 2 + Math.random() * 8;
    magneticPositions[i * 3 + 2] = 12 + (Math.random() - 0.5) * 16;
  }
  magneticGeo.setAttribute("position", new THREE.BufferAttribute(magneticPositions, 3));
  const magneticMat = new THREE.PointsMaterial({
    color: 0x06b6d4,
    size: 0.2,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
  });
  const magneticParticles = new THREE.Points(magneticGeo, magneticMat);
  magneticParticles.visible = false;
  weatherGroup.add(magneticParticles);

  // ── Trạng thái Khí hậu & Lerp Ánh sáng / Sương mù ──
  let currentWeather = "CLEAR";
  let currentDiurnal = "DAY";
  let lastWeatherState = null;

  const targetBgColor = new THREE.Color(0x06080f);
  const targetFogColor = new THREE.Color(0x06080f);
  let targetFogNear = 32;
  let targetFogFar = 75;

  const targetSunColor = new THREE.Color(0xfff7ed);
  let targetSunIntensity = 1.1;

  const targetAmbientColor = new THREE.Color(0x0f172a);
  let targetHemiSky = new THREE.Color(0xbfdbfe);
  let targetHemiGround = new THREE.Color(0x1e293b);

  function updateWeatherAtmosphere(weather) {
    if (!weather) return;
    currentWeather = weather.state || "CLEAR";
    currentDiurnal = weather.diurnal || "DAY";

    if (lastWeatherState && lastWeatherState !== currentWeather) {
      playWeatherShift(currentWeather);
    }
    lastWeatherState = currentWeather;

    if (currentWeather === "SPORE_STORM") {
      targetBgColor.setHex(0x06190f);
      targetFogColor.setHex(0x06190f);
      targetFogNear = 18; targetFogFar = 50;
      targetSunColor.setHex(0xa3e635);
      targetSunIntensity = 0.65;
      targetAmbientColor.setHex(0x052e16);
      targetHemiSky.setHex(0x86efac);
      targetHemiGround.setHex(0x3b0764);
    } else if (currentWeather === "SOLAR_FLARE") {
      targetBgColor.setHex(0x1c0a04);
      targetFogColor.setHex(0x1c0a04);
      targetFogNear = 24; targetFogFar = 60;
      targetSunColor.setHex(0xf97316);
      targetSunIntensity = 1.6;
      targetAmbientColor.setHex(0x451a03);
      targetHemiSky.setHex(0xfdba74);
      targetHemiGround.setHex(0x292524);
    } else if (currentWeather === "MAGNETIC_SHIFT") {
      targetBgColor.setHex(0x0e061a);
      targetFogColor.setHex(0x0e061a);
      targetFogNear = 22; targetFogFar = 62;
      targetSunColor.setHex(0x06b6d4);
      targetSunIntensity = 1.1;
      targetAmbientColor.setHex(0x2e1065);
      targetHemiSky.setHex(0x67e8f9);
      targetHemiGround.setHex(0x701a75);
    } else if (currentWeather === "STORM" || currentWeather === "RAIN") {
      targetBgColor.setHex(0x0c121e);
      targetFogColor.setHex(0x0c121e);
      targetFogNear = 16; targetFogFar = 46;
      targetSunColor.setHex(0x64748b);
      targetSunIntensity = 0.35;
      targetAmbientColor.setHex(0x1e293b);
      targetHemiSky.setHex(0x475569);
      targetHemiGround.setHex(0x0f172a);
    } else {
      // CLEAR
      if (currentDiurnal === "NIGHT") {
        targetBgColor.setHex(0x030408);
        targetFogColor.setHex(0x030408);
        targetFogNear = 22; targetFogFar = 55;
        targetSunColor.setHex(0x38bdf8);
        targetSunIntensity = 0.3;
        targetAmbientColor.setHex(0x050814);
        targetHemiSky.setHex(0x1e1b4b);
        targetHemiGround.setHex(0x020617);
      } else {
        targetBgColor.setHex(0x06080f);
        targetFogColor.setHex(0x06080f);
        targetFogNear = 32; targetFogFar = 75;
        targetSunColor.setHex(0xfff7ed);
        targetSunIntensity = 1.15;
        targetAmbientColor.setHex(0x0f172a);
        targetHemiSky.setHex(0xbfdbfe);
        targetHemiGround.setHex(0x1e293b);
      }
    }
  }

  function animateWeatherParticles(now) {
    const isRain = (currentWeather === "STORM" || currentWeather === "RAIN");
    const isSolar = (currentWeather === "SOLAR_FLARE");
    const isSpore = (currentWeather === "SPORE_STORM");
    const isMag = (currentWeather === "MAGNETIC_SHIFT");

    rainParticles.visible = isRain;
    solarParticles.visible = isSolar;
    sporeParticles.visible = isSpore;
    magneticParticles.visible = isMag;

    if (isRain) {
      const pos = rainGeo.attributes.position.array;
      for (let i = 0; i < 800; i++) {
        pos[i * 3 + 1] -= 0.45;
        if (pos[i * 3 + 1] < 0) {
          pos[i * 3 + 1] = 16.0;
        }
      }
      rainGeo.attributes.position.needsUpdate = true;
    }

    if (isSolar) {
      const pos = solarGeo.attributes.position.array;
      for (let i = 0; i < 400; i++) {
        pos[i * 3 + 1] += 0.12;
        pos[i * 3] += Math.sin(now * 0.002 + i) * 0.02;
        if (pos[i * 3 + 1] > 16.0) {
          pos[i * 3 + 1] = 0.1;
        }
      }
      solarGeo.attributes.position.needsUpdate = true;
    }

    if (isSpore) {
      const pos = sporeGeo.attributes.position.array;
      for (let i = 0; i < 500; i++) {
        pos[i * 3] += Math.sin(now * 0.001 + i) * 0.03;
        pos[i * 3 + 2] += Math.cos(now * 0.001 + i) * 0.03;
        pos[i * 3 + 1] += Math.sin(now * 0.002 + i * 2) * 0.015;
        if (pos[i * 3] < 0) pos[i * 3] = W;
        if (pos[i * 3] > W) pos[i * 3] = 0;
        if (pos[i * 3 + 2] < 0) pos[i * 3 + 2] = H;
        if (pos[i * 3 + 2] > H) pos[i * 3 + 2] = 0;
      }
      sporeGeo.attributes.position.needsUpdate = true;
    }

    if (isMag) {
      const pos = magneticGeo.attributes.position.array;
      const t = now * 0.0015;
      for (let i = 0; i < 300; i++) {
        const angle = i * 0.08 + t;
        const radius = 6 + Math.sin(t * 2 + i) * 4;
        pos[i * 3] = (W / 2) + Math.cos(angle) * radius;
        pos[i * 3 + 1] = 3.0 + Math.sin(t * 3 + i * 0.5) * 2.5;
        pos[i * 3 + 2] = (H / 2) + Math.sin(angle) * radius;
      }
      magneticGeo.attributes.position.needsUpdate = true;
    }
  }

  // ── Động cơ Âm thanh Thủ tục (Web Audio API - Zero Asset) ──
  let audioCtx = null;
  let masterGain = null;
  let compressor = null;
  let isAudioMuted = false;
  let masterVolume = 0.7;
  let lastMoveSoundTime = 0;

  function initAudio() {
    if (audioCtx) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      audioCtx = new AudioContextClass();

      // Bộ nén dải động bảo vệ thính giác (-6dB threshold)
      compressor = audioCtx.createDynamicsCompressor();
      compressor.threshold.setValueAtTime(-6, audioCtx.currentTime);
      compressor.knee.setValueAtTime(12, audioCtx.currentTime);
      compressor.ratio.setValueAtTime(8, audioCtx.currentTime);
      compressor.attack.setValueAtTime(0.003, audioCtx.currentTime);
      compressor.release.setValueAtTime(0.15, audioCtx.currentTime);

      // Âm lượng tổng
      masterGain = audioCtx.createGain();
      masterGain.gain.setValueAtTime(isAudioMuted ? 0 : masterVolume, audioCtx.currentTime);

      compressor.connect(masterGain);
      masterGain.connect(audioCtx.destination);
    } catch (_) {}
  }

  function unlockAudio() {
    if (!audioCtx) initAudio();
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume().catch(() => {});
    }
  }

  ["click", "keydown", "touchstart"].forEach((evt) => {
    addEventListener(evt, unlockAudio, { once: false, passive: true });
  });

  function playMoveSound(domain) {
    if (!audioCtx || isAudioMuted) return;
    const nowMs = performance.now();
    if (nowMs - lastMoveSoundTime < 70) return;
    lastMoveSoundTime = nowMs;
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      if (domain === "NUOC") {
        osc.type = "sine";
        osc.frequency.setValueAtTime(560, now);
        osc.frequency.exponentialRampToValueAtTime(200, now + 0.045);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.045);
      } else if (domain === "TROI") {
        osc.type = "triangle";
        osc.frequency.setValueAtTime(360, now);
        osc.frequency.exponentialRampToValueAtTime(520, now + 0.05);
        gain.gain.setValueAtTime(0.09, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);
      } else {
        osc.type = "triangle";
        osc.frequency.setValueAtTime(120, now);
        osc.frequency.exponentialRampToValueAtTime(60, now + 0.04);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.04);
      }

      osc.connect(gain);
      gain.connect(compressor);
      osc.start(now);
      osc.stop(now + 0.05);
    } catch (_) {}
  }

  function playLawFired() {
    if (!audioCtx || isAudioMuted) return;
    try {
      const now = audioCtx.currentTime;
      const freqs = [220, 277.18, 329.63, 440];
      const chordGain = audioCtx.createGain();
      chordGain.gain.setValueAtTime(0.2, now);
      chordGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.2);

      const filter = audioCtx.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(400, now);
      filter.frequency.exponentialRampToValueAtTime(2400, now + 0.3);
      filter.frequency.exponentialRampToValueAtTime(300, now + 1.2);
      filter.Q.setValueAtTime(4, now);

      freqs.forEach((f) => {
        const osc = audioCtx.createOscillator();
        osc.type = "sine";
        osc.frequency.setValueAtTime(f, now);
        osc.connect(chordGain);
        osc.start(now);
        osc.stop(now + 1.2);
      });

      chordGain.connect(filter);
      filter.connect(compressor);

      const subOsc = audioCtx.createOscillator();
      const subGain = audioCtx.createGain();
      subOsc.type = "sine";
      subOsc.frequency.setValueAtTime(55, now);
      subOsc.frequency.exponentialRampToValueAtTime(28, now + 0.45);
      subGain.gain.setValueAtTime(0.35, now);
      subGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);
      subOsc.connect(subGain);
      subGain.connect(compressor);
      subOsc.start(now);
      subOsc.stop(now + 0.45);
    } catch (_) {}
  }

  function playDeath() {
    if (!audioCtx || isAudioMuted) return;
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      const filter = audioCtx.createBiquadFilter();

      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(240, now);
      osc.frequency.exponentialRampToValueAtTime(40, now + 0.65);

      filter.type = "lowpass";
      filter.frequency.setValueAtTime(900, now);
      filter.frequency.exponentialRampToValueAtTime(60, now + 0.65);

      gain.gain.setValueAtTime(0.24, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.65);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(compressor);

      osc.start(now);
      osc.stop(now + 0.65);
    } catch (_) {}
  }

  function playReproduce() {
    if (!audioCtx || isAudioMuted) return;
    try {
      const now = audioCtx.currentTime;
      const notes = [523.25, 659.25, 783.99, 1046.50];
      notes.forEach((freq, idx) => {
        const t = now + idx * 0.055;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.18, t);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);
        osc.connect(gain);
        gain.connect(compressor);
        osc.start(t);
        osc.stop(t + 0.22);
      });
    } catch (_) {}
  }

  function playCombatHit() {
    if (!audioCtx || isAudioMuted) return;
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.exponentialRampToValueAtTime(45, now + 0.08);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.08);
      osc.connect(gain);
      gain.connect(compressor);
      osc.start(now);
      osc.stop(now + 0.08);
    } catch (_) {}
  }

  function playWeatherShift(state) {
    if (!audioCtx || isAudioMuted) return;
    try {
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      const filter = audioCtx.createBiquadFilter();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(82.4, now);
      osc2.type = "sine";
      osc2.frequency.setValueAtTime(123.47, now);

      filter.type = "lowpass";
      filter.frequency.setValueAtTime(250, now);
      filter.frequency.exponentialRampToValueAtTime(1200, now + 1.0);
      filter.frequency.exponentialRampToValueAtTime(180, now + 2.4);
      filter.Q.setValueAtTime(3, now);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.2, now + 0.6);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 2.4);

      osc.connect(filter);
      osc2.connect(filter);
      filter.connect(gain);
      gain.connect(compressor);

      osc.start(now);
      osc2.start(now);
      osc.stop(now + 2.4);
      osc2.stop(now + 2.4);
    } catch (_) {}
  }

  el("btn-audio-toggle")?.addEventListener("click", () => {
    unlockAudio();
    isAudioMuted = !isAudioMuted;
    if (masterGain && audioCtx) {
      masterGain.gain.setValueAtTime(isAudioMuted ? 0 : masterVolume, audioCtx.currentTime);
    }
    const btn = el("btn-audio-toggle");
    if (btn) {
      btn.textContent = isAudioMuted ? "🔇" : "🔊";
      btn.title = isAudioMuted ? "Bật âm thanh" : "Tắt âm thanh";
    }
  });

  el("audio-volume-slider")?.addEventListener("input", (e) => {
    unlockAudio();
    masterVolume = parseFloat(e.target.value);
    if (!isAudioMuted && masterGain && audioCtx) {
      masterGain.gain.setValueAtTime(masterVolume, audioCtx.currentTime);
    }
  });

  // ── Client Frame History Ring Buffer & Timeline Replay Engine ──
  const MAX_HISTORY = 1200;
  const historyBuffer = [];
  let isPaused = false;
  let playbackSpeed = 1;
  let scrubTick = 0;
  let isLive = true;
  let lastPlaybackStepTime = 0;

  function updateTimelineUI(currentTick, maxTick) {
    const disp = el("timeline-tick-display");
    if (disp) {
      disp.textContent = `Lượt ${currentTick} / ${maxTick}`;
    }
    const slider = el("timeline-slider");
    if (slider && isLive) {
      slider.value = currentTick;
    }
  }

  function updateLiveButtonState() {
    const liveBtn = el("btn-live-sync");
    if (liveBtn) {
      if (isLive) liveBtn.classList.add("active");
      else liveBtn.classList.remove("active");
    }
  }

  function getFrameByTick(t) {
    if (!historyBuffer.length) return null;
    let closest = historyBuffer[0];
    let minDiff = Math.abs(closest.t - t);
    for (let i = 1; i < historyBuffer.length; i++) {
      const diff = Math.abs(historyBuffer[i].t - t);
      if (diff < minDiff) {
        minDiff = diff;
        closest = historyBuffer[i];
      }
    }
    return closest;
  }

  function renderHistoricalFrame(t, isInstant = true) {
    const f = getFrameByTick(t);
    if (!f) return;
    scrubTick = f.t;
    applyFrame(f, isInstant);
    const maxTick = historyBuffer[historyBuffer.length - 1].t;
    const slider = el("timeline-slider");
    if (slider) slider.value = f.t;
    updateTimelineUI(f.t, maxTick);
  }

  function togglePlayback() {
    isPaused = !isPaused;
    const btn = el("btn-playback-toggle");
    if (btn) {
      btn.textContent = isPaused ? "▶ Tiếp tục" : "⏸ Tạm dừng";
    }
  }

  function setPlaybackSpeed(s) {
    playbackSpeed = s;
    ["btn-speed-1x", "btn-speed-2x", "btn-speed-5x"].forEach((id) => el(id)?.classList.remove("active"));
    el(`btn-speed-${s}x`)?.classList.add("active");
  }

  function rewind10() {
    if (!historyBuffer.length) return;
    isLive = false;
    updateLiveButtonState();
    const minTick = historyBuffer[0].t;
    scrubTick = Math.max(minTick, scrubTick - 10);
    renderHistoricalFrame(scrubTick, true);
  }

  function forward10() {
    if (!historyBuffer.length) return;
    const maxTick = historyBuffer[historyBuffer.length - 1].t;
    if (scrubTick + 10 >= maxTick) {
      goToLive();
    } else {
      isLive = false;
      updateLiveButtonState();
      scrubTick = scrubTick + 10;
      renderHistoricalFrame(scrubTick, true);
    }
  }

  function goToLive() {
    isLive = true;
    isPaused = false;
    const btn = el("btn-playback-toggle");
    if (btn) btn.textContent = "⏸ Tạm dừng";
    updateLiveButtonState();
    if (historyBuffer.length) {
      const latest = historyBuffer[historyBuffer.length - 1];
      scrubTick = latest.t;
      renderHistoricalFrame(latest.t, true);
    }
  }

  el("timeline-slider")?.addEventListener("input", (e) => {
    const targetTick = parseInt(e.target.value, 10);
    const maxTick = historyBuffer.length ? historyBuffer[historyBuffer.length - 1].t : 0;
    if (targetTick >= maxTick) {
      goToLive();
    } else {
      isLive = false;
      updateLiveButtonState();
      scrubTick = targetTick;
      renderHistoricalFrame(scrubTick, true);
    }
  });

  el("btn-playback-toggle")?.addEventListener("click", togglePlayback);
  el("btn-speed-1x")?.addEventListener("click", () => setPlaybackSpeed(1));
  el("btn-speed-2x")?.addEventListener("click", () => setPlaybackSpeed(2));
  el("btn-speed-5x")?.addEventListener("click", () => setPlaybackSpeed(5));
  el("btn-rewind-10")?.addEventListener("click", rewind10);
  el("btn-forward-10")?.addEventListener("click", forward10);
  el("btn-live-sync")?.addEventListener("click", goToLive);

  addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target.tagName !== "INPUT") {
      e.preventDefault();
      togglePlayback();
    }
  });

  // ── Trạng thái Dữ liệu ──
  let W = 24, H = 24;
  let terrainGrid = [];
  let terrainKey = "";
  let latestFrame = null;
  const bodies = new Map(); // id -> { group, currX, currY, currZ, targetX, targetY, targetZ, yaw, targetYaw, data }
  const flashes = [];
  const shockwaves = [];
  let totalLawTriggers = 0;
  const plantMeshes = new Map(); // "x,y" -> Mesh
  const corpseMeshes = new Map(); // "x,y" -> Mesh

  // Selection outline ring
  const selectRingGeo = new THREE.RingGeometry(0.35, 0.42, 24);
  const selectRingMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.9 });
  const selectRing = new THREE.Mesh(selectRingGeo, selectRingMat);
  selectRing.rotation.x = -Math.PI / 2;
  selectRing.visible = false;
  scene.add(selectRing);

  // ── Quản lý Camera Presets & 24-Angle Master Diorama Camera Rig ──
  const CAMERA_RIG_24_PRESETS = {
    CAM_01_ISO_SE: { pos: [140, 120, 140], tgt: [0, 6, 0], near: 0.5, far: 2000.0, fov: 46 },
    CAM_02_ISO_SW: { pos: [-140, 120, 140], tgt: [0, 6, 0], near: 0.5, far: 2000.0, fov: 46 },
    CAM_03_ISO_NW: { pos: [-140, 120, -140], tgt: [0, 6, 0], near: 0.5, far: 2000.0, fov: 46 },
    CAM_04_ISO_NE: { pos: [140, 120, -140], tgt: [0, 6, 0], near: 0.5, far: 2000.0, fov: 46 },
    CAM_05_TOP_ORTHO: { pos: [0, 200, 0], tgt: [0, 0, 0], near: 0.5, far: 1000.0, fov: 45 },
    CAM_06_CARDINAL_NORTH: { pos: [0, 6, -180], tgt: [0, 6, 0], near: 0.5, far: 1000.0, fov: 45 },
    CAM_07_CARDINAL_EAST: { pos: [180, 6, 0], tgt: [0, 6, 0], near: 0.5, far: 1000.0, fov: 45 },
    CAM_08_CARDINAL_SOUTH: { pos: [0, 6, 180], tgt: [0, 6, 0], near: 0.5, far: 1000.0, fov: 45 },
    CAM_09_CARDINAL_WEST: { pos: [-180, 6, 0], tgt: [0, 6, 0], near: 0.5, far: 1000.0, fov: 45 },
    CAM_10_CUTAWAY_AA: { pos: [0, -2, 200], tgt: [0, -2, 0], near: 200.0, far: 400.0, fov: 45 },
    CAM_11_CUTAWAY_BB: { pos: [-200, -2, 0], tgt: [0, -2, 0], near: 200.0, far: 400.0, fov: 45 },
    CAM_12_CLOSEUP_LAKE_BASIN: { pos: [8, 16, 28], tgt: [-18, 4.5, 6], near: 0.2, far: 500.0, fov: 48 },
    CAM_13_CLOSEUP_WATERFALL_GORGE: { pos: [46, 18, 6], tgt: [30, 5, 14], near: 0.2, far: 500.0, fov: 48 },
    CAM_14_CLOSEUP_ALPINE_SUMMIT: { pos: [-8, 38, -22], tgt: [-8, 28.5, -52], near: 0.2, far: 500.0, fov: 48 },
    CAM_15_CLOSEUP_LOWLAND_FOREST: { pos: [-18, 14, -2], tgt: [-36, 7, -18], near: 0.2, far: 500.0, fov: 48 },
    CAM_16_CLOSEUP_SUBTERRANEAN_CAVE: { pos: [8, -4.5, -7], tgt: [14, -5.5, -15], near: 0.1, far: 100.0, fov: 55 },
    CAM_17_CLOSEUP_CAVE_ENTRANCE: { pos: [26, 5.5, 14], tgt: [15, 2.2, 6.5], near: 0.2, far: 200.0, fov: 48 },
    CAM_18_CLOSEUP_RIVER_MEANDER: { pos: [-2, 20, -26], tgt: [-14, 10, -18], near: 0.2, far: 400.0, fov: 48 },
    CAM_19_CLOSEUP_COASTAL_BAY: { pos: [25, 16, 25], tgt: [52, 0, 50], near: 0.2, far: 500.0, fov: 48 },
    CAM_20_SLOPE_ANALYSIS_VIEW: { pos: [35, 24, -30], tgt: [6, 18, -44], near: 0.5, far: 600.0, fov: 46 },
    CAM_21_ELEVATION_HEATMAP_VIEW: { pos: [120, 160, 120], tgt: [0, 0, 0], near: 0.5, far: 2000.0, fov: 46 },
    CAM_22_BIOME_TRANSITION_CORRIDOR: { pos: [-55, 42, -65], tgt: [-5, 6, 15], near: 0.5, far: 1000.0, fov: 48 },
    CAM_23_UNDERWATER_SUBMERGED_BED: { pos: [-12, 3.2, 10], tgt: [-20, 2.3, 5], near: 0.05, far: 50.0, fov: 55 },
    CAM_24_NIGHT_BIOLUMINESCENCE: { pos: [30, 10, 0], tgt: [15, 0, -12], near: 0.2, far: 300.0, fov: 50 },
  };

  let camMode = "ISO"; // "ISO" | "TOP" | "FREE" | "FOLLOW" | "RIG"
  let activeRigCamName = null;
  function _createSafeRigVec3(x, y, z) {
    if (typeof THREE !== "undefined" && typeof THREE.Vector3 === "function") {
      return new THREE.Vector3(x, y, z);
    }
    return {
      x: x || 0,
      y: y || 0,
      z: z || 0,
      set(nx, ny, nz) {
        this.x = nx; this.y = ny; this.z = nz;
        return this;
      },
      copy(v) {
        this.x = v.x; this.y = v.y; this.z = v.z;
        return this;
      },
      lerp(v, alpha) {
        const vx = v.x !== undefined ? v.x : this.x;
        const vy = v.y !== undefined ? v.y : this.y;
        const vz = v.z !== undefined ? v.z : this.z;
        this.x += (vx - this.x) * alpha;
        this.y += (vy - this.y) * alpha;
        this.z += (vz - this.z) * alpha;
        return this;
      }
    };
  }

  const targetRigPos = _createSafeRigVec3(140, 120, 140);
  const targetRigTarget = _createSafeRigVec3(0, 6, 0);
  const currRigPos = _createSafeRigVec3(140, 120, 140);
  const currRigTarget = _createSafeRigVec3(0, 6, 0);

  let dioramaMasterModel = null;
  let dioramaMixer = null;
  const embeddedCameras = new Map();

  let yaw = 0.785, pitch = 0.88, dist = 36.0;
  let targetYaw = 0.785, targetPitch = 0.88, targetDist = 36.0;
  let cx = 12, cz = 12, targetCx = 12, targetCz = 12;
  let dragging = false, lx = 0, ly = 0;
  let selectedCreatureId = null;

  // Fog of War & Creature POV State
  let enableFogOfWar = false;
  let currentWeatherModifiers = {};

  // URL Parameters Initialization
  let paramCreature = null;
  let paramFow = null;
  let paramSetup = null;
  let urlParams = null;
  try {
    const searchStr = (typeof window !== "undefined" && window.location && window.location.search) ? window.location.search : "";
    if (typeof URLSearchParams !== "undefined") {
      urlParams = new URLSearchParams(searchStr);
      paramCreature = urlParams.get("creature") || urlParams.get("species");
      paramFow = urlParams.get("fow");
      paramSetup = urlParams.get("setup") || urlParams.get("menu");
    }
  } catch (_) {}
  let pendingCreatureSelect = paramCreature;

  function setCameraPreset(mode) {
    const povHud = el("creature-pov-hud");
    const rigSelect = el("select-camera-rig");

    if (mode && mode.startsWith("CAM_")) {
      camMode = "RIG";
      activeRigCamName = mode;
      ["btn-cam-iso", "btn-cam-top", "btn-cam-free", "btn-cam-follow"].forEach((id) => el(id)?.classList.remove("active"));
      if (rigSelect) rigSelect.value = mode;
      if (povHud) povHud.style.display = "none";

      const preset = CAMERA_RIG_24_PRESETS[mode];
      if (preset) {
        targetRigPos.set(preset.pos[0], preset.pos[1], preset.pos[2]);
        targetRigTarget.set(preset.tgt[0], preset.tgt[1], preset.tgt[2]);

        // Near-plane cutaways for Section A-A & B-B (e.g. clip_start = 200m)
        camera.near = preset.near || 0.5;
        camera.far = preset.far || 1000.0;
        if (preset.fov) camera.fov = preset.fov;
        camera.updateProjectionMatrix();
      }
      return;
    }

    // Returning to standard telemetry game camera presets
    camMode = mode;
    activeRigCamName = null;
    if (rigSelect) rigSelect.value = "";
    camera.near = 0.1;
    camera.far = 500.0;
    camera.fov = 46;
    camera.updateProjectionMatrix();

    ["btn-cam-iso", "btn-cam-top", "btn-cam-free", "btn-cam-follow"].forEach((id) => el(id)?.classList.remove("active"));
    if (mode === "ISO") {
      el("btn-cam-iso")?.classList.add("active");
      targetYaw = 0.785; targetPitch = 0.88; targetDist = 36.0;
      targetCx = W / 2; targetCz = H / 2;
      if (povHud) povHud.style.display = "none";
    } else if (mode === "TOP") {
      el("btn-cam-top")?.classList.add("active");
      targetYaw = 0.0; targetPitch = 1.52; targetDist = 28.0;
      targetCx = W / 2; targetCz = H / 2;
      if (povHud) povHud.style.display = "none";
    } else if (mode === "FREE") {
      el("btn-cam-free")?.classList.add("active");
      if (povHud) povHud.style.display = "none";
    } else if (mode === "FOLLOW") {
      el("btn-cam-follow")?.classList.add("active");
      if (!selectedCreatureId) {
        for (const [id, entity] of bodies) {
          if (entity.data && entity.data.alive) {
            selectCreature(id);
            break;
          }
        }
      }
      targetPitch = 0.38;
      targetDist = 6.2;
      if (selectedCreatureId) {
        const ent = bodies.get(selectedCreatureId);
        if (ent) {
          targetYaw = ent.yaw + Math.PI;
          targetCx = ent.currX;
          targetCz = ent.currZ;
        }
      }
      if (povHud) {
        povHud.style.display = "block";
        const tag = el("pov-creature-tag");
        if (tag) tag.textContent = `POV: ${selectedCreatureId || "—"}`;
      }
    }
  }

  function toggleFogOfWar() {
    enableFogOfWar = !enableFogOfWar;
    const btn = el("btn-toggle-fow");
    if (btn) {
      btn.classList.toggle("active", enableFogOfWar);
      btn.textContent = enableFogOfWar ? "👁️ Fog: BẬT" : "👁️ Fog of War";
    }
    if (enableFogOfWar && !selectedCreatureId) {
      for (const [id, entity] of bodies) {
        if (entity.data && entity.data.alive) {
          selectCreature(id);
          break;
        }
      }
    }
  }

  el("btn-cam-iso")?.addEventListener("click", () => setCameraPreset("ISO"));
  el("btn-cam-top")?.addEventListener("click", () => setCameraPreset("TOP"));
  el("btn-cam-free")?.addEventListener("click", () => setCameraPreset("FREE"));
  el("btn-cam-follow")?.addEventListener("click", () => setCameraPreset("FOLLOW"));
  el("btn-toggle-fow")?.addEventListener("click", toggleFogOfWar);

  const rigSelector = el("select-camera-rig");
  rigSelector?.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val) {
      setCameraPreset(val);
    } else {
      setCameraPreset("ISO");
    }
  });

  if (paramFow === "1" || paramFow === "true") {
    toggleFogOfWar();
  }

  // Dropdown chọn sinh vật của tôi
  const creatureSelect = el("select-my-creature");
  creatureSelect?.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val) {
      selectCreature(val);
      setCameraPreset("FOLLOW");
    } else {
      deselectCreature();
      setCameraPreset("ISO");
    }
  });

  function updateCreatureDropdown(creatures) {
    if (!creatureSelect || !creatureSelect.options) return;
    let living = (creatures || []).filter((c) => c.alive);
    if (myCreatureId) {
      living = living.filter((c) => c.id === myCreatureId || isMyOffspring(c.id, creatures));
    }
    const livingIds = living.map((c) => c.id);
    const existingOptions = Array.from(creatureSelect.options).map((o) => o.value);

    const hasChanged = existingOptions.join(",") !== livingIds.join(",");
    if (hasChanged) {
      creatureSelect.innerHTML = myCreatureId ? '' : '<option value="">— Toàn cảnh —</option>';
      for (const c of living) {
        const opt = document.createElement("option");
        opt.value = c.id;
        const dom = getDomain(c);
        const icon = dom === "NUOC" ? "🌊" : (dom === "TROI" ? "🦅" : "🌿");
        const isMine = c.id === myCreatureId;
        opt.textContent = `${icon} ${isMine ? (myCreatureName || c.id) : c.id} (Gen ${c.gen || 0})${isMine ? ' ★ CỦA BẠN' : ''}`;
        creatureSelect.appendChild(opt);
      }
      if (selectedCreatureId && livingIds.includes(selectedCreatureId)) {
        creatureSelect.value = selectedCreatureId;
      }
    }
  }

  // Mouse Orbit Navigation
  renderer.domElement.addEventListener("mousedown", (e) => {
    if (e.button === 0 || e.button === 2) {
      dragging = true;
      lx = e.clientX; ly = e.clientY;
      if (camMode === "RIG") {
        camMode = "FREE";
        if (el("select-camera-rig")) el("select-camera-rig").value = "";
      } else if (camMode !== "FREE" && camMode !== "FOLLOW") {
        camMode = "FREE";
      }
      ["btn-cam-iso", "btn-cam-top"].forEach((id) => el(id)?.classList.remove("active"));
      if (camMode === "FREE") el("btn-cam-free")?.classList.add("active");
    }
  });
  addEventListener("mouseup", () => { dragging = false; });
  addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - lx;
    const dy = e.clientY - ly;
    targetYaw -= dx * 0.006;
    targetPitch = Math.max(0.12, Math.min(1.54, targetPitch - dy * 0.006));
    lx = e.clientX; ly = e.clientY;
  });
  renderer.domElement.addEventListener("wheel", (e) => {
    targetDist = Math.max(camMode === "FOLLOW" ? 3 : 8, Math.min(80, targetDist + e.deltaY * 0.03));
    e.preventDefault();
  }, { passive: false });

  // ── Raycasting để chọn sinh vật ──
  const raycaster = new THREE.Raycaster();
  const mouseVec = new THREE.Vector2();
  renderer.domElement.addEventListener("click", (e) => {
    mouseVec.x = (e.clientX / innerWidth) * 2 - 1;
    mouseVec.y = -(e.clientY / innerHeight) * 2 + 1;
    raycaster.setFromCamera(mouseVec, camera);
    const intersects = raycaster.intersectObjects(bodyGroup.children, true);
    if (intersects.length > 0) {
      let topGroup = intersects[0].object;
      while (topGroup.parent && topGroup.parent !== bodyGroup) topGroup = topGroup.parent;
      if (topGroup.userData && topGroup.userData.creatureId) {
        const clickedId = topGroup.userData.creatureId;
        if (myCreatureId && clickedId !== myCreatureId && !isMyOffspring(clickedId, latestFrame ? latestFrame.creatures : [])) {
          showFloatingWarning("⚠️ Bạn chỉ có thể theo dõi sinh vật do bạn tạo ra!");
          return;
        }
        selectCreature(clickedId);
      }
    }
  });

  // Keyboard Shortcuts
  let showHear = true;
  let showJournal = true;
  let showMinimap = true;

  addEventListener("keydown", (e) => {
    const k = e.key.toUpperCase();
    if (k === "1") setCameraPreset("ISO");
    else if (k === "2") setCameraPreset("TOP");
    else if (k === "3") setCameraPreset("FREE");
    else if (k === "4") setCameraPreset("FOLLOW");
    else if (k === "P") toggleSetupLobby();
    else if (k === "G") toggleHearing();
    else if (k === "J") toggleJournal();
    else if (k === "M") toggleMinimap();
    else if (k === "F") toggleFogOfWar();
    else if (k === "ESCAPE") {
      const dm = el("creature-setup-lobby") || el("creature-dossier-modal");
      if (dm && dm.style.display !== "none") {
        closeSetupLobby();
      } else {
        deselectCreature();
      }
    }
  });

  function toggleHearing() {
    showHear = !showHear;
    el("btn-toggle-hear")?.classList.toggle("active", showHear);
    lineGroup.visible = showHear;
  }
  function toggleJournal() {
    showJournal = !showJournal;
    el("btn-toggle-journal")?.classList.toggle("active", showJournal);
    el("journal-panel")?.classList.toggle("collapsed", !showJournal);
    el("journal-toggle-icon").textContent = showJournal ? "▾" : "▸";
  }
  function toggleMinimap() {
    showMinimap = !showMinimap;
    el("btn-toggle-minimap")?.classList.toggle("active", showMinimap);
    el("minimap-container").style.display = showMinimap ? "flex" : "none";
  }

  el("btn-toggle-hear")?.addEventListener("click", toggleHearing);
  el("btn-toggle-journal")?.addEventListener("click", toggleJournal);
  el("btn-toggle-minimap")?.addEventListener("click", toggleMinimap);
  el("journal-header")?.addEventListener("click", toggleJournal);

  function hashStr(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) { h = ((h << 5) - h) + s.charCodeAt(i); h |= 0; }
    return Math.abs(h);
  }

  let dioramaOceanMesh = null;
  let waterSurfaceMesh = null;

  // ── 0. Tải Mô Hình Master Diorama 3D Bất Đồng Bộ (Genesis Zero Masterpiece) ──
  function _isHeadlessOrNodeContext() {
    const isNode = typeof process !== "undefined" && Boolean(process.versions && process.versions.node);
    const isMock = typeof navigator === "undefined" || !navigator.userAgent;
    return isNode || isMock;
  }

  function loadDioramaGLB() {
    if (typeof THREE === "undefined" || typeof THREE.GLTFLoader === "undefined") {
      if (!_isHeadlessOrNodeContext()) {
        console.info("[Genesis3D] THREE.GLTFLoader not found, using procedural diorama.");
      }
      return;
    }
    const loader = new THREE.GLTFLoader();
    const candidates = [
      "models/anima_world.glb",
      "../models/anima_world.glb",
      "/models/anima_world.glb",
      "../models/genesis_diorama.glb",
      "models/genesis_diorama.glb",
      "/models/genesis_diorama.glb",
    ];
    let idx = 0;

    function tryCandidate() {
      if (idx >= candidates.length) return;
      const url = candidates[idx++];
      loader.load(
        url,
        (gltf) => {
          console.log("[Genesis3D] Master diorama GLB loaded successfully from:", url);
          dioramaMasterModel = gltf.scene;
          dioramaMasterModel.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
            }
          });

          // Xóa bệ procedural sơ cấp để nhường chỗ cho khối Master Diorama
          while (dioramaGroup.children.length) dioramaGroup.remove(dioramaGroup.children[0]);
          dioramaGroup.add(dioramaMasterModel);

          // Trích xuất 24 góc máy nhúng từ glTF nếu có
          if (gltf.cameras && gltf.cameras.length > 0) {
            for (const cam of gltf.cameras) {
              if (cam.name) embeddedCameras.set(cam.name, cam);
            }
            console.log(`[Genesis3D] Linked ${embeddedCameras.size} embedded cameras from glTF.`);
          }

          // Kích hoạt animation fauna động vật nếu có
          if (gltf.animations && gltf.animations.length > 0) {
            dioramaMixer = new THREE.AnimationMixer(dioramaMasterModel);
            gltf.animations.forEach((clip) => {
              dioramaMixer.clipAction(clip).play();
            });
            console.log(`[Genesis3D] Started ${gltf.animations.length} fauna animation tracks.`);
          }
        },
        undefined,
        () => {
          tryCandidate();
        }
      );
    }
    tryCandidate();
  }

  // ── 1. Dựng Bệ Diorama & Khung Đảo Thu Nhỏ (Phong Cách Terrarium Anima-Engine) ──
  function buildDioramaPedestal(w, h) {
    if (dioramaMasterModel) return; // Bảo toàn khối Master Diorama 3D
    while (dioramaGroup.children.length) dioramaGroup.remove(dioramaGroup.children[0]);

    // Bệ đá chính nâng đỡ hòn đảo (lớp địa tầng đáy)
    const baseGeo = new THREE.BoxGeometry(w + 1.8, 2.2, h + 1.8);
    const baseMat = new THREE.MeshLambertMaterial({ color: 0x0f172a });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.set(w / 2, -1.15, h / 2);
    baseMesh.receiveShadow = true;
    dioramaGroup.add(baseMesh);

    // Lớp thổ nhưỡng trung gian mô phỏng đất phù sa
    const soilGeo = new THREE.BoxGeometry(w + 1.2, 0.35, h + 1.2);
    const soilMat = new THREE.MeshLambertMaterial({ color: 0x292524 });
    const soilMesh = new THREE.Mesh(soilGeo, soilMat);
    soilMesh.position.set(w / 2, -0.2, h / 2);
    dioramaGroup.add(soilMesh);

    // Viền khung kim loại sang trọng bao quanh đảo
    const bezelGeo = new THREE.BoxGeometry(w + 2.0, 0.25, h + 2.0);
    const bezelMat = new THREE.MeshLambertMaterial({ color: 0x1e293b });
    const bezelMesh = new THREE.Mesh(bezelGeo, bezelMat);
    bezelMesh.position.set(w / 2, -0.04, h / 2);
    dioramaGroup.add(bezelMesh);

    // Mặt nước biển đại dương bao quanh đảo tự nhiên
    const oceanGeo = new THREE.PlaneGeometry(w + 1.2, h + 1.2);
    const oceanMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.1,
      metalness: 0.18,
      transparent: true,
      opacity: 0.72,
    });
    dioramaOceanMesh = new THREE.Mesh(oceanGeo, oceanMat);
    dioramaOceanMesh.rotation.x = -Math.PI / 2;
    dioramaOceanMesh.position.set(w / 2, 0.02, h / 2);
    dioramaGroup.add(dioramaOceanMesh);
  }

  // ── 2. Dựng Địa Hình & Thảm Thực Vật Tự Nhiên 3D (Anima-Engine Style) ──
  function buildTerrain(rows) {
    if (!rows || !rows.length) return;
    const key = rows.join("|");
    if (key === terrainKey) return;
    terrainKey = key;
    terrainGrid = rows;

    while (terrainGroup.children.length) terrainGroup.remove(terrainGroup.children[0]);
    H = rows.length; W = rows[0].length;
    cx = W / 2; cz = H / 2;
    targetCx = cx; targetCz = cz;

    buildDioramaPedestal(W, H);

    const byType = {};
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const code = rows[y][x];
        (byType[code] ||= []).push([x, y]);
      }
    }

    const boxGeo = new THREE.BoxGeometry(CELL, 1, CELL);
    for (const [code, cells] of Object.entries(byType)) {
      const t = TERRAIN[code] || TERRAIN.P;
      const mat = new THREE.MeshLambertMaterial({
        color: t.c,
        emissive: code === "F" ? 0x9a3412 : (code === "C" ? 0x0c0a09 : 0x000000),
      });
      const mesh = new THREE.InstancedMesh(boxGeo, mat, cells.length);
      mesh.receiveShadow = true;
      mesh.castShadow = (code === "R" || code === "T" || code === "B");

      const m = new THREE.Matrix4();
      const height = Math.max(0.04, Math.abs(t.h));
      cells.forEach(([x, y], idx) => {
        const posY = t.h >= 0 ? t.h / 2 : t.h / 2;
        m.makeScale(1, height, 1);
        m.setPosition(x + 0.5, posY, y + 0.5);
        mesh.setMatrixAt(idx, m);
      });
      mesh.instanceMatrix.needsUpdate = true;
      terrainGroup.add(mesh);
    }

    // ── Thêm Cây Cối, Bụi Rậm & Đá Tự Nhiên 3D theo phong cách Anima-Engine ──
    // 1. Rừng Cây Cao (T): Cây sồi và cây thông 3D Low-Poly
    const treeCells = byType["T"] || [];
    if (treeCells.length > 0 && typeof THREE.InstancedMesh === "function") {
      const trunkGeo = new THREE.CylinderGeometry(0.09, 0.13, 0.7, 5);
      const trunkMat = new THREE.MeshLambertMaterial({ color: 0x78350f });
      const trunkMesh = new THREE.InstancedMesh(trunkGeo, trunkMat, treeCells.length);
      trunkMesh.castShadow = true;
      trunkMesh.receiveShadow = true;

      const leavesGeo = typeof THREE.DodecahedronGeometry === "function"
        ? new THREE.DodecahedronGeometry(0.48, 0)
        : new THREE.ConeGeometry(0.44, 0.75, 5);
      const leavesMat = new THREE.MeshLambertMaterial({ color: 0x15803d });
      const leavesMesh = new THREE.InstancedMesh(leavesGeo, leavesMat, treeCells.length);
      leavesMesh.castShadow = true;

      const mTrunk = new THREE.Matrix4();
      const mLeaves = new THREE.Matrix4();
      const mRot = new THREE.Matrix4();

      treeCells.forEach(([x, y], idx) => {
        const tH = TERRAIN.T.h;
        const seed = (x * 17 + y * 31);
        const scale = 0.85 + (seed % 30) * 0.01;
        const rotY = (seed % 628) / 100;

        mRot.makeRotationY(rotY);

        mTrunk.makeScale(scale, scale, scale);
        mTrunk.multiply(mRot);
        mTrunk.setPosition(x + 0.5, tH + 0.35 * scale, y + 0.5);
        trunkMesh.setMatrixAt(idx, mTrunk);

        mLeaves.makeScale(scale, scale * 1.08, scale);
        mLeaves.multiply(mRot);
        mLeaves.setPosition(x + 0.5, tH + 0.78 * scale, y + 0.5);
        leavesMesh.setMatrixAt(idx, mLeaves);
      });
      trunkMesh.instanceMatrix.needsUpdate = true;
      leavesMesh.instanceMatrix.needsUpdate = true;
      terrainGroup.add(trunkMesh, leavesMesh);
    }

    // 2. Bụi Rậm Thảo Mộc (B): Khóm bụi rậm Low-Poly tự nhiên
    const bushCells = byType["B"] || [];
    if (bushCells.length > 0 && typeof THREE.InstancedMesh === "function") {
      const bushGeo = typeof THREE.DodecahedronGeometry === "function"
        ? new THREE.DodecahedronGeometry(0.26, 0)
        : new THREE.BoxGeometry(0.3, 0.3, 0.3);
      const bushMat = new THREE.MeshLambertMaterial({ color: 0x16a34a });
      const bushMesh = new THREE.InstancedMesh(bushGeo, bushMat, bushCells.length);
      bushMesh.castShadow = true;
      bushMesh.receiveShadow = true;

      const mBush = new THREE.Matrix4();
      bushCells.forEach(([x, y], idx) => {
        const tH = TERRAIN.B.h;
        const seed = (x * 23 + y * 41);
        const scale = 0.8 + (seed % 40) * 0.01;
        mBush.makeScale(scale, scale * 0.85, scale);
        mBush.setPosition(x + 0.5, tH + 0.15 * scale, y + 0.5);
        bushMesh.setMatrixAt(idx, mBush);
      });
      bushMesh.instanceMatrix.needsUpdate = true;
      terrainGroup.add(bushMesh);
    }

    // 3. Khối Đá Vách Núi (R): Boulders góc cạnh màu đá tự nhiên
    const rockCells = byType["R"] || [];
    if (rockCells.length > 0 && typeof THREE.InstancedMesh === "function") {
      const rockGeo = typeof THREE.DodecahedronGeometry === "function"
        ? new THREE.DodecahedronGeometry(0.34, 0)
        : new THREE.BoxGeometry(0.4, 0.4, 0.4);
      const rockMat = new THREE.MeshLambertMaterial({ color: 0x94a3b8 });
      const rockMesh = new THREE.InstancedMesh(rockGeo, rockMat, rockCells.length);
      rockMesh.castShadow = true;
      rockMesh.receiveShadow = true;

      const mRock = new THREE.Matrix4();
      rockCells.forEach(([x, y], idx) => {
        const tH = TERRAIN.R.h;
        const seed = (x * 19 + y * 29);
        const scale = 0.85 + (seed % 35) * 0.01;
        mRock.makeScale(scale * 1.15, scale * 0.75, scale * 0.95);
        mRock.setPosition(x + 0.5, tH + 0.16 * scale, y + 0.5);
        rockMesh.setMatrixAt(idx, mRock);
      });
      rockMesh.instanceMatrix.needsUpdate = true;
      terrainGroup.add(rockMesh);
    }

    // 4. Lớp Mặt Nước Trong Suốt Có Sóng Gợn (W & D)
    const waterCells = [...(byType["W"] || []), ...(byType["D"] || [])];
    if (waterCells.length > 0 && typeof THREE.InstancedMesh === "function") {
      const waterPlaneGeo = new THREE.PlaneGeometry(1, 1);
      const waterMat = new THREE.MeshStandardMaterial({
        color: 0x2294a8,
        roughness: 0.08,
        metalness: 0.22,
        transparent: true,
        opacity: 0.82,
      });
      const wMesh = new THREE.InstancedMesh(waterPlaneGeo, waterMat, waterCells.length);
      const mW = new THREE.Matrix4();
      const mRotX = new THREE.Matrix4().makeRotationX(-Math.PI / 2);
      waterCells.forEach(([x, y], idx) => {
        mW.makeTranslation(x + 0.5, -0.02, y + 0.5);
        mW.multiply(mRotX);
        wMesh.setMatrixAt(idx, mW);
      });
      wMesh.instanceMatrix.needsUpdate = true;
      waterSurfaceMesh = wMesh;
      terrainGroup.add(wMesh);
    }
  }

  // ── 3. Xác định Tầng & Đặc Điểm của Sinh Vật ──
  function getDomain(c) {
    if (c.domain) return c.domain;
    const sid = (c.id || "").split(":")[0];
    if (sid.startsWith("W")) return "NUOC";
    if (sid.startsWith("A")) return "TROI";
    return "CAN";
  }

  function getSpeciesName(c) {
    return (c.id || "").split(":")[0] || "L1";
  }

  // ── 4. Độ cao 3 tầng sinh thái chuẩn hoá ──
  function getElevation(c) {
    const domain = getDomain(c);
    const x = Math.floor(c.x);
    const y = Math.floor(c.y);
    const terrainCode = (terrainGrid[y] && terrainGrid[y][x]) || "P";
    const speed = (c.tr && c.tr[TR.speed]) || 0;

    if (domain === "TROI") {
      // Tầng trời: bay lượn trên cao y = 2.5
      return 2.5;
    }
    if (domain === "NUOC") {
      // Tầng nước: bơi ngập dưới mặt nước y = -0.25
      return -0.25;
    }
    // Tầng cạn:
    if (terrainCode === "T" && speed >= 3) {
      // Leo trèo lên tán cây cao y = 1.45
      return 1.45;
    }
    if (terrainCode === "R") return 0.96 + 0.15;
    if (terrainCode === "C") return 0.20;
    if (terrainCode === "B") return 0.35;
    return 0.25;
  }

  // ── 5. Khởi tạo Hình thái Thủ tục 3D (6 Traits + 12 Biological Features) ──
  function makeBody(c) {
    const t = c.tr || [2, 2, 2, 2, 2, 2];
    const domain = getDomain(c);
    const species = getSpeciesName(c);
    const hue = ((hashStr(species) % 360) + ((hashStr(c.id) % 21) - 10) + 360) % 360;
    const mainCol = new THREE.Color().setHSL(hue / 360, 0.65, 0.52);
    const darkCol = new THREE.Color().setHSL(hue / 360, 0.85, 0.24);
    const accentCol = new THREE.Color().setHSL(((hue + 140) % 360) / 360, 0.85, 0.6);
    const g = new THREE.Group();
    g.userData.creatureId = c.id;

    // Kích thước dạ dày (stomach) -> vòng bụng
    const stomachR = 0.13 + t[TR.stomach] * 0.032;
    const speedZ = 1.0 + t[TR.speed] * 0.14;

    // ── Thân theo 3 Dáng Tầng (Domain Silhouettes) ──
    if (domain === "NUOC") {
      // Dáng Cá / Sinh vật thuỷ sinh: thân thuôn hình thoi, không chân, có vây đuôi & vây lưng
      const bodyGeo = new THREE.ConeGeometry(stomachR, 0.44 * speedZ, 12);
      const bodyMesh = new THREE.Mesh(bodyGeo, new THREE.MeshLambertMaterial({ color: mainCol }));
      bodyMesh.rotation.x = Math.PI / 2;
      g.add(bodyMesh);

      // Vây đuôi dựng đứng
      const tailGeo = new THREE.BoxGeometry(0.02, 0.22, 0.18);
      const tailMesh = new THREE.Mesh(tailGeo, new THREE.MeshLambertMaterial({ color: accentCol }));
      tailMesh.position.set(0, 0, -0.26 * speedZ);
      g.add(tailMesh);

      // Vây ngực 2 bên
      for (const s of [-1, 1]) {
        const fin = new THREE.Mesh(
          new THREE.BoxGeometry(0.12, 0.02, 0.08),
          new THREE.MeshLambertMaterial({ color: darkCol }));
        fin.position.set(s * (stomachR + 0.04), 0, 0.05);
        fin.rotation.z = s * 0.3;
        g.add(fin);
      }
    } else if (domain === "TROI") {
      // Dáng Chim / Sinh vật bay: thân khí động học, 2 cánh sải rộng, đuôi xoè quạt
      const bodyMesh = new THREE.Mesh(
        new THREE.SphereGeometry(stomachR * 0.9, 10, 8),
        new THREE.MeshLambertMaterial({ color: mainCol }));
      bodyMesh.scale.set(0.85, 0.8, 1.3 * speedZ);
      g.add(bodyMesh);

      // Đôi cánh lớn sải rộng
      for (const s of [-1, 1]) {
        const wing = new THREE.Mesh(
          new THREE.BoxGeometry(0.28, 0.02, 0.14),
          new THREE.MeshLambertMaterial({ color: accentCol }));
        wing.position.set(s * (stomachR + 0.12), 0.04, 0);
        wing.rotation.y = s * 0.15;
        g.add(wing);
      }
    } else {
      // Dáng Bốn chân sống trên cạn: thân elip, 4 chi, đuôi
      const bodyMesh = new THREE.Mesh(
        new THREE.SphereGeometry(stomachR, 12, 10),
        new THREE.MeshLambertMaterial({ color: mainCol }));
      bodyMesh.scale.z = speedZ;
      g.add(bodyMesh);

      // 4 chi dưới thân
      const legGeo = new THREE.CylinderGeometry(0.024, 0.024, 0.14 + t[TR.speed] * 0.018, 6);
      for (const sx of [-1, 1]) {
        for (const sz of [-1, 1]) {
          const leg = new THREE.Mesh(legGeo, new THREE.MeshLambertMaterial({ color: darkCol }));
          leg.position.set(sx * (stomachR * 0.7), -0.09, sz * (0.10 * speedZ));
          g.add(leg);
        }
      }

      // Đuôi
      const tail = new THREE.Mesh(
        new THREE.CylinderGeometry(0.015, 0.03, 0.18, 5),
        new THREE.MeshLambertMaterial({ color: darkCol }));
      tail.rotation.x = -Math.PI / 3;
      tail.position.set(0, 0.02, -stomachR * speedZ - 0.06);
      g.add(tail);
    }

    // ── Đầu & Trí tuệ (Brain trait) ──
    const headR = 0.06 + t[TR.brain] * 0.026;
    const headMesh = new THREE.Mesh(
      new THREE.SphereGeometry(headR, 10, 8),
      new THREE.MeshLambertMaterial({ color: mainCol }));
    headMesh.position.set(0, 0.10 + t[TR.brain] * 0.015, 0.16 + speedZ * 0.08);
    g.add(headMesh);

    // Vòng phát quang trí tuệ nếu brain >= 3
    if (t[TR.brain] >= 3) {
      const halo = new THREE.Mesh(
        new THREE.TorusGeometry(headR * 1.15, 0.014, 6, 16),
        new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.8 }));
      halo.rotation.x = Math.PI / 2;
      halo.position.set(0, headMesh.position.y + headR * 0.7, headMesh.position.z);
      g.add(halo);
    }

    // ── Giác quan (Sense trait) -> Cụm Mắt ──
    const eyeCount = t[TR.sense] >= 4 ? 4 : 2;
    const eyeR = 0.018 + t[TR.sense] * 0.009;
    for (let i = 0; i < eyeCount; i++) {
      const s = (i % 2 === 0) ? -1 : 1;
      const offY = i >= 2 ? 0.03 : 0;
      const eye = new THREE.Mesh(
        new THREE.SphereGeometry(eyeR, 6, 6),
        new THREE.MeshBasicMaterial({ color: 0xffffff }));
      eye.position.set(
        s * (headR * 0.65),
        headMesh.position.y + 0.02 + offY,
        headMesh.position.z + headR * 0.75);
      g.add(eye);
    }

    // ── Giáp (Armor trait) -> Phiến giáp / Gai bảo vệ lưng ──
    const armorCount = t[TR.armor];
    for (let i = 0; i < armorCount; i++) {
      const armorPlate = new THREE.Mesh(
        new THREE.ConeGeometry(0.035, 0.09, 5),
        new THREE.MeshLambertMaterial({ color: darkCol }));
      armorPlate.position.set(0, stomachR + 0.05, -0.12 + i * 0.07);
      g.add(armorPlate);
    }

    // ── Tấn công (Attack trait) -> Nanh / Vuốt / Sừng ──
    if (t[TR.attack] > 0) {
      for (const s of [-1, 1]) {
        const fang = new THREE.Mesh(
          new THREE.ConeGeometry(0.02, 0.05 + t[TR.attack] * 0.022, 5),
          new THREE.MeshLambertMaterial({ color: 0xf8fafc }));
        fang.rotation.x = Math.PI / 2 + 0.2;
        fang.position.set(s * 0.035, headMesh.position.y - 0.03, headMesh.position.z + headR * 0.9);
        g.add(fang);
      }
    }

    // ── 12 Biological Features (Đặc điểm sinh học) ──
    const feats = c.features || [];
    const featStr = feats.join(" ");

    // 1. LUONG_CU (Chân màng bơi)
    if (featStr.includes("LUONG_CU") || featStr.includes("VAY_BOI")) {
      for (const s of [-1, 1]) {
        const web = new THREE.Mesh(
          new THREE.PlaneGeometry(0.08, 0.08),
          new THREE.MeshLambertMaterial({ color: 0x0284c7, side: THREE.DoubleSide }));
        web.position.set(s * (stomachR + 0.08), -0.06, 0);
        web.rotation.x = Math.PI / 2;
        g.add(web);
      }
    }
    // 2. DAO_HANG (Móng bới đất to)
    if (featStr.includes("DAO_HANG")) {
      for (const s of [-1, 1]) {
        const claw = new THREE.Mesh(
          new THREE.BoxGeometry(0.04, 0.03, 0.08),
          new THREE.MeshLambertMaterial({ color: 0x78716c }));
        claw.position.set(s * (stomachR * 0.7), -0.12, 0.18);
        g.add(claw);
      }
    }
    // 3. TREO_GIOI (Đuôi cuốn dài)
    if (featStr.includes("TREO_GIOI")) {
      const curlTail = new THREE.Mesh(
        new THREE.TorusGeometry(0.08, 0.02, 6, 12, Math.PI * 1.5),
        new THREE.MeshLambertMaterial({ color: darkCol }));
      curlTail.position.set(0, 0.08, -stomachR * speedZ - 0.1);
      g.add(curlTail);
    }
    // 4. CANH_LUOT (Màng lượn)
    if (featStr.includes("CANH_LUOT") || featStr.includes("CANH_BAY")) {
      for (const s of [-1, 1]) {
        const flap = new THREE.Mesh(
          new THREE.PlaneGeometry(0.18, 0.22),
          new THREE.MeshLambertMaterial({ color: accentCol, side: THREE.DoubleSide, transparent: true, opacity: 0.85 }));
        flap.position.set(s * (stomachR + 0.09), 0, 0);
        flap.rotation.x = Math.PI / 2;
        g.add(flap);
      }
    }
    // 5. LONG_DAI (Bờm lông dày)
    if (featStr.includes("LONG_DAI")) {
      const ruff = new THREE.Mesh(
        new THREE.TorusGeometry(headR * 1.2, 0.035, 6, 10),
        new THREE.MeshLambertMaterial({ color: darkCol }));
      ruff.position.set(0, headMesh.position.y - 0.02, headMesh.position.z - 0.04);
      g.add(ruff);
    }
    // 6. GAI_DOC (Gai độc phát quang)
    if (featStr.includes("GAI_DOC") || featStr.includes("NOC_DOC")) {
      for (let i = 0; i < 3; i++) {
        const spike = new THREE.Mesh(
          new THREE.ConeGeometry(0.025, 0.12, 5),
          new THREE.MeshBasicMaterial({ color: 0xa855f7 }));
        spike.position.set(0, stomachR + 0.08, -0.08 + i * 0.08);
        g.add(spike);
      }
    }
    // 7. VO_SO (Mai sò cứng)
    if (featStr.includes("VO_SO") || featStr.includes("GIAP_CUNG")) {
      const shell = new THREE.Mesh(
        new THREE.SphereGeometry(stomachR * 1.15, 8, 8, 0, Math.PI * 2, 0, Math.PI / 2),
        new THREE.MeshLambertMaterial({ color: 0x475569 }));
      shell.position.set(0, 0.04, 0);
      g.add(shell);
    }
    // 8. MAT_DEM (Mắt đêm to sáng)
    if (featStr.includes("MAT_DEM")) {
      for (const s of [-1, 1]) {
        const nightEye = new THREE.Mesh(
          new THREE.SphereGeometry(0.035, 8, 8),
          new THREE.MeshBasicMaterial({ color: 0xfacc15 }));
        nightEye.position.set(s * (headR * 0.7), headMesh.position.y + 0.03, headMesh.position.z + headR * 0.8);
        g.add(nightEye);
      }
    }
    // 9. RAU_CAM_UNG (Râu cảm ứng dài)
    if (featStr.includes("RAU_CAM_UNG")) {
      for (const s of [-1, 1]) {
        const whisker = new THREE.Mesh(
          new THREE.CylinderGeometry(0.006, 0.006, 0.22, 4),
          new THREE.MeshLambertMaterial({ color: 0xf8fafc }));
        whisker.rotation.z = s * 0.7;
        whisker.rotation.x = Math.PI / 3;
        whisker.position.set(s * 0.06, headMesh.position.y - 0.01, headMesh.position.z + headR + 0.08);
        g.add(whisker);
      }
    }
    // 10. RANG_NANH (Răng nanh kiếm)
    if (featStr.includes("RANG_NANH") || featStr.includes("VAP_HAM")) {
      for (const s of [-1, 1]) {
        const tusk = new THREE.Mesh(
          new THREE.ConeGeometry(0.024, 0.11, 5),
          new THREE.MeshLambertMaterial({ color: 0xffffff }));
        tusk.rotation.x = Math.PI / 2 + 0.3;
        tusk.position.set(s * 0.04, headMesh.position.y - 0.05, headMesh.position.z + headR * 0.95);
        g.add(tusk);
      }
    }
    // 11. TUI_MA (Túi má phồng)
    if (featStr.includes("TUI_MA")) {
      for (const s of [-1, 1]) {
        const pouch = new THREE.Mesh(
          new THREE.SphereGeometry(0.04, 6, 6),
          new THREE.MeshLambertMaterial({ color: mainCol }));
        pouch.position.set(s * (headR + 0.02), headMesh.position.y - 0.02, headMesh.position.z);
        g.add(pouch);
      }
    }

    g.userData.mats = [];
    g.traverse((child) => { if (child.material) g.userData.mats.push(child.material); });
    return g;
  }

  // ── 6. Đồng bộ và Interpolate Chuyển động Sinh Vật ──
  function syncBodies(frame, isInstant = false) {
    const aliveSet = new Set();
    let cntNuoc = 0, cntCan = 0, cntTroi = 0;

    for (const c of frame.creatures || []) {
      const domain = getDomain(c);
      if (c.alive) {
        aliveSet.add(c.id);
        if (domain === "NUOC") cntNuoc++;
        else if (domain === "TROI") cntTroi++;
        else cntCan++;
      }

      let entity = bodies.get(c.id);
      const targetElev = getElevation(c);
      const targetX = c.x + 0.5;
      const targetZ = c.y + 0.5;

      if (!entity) {
        const group = makeBody(c);
        bodyGroup.add(group);
        entity = {
          group,
          currX: targetX,
          currY: targetElev,
          currZ: targetZ,
          targetX,
          targetY: targetElev,
          targetZ,
          yaw: 0,
          targetYaw: 0,
          data: c,
        };
        bodies.set(c.id, entity);
      } else {
        // Xử lý góc xoay hướng đi & bước nhảy wrap biên tròn
        const dx = targetX - entity.currX;
        const dz = targetZ - entity.currZ;
        if (Math.abs(dx) > W / 2 || Math.abs(dz) > H / 2) {
          // Wrap qua biên bản đồ: dịch chuyển tức thời không kéo dài vệt lerp
          entity.currX = targetX;
          entity.currZ = targetZ;
        } else if (Math.abs(dx) > 0.05 || Math.abs(dz) > 0.05) {
          entity.targetYaw = Math.atan2(dx, dz);
          if (c.alive && isLive && !isInstant) {
            playMoveSound(domain);
          }
        }
        entity.targetX = targetX;
        entity.targetY = targetElev;
        entity.targetZ = targetZ;
        entity.data = c;
      }

      if (isInstant) {
        entity.currX = targetX;
        entity.currY = targetElev;
        entity.currZ = targetZ;
        entity.yaw = entity.targetYaw;
        entity.group.position.set(targetX, targetElev, targetZ);
        entity.group.rotation.y = entity.yaw;
      }

      // Trạng thái sống / năng lượng & phát sáng mắt trong đêm
      const eRatio = Math.max(0.12, Math.min(1.0, (c.e || 0) / (c.e_max || 1)));
      const isNight = (currentDiurnal === "NIGHT");
      for (const m of entity.group.userData.mats) {
        if (m.opacity !== undefined) {
          m.transparent = true;
          m.opacity = c.alive ? 1.0 : 0.22;
        }
        if (m.emissive) {
          const glowBoost = isNight ? 1.8 : 1.0;
          m.emissive.setScalar(c.alive ? eRatio * 0.15 * glowBoost : 0);
        }
      }
      entity.group.visible = true;
    }

    for (const [id, entity] of bodies) {
      if (!aliveSet.has(id)) {
        for (const m of entity.group.userData.mats) {
          if (m.opacity !== undefined) { m.transparent = true; m.opacity = 0.2; }
        }
      }
    }

    // Cập nhật thống kê 3 tầng lên Header
    if (el("cnt-nuoc")) el("cnt-nuoc").textContent = cntNuoc;
    if (el("cnt-can")) el("cnt-can").textContent = cntCan;
    if (el("cnt-troi")) el("cnt-troi").textContent = cntTroi;

    // Cập nhật thẻ sinh vật đang soi
    if (selectedCreatureId) updateInspectCard();
  }

  // ── 7. Render Thức ăn (Plants / Fruits / Algae) & Xác chết (Corpses) ──
  function syncPlantsAndCorpses(frame) {
    // 1. Quả / Rong tảo
    const currentPlants = new Set();
    for (const p of frame.plants || []) {
      const key = `${p[0]},${p[1]}`;
      currentPlants.add(key);
      if (!plantMeshes.has(key)) {
        const x = p[0], y = p[1];
        const terrainCode = (terrainGrid[y] && terrainGrid[y][x]) || "P";
        const isWater = (terrainCode === "W" || terrainCode === "D");

        let mesh;
        if (isWater) {
          // Rong tảo nước
          const geo = new THREE.CylinderGeometry(0.02, 0.05, 0.28, 5);
          const mat = new THREE.MeshLambertMaterial({ color: 0x10b981 });
          mesh = new THREE.Mesh(geo, mat);
          mesh.position.set(x + 0.5, -0.05, y + 0.5);
        } else {
          // Quả dại trên cạn
          const geo = new THREE.SphereGeometry(0.08, 8, 8);
          const mat = new THREE.MeshLambertMaterial({ color: 0xef4444 });
          mesh = new THREE.Mesh(geo, mat);
          mesh.position.set(x + 0.5, 0.22, y + 0.5);
        }
        plantsGroup.add(mesh);
        plantMeshes.set(key, mesh);
      }
    }
    for (const [k, mesh] of plantMeshes) {
      if (!currentPlants.has(k)) {
        plantsGroup.remove(mesh);
        plantMeshes.delete(k);
      }
    }

    // 2. Xác sinh vật
    const currentCorpses = new Set();
    for (const c of frame.corpses || []) {
      const key = `${c[0]},${c[1]}`;
      currentCorpses.add(key);
      if (!corpseMeshes.has(key)) {
        const x = c[0], y = c[1];
        const geo = new THREE.BoxGeometry(0.18, 0.05, 0.18);
        const mat = new THREE.MeshLambertMaterial({ color: 0xe2e8f0 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x + 0.5, 0.12, y + 0.5);
        mesh.rotation.y = Math.random() * Math.PI;
        corpsesGroup.add(mesh);
        corpseMeshes.set(key, mesh);
      }
    }
    for (const [k, mesh] of corpseMeshes) {
      if (!currentCorpses.has(k)) {
        corpsesGroup.remove(mesh);
        corpseMeshes.delete(k);
      }
    }
  }

  // ── 8. Đồ thị Nghe (Tái sử dụng Geometry tránh GC churn) ──
  const MAX_HEAR_LINES = 120;
  const hearLinePositions = new Float32Array(MAX_HEAR_LINES * 6);
  const hearLineColors = new Float32Array(MAX_HEAR_LINES * 6);
  const hearBufferGeo = new THREE.BufferGeometry();
  hearBufferGeo.setAttribute("position", new THREE.BufferAttribute(hearLinePositions, 3));
  hearBufferGeo.setAttribute("color", new THREE.BufferAttribute(hearLineColors, 3));
  const hearLineMat = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.65 });
  const hearLineSegments = new THREE.LineSegments(hearBufferGeo, hearLineMat);
  lineGroup.add(hearLineSegments);

  function drawHearing(frame) {
    if (!showHear) { hearLineSegments.visible = false; return; }
    hearLineSegments.visible = true;
    const now = performance.now();
    const cs = (frame.creatures || []).filter((c) => c.alive);
    let lineIdx = 0;

    for (let i = 0; i < cs.length; i++) {
      for (let j = i + 1; j < cs.length; j++) {
        if (lineIdx >= MAX_HEAR_LINES) break;
        const a = cs[i], b = cs[j];
        let dx = Math.abs(a.x - b.x), dy = Math.abs(a.y - b.y);
        dx = Math.min(dx, W - dx); dy = Math.min(dy, H - dy);
        const d = Math.max(dx, dy);
        const ra = 2 + (a.tr ? a.tr[TR.sense] : 2);
        const rb = 2 + (b.tr ? b.tr[TR.sense] : 2);
        if (d > ra && d > rb) continue;

        const fl = flashes.find((f) => now - f.t0 < 350 &&
          ((f.a === a.id && f.b.includes(b.id)) || (f.a === b.id && f.b.includes(a.id))));

        const off = lineIdx * 6;
        const entA = bodies.get(a.id), entB = bodies.get(b.id);
        const ax = entA ? entA.currX : a.x + 0.5;
        const ay = (entA ? entA.currY : 0.25) + 0.15;
        const az = entA ? entA.currZ : a.y + 0.5;
        const bx = entB ? entB.currX : b.x + 0.5;
        const by = (entB ? entB.currY : 0.25) + 0.15;
        const bz = entB ? entB.currZ : b.y + 0.5;

        hearLinePositions[off] = ax; hearLinePositions[off + 1] = ay; hearLinePositions[off + 2] = az;
        hearLinePositions[off + 3] = bx; hearLinePositions[off + 4] = by; hearLinePositions[off + 5] = bz;

        const col = fl ? [0.22, 0.74, 0.97] : [0.58, 0.64, 0.72];
        hearLineColors[off] = col[0]; hearLineColors[off + 1] = col[1]; hearLineColors[off + 2] = col[2];
        hearLineColors[off + 3] = col[0]; hearLineColors[off + 4] = col[1]; hearLineColors[off + 5] = col[2];
        lineIdx++;
      }
    }
    hearBufferGeo.setDrawRange(0, lineIdx * 2);
    hearBufferGeo.attributes.position.needsUpdate = true;
    hearBufferGeo.attributes.color.needsUpdate = true;
  }

  // ── 9. Sóng Xung Kích & Hào quang Bí ẩn khi Luật Kích Hoạt (`LAW_FIRED`) ──
  function addLawFiredShockwave(x, y) {
    totalLawTriggers++;
    if (el("law-triggers-count")) el("law-triggers-count").textContent = totalLawTriggers;

    // Vòng sóng xung kích đa lớp
    const ringGeo = new THREE.RingGeometry(0.15, 0.28, 24);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      side: THREE.DoubleSide,
      opacity: 0.95,
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = -Math.PI / 2;
    ringMesh.position.set(x + 0.5, 0.28, y + 0.5);
    shockwaveGroup.add(ringMesh);

    // Vòng halo thứ hai toả lên cao
    const torusGeo = new THREE.TorusGeometry(0.2, 0.03, 8, 20);
    const torusMat = new THREE.MeshBasicMaterial({ color: 0xfde047, transparent: true, opacity: 0.8 });
    const torusMesh = new THREE.Mesh(torusGeo, torusMat);
    torusMesh.rotation.x = Math.PI / 2;
    torusMesh.position.set(x + 0.5, 0.35, y + 0.5);
    shockwaveGroup.add(torusMesh);

    shockwaves.push({ ring: ringMesh, torus: torusMesh, t0: performance.now() });
  }

  // ── 10. Bục Vinh Danh 3 Danh Hiệu ở Pha REVEAL ──
  let podiumsBuilt = false;
  function buildVictoryPodiums(frame) {
    if (podiumsBuilt) return;
    podiumsBuilt = true;

    // 3 Bục đứng trung tâm: Vàng (1), Bạc (2), Đồng (3)
    const configs = [
      { x: W / 2, z: H / 2, h: 0.7, r: 0.8, c: 0xf59e0b, title: "Nhà khoa học" },
      { x: W / 2 - 1.8, z: H / 2, h: 0.45, r: 0.7, c: 0x94a3b8, title: "Kẻ sống sót" },
      { x: W / 2 + 1.8, z: H / 2, h: 0.3, r: 0.65, c: 0xb45309, title: "Người đầu tiên" },
    ];

    for (const p of configs) {
      const cylGeo = new THREE.CylinderGeometry(p.r, p.r, p.h, 24);
      const cylMat = new THREE.MeshLambertMaterial({ color: p.c });
      const mesh = new THREE.Mesh(cylGeo, cylMat);
      mesh.position.set(p.x, p.h / 2 + 0.1, p.z);
      mesh.castShadow = true;
      podiumGroup.add(mesh);
    }

    // Hiển thị Modal Vinh danh
    if (el("reveal-modal")) el("reveal-modal").style.display = "flex";
    if (el("journal-status")) el("journal-status").textContent = "🏆 ĐÃ KHAI MỞ CHÂN LÝ!";

    // Trích xuất sự kiện luật đã lộ từ frame
    const lawsList = el("reveal-laws-list");
    if (lawsList) {
      lawsList.innerHTML = "";
      const publicLaws = (frame.events || [])
        .filter((e) => e.k === "LAW_FIRED" && e.law && e.law !== "?")
        .map((e) => e.law);
      const uniqueLaws = Array.from(new Set(publicLaws));
      if (uniqueLaws.length > 0) {
        uniqueLaws.forEach((l, idx) => {
          const card = document.createElement("div");
          card.className = "law-card";
          card.textContent = `Định luật #${idx + 1}: ${l}`;
          lawsList.appendChild(card);
        });
      } else {
        const card = document.createElement("div");
        card.className = "law-card";
        card.textContent = "Các quy luật vật lý ẩn giấu đã hoàn thành chu kỳ vận hành.";
        lawsList.appendChild(card);
      }
    }
  }

  el("btn-close-reveal")?.addEventListener("click", () => {
    if (el("reveal-modal")) el("reveal-modal").style.display = "none";
  });

  // ── 10.5. Quản Lý Sảnh Setup & Tạo Sinh Vật Trước Khi Vào Map (Setup Lobby) ──
  let myCreatureId = null;
  try { myCreatureId = localStorage.getItem("gz_my_creature_id"); } catch (_) {}
  let myCreatureName = "Thỏ Đồng Cỏ";
  try { myCreatureName = localStorage.getItem("gz_my_creature_name") || "Thỏ Đồng Cỏ"; } catch (_) {}

  let setupDomain = "CAN";
  let setupDiet = "HERBIVORE";
  let setupStrategy = "STRAT_R";
  let setupScientificName = "Sylvilagus Campestris";
  let setupNicheSummary = "Loài gặm nhấm bầy đàn tầng thấp, sinh sản cực nhanh.";
  let setupBehaviorLore = "Gặm cỏ dại và quả mọng trên mặt đất, liên tục di chuyển theo bầy để phân tán nguy cơ bị săn.";
  let setupTraits = [1, 0, 1, 4, 3, 3]; // Brain, Attack, Armor, Speed, Sense, Stomach
  let pointsBudget = 16;
  let maxTraitVal = 7;
  let setupCreatureDesc = "";
  try { setupCreatureDesc = localStorage.getItem("gz_my_creature_desc") || ""; } catch (_) {}
  let setupKingdom = "FAUNA";
  const setupFeatures = new Set(["CAMOUFLAGE"]);
  let customGeminiKey = "";
  try { customGeminiKey = localStorage.getItem("gz_gemini_key") || ""; } catch (_) {}

  const ALL_FEATURES = [
    { id: "WEB_FEET", name: "Chân màng bơi", icon: "🏊", desc: "Tăng 50% tốc độ trong nước" },
    { id: "HARD_SHELL", name: "Vảy sừng cứng", icon: "🛡️", desc: "Giảm 30% sát thương nhận vào" },
    { id: "FANGS", name: "Nanh kiếm săn mồi", icon: "🦷", desc: "Tăng uy lực tấn công va chạm" },
    { id: "CAMOUFLAGE", name: "Da ngụy trang", icon: "🦎", desc: "Khó bị phát hiện trong bụi rậm" },
    { id: "CHEEK_POUCH", name: "Túi má dự trữ", icon: "🎒", desc: "Dung lượng chứa năng lượng phụ" },
    { id: "GLIDER_FLAP", name: "Màng lượn trên không", icon: "🪽", desc: "Di chuyển lướt qua mỏm đá" },
  ];

  // Ma Trận 27 Archetypes Sinh Thái (Domain x Diet x Strategy)
  const CLIENT_ARCHETYPES_27 = {
    "CAN_HERBIVORE_STRAT_R": { name: "Thỏ Đồng Cỏ", latin: "Sylvilagus Campestris", niche: "Loài gặm nhấm bầy đàn tầng thấp, sinh sản cực nhanh.", lore: "Gặm cỏ dại và quả mọng trên mặt đất, liên tục di chuyển theo bầy để phân tán nguy cơ bị săn.", traits: [1, 0, 1, 4, 3, 3] },
    "CAN_HERBIVORE_STRAT_K": { name: "Tê Giác Thiết Giáp", latin: "Rhinoceros Titanus", niche: "Động vật ăn thực vật khổng lồ đơn độc, giáp dày sừng lớn.", lore: "Thong thả gặm cây bụi cứng, lớp da sừng bảo vệ nó khỏi hầu hết các đòn tấn công vật lý.", traits: [1, 2, 4, 1, 1, 3] },
    "CAN_HERBIVORE_STRAT_SOCIAL": { name: "Linh Dương Du Mục", latin: "Antilocapra Socialis", niche: "Đàn ăn cỏ cơ động, cảnh báo thính giác tương trợ.", lore: "Di cư liên tục qua các thảm cỏ rộng, cá thể đầu đàn dùng tiếng kêu để báo động khi có thú dữ.", traits: [2, 1, 1, 3, 3, 2] },
    "CAN_CARNIVORE_STRAT_R": { name: "Cáo Đỏ Bầy Đàn", latin: "Vulpes Gregaria", niche: "Kẻ săn mồi nhỏ bé số lượng đông, áp đảo con mồi bằng tốc độ.", lore: "Săn chuột và côn trùng theo nhóm nhỏ, luân phiên rượt đuổi để con mồi kiệt sức.", traits: [1, 3, 0, 4, 3, 1] },
    "CAN_CARNIVORE_STRAT_K": { name: "Hổ Nanh Kiếm", latin: "Smilodon Solitarius", niche: "Thợ săn thượng tầng uy lực, đơn độc kiểm soát lãnh thổ.", lore: "Phục kích từ trong bụi rậm và tung đòn kết liễu bằng răng nanh uy lực, không chia sẻ thức ăn.", traits: [1, 5, 2, 2, 1, 1] },
    "CAN_CARNIVORE_STRAT_SOCIAL": { name: "Lang Tộc Đồng Cỏ", latin: "Canis Pratorum", niche: "Bầy sói săn mồi kỷ luật, vây hãm và hạ gục con mồi lớn.", lore: "Giao tiếp bằng tiếng hú và phối hợp tác chiến chặt chẽ, chia sẻ chiến lợi phẩm sau khi hạ gục mục tiêu.", traits: [2, 3, 1, 3, 2, 1] },
    "CAN_OMNIVORE_STRAT_R": { name: "Chuột Chù Cơ Hội", latin: "Sorex Opportunus", niche: "Ăn tạp cơ hội, tận dụng mọi nguồn hạt quả và xác vụn.", lore: "Lùng sục mọi ngóc ngách mặt đất để tìm thức ăn, thích nghi cực tốt với mọi điều kiện biến đổi.", traits: [1, 1, 1, 3, 3, 3] },
    "CAN_OMNIVORE_STRAT_K": { name: "Hùng Tinh Rừng Già", latin: "Ursus Robur", niche: "Động vật ăn tạp khổng lồ, một mình thống trị khu rừng.", lore: "Ăn từ củ rễ, mật ong đến săn thú nhỏ, thể lực dồi dào và bảo vệ nghiêm ngặt khu vực hang trú ngụ.", traits: [2, 3, 3, 1, 1, 2] },
    "CAN_OMNIVORE_STRAT_SOCIAL": { name: "Linh Trưởng Thảo Nguyên", latin: "Simia Sapiens", niche: "Bầy đàn thông minh, hợp tác chia sẻ thức ăn và chế ngự tự nhiên.", lore: "Trí tuệ cao, biết dùng công cụ thô sơ và chia sẻ tài nguyên quả chín cũng như thịt săn được trong đàn.", traits: [4, 1, 1, 2, 2, 2] },

    "NUOC_HERBIVORE_STRAT_R": { name: "Thủy Điệp Đầm Nông", latin: "Hydrolepis Minuta", niche: "Đàn cá nhỏ gặm rêu tảo, bơi thành dải sóng ảo ảnh.", lore: "Bơi lội sát đáy đầm lầy để gặm tảo lam, phản ứng bầy đàn đồng loạt khi nước gợn sóng.", traits: [1, 0, 1, 4, 3, 3] },
    "NUOC_HERBIVORE_STRAT_K": { name: "Hải Ngưu Biển Sâu", latin: "Sirenia Gigantea", niche: "Thủy quái ăn thực vật đáy, lớp da dày chống va đập.", lore: "Thong dong hấp thu rong biển tại các rạn ngầm, hầu như không có kẻ thù tự nhiên nào dám tấn công.", traits: [1, 1, 4, 1, 1, 4] },
    "NUOC_HERBIVORE_STRAT_SOCIAL": { name: "Kình Ngư Thảo Bộc", latin: "Delphinus Herbivorus", niche: "Bầy động vật biển ăn tảo, di chuyển bảo bọc nhau.", lore: "Bơi theo đội hình hình chữ V để giảm sức cản dòng nước, che chở con non ở tâm bầy.", traits: [2, 1, 2, 3, 2, 2] },
    "NUOC_CARNIVORE_STRAT_R": { name: "Cá Răng Đao", latin: "Serrasalmus Vorax", niche: "Đàn cá săn mồi hung tợn, xé toạc con mồi tức thì.", lore: "Đánh hơi thấy máu là lao vào cắn xé cuồng loạn, số lượng áp đảo khiến con mồi không kịp trở tay.", traits: [1, 4, 0, 4, 2, 1] },
    "NUOC_CARNIVORE_STRAT_K": { name: "Hải Quái Nanh Nhọn", latin: "Leviathan Monodon", niche: "Sát thủ biển sâu cô độc, lực cắn nghiền nát vỏ giáp.", lore: "Ẩn mình dưới đáy vực tối tăm và phóng lên đớp gọn con mồi bằng cú cắn kinh hoàng.", traits: [1, 5, 2, 2, 1, 1] },
    "NUOC_CARNIVORE_STRAT_SOCIAL": { name: "Kình Sát Hải Đội", latin: "Orcinus Socialis", niche: "Bầy cá voi săn mồi theo nhóm, dồn ép con mồi bằng bọt khí.", lore: "Phối hợp quẫy đuôi tạo sóng làm choáng con mồi, giao tiếp phức tạp bằng sóng siêu âm định vị.", traits: [2, 4, 1, 3, 1, 1] },
    "NUOC_OMNIVORE_STRAT_R": { name: "Tôm Giáp Dọn Bể", latin: "Caridea Vulgata", niche: "Thủy sinh dọn vụn đáy nước, xử lý mọi phế phẩm hữu cơ.", lore: "Chân kìm linh hoạt lọc xác vụn và mầm rêu trên nền cát, sinh sản theo từng đợt trăng tròn.", traits: [1, 1, 1, 3, 3, 3] },
    "NUOC_OMNIVORE_STRAT_K": { name: "Bạch Tuộc Vực Thẳm", latin: "Octopus Abyssi", niche: "Kẻ ăn tạp bí ẩn trí tuệ cao, săn mồi và ăn xác ngầm.", lore: "Đổi màu da hòa nhập hoàn toàn vào san hô, dùng xúc tu khéo léo mở các lớp vỏ cứng tìm thức ăn.", traits: [3, 2, 2, 2, 2, 1] },
    "NUOC_OMNIVORE_STRAT_SOCIAL": { name: "Hải Cẩu Bầy Đảo Đá", latin: "Phoca Gregaria", niche: "Đàn thú lưỡng cư ăn cá và rong biển, chia sẻ điểm sưởi nắng.", lore: "Bơi lội kiếm ăn theo nhóm ven bờ và cùng leo lên các tảng đá phơi nắng, hỗ trợ canh gác cá mập.", traits: [2, 2, 2, 2, 2, 2] },

    "TROI_HERBIVORE_STRAT_R": { name: "Tước Điểu Hạt Cỏ", latin: "Passer Granivora", niche: "Chim nhỏ ăn hạt theo đàn lớn, phát tán hạt giống khắp nơi.", lore: "Sà xuống các vạt cỏ chín mọng rồi bay vút lên khi có động tĩnh, tiếng đập cánh rào rào xua tan mối nguy.", traits: [1, 0, 0, 5, 3, 3] },
    "TROI_HERBIVORE_STRAT_K": { name: "Tiên Hạc Thượng Tầng", latin: "Grus Titanica", niche: "Sải cánh khổng lồ lướt gió vô tận, ăn quả ngọt trên tán rừng.", lore: "Bay lượn ở độ cao cực lớn tận dụng luồng nhiệt, chỉ đáp xuống các ngọn cây cổ thụ để kiếm quả chín.", traits: [2, 1, 2, 3, 2, 2] },
    "TROI_HERBIVORE_STRAT_SOCIAL": { name: "Vẹt Rừng Giao Cảm", latin: "Psittacula Harmonica", niche: "Đàn chim ăn trái thông minh, hót vang cảnh báo thời tiết bão.", lore: "Sống thành cặp và bầy nhỏ bền vững, truyền dạy nhau lộ trình tìm cây ăn trái theo mùa khí hậu.", traits: [3, 1, 0, 3, 3, 2] },
    "TROI_CARNIVORE_STRAT_R": { name: "Dơi Đêm Săn Mồi", latin: "Microchiroptera Velox", niche: "Đàn thú bay săn mồi đêm, lùng sục sinh vật nhỏ và côn trùng.", lore: "Tung cánh hàng loạt lúc hoàng hôn, định vị hồi âm siêu nhạy giúp tóm gọn mục tiêu trong bóng tối.", traits: [1, 3, 0, 4, 3, 1] },
    "TROI_CARNIVORE_STRAT_K": { name: "Kim Ưng Đỉnh Núi", latin: "Aquila Excelsa", niche: "Thợ săn bầu trời tối thượng, bổ nhào đoạt mạng từ tầng mây.", lore: "Thị giác tinh tường phát hiện con mồi từ độ cao hàng trăm mét, bổ nhào như sấm sét với móng vuốt thép.", traits: [1, 5, 1, 3, 2, 0] },
    "TROI_CARNIVORE_STRAT_SOCIAL": { name: "Ưng Săn Bầy Hợp Lực", latin: "Falco Sociabilis", niche: "Biệt đội chim săn phối hợp ép góc và lùa con mồi.", lore: "Phân công cá thể bay cao quan sát và cá thể sà thấp rượt đuổi, ép con mồi chạy thẳng vào bẫy mai phục.", traits: [2, 3, 1, 4, 1, 1] },
    "TROI_OMNIVORE_STRAT_R": { name: "Hải Âu Duyên Hải", latin: "Larus Vagrans", niche: "Chim cơ hội ven biển, ăn xác cá trôi dạt và hạt quả.", lore: "Bay dập dờn theo các ngọn sóng nhặt nhạnh thức ăn thừa, tranh giành quyết liệt nhưng gắn kết theo bầy.", traits: [1, 1, 0, 4, 3, 3] },
    "TROI_OMNIVORE_STRAT_K": { name: "Quạ Thần Rừng Cổ", latin: "Corvus Arcanus", niche: "Chim ăn tạp tuổi thọ cao, hiểu rõ quy luật địa hình và bão.", lore: "Trí nhớ siêu phàm ghi nhớ vị trí cất giấu thức ăn, sống cô độc và quan sát diễn biến toàn bộ hệ sinh thái.", traits: [4, 1, 1, 2, 3, 1] },
    "TROI_OMNIVORE_STRAT_SOCIAL": { name: "Bồ Nông Hợp Sức", latin: "Pelecanus Cooperator", niche: "Đàn chim bắt cá và gắp quả, chia sẻ vị trí luồng gió.", lore: "Quây thành vòng cung trên mặt nước để dồn cá vào giữa, chiếc túi cổ họng rộng lớn chia sẻ thức ăn cho đồng loại.", traits: [2, 2, 1, 3, 2, 2] },
  };

  function getCurrentArchetype() {
    const key = `${setupDomain}_${setupDiet}_${setupStrategy}`;
    return CLIENT_ARCHETYPES_27[key] || CLIENT_ARCHETYPES_27["CAN_HERBIVORE_STRAT_R"];
  }

  function getPointsUsed() {
    return setupTraits.reduce((acc, v) => acc + v, 0);
  }

  function showFloatingWarning(text) {
    if (typeof document === "undefined" || typeof document.createElement !== "function") return;
    let toast = el("floating-warning-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "floating-warning-toast";
      toast.style.cssText = "position: fixed; top: 60px; left: 50%; transform: translateX(-50%); z-index: 99; background: rgba(239, 68, 68, 0.9); color: #ffffff; padding: 6px 16px; border-radius: 6px; font-size: .78rem; font-weight: 700; box-shadow: 0 4px 14px rgba(0,0,0,0.5); pointer-events: none; transition: opacity .3s;";
      document.body.appendChild(toast);
    }
    toast.textContent = text;
    toast.style.opacity = "1";
    toast.style.display = "block";
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => { toast.style.display = "none"; }, 300);
    }, 2200);
  }

  function isMyOffspring(id, creatures) {
    if (!myCreatureId) return false;
    if (id === myCreatureId) return true;
    const c = (creatures || []).find((x) => x.id === id);
    if (!c) return false;
    if (c.parent_id === myCreatureId) return true;
    return false;
  }

  function renderSetupTraitsUI() {
    if (typeof document === "undefined" || typeof document.createElement !== "function") return;
    const container = el("setup-traits-container");
    if (!container) return;
    container.innerHTML = "";

    const used = getPointsUsed();
    const left = pointsBudget - used;
    if (el("setup-points-left")) {
      el("setup-points-left").textContent = left;
      el("setup-points-left").style.color = left === 0 ? "#4ade80" : (left > 0 ? "#facc15" : "#ef4444");
    }
    if (el("setup-points-total")) {
      el("setup-points-total").textContent = pointsBudget;
    }

    const TRAIT_NAMES = [
      { label: "Trí tuệ", icon: "🧠", desc: "Dung lượng bộ nhớ Sổ Luật & khả năng suy luận" },
      { label: "Tấn công", icon: "⚔️", desc: "Sát thương và uy lực va chạm" },
      { label: "Giáp", icon: "🛡️", desc: "Kháng cự sát thương vật lý" },
      { label: "Tốc độ", icon: "⚡", desc: "Tốc độ di chuyển & thời gian hồi bước" },
      { label: "Giác quan", icon: "👁️", desc: "Bán kính sương mù Fog of War & nghe" },
      { label: "Dạ dày", icon: "🍖", desc: "Dung lượng chứa năng lượng tối đa" },
    ];

    TRAIT_NAMES.forEach((t, i) => {
      const val = setupTraits[i];
      const row = document.createElement("div");
      row.style.cssText = "display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.75); border: 1px solid #1e293b; border-radius: 6px; padding: 5px 10px;";
      row.innerHTML = `
        <div style="flex: 1.2;">
          <div style="font-size: .72rem; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 4px;">
            <span>${t.icon}</span> <span>${t.label}</span>
          </div>
          <div style="font-size: .6rem; color: #64748b;">${t.desc}</div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <button class="btn-trait-step btn-minus" data-idx="${i}" style="width: 22px; height: 22px; border-radius: 4px; border: 1px solid #334155; background: #1e293b; color: #cbd5e1; cursor: pointer; font-weight: 800;" ${val <= 0 ? 'disabled' : ''}>-</button>
          <span style="font-size: .85rem; font-weight: 800; color: ${val >= 6 ? '#f43f5e' : (val >= 4 ? '#facc15' : '#38bdf8')}; min-width: 14px; text-align: center; font-family: ui-monospace, monospace;">${val}</span>
          <button class="btn-trait-step btn-plus" data-idx="${i}" style="width: 22px; height: 22px; border-radius: 4px; border: 1px solid #334155; background: #1e293b; color: #cbd5e1; cursor: pointer; font-weight: 800;" ${(val >= maxTraitVal || left <= 0) ? 'disabled' : ''}>+</button>
        </div>
      `;
      container.appendChild(row);
    });

    if (typeof container.querySelectorAll === "function") {
      container.querySelectorAll(".btn-minus").forEach((btn) => {
        btn.addEventListener("click", () => {
          const idx = parseInt(btn.getAttribute("data-idx"), 10);
          if (setupTraits[idx] > 0) {
            setupTraits[idx]--;
            renderSetupTraitsUI();
            updateLivePreview();
          }
        });
      });

      container.querySelectorAll(".btn-plus").forEach((btn) => {
        btn.addEventListener("click", () => {
          const idx = parseInt(btn.getAttribute("data-idx"), 10);
          if (setupTraits[idx] < maxTraitVal && getPointsUsed() < pointsBudget) {
            setupTraits[idx]++;
            renderSetupTraitsUI();
            updateLivePreview();
          }
        });
      });
    }
  }

  function renderSetupFeaturesUI() {
    if (typeof document === "undefined" || typeof document.createElement !== "function") return;
    const container = el("setup-features-container");
    if (!container) return;
    container.innerHTML = "";
    ALL_FEATURES.forEach((f) => {
      const isChecked = setupFeatures.has(f.id);
      const badge = document.createElement("div");
      badge.style.cssText = `padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: .7rem; font-weight: 600; display: flex; align-items: center; gap: 4px; border: 1px solid ${isChecked ? '#38bdf8' : '#334155'}; background: ${isChecked ? 'rgba(56, 189, 248, 0.2)' : 'rgba(15, 23, 42, 0.8)'}; color: ${isChecked ? '#f8fafc' : '#94a3b8'}; transition: all .15s;`;
      badge.innerHTML = `<span>${f.icon}</span> <span>${f.name}</span>`;
      badge.addEventListener("click", () => {
        if (setupFeatures.has(f.id)) {
          setupFeatures.delete(f.id);
        } else {
          setupFeatures.add(f.id);
        }
        renderSetupFeaturesUI();
        updateLivePreview();
      });
      container.appendChild(badge);
    });
  }

  function applyCurrentArchetype(forceUpdateTraits = false) {
    const arch = getCurrentArchetype();
    const domCode = setupDomain;
    const dietCode = setupDiet === "HERBIVORE" ? "HERB" : (setupDiet === "CARNIVORE" ? "CARN" : "OMNI");
    const stratCode = setupStrategy === "STRAT_R" ? "r" : (setupStrategy === "STRAT_K" ? "K" : "Pack");

    if (el("setup-archetype-code")) {
      el("setup-archetype-code").textContent = `${domCode} · ${dietCode} · ${stratCode}`;
    }
    if (el("setup-archetype-title")) el("setup-archetype-title").textContent = arch.name;
    if (el("setup-archetype-latin")) el("setup-archetype-latin").textContent = `(${arch.latin})`;
    if (el("setup-archetype-niche")) el("setup-archetype-niche").textContent = arch.niche;

    if (forceUpdateTraits) {
      setupTraits = [...arch.traits];
      renderSetupTraitsUI();
    }

    // Cập nhật tên đề xuất
    const nameInput = el("setup-creature-name");
    if (nameInput) {
      nameInput.value = arch.name;
    }
    setupScientificName = arch.latin;
    setupNicheSummary = arch.niche;
    setupBehaviorLore = arch.lore;

    updateLivePreview();
  }

  function updateLivePreview() {
    const nameInput = el("setup-creature-name");
    const name = (nameInput && nameInput.value.trim()) ? nameInput.value.trim() : "Sinh vật của bạn";
    if (el("preview-name")) el("preview-name").textContent = name;
    if (el("preview-latin")) el("preview-latin").textContent = setupScientificName || "";
    if (el("preview-niche")) el("preview-niche").textContent = setupNicheSummary || "";
    if (el("preview-lore")) el("preview-lore").textContent = setupBehaviorLore || "";

    const icon = setupDomain === "NUOC" ? "🌊" : (setupDomain === "TROI" ? "🦅" : "🌿");
    const domainText = setupDomain === "NUOC" ? "DƯỚI NƯỚC" : (setupDomain === "TROI" ? "TRÊN KHÔNG" : "TRÊN CẠN");
    const domainColor = setupDomain === "NUOC" ? "#38bdf8" : (setupDomain === "TROI" ? "#facc15" : "#4ade80");

    if (el("preview-avatar")) el("preview-avatar").textContent = icon;
    if (el("preview-domain-tag")) {
      el("preview-domain-tag").textContent = domainText;
      el("preview-domain-tag").style.color = domainColor;
      el("preview-domain-tag").style.background = `${domainColor}26`;
    }

    const dietText = setupDiet === "HERBIVORE" ? "THỰC VẬT" : (setupDiet === "CARNIVORE" ? "ĂN THỊT" : "ĂN TẠP / XÁC");
    const dietColor = setupDiet === "HERBIVORE" ? "#4ade80" : (setupDiet === "CARNIVORE" ? "#f87171" : "#fbbf24");
    if (el("preview-diet-tag")) {
      el("preview-diet-tag").textContent = dietText;
      el("preview-diet-tag").style.color = dietColor;
      el("preview-diet-tag").style.background = `${dietColor}26`;
    }

    const stratText = setupStrategy === "STRAT_R" ? "CHIẾN LƯỢC r" : (setupStrategy === "STRAT_K" ? "CHIẾN LƯỢC K" : "XÃ HỘI (PACK)");
    const stratColor = setupStrategy === "STRAT_R" ? "#38bdf8" : (setupStrategy === "STRAT_K" ? "#c084fc" : "#facc15");
    if (el("preview-strat-tag")) {
      el("preview-strat-tag").textContent = stratText;
      el("preview-strat-tag").style.color = stratColor;
      el("preview-strat-tag").style.background = `${stratColor}26`;
    }

    const stomach = setupTraits[5];
    const sense = setupTraits[4];
    const speed = setupTraits[3];
    if (el("preview-energy")) el("preview-energy").textContent = `${40 + stomach * 10} E`;
    if (el("preview-vision")) el("preview-vision").textContent = `${3 + sense} ô`;
    if (el("preview-speed")) el("preview-speed").textContent = `${speed} / 5`;

    const featList = el("preview-features-list");
    if (featList) {
      featList.innerHTML = "";
      if (setupFeatures.size === 0) {
        featList.innerHTML = '<span style="font-size: .65rem; color: #64748b; font-style: italic;">Chưa chọn đặc tính</span>';
      } else if (typeof document !== "undefined" && typeof document.createElement === "function") {
        setupFeatures.forEach((fid) => {
          const f = ALL_FEATURES.find((x) => x.id === fid);
          if (f) {
            const badge = document.createElement("span");
            badge.style.cssText = "font-size: .65rem; padding: 2px 6px; border-radius: 4px; background: rgba(56, 189, 248, 0.12); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.25);";
            badge.textContent = `${f.icon} ${f.name}`;
            featList.appendChild(badge);
          }
        });
      }
    }

    const descInput = el("setup-creature-desc");
    const descCounter = el("setup-desc-counter");
    if (descInput && descCounter) {
      const len = descInput.value.length;
      descCounter.textContent = `${len} / 500`;
      descCounter.style.color = len >= 480 ? "#f87171" : (len > 0 ? "#38bdf8" : "#94a3b8");
    }
    const userDescBox = el("preview-user-desc-container");
    const userDescText = el("preview-user-desc-content");
    if (userDescBox && userDescText) {
      const descVal = descInput ? descInput.value.trim() : "";
      if (descVal) {
        userDescBox.style.display = "block";
        userDescText.textContent = `"${descVal}"`;
      } else {
        userDescBox.style.display = "none";
      }
    }
  }

  async function requestConceptAnd3D() {
    const btn = el("btn-create-concept-3d");
    const iconSpan = el("icon-create-concept");
    const textSpan = el("text-create-concept");
    const statusDiv = el("status-create-concept");
    const conceptBox = el("preview-concept-box");
    const conceptImg = el("preview-concept-image");
    const nameInput = el("setup-creature-name");
    const descInput = el("setup-creature-desc");

    const cName = (nameInput && nameInput.value.trim()) ? nameInput.value.trim() : myCreatureName;
    const cDesc = (descInput && descInput.value.trim()) ? descInput.value.trim() : "";

    if (btn) btn.disabled = true;
    if (iconSpan) iconSpan.textContent = "⏳";
    if (textSpan) textSpan.textContent = "Đang gửi prompt đến AGY AI...";
    if (statusDiv) {
      statusDiv.textContent = "1/2: AGY đang phân tích thuộc tính & vẽ ảnh concept...";
      statusDiv.style.color = "#38bdf8";
    }

    try {
      const payload = {
        name: cName,
        latin: setupScientificName,
        domain: setupDomain,
        diet: setupDiet,
        strategy: setupStrategy,
        traits: setupTraits,
        features: Array.from(setupFeatures),
        description: cDesc,
        kingdom: setupKingdom,
        api_key: customGeminiKey || undefined,
      };

      const res = await fetch("/v1/spectate/generate_concept", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Server status ${res.status}`);
      }

      const data = await res.json();
      if (data && data.image_url) {
        if (conceptBox && conceptImg) {
          conceptImg.src = data.image_url + "?t=" + Date.now();
          conceptBox.style.display = "block";
        }
      }

      if (data && data.ok) {
        if (statusDiv) {
          statusDiv.textContent = `✓ Đã tạo xong Concept & Dựng 3D Blender (8 Animations: Idle, Alert, Walk, Run, Attack, Hurt, Eat, Death)!`;
          statusDiv.style.color = "#4ade80";
        }
        showFloatingWarning(`🎨 Concept Art & 3D Model 8-Animation của ${cName} đã sẵn sàng!`);
      }
    } catch (err) {
      console.warn("Concept generation failed:", err);
      if (statusDiv) {
        statusDiv.textContent = "Lỗi khi tạo ảnh/3D: " + err.message;
        statusDiv.style.color = "#f87171";
      }
    } finally {
      if (btn) btn.disabled = false;
      if (iconSpan) iconSpan.textContent = "🎨";
      if (textSpan) textSpan.textContent = "Vẽ Lại Concept & Dựng 3D (Blender)";
    }
  }

  let geminiNamingDebounceTimer = null;
  function triggerAutoGeminiNaming() {
    if (typeof setTimeout === "undefined") return;
    if (geminiNamingDebounceTimer && typeof clearTimeout !== "undefined") clearTimeout(geminiNamingDebounceTimer);
    geminiNamingDebounceTimer = setTimeout(() => {
      requestGeminiNaming(false);
    }, 280);
  }

  async function requestGeminiNaming(isManualClick = true) {
    const btn = el("btn-gemini-name");
    const iconSpan = el("gemini-name-icon");
    const textSpan = el("gemini-name-text");
    const statusInd = el("naming-status-indicator");
    if (iconSpan) iconSpan.textContent = "⏳";
    if (textSpan) textSpan.textContent = isManualClick ? "Đang suy luận..." : "Đang tải tên AI...";
    if (statusInd) statusInd.textContent = "✨ Đang sinh tên sinh thái bằng Gemini AI (Flash-Lite)...";
    if (btn && isManualClick) btn.disabled = true;

    try {
      const payload = {
        domain: setupDomain,
        diet: setupDiet,
        strategy: setupStrategy,
        traits: setupTraits,
        features: Array.from(setupFeatures),
        api_key: customGeminiKey || null,
      };
      if (typeof fetch === "undefined") return;
      const res = await fetch("/v1/spectate/generate_name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res && res.ok) {
        const data = await res.json();
        if (data && data.name) {
          if (el("setup-creature-name")) el("setup-creature-name").value = data.name;
          setupScientificName = data.scientific_name || setupScientificName;
          setupNicheSummary = data.niche_summary || setupNicheSummary;
          setupBehaviorLore = data.behavior_lore || setupBehaviorLore;
          updateLivePreview();
          const sourceTag = data.source === "gemini" ? "Gemini AI ✨" : "Ma Trận Sinh Thái 🌿";
          if (statusInd) statusInd.textContent = `✓ Đã tự động cập nhật từ ${sourceTag}: ${data.name} (${setupScientificName})`;
          if (typeof setTimeout !== "undefined") {
            setTimeout(() => { if (statusInd) statusInd.textContent = ""; }, 3000);
          }
          if (isManualClick) {
            showFloatingWarning(`Đã sinh tên: ${data.name} (${setupScientificName}) [${sourceTag}]`);
          }
        }
      }
    } catch (_) {
      // Fallback cục bộ tức thời
      const arch = getCurrentArchetype();
      if (el("setup-creature-name")) el("setup-creature-name").value = arch.name;
      setupScientificName = arch.latin;
      setupNicheSummary = arch.niche;
      setupBehaviorLore = arch.lore;
      updateLivePreview();
      if (statusInd) statusInd.textContent = `✓ Đã áp dụng Archetype: ${arch.name}`;
      if (typeof setTimeout !== "undefined") {
        setTimeout(() => { if (statusInd) statusInd.textContent = ""; }, 2500);
      }
      if (isManualClick) {
        showFloatingWarning(`Đã áp dụng tên sinh thái: ${arch.name} (${arch.latin})`);
      }
    } finally {
      if (iconSpan) iconSpan.textContent = "🎲";
      if (textSpan) textSpan.textContent = "Đổi tên khác (Gemini AI)";
      if (btn) btn.disabled = false;
    }
  }

  function renderTabLawsUI() {
    if (typeof document === "undefined" || typeof document.createElement !== "function") return;
    const lawsList = el("tab-laws-list");
    if (!lawsList) return;
    lawsList.innerHTML = "";

    const displayLaws = [
      {
        text: "KHI uống nước VÀ đang đứng trên ô nước THÌ chịu sát thương (mức vừa, tức thì)",
        summary: "Uống nước mất máu",
        icon: "⚡",
        conf: 4,
        status: "Đã kiểm chứng thực địa",
        source: "Trải nghiệm cá thể khi thử nghiệm ô nước",
      },
      {
        text: "KHI ăn quả mọng VÀ đang là ban ngày THÌ hồi máu (mức vừa)",
        summary: "Ăn quả đỏ ban ngày hồi phục sinh lực",
        icon: "🍎",
        conf: 5,
        status: "Đã kiểm chứng thực địa",
        source: "Hấp thu tài nguyên thực vật",
      },
      {
        text: "KHI bước vào ô lửa THÌ chịu sát thương (mức nặng)",
        summary: "Lửa thiêu đốt sinh lực",
        icon: "🔥",
        conf: 5,
        status: "Định luật vật lý môi trường",
        source: "Phản xạ sinh tồn",
      },
      {
        text: "KHI năng lượng tụt dưới 25% THÌ tăng tốc độ di chuyển",
        summary: "Bản năng sinh tồn khi kiệt sức",
        icon: "🏃‍♂️",
        conf: 3,
        status: "Đang theo dõi kiểm chứng",
        source: "Phản ứng tự nhiên",
      },
      {
        text: "KHI bão mưa bùng phát THÌ tăng tiêu hao năng lượng di chuyển",
        summary: "Thời tiết khắc nghiệt cản trở",
        icon: "🌧️",
        conf: 4,
        status: "Đã ghi nhận chu kỳ khí hậu",
        source: "Quan trắc khí hậu",
      }
    ];

    if (el("tab-laws-count")) el("tab-laws-count").textContent = `${displayLaws.length} quy luật`;

    displayLaws.forEach((l) => {
      const card = document.createElement("div");
      card.style.cssText = "background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 10px 14px; display: flex; flex-direction: column; gap: 6px;";
      const stars = "★".repeat(l.conf || 3) + "☆".repeat(5 - (l.conf || 3));
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
          <div style="font-size: .82rem; font-weight: 700; color: #fef08a; display: flex; align-items: center; gap: 6px;">
            <span>${l.icon}</span>
            <span>${l.summary}</span>
          </div>
          <span style="font-size: .7rem; color: #facc15; font-weight: 700;">${stars}</span>
        </div>
        <div style="font-size: .72rem; color: #e2e8f0; font-family: ui-monospace, Menlo, monospace; background: rgba(0,0,0,0.35); padding: 5px 8px; border-radius: 4px; border-left: 2px solid #f59e0b;">
          ${l.text}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: .65rem; color: #94a3b8; margin-top: 2px;">
          <span>Nguồn: <b>${l.source}</b></span>
          <span style="color: #4ade80; background: rgba(74, 222, 128, 0.12); padding: 1px 6px; border-radius: 3px;">${l.status}</span>
        </div>
      `;
      lawsList.appendChild(card);
    });
  }

  function spawnAndEnterWorld() {
    const nameInput = el("setup-creature-name");
    myCreatureName = (nameInput && nameInput.value.trim()) ? nameInput.value.trim() : "Sinh vật của bạn";
    try {
      localStorage.setItem("gz_my_creature_name", myCreatureName);
      localStorage.setItem("gz_my_creature_latin", setupScientificName);
      localStorage.setItem("gz_my_creature_diet", setupDiet);
      localStorage.setItem("gz_my_creature_strategy", setupStrategy);
    } catch (_) {}

    let chosen = null;
    const creatures = latestFrame && latestFrame.creatures ? latestFrame.creatures : [];
    const alive = creatures.filter((c) => c.alive);

    if (setupDomain === "NUOC") {
      chosen = alive.find((c) => c.id.startsWith("W") || getDomain(c) === "NUOC");
    } else if (setupDomain === "CAN") {
      chosen = alive.find((c) => c.id.startsWith("L") || getDomain(c) === "CAN");
    } else if (setupDomain === "TROI") {
      chosen = alive.find((c) => c.id.startsWith("A") || getDomain(c) === "TROI");
    }

    if (!chosen && alive.length > 0) chosen = alive[0];
    if (chosen) {
      myCreatureId = chosen.id;
      try { localStorage.setItem("gz_my_creature_id", myCreatureId); } catch (_) {}
    }

    closeSetupLobby();

    if (myCreatureId) {
      selectCreature(myCreatureId);
      setCameraPreset("FOLLOW");
      if (!enableFogOfWar) toggleFogOfWar();
      showFloatingWarning(`🚀 Đã khởi sinh: ${myCreatureName} (${myCreatureId})! Góc nhìn thứ 3 bám đuôi đã kích hoạt.`);
    } else {
      setCameraPreset("FOLLOW");
      if (!enableFogOfWar) toggleFogOfWar();
    }
  }

  function openSetupLobby() {
    const lobby = el("creature-setup-lobby") || el("creature-dossier-modal");
    if (lobby) {
      lobby.style.display = "flex";
      renderSetupTraitsUI();
      renderSetupFeaturesUI();
      applyCurrentArchetype(false);
      triggerAutoGeminiNaming();
      renderTabLawsUI();
    }
  }

  function closeSetupLobby() {
    const lobby = el("creature-setup-lobby") || el("creature-dossier-modal");
    if (lobby) lobby.style.display = "none";
  }

  function toggleSetupLobby() {
    const lobby = el("creature-setup-lobby") || el("creature-dossier-modal");
    if (lobby && lobby.style.display !== "none") {
      closeSetupLobby();
    } else {
      openSetupLobby();
    }
  }

  // ── 1. Tiêu Chí Domain Handlers (Tự Động Sinh Tên Sinh Thái AI) ──
  ["can", "nuoc", "troi"].forEach((domKey) => {
    el(`domain-opt-${domKey}`)?.addEventListener("click", () => {
      setupDomain = domKey.toUpperCase();
      ["can", "nuoc", "troi"].forEach((k) => {
        const c = el(`domain-opt-${k}`);
        if (c) {
          c.classList.toggle("active", k === domKey);
          c.style.borderColor = k === domKey ? "#38bdf8" : "#334155";
          c.style.background = k === domKey ? "rgba(56, 189, 248, 0.15)" : "rgba(15, 23, 42, 0.8)";
        }
      });
      applyCurrentArchetype(true);
      triggerAutoGeminiNaming();
    });
  });

  // ── 2. Tiêu Chí Diet Handlers (Tự Động Sinh Tên Sinh Thái AI) ──
  ["herbivore", "carnivore", "omnivore"].forEach((dietKey) => {
    el(`diet-opt-${dietKey}`)?.addEventListener("click", () => {
      setupDiet = dietKey.toUpperCase();
      ["herbivore", "carnivore", "omnivore"].forEach((k) => {
        const c = el(`diet-opt-${k}`);
        if (c) {
          c.classList.toggle("active", k === dietKey);
          c.style.borderColor = k === dietKey ? "#38bdf8" : "#334155";
          c.style.background = k === dietKey ? "rgba(56, 189, 248, 0.15)" : "rgba(15, 23, 42, 0.8)";
        }
      });
      applyCurrentArchetype(true);
      triggerAutoGeminiNaming();
    });
  });

  // ── 3. Tiêu Chí Strategy Handlers (Tự Động Sinh Tên Sinh Thái AI) ──
  [
    { key: "r", id: "STRAT_R" },
    { key: "k", id: "STRAT_K" },
    { key: "social", id: "STRAT_SOCIAL" },
  ].forEach((stratItem) => {
    el(`strat-opt-${stratItem.key}`)?.addEventListener("click", () => {
      setupStrategy = stratItem.id;
      ["r", "k", "social"].forEach((k) => {
        const c = el(`strat-opt-${k}`);
        if (c) {
          const isActive = k === stratItem.key;
          c.classList.toggle("active", isActive);
          c.style.borderColor = isActive ? "#38bdf8" : "#334155";
          c.style.background = isActive ? "rgba(56, 189, 248, 0.15)" : "rgba(15, 23, 42, 0.8)";
        }
      });
      applyCurrentArchetype(true);
      triggerAutoGeminiNaming();
    });
  });

  // Nạp chỉ số chuẩn của Archetype
  el("btn-load-rec-traits")?.addEventListener("click", () => {
    applyCurrentArchetype(true);
    showFloatingWarning("🎯 Đã nạp 6 chỉ số cân bằng tối ưu cho Archetype sinh thái này!");
  });

  // Re-roll Gemini Naming Button
  el("btn-gemini-name")?.addEventListener("click", () => requestGeminiNaming(true));

  // Gemini Key Configuration Toggle & Save
  el("btn-toggle-key-input")?.addEventListener("click", () => {
    const box = el("container-gemini-key");
    if (box) {
      box.style.display = box.style.display === "none" ? "flex" : "none";
      if (el("input-gemini-key") && customGeminiKey) {
        el("input-gemini-key").value = customGeminiKey;
      }
    }
  });

  el("btn-save-gemini-key")?.addEventListener("click", () => {
    const input = el("input-gemini-key");
    if (input) {
      customGeminiKey = input.value.trim();
      try { localStorage.setItem("gz_gemini_key", customGeminiKey); } catch (_) {}
      showFloatingWarning(customGeminiKey ? "🔑 Đã lưu Gemini API Key!" : "🔑 Đã xóa Gemini API Key (sử dụng mặc định)!");
      const box = el("container-gemini-key");
      if (box) box.style.display = "none";
    }
  });

  // Tab Handlers
  el("tab-btn-create")?.addEventListener("click", () => {
    el("tab-btn-create")?.classList.add("active");
    el("tab-btn-laws")?.classList.remove("active");
    if (el("tab-btn-create")) {
      el("tab-btn-create").style.color = "#38bdf8";
      el("tab-btn-create").style.borderBottomColor = "#38bdf8";
    }
    if (el("tab-btn-laws")) {
      el("tab-btn-laws").style.color = "#94a3b8";
      el("tab-btn-laws").style.borderBottomColor = "transparent";
    }
    if (el("tab-content-create")) el("tab-content-create").style.display = "flex";
    if (el("tab-content-laws")) el("tab-content-laws").style.display = "none";
  });

  el("tab-btn-laws")?.addEventListener("click", () => {
    el("tab-btn-laws")?.classList.add("active");
    el("tab-btn-create")?.classList.remove("active");
    if (el("tab-btn-laws")) {
      el("tab-btn-laws").style.color = "#38bdf8";
      el("tab-btn-laws").style.borderBottomColor = "#38bdf8";
    }
    if (el("tab-btn-create")) {
      el("tab-btn-create").style.color = "#94a3b8";
      el("tab-btn-create").style.borderBottomColor = "transparent";
    }
    if (el("tab-content-create")) el("tab-content-create").style.display = "none";
    if (el("tab-content-laws")) el("tab-content-laws").style.display = "flex";
    renderTabLawsUI();
  });

  el("setup-creature-name")?.addEventListener("input", updateLivePreview);
  el("setup-creature-desc")?.addEventListener("input", (e) => {
    updateLivePreview();
    try { localStorage.setItem("gz_my_creature_desc", e.target.value); } catch (_) {}
  });
  el("btn-create-concept-3d")?.addEventListener("click", requestConceptAnd3D);

  // Quỹ điểm linh hoạt (Tier 1: 16đ, Tier 2: 20đ, Tier 3: 23đ Apex)
  if (typeof document !== "undefined" && typeof document.querySelectorAll === "function") {
    document.querySelectorAll(".btn-tier-budget").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".btn-tier-budget").forEach((b) => {
          b.style.borderColor = "#334155";
          b.style.background = "rgba(15, 23, 42, 0.8)";
          b.style.color = "#94a3b8";
        });
        btn.style.borderColor = "#38bdf8";
        btn.style.background = "rgba(56, 189, 248, 0.2)";
        btn.style.color = "#38bdf8";
        pointsBudget = parseInt(btn.getAttribute("data-budget"), 10) || 16;
        renderSetupTraitsUI();
        updateLivePreview();
      });
    });

    // Dạng sống Sinh học (Động vật, Thực vật, Nấm, Lai)
    document.querySelectorAll(".kingdom-card").forEach((card) => {
      card.addEventListener("click", () => {
        document.querySelectorAll(".kingdom-card").forEach((c) => {
          c.classList.remove("active");
          c.style.borderColor = "#334155";
          c.style.background = "rgba(15, 23, 42, 0.8)";
          const t = c.querySelector("div:nth-child(2)");
          if (t) t.style.color = "#cbd5e1";
        });
        card.classList.add("active");
        setupKingdom = card.getAttribute("data-kingdom") || "FAUNA";
        const primaryCol = setupKingdom === "FLORA" ? "#22c55e" : (setupKingdom === "FUNGI" ? "#eab308" : (setupKingdom === "HYBRID" ? "#ec4899" : "#38bdf8"));
        card.style.borderColor = primaryCol;
        card.style.background = `${primaryCol}26`;
        const t = card.querySelector("div:nth-child(2)");
        if (t) t.style.color = primaryCol;

        const descBox = el("setup-creature-desc");
        if (descBox && !descBox.value.trim()) {
          if (setupKingdom === "FLORA") {
            descBox.placeholder = "Ví dụ: Cây hoa ăn thịt di động, bốn rễ cọc bẩy đất bò trườn, đài hoa răng cưa tiết dịch tiêu hóa, cành gai và dây leo quất roi bảo vệ...";
          } else if (setupKingdom === "FUNGI") {
            descBox.placeholder = "Ví dụ: Nấm bào tử phát quang lơ lửng, túi khí nén phóng acid hoại tử, mạng sợi nấm bám đất hút dinh dưỡng...";
          } else if (setupKingdom === "HYBRID") {
            descBox.placeholder = "Ví dụ: Thằn lằn mai cổ thụ cộng sinh rêu gai, thân phủ lớp vỏ gỗ kháng chấn, mõm nanh nhọn kết hợp xúc tu hoa...";
          } else {
            descBox.placeholder = "Ví dụ: Thỏ rừng bốn chân nhỏ gọn, lông màu xám tro pha vệt cát ngụy trang, tai dài vểnh nghe ngóng, mắt to tròn đen láy...";
          }
        }
        updateLivePreview();
      });
    });
  }

  el("btn-setup-spawn")?.addEventListener("click", spawnAndEnterWorld);
  el("btn-open-setup")?.addEventListener("click", toggleSetupLobby);
  el("btn-open-dossier")?.addEventListener("click", toggleSetupLobby);
  el("btn-close-setup")?.addEventListener("click", closeSetupLobby);
  el("btn-close-dossier")?.addEventListener("click", closeSetupLobby);

  // Khởi tạo giao diện setup ban đầu
  renderSetupTraitsUI();
  renderSetupFeaturesUI();
  applyCurrentArchetype(false);
  renderTabLawsUI();

  if (paramCreature) {
    myCreatureId = paramCreature;
    try { localStorage.setItem("gz_my_creature_id", myCreatureId); } catch (_) {}
  }

  // Mặc định mở sảnh setup lúc mở trang, trừ khi có cờ setup=0 (xem trực tiếp map)
  if (paramSetup === "0" || paramSetup === "false") {
    closeSetupLobby();
  } else {
    openSetupLobby();
  }
  if (urlParams && urlParams.get("tab") === "laws") {
    el("tab-btn-laws")?.click();
  }

  // ── 11. Bảng Soi Chi Tiết Sinh Vật (Inspection Card) ──
  function selectCreature(id) {
    selectedCreatureId = id;
    selectRing.visible = true;
    updateInspectCard();
    if (el("inspect-card")) el("inspect-card").style.display = "flex";
    if (creatureSelect) creatureSelect.value = id;
    if (camMode === "FOLLOW") {
      const tag = el("pov-creature-tag");
      if (tag) tag.textContent = `POV: ${id}`;
    }
  }

  function deselectCreature() {
    selectedCreatureId = null;
    selectRing.visible = false;
    if (el("inspect-card")) el("inspect-card").style.display = "none";
    if (creatureSelect) creatureSelect.value = "";
    const povHud = el("creature-pov-hud");
    if (povHud) povHud.style.display = "none";
    if (camMode === "FOLLOW") setCameraPreset("ISO");
  }

  el("btn-insp-close")?.addEventListener("click", deselectCreature);
  el("btn-insp-follow")?.addEventListener("click", () => {
    if (selectedCreatureId) setCameraPreset("FOLLOW");
  });

  function updateInspectCard() {
    const entity = bodies.get(selectedCreatureId);
    if (!entity) return;
    const c = entity.data;
    const t = c.tr || [2, 2, 2, 2, 2, 2];
    const domain = getDomain(c);

    el("insp-id").textContent = `${c.id} (${c.species || c.id.split(":")[0]})`;
    const domainTag = el("insp-domain-tag");
    if (domain === "NUOC") { domainTag.textContent = "🌊 DƯỚI NƯỚC"; domainTag.style.color = "#38bdf8"; }
    else if (domain === "TROI") { domainTag.textContent = "🦅 TRÊN TRỜI"; domainTag.style.color = "#facc15"; }
    else { domainTag.textContent = "🌿 TRÊN CẠN"; domainTag.style.color = "#4ade80"; }

    el("insp-hp-val").textContent = `${c.hp} / 100`;
    el("insp-hp-bar").style.width = `${Math.max(0, Math.min(100, c.hp))}%`;

    el("insp-e-val").textContent = `${c.e} / ${c.e_max}`;
    el("insp-e-bar").style.width = `${Math.max(0, Math.min(100, (c.e / (c.e_max || 100)) * 100))}%`;

    el("insp-tr-brain").textContent = t[TR.brain];
    el("insp-tr-attack").textContent = t[TR.attack];
    el("insp-tr-armor").textContent = t[TR.armor];
    el("insp-tr-speed").textContent = t[TR.speed];
    el("insp-tr-sense").textContent = t[TR.sense];
    el("insp-tr-stomach").textContent = t[TR.stomach];

    if (el("insp-gen")) el("insp-gen").textContent = (c.gen !== undefined && c.gen !== null) ? c.gen : 0;
    if (el("insp-parent")) el("insp-parent").textContent = c.parent_id || "Gốc (Gen 0)";
    if (el("insp-lineage")) el("insp-lineage").textContent = c.lineage || c.species || "—";
    if (el("insp-dtr")) el("insp-dtr").textContent = c.d_tr ? JSON.stringify(c.d_tr) : "[0, 0, 0, 0, 0, 0]";

    const featBox = el("insp-features");
    if (featBox) {
      featBox.innerHTML = "";
      const feats = c.features || [];
      if (feats.length > 0) {
        feats.forEach((f) => {
          const badge = document.createElement("span");
          badge.className = "feat-badge";
          badge.textContent = FEATURE_NAMES_VN[f] || f;
          featBox.appendChild(badge);
        });
      } else {
        const badge = document.createElement("span");
        badge.className = "feat-badge";
        badge.textContent = "Đặc tính di truyền tự nhiên";
        featBox.appendChild(badge);
      }
    }
  }

  // ── 12. Minimap Chiến thuật 2D ──
  const minimapCanvas = el("minimap");
  const minimapCtx = minimapCanvas ? minimapCanvas.getContext("2d") : null;

  function renderMinimap(frame) {
    if (!minimapCtx || !terrainGrid.length) return;
    const w = minimapCanvas.width;
    const h = minimapCanvas.height;
    const cellW = w / W;
    const cellH = h / H;

    let myCreature = null;
    let sightRadius = 6;
    if (enableFogOfWar && selectedCreatureId) {
      myCreature = (frame.creatures || []).find((c) => c.id === selectedCreatureId);
      if (myCreature) {
        const tr = myCreature.tr || [];
        const sense = tr[TR.sense] !== undefined ? tr[TR.sense] : 2;
        const sightMod = (currentWeatherModifiers && currentWeatherModifiers.sight_penalty) || 0;
        sightRadius = Math.max(2.5, (sense + 4) - sightMod);
      }
    }

    // Vẽ nền địa hình
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const code = terrainGrid[y][x];
        const t = TERRAIN[code] || TERRAIN.P;
        minimapCtx.fillStyle = `#${t.c.toString(16).padStart(6, "0")}`;
        minimapCtx.fillRect(x * cellW, y * cellH, cellW, cellH);
      }
    }

    // Vẽ thức ăn
    minimapCtx.fillStyle = "#ef4444";
    for (const p of frame.plants || []) {
      if (enableFogOfWar && myCreature) {
        const d = Math.hypot(p[0] - myCreature.x, p[1] - myCreature.y);
        if (d > sightRadius) continue;
      }
      minimapCtx.fillRect(p[0] * cellW + 1, p[1] * cellH + 1, cellW - 2, cellH - 2);
    }

    // Vẽ sinh vật
    for (const c of frame.creatures || []) {
      if (!c.alive) continue;
      if (enableFogOfWar && myCreature && c.id !== selectedCreatureId) {
        const d = Math.hypot(c.x - myCreature.x, c.y - myCreature.y);
        if (d > sightRadius) continue;
      }
      const domain = getDomain(c);
      minimapCtx.fillStyle = domain === "NUOC" ? "#38bdf8" : (domain === "TROI" ? "#facc15" : "#4ade80");
      minimapCtx.beginPath();
      minimapCtx.arc((c.x + 0.5) * cellW, (c.y + 0.5) * cellH, cellW * 0.45, 0, Math.PI * 2);
      minimapCtx.fill();
    }

    // Lớp phủ Fog of War trên minimap nếu được bật
    if (enableFogOfWar && myCreature) {
      const cx_px = (myCreature.x + 0.5) * cellW;
      const cy_px = (myCreature.y + 0.5) * cellH;
      const r_px = sightRadius * cellW;

      const grad = minimapCtx.createRadialGradient(cx_px, cy_px, r_px * 0.45, cx_px, cy_px, r_px);
      grad.addColorStop(0, "rgba(2, 6, 23, 0)");
      grad.addColorStop(0.75, "rgba(2, 6, 23, 0.65)");
      grad.addColorStop(1, "rgba(2, 6, 23, 0.94)");
      minimapCtx.fillStyle = grad;
      minimapCtx.fillRect(0, 0, w, h);

      minimapCtx.strokeStyle = "rgba(56, 189, 248, 0.5)";
      minimapCtx.lineWidth = 1;
      minimapCtx.beginPath();
      minimapCtx.arc(cx_px, cy_px, r_px, 0, Math.PI * 2);
      minimapCtx.stroke();
    }
  }

  // ── 13. Nhật Ký Sự Kiện ──
  function logEvent(ev) {
    const d = document.createElement("div");
    d.className = "ev " + (ev.k || "");
    d.textContent =
      ev.k === "SPEAK" ? `💬 [NÓI] ${ev.who} (${ev.sig}) → ${(ev.hear || []).length} kẻ nghe`
      : ev.k === "LAW_FIRED" ? `⚡ [LUẬT] Kích hoạt tại ${ev.pos ? ev.pos.join(",") : "?"} · ${ev.law || "Bí ẩn"}`
      : ev.k === "DEATH" ? `💀 [CHẾT] ${ev.who} (${ev.cause || "Kiệt sức"})`
      : ev.k === "ATTACK" ? `⚔️ [ĐÁNH] ${ev.who} → ${ev.target || "?"}`
      : ev.k === "EAT" ? `🍎 [ĂN] ${ev.who}`
      : `[${ev.k}] ${ev.who || ""}`;
    const log = el("log");
    if (log) {
      log.insertBefore(d, log.firstChild);
      while (log.childNodes.length > 60) log.removeChild(log.lastChild);
    }
  }

  // ── 14. Tiếp nhận và Xử lý Khung Telemetry ──
  function updateWeatherHUD(weather) {
    if (!weather) return;
    const badge = el("weather-badge");
    const icon = el("weather-icon");
    const name = el("weather-name");
    const prog = el("weather-progress");
    const mods = el("weather-modifiers");

    const state = weather.state || "CLEAR";
    const diurnal = weather.diurnal || "DAY";
    const progress = weather.progress !== undefined ? weather.progress :
      ((weather.cycle_tick || 0) / (weather.cycle_len || 50));
    const m = weather.modifiers || {};
    currentWeatherModifiers = m;

    if (icon) {
      if (state === "CLEAR") icon.textContent = (diurnal === "NIGHT" ? "🌙" : "☀️");
      else if (state === "SPORE_STORM") icon.textContent = "☣️";
      else if (state === "SOLAR_FLARE") icon.textContent = "🔥";
      else if (state === "MAGNETIC_SHIFT") icon.textContent = "🧲";
      else if (state === "STORM" || state === "RAIN") icon.textContent = "⛈️";
      else icon.textContent = "🌍";
    }

    if (name) {
      if (state === "CLEAR") name.textContent = (diurnal === "NIGHT" ? "NIGHT" : "CLEAR");
      else if (state === "SPORE_STORM") name.textContent = "SPORE STORM";
      else if (state === "SOLAR_FLARE") name.textContent = "SOLAR FLARE";
      else if (state === "MAGNETIC_SHIFT") name.textContent = "MAGNETIC SHIFT";
      else name.textContent = state;
    }

    if (prog) {
      prog.style.width = `${Math.min(100, Math.max(0, Math.round(progress * 100)))}%`;
    }

    if (mods) {
      const parts = [];
      if (m.move_cost_mult !== undefined && m.move_cost_mult !== 1.0) parts.push(`mv ${m.move_cost_mult}x`);
      if (m.sight_penalty) parts.push(`vis -${m.sight_penalty}`);
      mods.textContent = parts.length > 0 ? parts.join(" ") : "1.0x";
    }

    if (badge) {
      badge.title = `Khí hậu: ${state} (${diurnal}) · Tiến độ: ${Math.round(progress * 100)}%`;
    }
  }

  function applyFrame(frame, isInstant = false) {
    latestFrame = frame;
    buildTerrain(frame.terrain);

    if (el("phase")) {
      el("phase").textContent = frame.phase;
      el("phase").className = "badge " + frame.phase;
    }
    if (el("tick")) el("tick").textContent = frame.t;
    if (el("map")) el("map").textContent = frame.map || "—";

    const cs = frame.creatures || [];
    if (el("alive")) el("alive").textContent = `${cs.filter((c) => c.alive).length}/${cs.length}`;

    if (frame.weather) {
      updateWeatherHUD(frame.weather);
      updateWeatherAtmosphere(frame.weather);
    }

    syncBodies(frame, isInstant);
    syncPlantsAndCorpses(frame);

    // Cập nhật danh sách sinh vật & tự động chọn theo URL nếu có
    updateCreatureDropdown(frame.creatures);
    if (pendingCreatureSelect && frame.creatures) {
      const match = frame.creatures.find(
        (c) => c.id === pendingCreatureSelect || c.species === pendingCreatureSelect || c.id.startsWith(pendingCreatureSelect + ":")
      );
      if (match) {
        selectCreature(match.id);
        setCameraPreset("FOLLOW");
        pendingCreatureSelect = null;
      }
    } else if ((enableFogOfWar || camMode === "FOLLOW") && !selectedCreatureId && frame.creatures) {
      const firstAlive = frame.creatures.find((c) => c.alive);
      if (firstAlive) {
        selectCreature(firstAlive.id);
        if (camMode === "FOLLOW") setCameraPreset("FOLLOW");
      }
    }

    if (frame.phase === "REVEAL") {
      buildVictoryPodiums(frame);
    }

    renderMinimap(frame);
  }

  function onFrame(frame) {
    // 1. Ghi nhận khung vào Ring Buffer 1200 khung
    const existingIdx = historyBuffer.findIndex((f) => f.t === frame.t);
    if (existingIdx >= 0) {
      historyBuffer[existingIdx] = frame;
    } else {
      historyBuffer.push(frame);
      if (historyBuffer.length > MAX_HISTORY) {
        historyBuffer.shift();
      }
    }

    // 2. Cập nhật phạm vi timeline slider
    const minTick = historyBuffer[0].t;
    const maxTick = historyBuffer[historyBuffer.length - 1].t;
    const slider = el("timeline-slider");
    if (slider) {
      slider.min = minTick;
      slider.max = maxTick;
      if (isLive) {
        slider.value = frame.t;
        scrubTick = frame.t;
      }
    }
    updateTimelineUI(isLive ? frame.t : scrubTick, maxTick);

    // 3. Xử lý sự kiện & kích hoạt âm thanh thủ tục
    const now = performance.now();
    for (const ev of frame.events || []) {
      logEvent(ev);
      if (ev.k === "SPEAK") flashes.push({ a: ev.who, b: ev.hear || [], t0: now });
      if (ev.k === "LAW_FIRED" && ev.pos) {
        addLawFiredShockwave(ev.pos[0], ev.pos[1]);
        if (isLive) playLawFired();
      }
      if (ev.k === "DEATH" && isLive) playDeath();
      if (ev.k === "REPRODUCE" && isLive) playReproduce();
      if (ev.k === "ATTACK" && isLive) playCombatHit();
    }
    while (flashes.length && now - flashes[0].t0 > 350) flashes.shift();

    // 4. Nếu đang ở chế độ LIVE và không tạm dừng, hiển thị khung trực tiếp
    if (isLive && !isPaused) {
      applyFrame(frame, false);
    }
  }

  // ── 15. Kết nối WebSocket ──
  function connect() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${location.host || "localhost:8000"}/v1/spectate`);
    ws.onmessage = (e) => {
      try { onFrame(JSON.parse(e.data)); } catch (_) {}
    };
    ws.onclose = () => setTimeout(connect, 1000);
  }

  // ── 16. Vòng Lặp Render 60 FPS ──
  function loop() {
    const now = performance.now();

    // 0. Tua dòng thời gian nếu đang phát lại lịch sử
    if (!isLive && !isPaused && historyBuffer.length > 0) {
      const stepInterval = 120 / playbackSpeed;
      if (now - lastPlaybackStepTime >= stepInterval) {
        lastPlaybackStepTime = now;
        const maxTick = historyBuffer[historyBuffer.length - 1].t;
        if (scrubTick >= maxTick) {
          goToLive();
        } else {
          scrubTick += 1;
          renderHistoricalFrame(scrubTick, false);
        }
      }
    }

    // 1. Cập nhật sóng xung kích
    for (let i = shockwaves.length - 1; i >= 0; i--) {
      const p = (now - shockwaves[i].t0) / 600;
      if (p >= 1.0) {
        shockwaveGroup.remove(shockwaves[i].ring);
        shockwaveGroup.remove(shockwaves[i].torus);
        shockwaves.splice(i, 1);
        continue;
      }
      shockwaves[i].ring.scale.setScalar(1 + p * 3.2);
      shockwaves[i].ring.material.opacity = (1 - p) * 0.95;
      shockwaves[i].torus.scale.setScalar(1 + p * 2.6);
      shockwaves[i].torus.position.y = 0.35 + p * 0.6;
      shockwaves[i].torus.material.opacity = (1 - p) * 0.8;
    }

    // 2. Interpolate thực thể sinh vật
    for (const [, ent] of bodies) {
      ent.currX += (ent.targetX - ent.currX) * 0.18;
      ent.currY += (ent.targetY - ent.currY) * 0.2;
      ent.currZ += (ent.targetZ - ent.currZ) * 0.18;

      let yawDiff = ent.targetYaw - ent.yaw;
      while (yawDiff > Math.PI) yawDiff -= Math.PI * 2;
      while (yawDiff < -Math.PI) yawDiff += Math.PI * 2;
      ent.yaw += yawDiff * 0.2;

      ent.group.position.set(ent.currX, ent.currY, ent.currZ);
      ent.group.rotation.y = ent.yaw;
    }

    // 3. Vòng chọn quanh sinh vật & Camera Follow
    let camTargetY = 0.2;
    if (selectedCreatureId) {
      const ent = bodies.get(selectedCreatureId);
      if (ent) {
        selectRing.position.set(ent.currX, ent.currY + 0.02, ent.currZ);
        if (camMode === "FOLLOW") {
          targetCx = ent.currX;
          targetCz = ent.currZ;
          camTargetY = ent.currY + 0.45;
          if (!dragging) {
            const idealYaw = ent.yaw + Math.PI;
            let diff = (idealYaw - targetYaw) % (Math.PI * 2);
            if (diff > Math.PI) diff -= Math.PI * 2;
            if (diff < -Math.PI) diff += Math.PI * 2;
            targetYaw += diff * 0.06;
          }
        }
      }
    }

    // 4. Smooth Camera Damping
    if (camMode === "RIG") {
      currRigPos.lerp(targetRigPos, 0.08);
      currRigTarget.lerp(targetRigTarget, 0.08);
      camera.position.copy(currRigPos);
      camera.lookAt(currRigTarget);
    } else {
      yaw += (targetYaw - yaw) * 0.08;
      pitch += (targetPitch - pitch) * 0.08;
      dist += (targetDist - dist) * 0.08;
      cx += (targetCx - cx) * 0.08;
      cz += (targetCz - cz) * 0.08;

      camera.position.set(
        cx + dist * Math.cos(pitch) * Math.sin(yaw),
        camTargetY + dist * Math.sin(pitch),
        cz + dist * Math.cos(pitch) * Math.cos(yaw)
      );
      camera.lookAt(cx, camTargetY, cz);
    }

    // 4.2. Master Diorama Fauna Animation Mixer
    if (dioramaMixer) {
      dioramaMixer.update(0.016);
    }

    // 4.5. Lọc Tầm Nhìn Sinh Vật (Fog of War 3D)
    if (enableFogOfWar && selectedCreatureId) {
      const myEnt = bodies.get(selectedCreatureId);
      if (myEnt && myEnt.data) {
        const tr = myEnt.data.tr || [];
        const sense = tr[TR.sense] !== undefined ? tr[TR.sense] : 2;
        const sightMod = (currentWeatherModifiers && currentWeatherModifiers.sight_penalty) || 0;
        const sightRadius = Math.max(2.5, (sense + 4) - sightMod);

        // Lọc sinh vật khác ngoài tầm nhìn
        for (const [cid, otherEnt] of bodies) {
          if (cid === selectedCreatureId) {
            otherEnt.group.visible = true;
            continue;
          }
          const d = Math.hypot(otherEnt.currX - myEnt.currX, otherEnt.currZ - myEnt.currZ);
          otherEnt.group.visible = d <= sightRadius;
        }

        // Lọc thực vật ngoài tầm nhìn
        for (const child of plantsGroup.children) {
          const d = Math.hypot(child.position.x - myEnt.currX, child.position.z - myEnt.currZ);
          child.visible = d <= sightRadius;
        }

        // Lọc xác chết ngoài tầm nhìn
        for (const child of corpsesGroup.children) {
          const d = Math.hypot(child.position.x - myEnt.currX, child.position.z - myEnt.currZ);
          child.visible = d <= sightRadius;
        }
      }
    } else {
      for (const [, otherEnt] of bodies) {
        otherEnt.group.visible = true;
      }
      for (const child of plantsGroup.children) {
        child.visible = true;
      }
      for (const child of corpsesGroup.children) {
        child.visible = true;
      }
    }

    // 5. Cập nhật ánh sáng & sương mù thời tiết (Smooth Lerp)
    scene.background.lerp(targetBgColor, 0.04);
    scene.fog.color.lerp(targetFogColor, 0.04);
    scene.fog.near += (targetFogNear - scene.fog.near) * 0.04;
    scene.fog.far += (targetFogFar - scene.fog.far) * 0.04;
    sunLight.color.lerp(targetSunColor, 0.04);
    sunLight.intensity += (targetSunIntensity - sunLight.intensity) * 0.04;
    ambientFill.color.lerp(targetAmbientColor, 0.04);
    hemiLight.color.lerp(targetHemiSky, 0.04);
    hemiLight.groundColor.lerp(targetHemiGround, 0.04);

    // 5.5. Hiệu ứng sóng nước tự nhiên gợn lăn tăn (Anima-Engine style)
    if (dioramaOceanMesh) {
      dioramaOceanMesh.position.y = 0.02 + Math.sin(now * 0.002) * 0.012;
    }
    if (waterSurfaceMesh) {
      waterSurfaceMesh.position.y = -0.02 + Math.sin(now * 0.0025) * 0.008;
    }

    // 6. Hoạt hoá các hệ hạt thời tiết
    animateWeatherParticles(now);

    // 7. Vẽ đồ thị nghe
    if (latestFrame) drawHearing(latestFrame);

    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  }

  if (typeof window !== "undefined") {
    window.Genesis3D = {
      historyBuffer,
      playLawFired,
      playDeath,
      playReproduce,
      playWeatherShift,
      playMoveSound,
      playCombatHit,
      setCameraPreset,
      toggleFogOfWar,
      selectCreature,
      loadDioramaGLB,
      CAMERA_RIG_24_PRESETS,
      weatherParticles: {
        rain: rainParticles,
        solar: solarParticles,
        spore: sporeParticles,
        magnetic: magneticParticles,
      },
    };
  }

  if (!_isHeadlessOrNodeContext()) {
    loadDioramaGLB();
  }
  connect();
  loop();
})();
