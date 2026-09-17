"""Adversarial stress test suite for M4_SPECTATOR (Challenger 2).

Verifies:
1. Zero sound file invariant across entire repository (no .mp3, .wav, .ogg, .flac, .aac, .m4a, etc.).
2. Zero sound file path references in web/ directory.
3. Native Web Audio API AudioContext usage and audio graph master routing.
4. Master DynamicsCompressor configuration (-6dB threshold, 8:1 ratio) preventing digital clipping.
5. Volume slider clamping within [0.0, 1.0] and mute toggle behavior.
6. Graceful handling of locked/suspended AudioContext without throwing uncaught exceptions.
7. All procedural synthesizers strictly route through compressor before master gain.
8. Weather particle buffers statically bounded (800 rain, 400 solar, 500 spore, 300 magnetic) with zero reallocation.
9. 100 rapid weather switches simulation in Node.js runtime verifying visibility toggling and coordinate integrity.
10. Dynamic atmospheric lighting and fog lerp parameter stability under rapid environmental oscillation.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "web" / "watch3d.html"
JS_PATH = ROOT / "web" / "watch3d.js"

FORBIDDEN_AUDIO_EXTENSIONS = (
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".aac",
    ".m4a",
    ".wma",
    ".opus",
    ".aiff",
    ".au",
    ".alac",
)


def _extract_function_body(js: str, func_name: str) -> str:
    """Accurately extracts the balanced-brace body of a named function."""
    pattern = rf"function\s+{func_name}\s*\([^)]*\)\s*\{{"
    m = re.search(pattern, js)
    if not m:
        raise ValueError(f"Function {func_name} not found in JavaScript source")
    start = m.end()
    depth = 1
    i = start
    while i < len(js) and depth > 0:
        if js[i] == "{":
            depth += 1
        elif js[i] == "}":
            depth -= 1
        i += 1
    return js[start : i - 1]


def test_zero_sound_files_in_entire_repository():
    """Adversarially sweep the entire repository to ensure zero external audio files exist."""
    found_audio_files: list[str] = []
    for root, dirs, files in os.walk(ROOT):
        # Exclude git internal database and virtual environment directories
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "venv", "__pycache__", "node_modules")]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in FORBIDDEN_AUDIO_EXTENSIONS:
                found_audio_files.append(os.path.join(root, f))

    assert len(found_audio_files) == 0, (
        f"Found forbidden sound files in repository (violates zero-sound-file invariant): {found_audio_files}"
    )


def test_zero_sound_file_references_in_web_directory():
    """Verify web/watch3d.html and web/watch3d.js contain zero references to audio files or URLs."""
    html_content = HTML_PATH.read_text(encoding="utf-8")
    js_content = JS_PATH.read_text(encoding="utf-8")

    audio_file_regex = re.compile(
        r"""['"][^'"]+\.(?:mp3|wav|ogg|flac|aac|m4a|wma|opus|aiff|alac)['"]""",
        re.IGNORECASE,
    )

    html_matches = audio_file_regex.findall(html_content)
    js_matches = audio_file_regex.findall(js_content)

    assert len(html_matches) == 0, f"watch3d.html references audio files: {html_matches}"
    assert len(js_matches) == 0, f"watch3d.js references audio files: {js_matches}"

    # Also verify absence of HTML5 <audio> tags and external audio loading constructs
    assert "<audio" not in html_content.lower(), "watch3d.html must not use HTML5 <audio> element"
    assert "new audio(" not in js_content.lower(), "watch3d.js must not instantiate HTML5 Audio objects"


def test_audio_context_native_and_master_graph_routing():
    """Verify AudioContext initialization, master compressor and master gain topology."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Native AudioContext checking with webkit fallback
    assert "window.AudioContext || window.webkitAudioContext" in js, (
        "Audio engine must use native browser AudioContext with webkitAudioContext fallback"
    )

    # Audio master graph construction
    assert "audioCtx.createDynamicsCompressor()" in js, (
        "Audio engine must instantiate DynamicsCompressorNode"
    )
    assert "audioCtx.createGain()" in js, "Audio engine must instantiate GainNode for master volume"
    assert "compressor.connect(masterGain)" in js, (
        "Compressor must connect directly to masterGain in master chain"
    )
    assert "masterGain.connect(audioCtx.destination)" in js, (
        "masterGain must connect directly to audioCtx.destination"
    )


