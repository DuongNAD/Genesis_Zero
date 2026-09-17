"""Adversarial stress test suite for Genesis Zero 3D Spectator Scrubber & Replay Buffer.

Empirical Challenger verification for Milestone M4_SPECTATOR.
Validates boundary cases and hostile stress scenarios against web/watch3d.js:
1. Empty buffer behavior (tick 0, connect before ticks start).
2. Buffer saturation beyond 1200 frames (FIFO ring buffer sliding window without leak).
3. Out-of-bounds scrub requests (tick < min_buffered, tick > max_buffered, negative ticks).
4. Rapid scrub thrashing (150 random scrub jumps in milliseconds).
5. 1x / 2x / 5x playback speed transitions and simulated loop stepping intervals.
6. Live sync resumption (goToLive) from deep history with active stream hydration.
7. Rewind 10 and Forward 10 stepping boundary conditions.
8. Spacebar play/pause toggling and input tag event isolation.
9. Frame deduplication and in-place tick replacement.
10. Sustained high-throughput memory stress (10,000 frames under 15MB heap growth).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_BIN = shutil.which("node")

HARNESS_SETUP_JS = """
const fs = require('fs');
const vm = require('vm');

function createHarness() {
  const elements = new Map();
  function getOrCreateEl(id) {
    if (!elements.has(id)) {
      const initialClasses = new Set();
      let initialText = '';
      if (id === 'btn-live-sync') {
        initialClasses.add('btn-dock');
        initialClasses.add('live');
        initialClasses.add('active');
        initialText = '🔴 LIVE';
      } else if (id === 'btn-playback-toggle') {
        initialClasses.add('btn-dock');
        initialText = '⏸ Tạm dừng';
      } else if (id === 'btn-speed-1x') {
        initialClasses.add('btn-dock');
        initialClasses.add('active');
        initialText = '1x';
      } else if (id === 'btn-speed-2x' || id === 'btn-speed-5x') {
        initialClasses.add('btn-dock');
        initialText = id.replace('btn-speed-', '');
      }

      elements.set(id, {
        id,
        textContent: initialText,
        className: Array.from(initialClasses).join(' '),
        classList: {
          _classes: initialClasses,
          add(c) { this._classes.add(c); },
          remove(c) { this._classes.delete(c); },
          contains(c) { return this._classes.has(c); },
          toggle(c, force) {
            if (force === undefined) force = !this._classes.has(c);
            if (force) this._classes.add(c); else this._classes.delete(c);
            return force;
          }
        },
        style: {},
        value: '0',
        min: '0',
        max: '0',
        width: 132,
        height: 132,
        tagName: 'DIV',
        addEventListener(ev, fn) {
          this._listeners = this._listeners || {};
          (this._listeners[ev] = this._listeners[ev] || []).push(fn);
        },
        dispatchEvent(ev) {
          (this._listeners && this._listeners[ev.type] || []).forEach(fn => fn(ev));
        },
        appendChild() {},
        getContext() {
          return {
            fillRect(){}, clearRect(){}, beginPath(){}, arc(){}, fill(){}, stroke(){}
          };
        }
      });
    }
    return elements.get(id);
  }

  const mockDoc = {
    getElementById: getOrCreateEl,
    createElement(tag) { return getOrCreateEl('mock_' + tag); },
    body: getOrCreateEl('body')
  };

  let capturedWs = null;
  const windowListeners = {};
  let animationCb = null;
  let simulatedTime = 1000;
  const mockWindow = {
    document: mockDoc,
    location: { protocol: 'http:', host: 'localhost:8000' },
    innerWidth: 1920,
    innerHeight: 1080,
    devicePixelRatio: 1,
    addEventListener(ev, fn) {
      (windowListeners[ev] = windowListeners[ev] || []).push(fn);
    },
    removeEventListener() {},
    requestAnimationFrame(cb) {
      animationCb = cb;
      return 1;
    },
    performance: { now: () => simulatedTime },
    AudioContext: class {
      constructor() { this.currentTime = 0; this.destination = {}; }
      createGain() {
        return {
          gain: {
            setValueAtTime() {},
            linearRampToValueAtTime() {},
            exponentialRampToValueAtTime() {}
          },
          connect() {}
        };
      }
      createDynamicsCompressor() {
        return {
          threshold: { value: 0 },
          knee: { value: 0 },
          ratio: { value: 0 },
          attack: { value: 0 },
          release: { value: 0 },
          connect() {}
        };
      }
      createOscillator() {
        return {
          type: '',
          frequency: {
            setValueAtTime() {},
            exponentialRampToValueAtTime() {},
            linearRampToValueAtTime() {}
          },
          connect() {},
          start() {},
          stop() {}
        };
      }
      createBiquadFilter() {
        return {
          type: '',
          frequency: {
            setValueAtTime() {},
            exponentialRampToValueAtTime() {}
          },
          Q: { value: 0 },
          connect() {}
        };
      }
      resume() { return Promise.resolve(); }
    },
    WebSocket: class {
      constructor(url) { capturedWs = this; this.url = url; }
      send() {}
      close() {}
    }
  };

  const sandbox = {
    window: mockWindow,
    document: mockDoc,
    location: mockWindow.location,
    innerWidth: 1920,
    innerHeight: 1080,
    devicePixelRatio: 1,
    addEventListener: mockWindow.addEventListener,
    performance: mockWindow.performance,
    requestAnimationFrame: mockWindow.requestAnimationFrame,
    AudioContext: mockWindow.AudioContext,
    WebSocket: mockWindow.WebSocket,
    console: console,
    setTimeout: () => {},
    clearTimeout: () => {}
  };

  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync('web/vendor/three.min.js', 'utf8'), sandbox);
  sandbox.THREE.WebGLRenderer = class {
    constructor() {
      this.domElement = getOrCreateEl('scene_canvas');
      this.shadowMap = {};
    }
    setPixelRatio() {}
    setSize() {}
    render() {}
  };

  vm.runInContext(fs.readFileSync('web/watch3d.js', 'utf8'), sandbox);

  return {
    sandbox,
    getEl: getOrCreateEl,
    getWs: () => capturedWs,
    windowListeners,
    advanceTime: (dt) => { simulatedTime += dt; },
    stepLoop: () => { if (animationCb) animationCb(); },
    pushFrame: (f) => capturedWs.onmessage({ data: JSON.stringify(f) })
  };
}
"""


def _run_node_script(script: str) -> dict:
    """Execute a Node.js verification script with the watch3d harness and return parsed JSON."""
    assert NODE_BIN, "Node.js executable is required for empirical visualizer stress testing"
    full_script = HARNESS_SETUP_JS + "\n" + script
    proc = subprocess.run(
        [NODE_BIN, "-e", full_script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if proc.returncode != 0:
        pytest.fail(
            f"Node.js empirical test failed (exit code {proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return json.loads(proc.stdout.strip())


def test_scrubber_empty_buffer_boundary():
    """Verify scrubber gracefully tolerates empty buffer (tick 0, connect before ticks)."""
    script = """
    const h = createHarness();
    let errors = [];

    // Trigger all interactive controls on an empty buffer
    try { h.getEl('btn-rewind-10').dispatchEvent({ type: 'click' }); } catch(e) { errors.push(e.message); }
    try { h.getEl('btn-forward-10').dispatchEvent({ type: 'click' }); } catch(e) { errors.push(e.message); }
    try { h.getEl('btn-playback-toggle').dispatchEvent({ type: 'click' }); } catch(e) { errors.push(e.message); }

    // Input on slider with empty buffer
    const slider = h.getEl('timeline-slider');
    try {
      slider.value = '100';
      slider.dispatchEvent({ type: 'input', target: slider });
    } catch(e) { errors.push(e.message); }

    try {
      slider.value = '-50';
      slider.dispatchEvent({ type: 'input', target: slider });
    } catch(e) { errors.push(e.message); }

    // Clicking live sync restores live state even after out-of-bounds input
    try { h.getEl('btn-live-sync').dispatchEvent({ type: 'click' }); } catch(e) { errors.push(e.message); }

    // Stepping loop on empty buffer
    try {
      h.advanceTime(200);
      h.stepLoop();
    } catch(e) { errors.push(e.message); }

    const buf = h.sandbox.window.Genesis3D.historyBuffer;
    console.log(JSON.stringify({
      errors,
      bufferLength: buf.length,
      tickDisplay: h.getEl('timeline-tick-display').textContent,
      liveActive: h.getEl('btn-live-sync').classList.contains('active')
    }));
    """
    res = _run_node_script(script)
    assert res["errors"] == [], f"Empty buffer operations threw exceptions: {res['errors']}"
    assert res["bufferLength"] == 0
    assert res["liveActive"] is True


def test_scrubber_buffer_saturation_and_fifo_eviction():
    """Verify 1200 frame ring buffer enforces strict FIFO eviction without overflowing."""
    script = """
    const h = createHarness();

    // 1. Fill exactly to 1200 capacity
    for (let i = 0; i < 1200; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: []
      });
    }

    const buf = h.sandbox.window.Genesis3D.historyBuffer;
    const lenAt1200 = buf.length;
    const minAt1200 = buf[0].t;
    const maxAt1200 = buf[buf.length - 1].t;

    // 2. Push 1 frame more (tick 1200): must evict tick 0, length remains 1200
    h.pushFrame({
      t: 1200,
      phase: 'RUNNING',
      weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
      creatures: []
    });

    const lenAt1201 = buf.length;
    const minAt1201 = buf[0].t;
    const maxAt1201 = buf[buf.length - 1].t;

    // 3. Saturate up to 2500 frames
    for (let i = 1201; i <= 2500; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: []
      });
    }

    const lenAt2500 = buf.length;
    const minAt2500 = buf[0].t;
    const maxAt2500 = buf[buf.length - 1].t;
    const slider = h.getEl('timeline-slider');

    console.log(JSON.stringify({
      lenAt1200, minAt1200, maxAt1200,
      lenAt1201, minAt1201, maxAt1201,
      lenAt2500, minAt2500, maxAt2500,
      sliderMin: parseInt(slider.min, 10),
      sliderMax: parseInt(slider.max, 10),
      sliderVal: parseInt(slider.value, 10)
    }));
    """
    res = _run_node_script(script)
    assert res["lenAt1200"] == 1200
    assert res["minAt1200"] == 0
    assert res["maxAt1200"] == 1199

    assert res["lenAt1201"] == 1200
    assert res["minAt1201"] == 1
    assert res["maxAt1201"] == 1200

    assert res["lenAt2500"] == 1200
    assert res["minAt2500"] == 1301
    assert res["maxAt2500"] == 2500
    assert res["sliderMin"] == 1301
    assert res["sliderMax"] == 2500
    assert res["sliderVal"] == 2500


def test_scrubber_out_of_bounds_clamping_and_nearest_snap():
    """Verify out-of-bounds scrub requests gracefully clamp to boundaries or resume live."""
    script = """
    const h = createHarness();

    // Fill frames 500..700
    for (let i = 500; i <= 700; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: [{ id: 'L1:0', x: 5, y: 5, hp: 50, e: 80, e_max: 100, alive: true, species: 'L1', domain: 'CAN', tr: [2,2,2,2,2,2] }]
      });
    }

    const slider = h.getEl('timeline-slider');

    // 1. Scrub to tick 200 (well below minimum 500)
    slider.value = '200';
    slider.dispatchEvent({ type: 'input', target: slider });
    const belowMinSliderVal = parseInt(slider.value, 10);
    const belowMinTickText = h.getEl('timeline-tick-display').textContent;
    const belowMinLive = h.getEl('btn-live-sync').classList.contains('active');

    // 2. Scrub to negative tick -999
    slider.value = '-999';
    slider.dispatchEvent({ type: 'input', target: slider });
    const negSliderVal = parseInt(slider.value, 10);

    // 3. Scrub to tick 99999 (far in future beyond max 700) -> must trigger goToLive()
    slider.value = '99999';
    slider.dispatchEvent({ type: 'input', target: slider });
    const futureSliderVal = parseInt(slider.value, 10);
    const futureTickText = h.getEl('timeline-tick-display').textContent;
    const futureLive = h.getEl('btn-live-sync').classList.contains('active');

    console.log(JSON.stringify({
      belowMinSliderVal,
      belowMinTickText,
      belowMinLive,
      negSliderVal,
      futureSliderVal,
      futureTickText,
      futureLive
    }));
    """
    res = _run_node_script(script)
    assert res["belowMinSliderVal"] == 500
    assert "500 / 700" in res["belowMinTickText"]
    assert res["belowMinLive"] is False

    assert res["negSliderVal"] == 500

    assert res["futureSliderVal"] == 700
    assert "700 / 700" in res["futureTickText"]
    assert res["futureLive"] is True


def test_scrubber_rapid_thrashing_stress():
    """Verify rapid chaotic scrub jumping maintains state invariants and coordinates."""
    script = """
    const h = createHarness();

    // Populate 600 frames
    for (let i = 0; i < 600; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: [
          { id: 'L1:0', x: (i * 2) % 20, y: (i * 3) % 20, hp: 50, e: 80, e_max: 100, alive: true, species: 'L1', domain: 'CAN', tr: [2,2,2,2,2,2] }
        ]
      });
    }

    const slider = h.getEl('timeline-slider');
    let errors = [];

    // Rapid thrash: 150 random jumps across wide tick span
    for (let step = 0; step < 150; step++) {
      const targetTick = Math.floor(Math.sin(step * 3.7) * 400 + 300);
      try {
        slider.value = String(targetTick);
        slider.dispatchEvent({ type: 'input', target: slider });
      } catch (e) {
        errors.push({ step, targetTick, error: e.message });
      }
    }

    // Snap to live
    h.getEl('btn-live-sync').dispatchEvent({ type: 'click' });

    console.log(JSON.stringify({
      errorsCount: errors.length,
      finalSliderVal: parseInt(slider.value, 10),
      finalTickDisplay: h.getEl('timeline-tick-display').textContent,
      liveActive: h.getEl('btn-live-sync').classList.contains('active')
    }));
    """
    res = _run_node_script(script)
    assert res["errorsCount"] == 0
    assert res["finalSliderVal"] == 599
    assert "599 / 599" in res["finalTickDisplay"]
    assert res["liveActive"] is True


def test_scrubber_speed_transitions_and_playback_clock():
    """Verify 1x, 2x, 5x speed buttons and loop step intervals."""
    script = """
    const h = createHarness();

    for (let i = 0; i <= 50; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: []
      });
    }

    // 1. Check speed button mutual exclusivity
    h.getEl('btn-speed-2x').dispatchEvent({ type: 'click' });
    const s2Active = h.getEl('btn-speed-2x').classList.contains('active');
    const s1ActiveUnder2 = h.getEl('btn-speed-1x').classList.contains('active');
    const s5ActiveUnder2 = h.getEl('btn-speed-5x').classList.contains('active');

    h.getEl('btn-speed-5x').dispatchEvent({ type: 'click' });
    const s5Active = h.getEl('btn-speed-5x').classList.contains('active');
    const s2ActiveUnder5 = h.getEl('btn-speed-2x').classList.contains('active');

    h.getEl('btn-speed-1x').dispatchEvent({ type: 'click' });
    const s1Active = h.getEl('btn-speed-1x').classList.contains('active');

    // 2. Test replay stepping at 1x (120ms interval)
    const slider = h.getEl('timeline-slider');
    slider.value = '10';
    slider.dispatchEvent({ type: 'input', target: slider });

    // Initial step initializes lastPlaybackStepTime and steps 10 -> 11
    h.stepLoop();
    const tickInitial = parseInt(slider.value, 10);

    // Advance 60ms (< 120ms interval): tick should not advance yet
    h.advanceTime(60);
    h.stepLoop();
    const tickAfter60ms = parseInt(slider.value, 10);

    // Advance another 60ms (total 120ms): tick must advance to 12
    h.advanceTime(60);
    h.stepLoop();
    const tickAfter120ms = parseInt(slider.value, 10);

    // 3. Switch to 2x speed (60ms interval) and advance 60ms -> advances to 13
    h.getEl('btn-speed-2x').dispatchEvent({ type: 'click' });
    h.advanceTime(60);
    h.stepLoop();
    const tickAfter60msAt2x = parseInt(slider.value, 10);

    // 4. Switch to 5x speed (24ms interval) and advance 25ms -> advances to 14
    h.getEl('btn-speed-5x').dispatchEvent({ type: 'click' });
    h.advanceTime(25);
    h.stepLoop();
    const tickAfter25msAt5x = parseInt(slider.value, 10);

    // 5. Fast forward to end of replay buffer (tick 50)
    for (let k = 0; k < 45; k++) {
      h.advanceTime(25);
      h.stepLoop();
    }
    const tickAtReplayEnd = parseInt(slider.value, 10);
    const liveAtReplayEnd = h.getEl('btn-live-sync').classList.contains('active');

    console.log(JSON.stringify({
      s2Active, s1ActiveUnder2, s5ActiveUnder2,
      s5Active, s2ActiveUnder5, s1Active,
      tickInitial,
      tickAfter60ms,
      tickAfter120ms,
      tickAfter60msAt2x,
      tickAfter25msAt5x,
      tickAtReplayEnd,
      liveAtReplayEnd
    }));
    """
    res = _run_node_script(script)
    assert res["s2Active"] is True and not res["s1ActiveUnder2"] and not res["s5ActiveUnder2"]
    assert res["s5Active"] is True and not res["s2ActiveUnder5"]
    assert res["s1Active"] is True
    assert res["tickInitial"] == 11
    assert res["tickAfter60ms"] == 11
    assert res["tickAfter120ms"] == 12
    assert res["tickAfter60msAt2x"] == 13
    assert res["tickAfter25msAt5x"] == 14
    assert res["tickAtReplayEnd"] == 50
    assert res["liveAtReplayEnd"] is True


def test_scrubber_live_resync_from_deep_history():
    """Verify scrubbing deep into history preserves user focus during active stream hydration."""
    script = """
    const h = createHarness();

    // Populate initial 50 ticks
    for (let i = 0; i <= 50; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: [{ id: 'L1:0', x: i, y: i, hp: 50, e: 80, e_max: 100, alive: true, species: 'L1', domain: 'CAN', tr: [2,2,2,2,2,2] }]
      });
    }

    // User pauses and scrubs deep into history at tick 12
    h.getEl('btn-playback-toggle').dispatchEvent({ type: 'click' }); // pause
    const slider = h.getEl('timeline-slider');
    slider.value = '12';
    slider.dispatchEvent({ type: 'input', target: slider });

    const viewAtScrub = parseInt(h.getEl('tick').textContent, 10);
    const isLiveAtScrub = h.getEl('btn-live-sync').classList.contains('active');

    // 20 new frames arrive over WebSocket (ticks 51..70) while user is inspecting tick 12
    for (let i = 51; i <= 70; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: [{ id: 'L1:0', x: i, y: i, hp: 50, e: 80, e_max: 100, alive: true, species: 'L1', domain: 'CAN', tr: [2,2,2,2,2,2] }]
      });
    }

    // Spectator view must STILL be at tick 12, not hijacked by incoming live frames
    const viewWhileHydrating = parseInt(h.getEl('tick').textContent, 10);
    const sliderMaxWhileHydrating = parseInt(slider.max, 10);
    const displayWhileHydrating = h.getEl('timeline-tick-display').textContent;

    // User clicks LIVE sync button
    h.getEl('btn-live-sync').dispatchEvent({ type: 'click' });

    const viewAfterLiveSync = parseInt(h.getEl('tick').textContent, 10);
    const sliderValAfterLiveSync = parseInt(slider.value, 10);
    const isLiveAfterSync = h.getEl('btn-live-sync').classList.contains('active');

    // Next incoming frame (71) should now render immediately live
    h.pushFrame({
      t: 71,
      phase: 'RUNNING',
      weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
      creatures: [{ id: 'L1:0', x: 71, y: 71, hp: 50, e: 80, e_max: 100, alive: true, species: 'L1', domain: 'CAN', tr: [2,2,2,2,2,2] }]
    });

    const viewAtTick71 = parseInt(h.getEl('tick').textContent, 10);

    console.log(JSON.stringify({
      viewAtScrub, isLiveAtScrub,
      viewWhileHydrating, sliderMaxWhileHydrating, displayWhileHydrating,
      viewAfterLiveSync, sliderValAfterLiveSync, isLiveAfterSync,
      viewAtTick71
    }));
    """
    res = _run_node_script(script)
    assert res["viewAtScrub"] == 12
    assert res["isLiveAtScrub"] is False
    assert res["viewWhileHydrating"] == 12
    assert res["sliderMaxWhileHydrating"] == 70
    assert "12 / 70" in res["displayWhileHydrating"]
    assert res["viewAfterLiveSync"] == 70
    assert res["sliderValAfterLiveSync"] == 70
    assert res["isLiveAfterSync"] is True
    assert res["viewAtTick71"] == 71


def test_scrubber_rewind10_and_forward10_steppers():
    """Verify rewind10 and forward10 step buttons clamp to boundary limits."""
    script = """
    const h = createHarness();

    // Populate 50 ticks (0..50)
    for (let i = 0; i <= 50; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
        creatures: []
      });
    }

    const slider = h.getEl('timeline-slider');

    // 1. Rewind from live (tick 50) -> should be 40
    h.getEl('btn-rewind-10').dispatchEvent({ type: 'click' });
    const tickAfterRewind1 = parseInt(slider.value, 10);
    const liveAfterRewind1 = h.getEl('btn-live-sync').classList.contains('active');

    // 2. Rewind 6 more times -> should clamp at 0 without going negative
    for (let i = 0; i < 6; i++) {
      h.getEl('btn-rewind-10').dispatchEvent({ type: 'click' });
    }
    const tickAtFloor = parseInt(slider.value, 10);

    // 3. Forward 10 from 0 -> should be 10
    h.getEl('btn-forward-10').dispatchEvent({ type: 'click' });
    const tickAfterFwd1 = parseInt(slider.value, 10);

    // 4. Forward 4 more times (to 50) -> should trigger goToLive
    for (let i = 0; i < 4; i++) {
      h.getEl('btn-forward-10').dispatchEvent({ type: 'click' });
    }
    const tickAtMax = parseInt(slider.value, 10);
    const liveAtMax = h.getEl('btn-live-sync').classList.contains('active');

    console.log(JSON.stringify({
      tickAfterRewind1,
      liveAfterRewind1,
      tickAtFloor,
      tickAfterFwd1,
      tickAtMax,
      liveAtMax
    }));
    """
    res = _run_node_script(script)
    assert res["tickAfterRewind1"] == 40
    assert res["liveAfterRewind1"] is False
    assert res["tickAtFloor"] == 0
    assert res["tickAfterFwd1"] == 10
    assert res["tickAtMax"] == 50
    assert res["liveAtMax"] is True


def test_scrubber_spacebar_toggle_and_input_isolation():
    """Verify Spacebar toggles playback state while ignoring input element keystrokes."""
    script = """
    const h = createHarness();

    const keyListeners = h.windowListeners['keydown'] || [];
    const btn = h.getEl('btn-playback-toggle');

    const initialText = btn.textContent;

    // Press spacebar on BODY
    keyListeners.forEach(fn => fn({ key: ' ', code: 'Space', target: { tagName: 'BODY' }, preventDefault() {} }));
    const textAfterSpace1 = btn.textContent;

    // Press spacebar while focused in an INPUT element (must NOT toggle)
    keyListeners.forEach(fn => fn({ key: ' ', code: 'Space', target: { tagName: 'INPUT' }, preventDefault() {} }));
    const textAfterSpaceInput = btn.textContent;

    // Press spacebar again on BODY (toggles back)
    keyListeners.forEach(fn => fn({ key: ' ', code: 'Space', target: { tagName: 'BODY' }, preventDefault() {} }));
    const textAfterSpace2 = btn.textContent;

    console.log(JSON.stringify({
      initialText,
      textAfterSpace1,
      textAfterSpaceInput,
      textAfterSpace2
    }));
    """
    res = _run_node_script(script)
    assert "Tạm dừng" in res["initialText"]
    assert "Tiếp tục" in res["textAfterSpace1"]
    assert "Tiếp tục" in res["textAfterSpaceInput"]
    assert "Tạm dừng" in res["textAfterSpace2"]


def test_scrubber_frame_deduplication_and_in_place_update():
    """Verify duplicate incoming frames with the same tick update in place."""
    script = """
    const h = createHarness();

    // Push initial frame 10
    h.pushFrame({
      t: 10,
      phase: 'RUNNING',
      map: 'MAP_A',
      weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
      creatures: []
    });

    const buf = h.sandbox.window.Genesis3D.historyBuffer;
    const len1 = buf.length;
    const map1 = buf[0].map;

    // Push duplicate frame 10 with updated payload
    h.pushFrame({
      t: 10,
      phase: 'RUNNING',
      map: 'MAP_B_UPDATED',
      weather: { state: 'CLEAR', diurnal: 'DAY', progress: 0, modifiers: {} },
      creatures: []
    });

    const len2 = buf.length;
    const map2 = buf[0].map;

    console.log(JSON.stringify({
      len1, map1, len2, map2
    }));
    """
    res = _run_node_script(script)
    assert res["len1"] == 1
    assert res["map1"] == "MAP_A"
    assert res["len2"] == 1
    assert res["map2"] == "MAP_B_UPDATED"


def test_scrubber_memory_leak_and_fifo_durability_10000_frames():
    """Verify 10,000 frames under continuous streaming keep buffer capped and memory bounded."""
    script = """
    const h = createHarness();

    const initialMem = process.memoryUsage().heapUsed;

    for (let i = 0; i < 10000; i++) {
      h.pushFrame({
        t: i,
        phase: 'RUNNING',
        weather: { state: 'CLEAR', diurnal: 'DAY', progress: (i % 50) / 50, modifiers: {} },
        creatures: [
          { id: 'L1:0', x: (i % 24), y: ((i * 3) % 24), hp: 50, e: 80, e_max: 100, alive: true, species: 'L1', domain: 'CAN', tr: [2,2,2,2,2,2] },
          { id: 'L2:1', x: ((i * 5) % 24), y: (i % 24), hp: 40, e: 60, e_max: 90, alive: true, species: 'L2', domain: 'NUOC', tr: [1,3,2,3,1,2] }
        ]
      });
    }

    const finalMem = process.memoryUsage().heapUsed;
    const buf = h.sandbox.window.Genesis3D.historyBuffer;
    const memDeltaMB = (finalMem - initialMem) / (1024 * 1024);

    let isStrictlyMonotonic = true;
    for (let j = 1; j < buf.length; j++) {
      if (buf[j].t !== buf[j - 1].t + 1) {
        isStrictlyMonotonic = false;
        break;
      }
    }

    console.log(JSON.stringify({
      bufferLength: buf.length,
      firstTick: buf[0].t,
      lastTick: buf[buf.length - 1].t,
      memDeltaMB: parseFloat(memDeltaMB.toFixed(2)),
      isStrictlyMonotonic
    }));
    """
    res = _run_node_script(script)
    assert res["bufferLength"] == 1200
    assert res["firstTick"] == 8800
    assert res["lastTick"] == 9999
    assert res["isStrictlyMonotonic"] is True
    # Memory growth for 10k frames in bounded buffer should be well under 15MB
    assert res["memDeltaMB"] < 15.0, f"Excessive heap memory growth: {res['memDeltaMB']}MB"
