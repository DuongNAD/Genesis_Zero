/**
 * AnimationDispatcher.js - AnimationMixer cross-fading for 8 canonical animation clips
 * Part of Genesis Zero Modular Architecture (Module 3: Entity & Creature Logic).
 * Handles Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death.
 * 100% Offline, Zero-CDN compliant.
 */

export const ACTION_CLIPS = [
  "Idle_Normal",
  "Idle_Alert",
  "Walk",
  "Run",
  "Attack",
  "Hurt_Defend",
  "Eat",
  "Death"
];

export class AnimationDispatcher {
  constructor(rootScene, animationClips = []) {
    this.root = rootScene;
    this.mixer = (typeof THREE !== "undefined" && rootScene) ? new THREE.AnimationMixer(rootScene) : null;
    this.actions = new Map();
    this.currentAction = null;
    this.currentClipName = null;

    if (this.mixer && animationClips.length > 0) {
      this.initActions(animationClips);
    }
  }

  initActions(clips) {
    for (const clip of clips) {
      const action = this.mixer.clipAction(clip);
      this.actions.set(clip.name, action);
    }

    // Start with Idle_Normal or first available clip
    const startClip = this.actions.get("Idle_Normal") || this.actions.values().next().value;
    if (startClip) {
      startClip.play();
      this.currentAction = startClip;
      this.currentClipName = "Idle_Normal";
    }
  }

  crossFadeTo(clipName, duration = 0.25) {
    if (!this.mixer || !clipName || typeof clipName !== "string") return;
    if (this.currentClipName === clipName) return;

    let nextAction = this.actions.get(clipName);
    // Fallback search by partial name
    if (!nextAction) {
      const lowerTarget = clipName.toLowerCase().trim();
      if (lowerTarget.length > 0) {
        for (const [name, act] of this.actions.entries()) {
          if (typeof name === "string" && name.toLowerCase().includes(lowerTarget)) {
            nextAction = act;
            break;
          }
        }
      }
    }

    if (!nextAction) return;

    nextAction.reset();
    nextAction.fadeIn(duration);
    nextAction.play();

    if (clipName === "Death") {
      nextAction.clampWhenFinished = true;
      nextAction.setLoop(THREE.LoopOnce, 1);
    }

    if (this.currentAction && this.currentAction !== nextAction) {
      this.currentAction.fadeOut(duration);
    }

    this.currentAction = nextAction;
    this.currentClipName = clipName;
  }

  update(delta) {
    if (this.mixer) {
      this.mixer.update(delta);
    }
  }

  dispose() {
    if (this.mixer) {
      this.mixer.stopAllAction();
      this.mixer.uncacheRoot(this.root);
    }
    this.actions.clear();
  }
}

if (typeof window !== "undefined") {
  window.AnimationDispatcher = AnimationDispatcher;
  window.ACTION_CLIPS = ACTION_CLIPS;
}