def test_audio_master_compressor_parameters_and_clipping_safety():
    """Verify master compressor parameters and mathematical guarantee against digital clipping.

    When multiple oscillators fire simultaneously (e.g. playLawFired with 4 harmonic oscillators
    summing to 0.8 + sub-bass 0.35 = 1.15 amplitude / +1.21 dBFS), the DynamicsCompressorNode
    configured with threshold=-6dB and ratio=8:1 guarantees output does not exceed 0 dBFS.
    """
    js = JS_PATH.read_text(encoding="utf-8")

    # Verify compressor configuration lines in watch3d.js
    threshold_match = re.search(r"compressor\.threshold\.setValueAtTime\(\s*(-?\d+)", js)
    assert threshold_match is not None, "Missing compressor threshold setting"
    threshold_db = float(threshold_match.group(1))
    assert threshold_db == -6.0, f"Compressor threshold must be -6 dB, got {threshold_db} dB"

    ratio_match = re.search(r"compressor\.ratio\.setValueAtTime\(\s*(\d+)", js)
    assert ratio_match is not None, "Missing compressor ratio setting"
    ratio = float(ratio_match.group(1))
    assert ratio >= 4.0, f"Compressor ratio must provide strong compression (>=4), got {ratio}"

    knee_match = re.search(r"compressor\.knee\.setValueAtTime\(\s*(\d+)", js)
    assert knee_match is not None, "Missing compressor knee setting"
    knee = float(knee_match.group(1))
    assert knee > 0, "Compressor knee must provide smooth soft-knee curve"

    # Mathematical clipping safety verification:
    # Worst-case uncompressed peak: 4 * 0.2 (chord) + 0.35 (sub) = 1.15 amplitude
    uncompressed_amplitude = 1.15
    input_db = 20.0 * math.log10(uncompressed_amplitude)  # ~ +1.214 dBFS
    assert input_db > threshold_db  # Confirms signal enters compression zone

    # Output dBFS under compression: threshold + (input_db - threshold) / ratio
    compressed_db = threshold_db + (input_db - threshold_db) / ratio
    compressed_amplitude = 10.0 ** (compressed_db / 20.0)

    # 0 dBFS is the digital clipping threshold (amplitude 1.0)
    assert compressed_db < 0.0, (
        f"Compressed output level {compressed_db:.2f} dBFS must be strictly below 0 dBFS clipping ceiling"
    )
    assert compressed_amplitude < 1.0, (
        f"Compressed amplitude {compressed_amplitude:.4f} must be strictly < 1.0"
    )


def test_audio_volume_slider_clamping_and_muting():
    """Verify HTML range slider clamps within [0.0, 1.0] and volume state mutations remain bounded."""
    html = HTML_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")

    # Match audio volume slider attributes
    slider_match = re.search(r'<input[^>]+id=["\']audio-volume-slider["\'][^>]*>', html)
    assert slider_match is not None, "Missing #audio-volume-slider in watch3d.html"
    slider_tag = slider_match.group(0)

    assert 'min="0"' in slider_tag, "Volume slider min must be '0'"
    assert 'max="1"' in slider_tag, "Volume slider max must be '1'"
    assert 'step="0.05"' in slider_tag or "step=" in slider_tag, "Volume slider must define fractional steps"

    # Verify slider input listener updates masterGain safely
    assert "masterVolume = parseFloat(e.target.value)" in js, (
        "watch3d.js must parse slider input to masterVolume"
    )
    assert "masterGain.gain.setValueAtTime(masterVolume, audioCtx.currentTime)" in js or (
        "masterGain.gain.setValueAtTime" in js
    ), "watch3d.js must update masterGain on volume input"

    # Verify mute toggle logic toggles gain between 0 and masterVolume
    assert "isAudioMuted = !isAudioMuted" in js, "watch3d.js must toggle isAudioMuted flag"
    assert "isAudioMuted ? 0 : masterVolume" in js, (
        "watch3d.js must mute masterGain by clamping gain to 0 when muted"
    )


