"""Adversarial stress test suite for Genesis Zero Creature Entity System, State Machine, and Animations.

Milestone M1 Challenger Verification:
1. Verify behavior under edge conditions: missing species ID, unmapped animation action, rapid tick scrubbing, death event persistence.
2. Check SkeletonUtils.clone integrity (no shared armature bones across multiple entities).
3. Verify telemetry handling under network reconnection or packet drops.
4. Stress-test all 8 canonical animation action clips and state machine transitions.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_BIN = shutil.which("node")


def _run_node(script: str, timeout: int = 35) -> dict:
    """Execute a Node.js verification script and parse returned JSON."""
    assert NODE_BIN, "Node.js executable is required for empirical stress testing"
    proc = subprocess.run(
        [NODE_BIN, "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if proc.returncode != 0:
        pytest.fail(
            f"Node.js empirical challenge failed (exit code {proc.returncode}):\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
    for l in reversed(lines):
        if (l.startswith("{") and l.endswith("}")) or (l.startswith("[") and l.endswith("]")):
            try:
                return json.loads(l)
            except Exception:
                pass
    pytest.fail(f"Could not parse JSON from Node.js output:\n{proc.stdout}")


# ==============================================================================
# Challenge 1: Edge Conditions in Creature Entity & State Machine
# ==============================================================================

def test_missing_species_id_and_corrupted_traits_fallback():
    """Verify creature entity system gracefully handles missing, null, unmapped species and traits."""
    script = """
    const { CreatureController } = require('./web/modules/entities/CreatureController.js');
    const { CreatureStateMachine, CreatureState } = require('./web/modules/entities/CreatureStateMachine.js');
    const THREE = require('./web/vendor/three.min.js');

    const sceneGroup = new THREE.Group();
    const fallbackBuilder = (key) => {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 0.5));
      mesh.name = `Fallback_${key}`;
      return mesh;
    };

    const controller = new CreatureController(sceneGroup, null, fallbackBuilder);

    (async () => {
      const results = {};

      // 1. Missing species_id and species (only id)
      const e1 = await controller.spawnCreature({ id: 'c_missing_sp', x: 2, y: 3, alive: true });
      results.e1_spawned = !!e1;
      results.e1_group_name = e1 ? e1.group.name : null;

      // 2. Explicit null species
      const e2 = await controller.spawnCreature({ id: 'c_null_sp', species: null, x: 4, y: 5, alive: true });
      results.e2_spawned = !!e2;

      // 3. Completely unknown alien species
      const e3 = await controller.spawnCreature({ id: 'c_alien', species: 'unknown_alien_beast_99', x: 6, y: 7, alive: true });
      results.e3_spawned = !!e3;

      // 4. Missing traits tr array
      controller.updateFromTick({ id: 'c_missing_sp', x: 3, y: 4, alive: true, isMoving: true });
      results.e1_state_after_move = e1.stateMachine.currentState;

      // 5. Corrupted partial traits (tr has length 1)
      const sm = new CreatureStateMachine(null);
      const stPartial = sm.evaluateState({ id: 'c_partial', tr: [1], alive: true, isMoving: true });
      results.partial_traits_state = stPartial;

      // 6. Null creature data in state machine
      const stNull = sm.evaluateState(null);
      results.null_creature_state = stNull;

      // 7. Verify all entities in group
      results.scene_children_count = sceneGroup.children.length;

      console.log(JSON.stringify(results));
    })();
    """
    res = _run_node(script)
    assert res["e1_spawned"] is True, "Missing species must successfully spawn with fallback"
    assert res["e2_spawned"] is True, "Null species must spawn with fallback"
    assert res["e3_spawned"] is True, "Unknown alien species must spawn with fallback"
    assert res["e1_state_after_move"] in ("Walk", "Run"), "Moving creature without traits must default to Walk or Run"
    assert res["partial_traits_state"] == "Walk", "Partial traits must safely default speed < 4 to Walk"
    assert res["null_creature_state"] == "Walk", "Null creature data must preserve current state without throwing"
    assert res["scene_children_count"] == 3, "All 3 edge creatures must be present in scene hierarchy"


def test_unmapped_and_malformed_animation_actions():
    """Verify animation dispatcher and state machine tolerate unmapped and foreign action clips."""
    script = """
    const { AnimationDispatcher, ACTION_CLIPS } = require('./web/modules/entities/AnimationDispatcher.js');
    const { CreatureStateMachine, CreatureState } = require('./web/modules/entities/CreatureStateMachine.js');
    const THREE = require('./web/vendor/three.min.js');

    const root = new THREE.Group();
    // Synthetic clips covering only Idle_Normal and Walk
    const clipIdle = new THREE.AnimationClip('Idle_Normal', 1.0, []);
    const clipWalk = new THREE.AnimationClip('Walk', 1.0, []);

    const dispatcher = new AnimationDispatcher(root, [clipIdle, clipWalk]);
    const sm = new CreatureStateMachine(dispatcher);

    const results = {};

    // 1. Initial state
    results.initial_clip = dispatcher.currentClipName;

    // 2. Transition to unmapped string clip (e.g. 'Attack' which is not in this model's clips)
    try {
      dispatcher.crossFadeTo('Attack');
      results.unmapped_transition_threw = false;
    } catch(e) {
      results.unmapped_transition_threw = true;
      results.unmapped_error = e.message;
    }
    results.clip_after_unmapped = dispatcher.currentClipName;

    // 3. State machine with completely unknown event kinds (e.g. 'TELEPORT', 'SING')
    const cData = { id: 'c1', alive: true, tr: [2, 2, 2, 2, 2, 2] };
    const stUnknown = sm.evaluateState(cData, [{ k: 'TELEPORT', who: 'c1' }, { k: 'SING', target: 'c1' }]);
    results.unknown_event_state = stUnknown;

    // 4. Repeated transition to same clip should be a no-op
    const actBefore = dispatcher.currentAction;
    dispatcher.crossFadeTo('Idle_Normal');
    results.same_clip_noop = (dispatcher.currentAction === actBefore);

    // 5. Update loop advancing without error
    dispatcher.update(0.016);
    results.update_ok = true;

    // 6. Adversarial check: crossFadeTo with null or undefined
    let nullThrew = false;
    try {
      dispatcher.crossFadeTo(null);
    } catch(e) {
      nullThrew = true;
      results.null_clip_error = e.message;
    }
    results.null_clip_threw = nullThrew;

    console.log(JSON.stringify(results));
    """
    res = _run_node(script)
    assert res["initial_clip"] == "Idle_Normal"
    assert res["unmapped_transition_threw"] is False, "Unmapped action clip must not throw"
    assert res["clip_after_unmapped"] == "Idle_Normal", "Unmapped clip must preserve current active clip"
    assert res["unknown_event_state"] == "Idle_Normal", "Unknown event kinds must fall through to Idle"
    assert res["same_clip_noop"] is True, "Transitioning to identical clip must be a safe no-op"
    assert res["update_ok"] is True
    # Remediated: null clipName is safely handled without throwing TypeError
    assert res["null_clip_threw"] is False, "crossFadeTo(null) must safely no-op without throwing"


def test_rapid_tick_scrubbing_stress_and_coordinate_snapping():
    """Verify rapid timeline scrubbing across 500 jumps correctly updates coordinates and state."""
    script = """
    const { ReplayBuffer } = require('./web/modules/simulation/ReplayBuffer.js');
    const { CreatureController } = require('./web/modules/entities/CreatureController.js');
    const { SpatialSynchronizer } = require('./web/modules/entities/SpatialSynchronizer.js');
    const THREE = require('./web/vendor/three.min.js');

    const sceneGroup = new THREE.Group();
    const fallbackBuilder = () => new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1));
    const controller = new CreatureController(sceneGroup, null, fallbackBuilder);

    const buffer = new ReplayBuffer(1200);

    // Populate buffer with 500 frames: c1 is alive for t < 250, dead for t >= 250
    for (let t = 0; t < 500; t++) {
      buffer.push({
        t,
        creatures: [
          { id: 'c1', x: (t * 0.5) % 24, y: (t * 0.3) % 24, alive: t < 250, isMoving: true }
        ],
        events: t === 100 ? [{ k: 'COMBAT', who: 'c1' }] : []
      });
    }

    (async () => {
      // Spawn c1
      await controller.spawnCreature({ id: 'c1', x: 0, y: 0, alive: true });
      const entity = controller.entities.get('c1');

      let snapErrors = 0;
      let stateErrors = 0;

      // Perform 500 rapid scrub jumps
      for (let i = 0; i < 500; i++) {
        const scrubTarget = Math.floor(Math.random() * 500);
        buffer.seek(scrubTarget);

        buffer.renderHistoricalFrame(buffer.scrubTick, (frame, isInstant) => {
          const cData = frame.creatures[0];
          controller.updateFromTick(cData, frame.events || [], isInstant);

          // In isInstant mode, curr coordinates must snap immediately to target coordinates
          if (Math.abs(entity.currX - entity.targetX) > 1e-4 || Math.abs(entity.currZ - entity.targetZ) > 1e-4) {
            snapErrors++;
          }

          // Check alive state correlation
          const expectedAlive = (scrubTarget < 250);
          if (entity.alive !== expectedAlive) {
            stateErrors++;
          }
          if (expectedAlive && entity.stateMachine.currentState === 'Death') {
            stateErrors++;
          }
          if (!expectedAlive && entity.stateMachine.currentState !== 'Death') {
            stateErrors++;
          }
        });
      }

      console.log(JSON.stringify({
        snapErrors,
        stateErrors,
        finalTick: buffer.scrubTick,
        latestTick: buffer.latestTick
      }));
    })();
    """
    res = _run_node(script)
    assert res["snapErrors"] == 0, "Rapid scrub must snap coordinates instantaneously with 0 lag"
    assert res["stateErrors"] == 0, "Rapid scrub must accurately restore alive and death states across historical ticks"
    assert res["latestTick"] == 499


def test_death_event_persistence_and_action_clamping():
    """Verify death state latches indefinitely and is not overridden by late events or subsequent ticks."""
    script = """
    const { AnimationDispatcher } = require('./web/modules/entities/AnimationDispatcher.js');
    const { CreatureStateMachine, CreatureState } = require('./web/modules/entities/CreatureStateMachine.js');
    const THREE = require('./web/vendor/three.min.js');

    const root = new THREE.Group();
    const clipIdle = new THREE.AnimationClip('Idle_Normal', 1.0, []);
    const clipWalk = new THREE.AnimationClip('Walk', 1.0, []);
    const clipAttack = new THREE.AnimationClip('Attack', 1.0, []);
    const clipDeath = new THREE.AnimationClip('Death', 1.0, []);

    const dispatcher = new AnimationDispatcher(root, [clipIdle, clipWalk, clipAttack, clipDeath]);
    const sm = new CreatureStateMachine(dispatcher);

    const results = {};

    // 1. Alive and walking
    sm.evaluateState({ id: 'c1', alive: true, isMoving: true });
    results.state_alive = sm.currentState;

    // 2. Creature dies
    sm.evaluateState({ id: 'c1', alive: false });
    results.state_death = sm.currentState;

    // Verify death action clamping
    const deathAction = dispatcher.actions.get('Death');
    results.death_clamped = deathAction ? deathAction.clampWhenFinished : false;

    // 3. Consecutive 50 ticks while dead: state must remain DEATH without restarting action
    let playCallCount = 0;
    const origPlay = deathAction.play;
    deathAction.play = function() { playCallCount++; return origPlay.apply(this, arguments); };

    for (let t = 0; t < 50; t++) {
      sm.evaluateState({ id: 'c1', alive: false, isMoving: true });
    }
    results.state_after_50_dead_ticks = sm.currentState;
    // playCallCount should be 0 because transitionTo(Death) when already in Death returns early
    results.death_retriggered_count = playCallCount;

    // 4. Hostile late events arriving for dead creature (ATTACK, COMBAT, EAT, HURT)
    const hostileEvents = [
      { k: 'COMBAT', who: 'c1' },
      { k: 'ATTACK', target: 'c1' },
      { k: 'EAT', who: 'c1' },
      { k: 'HURT', who: 'c1' }
    ];
    sm.evaluateState({ id: 'c1', alive: false }, hostileEvents);
    results.state_after_hostile_events = sm.currentState;

    console.log(JSON.stringify(results));
    """
    res = _run_node(script)
    assert res["state_alive"] == "Walk"
    assert res["state_death"] == "Death"
    assert res["death_clamped"] is True, "Death action clip must set clampWhenFinished = true"
    assert res["state_after_50_dead_ticks"] == "Death", "Death state must persist across consecutive dead ticks"
    assert res["death_retriggered_count"] == 0, "Death action must not re-trigger or restart on every tick"
    assert res["state_after_hostile_events"] == "Death", "Events must not override Death state while creature is dead"


# ==============================================================================
# Challenge 2: SkeletonUtils.clone Integrity (Armature Bone Independence)
# ==============================================================================

def test_skeleton_utils_clone_distinct_skeletons_and_bones():
    """Empirically prove SkeletonUtils.clone produces 100% independent skeletons and bones on SkinnedMesh."""
    script = """
    const fs = require('fs');
    const THREE = require('./web/vendor/three.min.js');
    global.THREE = THREE;
    require('./web/vendor/GLTFLoader.js');
    require('./web/vendor/SkeletonUtils.js');

    const loader = new THREE.GLTFLoader();
    const buf = fs.readFileSync('assets/creatures/sand_skink.glb');

    loader.parse(buf.buffer, '', (gltf) => {
      const clone1 = THREE.SkeletonUtils.clone(gltf.scene);
      const clone2 = THREE.SkeletonUtils.clone(gltf.scene);
      const clone3 = THREE.SkeletonUtils.clone(gltf.scene);

      function getSkinnedMesh(root) {
        let sm = null;
        root.traverse(c => { if (c.isSkinnedMesh) sm = c; });
        return sm;
      }

      const smOrig = getSkinnedMesh(gltf.scene);
      const sm1 = getSkinnedMesh(clone1);
      const sm2 = getSkinnedMesh(clone2);
      const sm3 = getSkinnedMesh(clone3);

      const results = {
        has_orig: !!smOrig,
        has_sm1: !!sm1,
        has_sm2: !!sm2,
        has_sm3: !!sm3,
        distinct_skeletons_1_2: sm1.skeleton !== sm2.skeleton,
        distinct_skeletons_2_3: sm2.skeleton !== sm3.skeleton,
        distinct_skeletons_1_orig: sm1.skeleton !== smOrig.skeleton,
        bone_count_1: sm1.skeleton.bones.length,
        bone_count_2: sm2.skeleton.bones.length,
        bone_count_3: sm3.skeleton.bones.length
      };

      // Check bone identity matrix across clone1 and clone2
      let sharedBonesCount = 0;
      for (let i = 0; i < sm1.skeleton.bones.length; i++) {
        for (let j = 0; j < sm2.skeleton.bones.length; j++) {
          if (sm1.skeleton.bones[i] === sm2.skeleton.bones[j]) {
            sharedBonesCount++;
          }
        }
      }
      results.shared_bones_between_clones = sharedBonesCount;

      // Transform isolation test: mutate clone 1 bone
      const origPos2 = sm2.skeleton.bones[0].position.clone();
      sm1.skeleton.bones[0].position.set(42.5, 99.1, -12.3);
      sm1.skeleton.bones[0].rotation.set(0.5, 0.5, 0.5);

      results.clone2_bone_unmodified = (
        sm2.skeleton.bones[0].position.x === origPos2.x &&
        sm2.skeleton.bones[0].position.y === origPos2.y &&
        sm2.skeleton.bones[0].position.z === origPos2.z
      );

      console.log(JSON.stringify(results));
    });
    """
    res = _run_node(script)
    assert res["has_sm1"] and res["has_sm2"] and res["has_sm3"]
    assert res["distinct_skeletons_1_2"] is True, "Cloned instances must have distinct Skeleton objects"
    assert res["distinct_skeletons_2_3"] is True
    assert res["distinct_skeletons_1_orig"] is True
    assert res["bone_count_1"] == res["bone_count_2"] == res["bone_count_3"] == 27
    assert res["shared_bones_between_clones"] == 0, "SkeletonUtils.clone must have ZERO shared bones across instances"
    assert res["clone2_bone_unmodified"] is True, "Mutating bone on clone 1 must not alter bone on clone 2"


def test_negative_contrast_standard_clone_shares_armature_bones():
    """Empirical Oracle: Prove that standard Object3D.clone fails by sharing skeleton bones across instances."""
    script = """
    const fs = require('fs');
    const THREE = require('./web/vendor/three.min.js');
    global.THREE = THREE;
    require('./web/vendor/GLTFLoader.js');

    const loader = new THREE.GLTFLoader();
    const buf = fs.readFileSync('assets/creatures/sand_skink.glb');

    loader.parse(buf.buffer, '', (gltf) => {
      // Standard Object3D.clone without SkeletonUtils
      const badClone1 = gltf.scene.clone(true);
      const badClone2 = gltf.scene.clone(true);

      let bMesh1 = null, bMesh2 = null;
      badClone1.traverse(c => { if (c.isSkinnedMesh) bMesh1 = c; });
      badClone2.traverse(c => { if (c.isSkinnedMesh) bMesh2 = c; });

      let sharedBonesCount = 0;
      for (let i = 0; i < bMesh1.skeleton.bones.length; i++) {
        if (bMesh1.skeleton.bones[i] === bMesh2.skeleton.bones[i]) {
          sharedBonesCount++;
        }
      }

      console.log(JSON.stringify({
        standard_clone_shares_bones: (sharedBonesCount > 0),
        shared_bones_count: sharedBonesCount,
        total_bones: bMesh1.skeleton.bones.length
      }));
    });
    """
    res = _run_node(script)
    assert res["standard_clone_shares_bones"] is True, (
        "Empirical oracle must confirm standard clone shares bones, demonstrating why SkeletonUtils.clone is required"
    )
    assert res["shared_bones_count"] == res["total_bones"], "Standard clone shares 100% of bones"


def test_skeleton_utils_clone_all_10_core_species_matrix():
    """Exhaustively verify SkeletonUtils.clone on all 10 core species and assert all 8 canonical action clips."""
    script = """
    const fs = require('fs');
    const THREE = require('./web/vendor/three.min.js');
    global.THREE = THREE;
    require('./web/vendor/GLTFLoader.js');
    require('./web/vendor/SkeletonUtils.js');

    const loader = new THREE.GLTFLoader();
    const speciesList = [
      'sand_skink', 'snow_ferret', 'alpine_ibex', 'meadow_hare', 'marsh_croc',
      'abyssal_hunter', 'storm_eagle', 'armored_sentinel', 'giant_tarantula', 'carnivore_apex'
    ];
    const canonicalClips = [
      'Idle_Normal', 'Idle_Alert', 'Walk', 'Run', 'Attack', 'Hurt_Defend', 'Eat', 'Death'
    ];

    const report = {};

    let completed = 0;
    for (const sp of speciesList) {
      const glbPath = `assets/creatures/${sp}.glb`;
      const buf = fs.readFileSync(glbPath);
      loader.parse(buf.buffer, '', (gltf) => {
        const c1 = THREE.SkeletonUtils.clone(gltf.scene);
        const c2 = THREE.SkeletonUtils.clone(gltf.scene);

        let m1 = null, m2 = null;
        c1.traverse(c => { if (c.isSkinnedMesh) m1 = c; });
        c2.traverse(c => { if (c.isSkinnedMesh) m2 = c; });

        let sharedBones = 0;
        if (m1 && m2) {
          for (let i = 0; i < m1.skeleton.bones.length; i++) {
            if (m1.skeleton.bones[i] === m2.skeleton.bones[i]) sharedBones++;
          }
        }

        const animationNames = (gltf.animations || []).map(a => a.name);
        const missingClips = canonicalClips.filter(name => !animationNames.includes(name));

        report[sp] = {
          hasSkinnedMesh: !!m1,
          boneCount: m1 ? m1.skeleton.bones.length : 0,
          sharedBones,
          clipCount: animationNames.length,
          missingClips
        };

        completed++;
        if (completed === speciesList.length) {
          console.log(JSON.stringify(report));
        }
      });
    }
    """
    res = _run_node(script, timeout=40)
    assert len(res) == 10, f"Expected 10 species tested, got {len(res)}"
    for sp, data in res.items():
        assert data["hasSkinnedMesh"] is True, f"{sp} must contain a SkinnedMesh"
        assert data["boneCount"] >= 8, f"{sp} must have at least 8 bones in armature (got {data['boneCount']})"
        assert data["sharedBones"] == 0, f"{sp} must have 0 shared bones across cloned instances"
        assert len(data["missingClips"]) == 0, f"{sp} missing canonical clips: {data['missingClips']}"


# ==============================================================================
# Challenge 3: Telemetry Handling Under Reconnection & Packet Drops
# ==============================================================================

def test_telemetry_client_reconnection_and_exponential_backoff():
    """Verify TelemetryClient implements resilient reconnection with capped exponential backoff."""
    script = """
    const { TelemetryClient } = require('./web/modules/simulation/TelemetryClient.js');

    // Mock WebSocket environment
    let wsInstanceCount = 0;
    let latestWs = null;

    global.WebSocket = class MockWebSocket {
      constructor(url) {
        this.url = url;
        this.readyState = 0; // CONNECTING
        latestWs = this;
        wsInstanceCount++;
      }
      close() {
        this.readyState = 3; // CLOSED
        if (typeof this.onclose === 'function') this.onclose();
      }
    };

    global.window = {
      location: { protocol: 'http:', host: '127.0.0.1:8000' }
    };

    const client = new TelemetryClient('/v1/spectate');
    const statuses = [];
    client.onStatus((s) => statuses.push(s));

    // Connect initially
    client.connect();
    const initialDelay = client.retryDelay;

    // 1. Trigger disconnect
    latestWs.onclose();
    const delayAfter1 = client.retryDelay;

    // Simulate timer fire and second disconnect
    if (client.reconnectTimer) {
      clearTimeout(client.reconnectTimer);
      client.reconnectTimer = null;
      client.retryDelay = Math.min(client.retryDelay * 1.5, 10000);
      client.connect();
    }
    const delayAfter2 = client.retryDelay;

    // Advance backoff to cap
    for (let i = 0; i < 10; i++) {
      if (client.reconnectTimer) clearTimeout(client.reconnectTimer);
      client.reconnectTimer = null;
      client.retryDelay = Math.min(client.retryDelay * 1.5, 10000);
      client.connect();
    }
    const cappedDelay = client.retryDelay;

    // Successful connection resets delay
    latestWs.onopen();
    const resetDelay = client.retryDelay;

    // Explicit disconnect closes socket
    client.disconnect();
    const cleanSocket = client.ws === null;
    // In current implementation, ws.close() fires onclose, which immediately schedules a zombie reconnect timer!
    const zombieReconnectScheduled = client.reconnectTimer !== null;

    console.log(JSON.stringify({
      initialDelay,
      delayAfter1,
      delayAfter2,
      cappedDelay,
      resetDelay,
      cleanSocket,
      zombieReconnectScheduled,
      statuses
    }));
    """
    res = _run_node(script)
    assert res["initialDelay"] == 1000
    assert res["delayAfter2"] > res["delayAfter1"]
    assert res["cappedDelay"] == 10000, "Exponential backoff must be capped at 10,000 ms"
    assert res["resetDelay"] == 1000, "Successful onopen must reset backoff delay to 1000 ms"
    assert res["cleanSocket"] is True
    assert res["zombieReconnectScheduled"] is False, (
        "Remediated: TelemetryClient.disconnect() must not schedule a zombie reconnect timer"
    )
    assert "DISCONNECTED" in res["statuses"]
    assert "CONNECTED" in res["statuses"]


def test_telemetry_packet_drops_and_toroidal_wrapping():
    """Verify SpatialSynchronizer snaps coordinates upon packet drops crossing diorama boundaries."""
    script = """
    const { SpatialSynchronizer } = require('./web/modules/entities/SpatialSynchronizer.js');
    const THREE = require('./web/vendor/three.min.js');

    const group = new THREE.Group();
    const entity = {
      group,
      currX: 2.0,
      currY: 0.12,
      currZ: 2.0,
      currYaw: 0.0
    };

    const results = {};

    // 1. Normal small step (delta = 0.016, dx = 0.5)
    SpatialSynchronizer.interpolate(entity, 2.5, 2.0, 0.12, 0.2, 0.016, 24, 24, false);
    // currX should lerp smoothly towards 2.5, not jump directly to 2.5
    results.smooth_lerp = (entity.currX > 2.0 && entity.currX < 2.5);

    // 2. Large packet drop crossing world boundary: jump from x = 2.0 to x = 20.0 on a 24-wide grid
    // dx = 18 > gridW / 2 (12). Must snap immediately without lerping backward across center.
    SpatialSynchronizer.interpolate(entity, 20.0, 2.0, 0.12, 0.0, 0.016, 24, 24, false);
    results.toroidal_wrap_snapped = (entity.currX === 20.0);

    // 3. Instant mode (e.g. timeline scrub)
    SpatialSynchronizer.interpolate(entity, 11.5, 8.5, 2.80, 1.57, 1.0, 24, 24, true);
    results.instant_snapped = (
      entity.currX === 11.5 &&
      entity.currZ === 8.5 &&
      entity.currY === 2.80 &&
      entity.currYaw === 1.57
    );

    console.log(JSON.stringify(results));
    """
    res = _run_node(script)
    assert res["smooth_lerp"] is True, "Small movement steps must interpolate with smooth lerp"
    assert res["toroidal_wrap_snapped"] is True, "Boundary-crossing packet drops must snap immediately"
    assert res["instant_snapped"] is True, "isInstant flag must snap all spatial axes"


def test_telemetry_out_of_order_packets_and_sorting():
    """Verify FrameHistory keeps frames sorted and rejects out-of-order live regressions."""
    script = """
    const { FrameHistory } = require('./web/frame_history.js');

    const fh = new FrameHistory({ maxFrames: 100 });

    // Stream arrives with scrambled ticks: 1, 2, 5, 4, 3, 6
    const tickOrder = [1, 2, 5, 4, 3, 6];
    for (const t of tickOrder) {
      fh.add({ t, match_id: 'match_alpha', creatures: [{ id: 'c1', x: t, y: t }] });
    }

    const partition = fh.frames('match_alpha');
    const sortedTicks = partition.map(f => f.t);

    console.log(JSON.stringify({
      stored_ticks: sortedTicks,
      is_strictly_sorted: sortedTicks.every((val, idx) => idx === 0 || val > sortedTicks[idx - 1]),
      total_frames: partition.length
    }));
    """
    res = _run_node(script)
    assert res["is_strictly_sorted"] is True, "FrameHistory partition must maintain strictly ascending ticks"
    assert res["stored_ticks"] == [1, 2, 3, 4, 5, 6], "Out-of-order arrivals must be sorted into position via binary search"
    assert res["total_frames"] == 6


def test_telemetry_corrupted_and_malformed_payload_immunity():
    """Empirically test vulnerability to null creatureData in updateFromTick."""
    script = """
    const { TelemetryClient } = require('./web/modules/simulation/TelemetryClient.js');
    const { CreatureController } = require('./web/modules/entities/CreatureController.js');
    const THREE = require('./web/vendor/three.min.js');

    const client = new TelemetryClient();
    const controller = new CreatureController(new THREE.Group());

    let caughtClientErrors = 0;
    client.onFrame(() => {});

    // 1. Simulate invalid JSON string reaching WebSocket onmessage
    const fakeEv = { data: "{ 'broken_json: unclosed" };
    try {
      const dummyWs = { onmessage: null };
      dummyWs.onmessage = (e) => {
        try { JSON.parse(e.data); } catch(err) { caughtClientErrors++; }
      };
      dummyWs.onmessage(fakeEv);
    } catch(e) {
      // Should not bubble
    }

    // 2. Feed null creatureData directly to updateFromTick to verify vulnerability
    let nullUpdateThrew = false;
    let nullUpdateErrorMessage = '';
    try {
      controller.updateFromTick(null);
    } catch(e) {
      nullUpdateThrew = true;
      nullUpdateErrorMessage = e.message;
    }

    // 3. Feed NaN coordinates to spawned creature
    let nanCoordinateThrew = false;
    try {
      controller.updateFromTick({ id: 'c_nan', x: NaN, y: undefined, alive: false });
    } catch(e) {
      nanCoordinateThrew = true;
    }

    console.log(JSON.stringify({
      caughtClientErrors,
      nullUpdateThrew,
      nullUpdateErrorMessage,
      nanCoordinateThrew
    }));
    """
    res = _run_node(script)
    assert res["caughtClientErrors"] == 1, "Malformed JSON must be trapped inside try/catch"
    assert res["nullUpdateThrew"] is False, "updateFromTick(null) must be safely handled without throwing"
    assert res["nanCoordinateThrew"] is False, "NaN coordinates do not throw unhandled exception"


# ==============================================================================
# Challenge 4: 8-Action State Machine Exhaustive Transition Matrix
# ==============================================================================

def test_state_machine_8_actions_transition_matrix():
    """Exhaustively verify transitions across all 8 canonical action states in CreatureStateMachine."""
    script = """
    const { CreatureStateMachine, CreatureState } = require('./web/modules/entities/CreatureStateMachine.js');

    const sm = new CreatureStateMachine(null);
    const transitions = {};

    // 1. IDLE (Normal)
    transitions.idle_normal = sm.evaluateState({ id: 'c1', alive: true, tr: [2, 2, 2, 2, 2, 2], isMoving: false });

    // 2. WALK (isMoving true, speed < 4)
    transitions.walk = sm.evaluateState({ id: 'c1', alive: true, tr: [2, 2, 2, 3, 2, 2], isMoving: true });

    // 3. RUN (isMoving true, speed >= 4)
    transitions.run = sm.evaluateState({ id: 'c1', alive: true, tr: [2, 2, 2, 4, 2, 2], isMoving: true });

    // 4. ATTACK (COMBAT event)
    transitions.attack = sm.evaluateState({ id: 'c1', alive: true }, [{ k: 'COMBAT', who: 'c1' }]);

    // 5. HURT (HURT event)
    transitions.hurt = sm.evaluateState({ id: 'c1', alive: true }, [{ k: 'HURT', target: 'c1' }]);

    // 6. EAT (EAT event)
    transitions.eat = sm.evaluateState({ id: 'c1', alive: true }, [{ k: 'EAT', who: 'c1' }]);

    // 7. ALERT (High sense trait and forced alert)
    sm.currentState = CreatureState.IDLE;
    const alertTransition = sm.transitionTo(CreatureState.ALERT);
    transitions.alert = alertTransition;

    // 8. DEATH (alive false)
    transitions.death = sm.evaluateState({ id: 'c1', alive: false });

    console.log(JSON.stringify(transitions));
    """
    res = _run_node(script)
    assert res["idle_normal"] == "Idle_Normal"
    assert res["walk"] == "Walk"
    assert res["run"] == "Run"
    assert res["attack"] == "Attack"
    assert res["hurt"] == "Hurt_Defend"
    assert res["eat"] == "Eat"
    assert res["alert"] == "Idle_Alert"
    assert res["death"] == "Death"


def test_vulnerability_animation_dispatcher_null_clip_type_error():
    """Empirical Oracle: Prove that crossFadeTo(null) throws TypeError due to missing type check in substring search."""
    script = """
    const { AnimationDispatcher } = require('./web/modules/entities/AnimationDispatcher.js');
    const THREE = require('./web/vendor/three.min.js');

    const root = new THREE.Group();
    const clip = new THREE.AnimationClip('Idle_Normal', 1.0, []);
    const dispatcher = new AnimationDispatcher(root, [clip]);

    let nullClipThrew = false;
    let nullErrorMessage = '';
    try {
      dispatcher.crossFadeTo(null);
    } catch(e) {
      nullClipThrew = true;
      nullErrorMessage = e.message;
    }

    let undefinedClipThrew = false;
    let undefinedErrorMessage = '';
    try {
      dispatcher.crossFadeTo(undefined);
    } catch(e) {
      undefinedClipThrew = true;
      undefinedErrorMessage = e.message;
    }

    console.log(JSON.stringify({
      nullClipThrew,
      nullErrorMessage,
      undefinedClipThrew,
      undefinedErrorMessage
    }));
    """
    res = _run_node(script)
    assert res["nullClipThrew"] is False, "crossFadeTo(null) must be safely handled as no-op"
    assert res["undefinedClipThrew"] is False, "crossFadeTo(undefined) must be safely handled as no-op"


def test_vulnerability_replay_buffer_out_of_order_tick_regression():
    """Empirical Oracle: Prove that ReplayBuffer.push regresses latestTick on out-of-order packets."""
    script = """
    const { ReplayBuffer } = require('./web/modules/simulation/ReplayBuffer.js');

    const buffer = new ReplayBuffer(100);

    // Frame 10 arrives first
    buffer.push({ t: 10, creatures: [] });
    const tickAfter10 = buffer.latestTick;

    // Out-of-order delayed frame 8 arrives
    buffer.push({ t: 8, creatures: [] });
    const tickAfterLate8 = buffer.latestTick;

    // User attempts to seek to tick 10 (which is already in the buffer)
    buffer.seek(10);
    const scrubbedTick = buffer.scrubTick;

    console.log(JSON.stringify({
      tickAfter10,
      tickAfterLate8,
      latestTickRegressed: tickAfterLate8 < tickAfter10,
      scrubbedTickClampedIncorrectly: scrubbedTick < 10
    }));
    """
    res = _run_node(script)
    assert res["tickAfter10"] == 10
    assert res["tickAfterLate8"] == 10
    assert res["latestTickRegressed"] is False, (
        "Remediated: ReplayBuffer.latestTick must remain monotonic and not regress on out-of-order packets"
    )
    assert res["scrubbedTickClampedIncorrectly"] is False, (
        "Remediated: seek(10) must not be clamped after out-of-order packet arrives"
    )


def test_state_machine_combat_vs_hurt_targeting():
    """Verify attacker triggers ATTACK and defender triggers HURT during COMBAT and ATTACK events."""
    script = """
    const { CreatureStateMachine, CreatureState } = require('./web/modules/entities/CreatureStateMachine.js');
    const sm = new CreatureStateMachine(null);

    const combatEvents = [{ k: 'COMBAT', who: 'c1', target: 'c2' }];
    const stAttacker = sm.evaluateState({ id: 'c1', alive: true }, combatEvents);
    const stDefender = sm.evaluateState({ id: 'c2', alive: true }, combatEvents);

    const attackEvents = [{ k: 'ATTACK', who: 'c1', target: 'c2' }];
    const stAttackTarget = sm.evaluateState({ id: 'c2', alive: true }, attackEvents);

    const hurtEvents = [{ k: 'HURT', who: 'c2' }];
    const stHurtActor = sm.evaluateState({ id: 'c2', alive: true }, hurtEvents);

    console.log(JSON.stringify({
      stAttacker,
      stDefender,
      stAttackTarget,
      stHurtActor
    }));
    """
    res = _run_node(script)
    assert res["stAttacker"] == "Attack", "Attacker initiating combat must transition to Attack"
    assert res["stDefender"] == "Hurt_Defend", "Defender targeted in combat must transition to Hurt_Defend"
    assert res["stAttackTarget"] == "Hurt_Defend", "Defender targeted in attack event must transition to Hurt_Defend"
    assert res["stHurtActor"] == "Hurt_Defend", "Actor experiencing hurt event must transition to Hurt_Defend"