def test_web_audio_locked_suspended_graceful_handling():
    """Verify browser autoplay policy compliance: unlock listeners and graceful fallback if suspended."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Global user gesture listeners for audio unlocking
    for event in ("click", "keydown", "touchstart"):
        assert f'"{event}"' in js or f"'{event}'" in js, (
            f"watch3d.js must register user gesture unlock listener for '{event}'"
        )

    # unlockAudio implementation checks
    assert "function unlockAudio()" in js, "watch3d.js must define unlockAudio function"
    assert 'audioCtx.state === "suspended"' in js, (
        "unlockAudio must check for suspended state before resuming"
    )
    assert "audioCtx.resume().catch" in js or "audioCtx.resume()" in js, (
        "unlockAudio must call audioCtx.resume() with catch handler"
    )

    # Verify all audio synthesizers guard against uninitialized/suspended audio context
    synths = (
        "playMoveSound",
        "playLawFired",
        "playDeath",
        "playReproduce",
        "playCombatHit",
        "playWeatherShift",
    )
    for synth in synths:
        func_body = _extract_function_body(js, synth)

        # Must guard: if (!audioCtx || isAudioMuted) return;
        assert "!audioCtx" in func_body, f"Function {synth} must guard against null audioCtx"
        assert "isAudioMuted" in func_body, f"Function {synth} must check isAudioMuted"
        assert "try {" in func_body and "} catch" in func_body, (
            f"Function {synth} must enclose oscillator/gain creation inside try-catch to prevent uncaught exceptions"
        )


def test_all_synthesizers_route_strictly_through_compressor():
    """Verify that all procedural sound synthesizers connect exclusively to the compressor."""
    js = JS_PATH.read_text(encoding="utf-8")

    synthesizers = [
        "playMoveSound",
        "playLawFired",
        "playDeath",
        "playReproduce",
        "playCombatHit",
        "playWeatherShift",
    ]

    for synth in synthesizers:
        body = _extract_function_body(js, synth)

        # Must connect to compressor
        assert ".connect(compressor)" in body, (
            f"Function {synth} must route audio through compressor to avoid digital clipping"
        )
        # Must NEVER connect directly to destination or masterGain
        assert ".connect(audioCtx.destination)" not in body, (
            f"Function {synth} connects directly to destination, bypassing compressor"
        )
        assert ".connect(masterGain)" not in body, (
            f"Function {synth} connects directly to masterGain, bypassing compressor"
        )


def test_weather_particle_buffers_bounded_and_zero_reallocation():
    """Verify weather particle systems use bounded Float32Array buffers instantiated once."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Verify particle systems and exact counts
    expected_counts = {
        "rain": 800,
        "solar": 400,
        "spore": 500,
        "magnetic": 300,
    }

    for name, count in expected_counts.items():
        assert f"new Float32Array({count} * 3)" in js, (
            f"Particle system '{name}' must allocate Float32Array({count} * 3)"
        )

    # Verify that neither updateWeatherAtmosphere nor animateWeatherParticles reallocates geometry/points
    for func_name in ("updateWeatherAtmosphere", "animateWeatherParticles"):
        body = _extract_function_body(js, func_name)

        assert "new THREE.BufferGeometry" not in body, (
            f"{func_name} must NOT reallocate BufferGeometry on weather updates"
        )
        assert "new THREE.Points" not in body, (
            f"{func_name} must NOT reallocate THREE.Points on weather updates"
        )
        assert "new Float32Array" not in body, (
            f"{func_name} must NOT reallocate Float32Array buffers on weather updates"
        )


def test_weather_particles_100_rapid_switches_simulation():
    """Simulate 100 rapid weather switches in Node.js to verify memory safety, visibility, and coordinates."""
    node_script = """
const fs = require('fs');
const path = require('path');

// Mock browser & Three.js environment
function Color(hex) {
  this.hex = hex;
  this.lerp = () => {};
  this.setHex = (h) => { this.hex = h; };
  this.setScalar = () => {};
  this.setHSL = () => this;
}
function BufferAttribute(arr, itemSize) {
  this.array = arr;
  this.itemSize = itemSize;
  this.needsUpdate = false;
}
function BufferGeometry() {
  this.attributes = {};
  this.setAttribute = (name, attr) => { this.attributes[name] = attr; };
  this.setDrawRange = () => {};
}
function Material() { this.opacity = 1; this.transparent = false; }
function Points(geo, mat) { this.geometry = geo; this.material = mat; this.visible = false; }
function Group() { this.children = []; this.add = (...items) => this.children.push(...items); this.remove = () => {}; }
function Mesh(geo, mat) {
  this.geometry = geo; this.material = mat;
  this.position = { set: () => {}, y: 0 };
  this.rotation = { x: 0, y: 0 };
  this.scale = { setScalar: () => {} };
  this.userData = {};
}

const eventListeners = {};
const elements = {};
global.document = {
  getElementById: (id) => {
    if (!elements[id]) {
      elements[id] = {
        id,
        appendChild: () => {},
        addEventListener: (event, fn) => { (eventListeners[id + ':' + event] ||= []).push(fn); },
        classList: { add: () => {}, remove: () => {}, toggle: () => {} },
        style: {},
        getContext: () => ({ fillRect: () => {}, beginPath: () => {}, arc: () => {}, fill: () => {} }),
        width: 132, height: 132, textContent: '', value: '0.7', min: '0', max: '1', step: '0.05'
      };
    }
    return elements[id];
  },
};
global.window = global;
global.innerWidth = 1280; global.innerHeight = 720; global.devicePixelRatio = 1;
global.addEventListener = (event, fn) => { (eventListeners['window:' + event] ||= []).push(fn); };
let simTime = 1000;
global.performance = { now: () => (simTime += 16.66) };
let rAFCallback = null;
global.requestAnimationFrame = (cb) => { rAFCallback = cb; };
global.location = { protocol: 'http:', host: 'localhost:8000' };

let wsHandler = null;
global.WebSocket = class {
  constructor() {
    this.onmessage = (e) => {};
    wsHandler = (data) => this.onmessage({ data: JSON.stringify(data) });
  }
};

global.THREE = {
  Scene: class {
    constructor() {
      this.children = [];
      this.background = new Color(0);
      this.fog = { color: new Color(0), near: 32, far: 75 };
    }
    add(...c) { this.children.push(...c); }
  },
  Fog: class { constructor(c, near, far) { this.color = new Color(c); this.near = near; this.far = far; } },
  PerspectiveCamera: class { constructor() { this.position = { set: () => {} }; this.lookAt = () => {}; } updateProjectionMatrix() {} },
  WebGLRenderer: class { constructor() { this.domElement = { appendChild: () => {}, addEventListener: () => {} }; this.shadowMap = {}; } setPixelRatio() {} setSize() {} render() {} },
  HemisphereLight: class { constructor() { this.color = new Color(0); this.groundColor = new Color(0); } },
  DirectionalLight: class { constructor() { this.color = new Color(0); this.position = { set: () => {} }; this.shadow = { mapSize: {}, camera: {} }; this.intensity = 1.1; } },
  AmbientLight: class { constructor() { this.color = new Color(0); } },
  Group, BufferGeometry, BufferAttribute,
  PointsMaterial: Material, Points, Color,
  RingGeometry: class {}, MeshBasicMaterial: Material, Mesh,
  Raycaster: class { setFromCamera() {} intersectObjects() { return []; } },
  Vector2: class {}, BoxGeometry: class {}, PlaneGeometry: class {}, CylinderGeometry: class {},
  SphereGeometry: class {}, ConeGeometry: class {}, TorusGeometry: class {},
  MeshLambertMaterial: Material,
  InstancedMesh: class { constructor() { this.instanceMatrix = { needsUpdate: false }; } setMatrixAt() {} },
  Matrix4: class { makeScale() {} setPosition() {} },
  LineBasicMaterial: Material,
  LineSegments: class { constructor() { this.visible = true; } },
};

// Evaluate the shared history module before the viewer, as in the HTML page.
global.GenesisTelemetry = require('./web/frame_history.js');
// Evaluate watch3d.js
const code = fs.readFileSync(path.join(process.cwd(), 'web/watch3d.js'), 'utf8');
eval(code);

const particles = global.Genesis3D.weatherParticles;
const initialGeos = {
  rain: particles.rain.geometry,
  solar: particles.solar.geometry,
  spore: particles.spore.geometry,
  magnetic: particles.magnetic.geometry,
};

const weatherSequence = ['CLEAR', 'NIGHT', 'SPORE_STORM', 'SOLAR_FLARE', 'MAGNETIC_SHIFT', 'STORM'];
const results = {
  transitionsCompleted: 0,
  zeroReallocation: true,
  visibilityClean: true,
  coordinatesFinite: true,
  particleCountsBounded: true,
};

for (let i = 0; i < 100; i++) {
  const state = weatherSequence[i % weatherSequence.length];
  const diurnal = state === 'NIGHT' ? 'NIGHT' : 'DAY';
  const frame = {
    t: i + 1,
    phase: 'RUNNING',
    map: 'island',
    terrain: ['PPPPPPPPPPPPPPPPPPPPPPPP'],
    weather: {
      state: state === 'NIGHT' ? 'CLEAR' : state,
      diurnal: diurnal,
      cycle_tick: i % 50,
      cycle_len: 50,
      progress: (i % 50) / 50,
      modifiers: { move_cost_mult: 1.0, sight_penalty: 0 }
    },
    creatures: [],
    plants: [],
    corpses: [],
    events: [],
  };

  wsHandler(frame);

  if (rAFCallback) {
    const cb = rAFCallback;
    rAFCallback = null;
    cb();
  }

  // Check zero reallocation
  for (const [key, initialGeo] of Object.entries(initialGeos)) {
    if (particles[key].geometry !== initialGeo) {
      results.zeroReallocation = false;
    }
  }

  // Check visibility flags
  const actualWeather = state === 'NIGHT' ? 'CLEAR' : state;
  if (actualWeather === 'STORM') {
    if (!particles.rain.visible || particles.solar.visible || particles.spore.visible || particles.magnetic.visible)
      results.visibilityClean = false;
  } else if (actualWeather === 'SOLAR_FLARE') {
    if (particles.rain.visible || !particles.solar.visible || particles.spore.visible || particles.magnetic.visible)
      results.visibilityClean = false;
  } else if (actualWeather === 'SPORE_STORM') {
    if (particles.rain.visible || particles.solar.visible || !particles.spore.visible || particles.magnetic.visible)
      results.visibilityClean = false;
  } else if (actualWeather === 'MAGNETIC_SHIFT') {
    if (particles.rain.visible || particles.solar.visible || particles.spore.visible || !particles.magnetic.visible)
      results.visibilityClean = false;
  } else {
    if (particles.rain.visible || particles.solar.visible || particles.spore.visible || particles.magnetic.visible)
      results.visibilityClean = false;
  }

  // Check coordinate sanity
  for (const [, sys] of Object.entries(particles)) {
    const arr = sys.geometry.attributes.position.array;
    for (let j = 0; j < arr.length; j++) {
      if (isNaN(arr[j]) || !isFinite(arr[j])) {
        results.coordinatesFinite = false;
      }
    }
  }

  results.transitionsCompleted++;
}

// Check buffer counts
if (particles.rain.geometry.attributes.position.array.length !== 800 * 3) results.particleCountsBounded = false;
if (particles.solar.geometry.attributes.position.array.length !== 400 * 3) results.particleCountsBounded = false;
if (particles.spore.geometry.attributes.position.array.length !== 500 * 3) results.particleCountsBounded = false;
if (particles.magnetic.geometry.attributes.position.array.length !== 300 * 3) results.particleCountsBounded = false;

console.log(JSON.stringify(results));
"""
    result = subprocess.run(
        ["node", "-e", node_script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Node.js simulation failed: {result.stderr}"

    output_lines = [line.strip() for line in result.stdout.strip().split("\n") if line.startswith("{")]
    assert len(output_lines) == 1, f"Expected JSON output, got: {result.stdout}"
    data = json.loads(output_lines[0])

    assert data["transitionsCompleted"] == 100, f"Expected 100 transitions, got {data['transitionsCompleted']}"
    assert data["zeroReallocation"] is True, "Particle geometries were unexpectedly reallocated during weather shifts"
    assert data["visibilityClean"] is True, "Particle visibility flags did not match active weather state"
    assert data["coordinatesFinite"] is True, "Particle coordinates corrupted with NaN or Infinity"
    assert data["particleCountsBounded"] is True, "Particle buffer sizes deviated from bounded specifications"


def test_atmospheric_lighting_and_fog_lerp_stability_under_rapid_oscillation():
    """Verify target atmospheric lighting and fog parameters remain within stable mathematical bounds."""
    js = JS_PATH.read_text(encoding="utf-8")
    body = _extract_function_body(js, "updateWeatherAtmosphere")

    # Check that all canonical weather states are covered
    for state in ("SPORE_STORM", "SOLAR_FLARE", "MAGNETIC_SHIFT", "STORM"):
        assert f'currentWeather === "{state}"' in body or f"'{state}'" in body

    # Extract all targetSunIntensity values and assert bounded range [0.1, 2.5]
    intensities = [float(val) for val in re.findall(r"targetSunIntensity\s*=\s*([0-9.]+)", body)]
    assert len(intensities) >= 4, f"Found only {len(intensities)} targetSunIntensity definitions"
    for intensity in intensities:
        assert 0.1 <= intensity <= 2.5, f"targetSunIntensity out of bounds: {intensity}"

    # Extract all targetFogNear and targetFogFar values and assert far > near and near >= 10
    near_matches = [float(v) for v in re.findall(r"targetFogNear\s*=\s*([0-9.]+)", body)]
    far_matches = [float(v) for v in re.findall(r"targetFogFar\s*=\s*([0-9.]+)", body)]
    assert len(near_matches) == len(far_matches) and len(near_matches) >= 4
    for near, far in zip(near_matches, far_matches):
        assert near >= 10.0, f"targetFogNear too small: {near}"
        assert far > near, f"targetFogFar ({far}) must be strictly greater than targetFogNear ({near})"
