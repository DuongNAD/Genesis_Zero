/**
 * CreatureStateMachine.js - Action state machine mapping simulation ticks to 8 animation clips
 * Part of Genesis Zero Modular Architecture (Module 3: Entity & Creature Logic).
 * 100% Offline, Zero-CDN compliant.
 */

export const CreatureState = {
  IDLE:   "Idle_Normal",
  ALERT:  "Idle_Alert",
  WALK:   "Walk",
  RUN:    "Run",
  ATTACK: "Attack",
  HURT:   "Hurt_Defend",
  EAT:    "Eat",
  DEATH:  "Death"
};

export class CreatureStateMachine {
  constructor(animationDispatcher) {
    this.dispatcher = animationDispatcher;
    this.currentState = CreatureState.IDLE;
  }

  evaluateState(creatureData, eventsThisTick = []) {
    if (!creatureData) return this.currentState;

    // 1. Check Death state
    if (!creatureData.alive) {
      return this.transitionTo(CreatureState.DEATH);
    }

    // 2. Check Event triggers with precise Actor vs Target role separation
    const creatureId = creatureData.id;
    const safeEvents = Array.isArray(eventsThisTick) ? eventsThisTick : [];

    const isHurt = safeEvents.some((e) => {
      const kind = e.k || e.kind;
      const isTarget = (e.target === creatureId || e.target_id === creatureId);
      const isActor = (e.who === creatureId || e.id === creatureId || e.creature_id === creatureId);
      return (isTarget && (kind === "COMBAT" || kind === "ATTACK" || kind === "HURT" || kind === "DEFEND")) ||
             (isActor && (kind === "HURT" || kind === "DEFEND"));
    });

    const isAttacking = safeEvents.some((e) => {
      const kind = e.k || e.kind;
      const isActor = (e.who === creatureId || e.id === creatureId || e.creature_id === creatureId);
      return isActor && (kind === "COMBAT" || kind === "ATTACK");
    });

    const isEating = safeEvents.some((e) => {
      const kind = e.k || e.kind;
      const isActor = (e.who === creatureId || e.id === creatureId || e.creature_id === creatureId);
      return isActor && (kind === "EAT");
    });

    if (isHurt) {
      return this.transitionTo(CreatureState.HURT);
    }
    if (isAttacking) {
      return this.transitionTo(CreatureState.ATTACK);
    }
    if (isEating) {
      return this.transitionTo(CreatureState.EAT);
    }

    // 3. Movement and Locomotion state
    const speedTrait = (creatureData.tr && creatureData.tr[3] !== undefined) ? creatureData.tr[3] : 2;
    const isMoving = Boolean(creatureData.isMoving || creatureData.moving);

    if (isMoving) {
      const moveState = (speedTrait >= 4) ? CreatureState.RUN : CreatureState.WALK;
      return this.transitionTo(moveState);
    }

    // 4. Alert vs Normal Idle
    const senseTrait = (creatureData.tr && creatureData.tr[4] !== undefined) ? creatureData.tr[4] : 2;
    if (senseTrait >= 4 && Math.random() < 0.2) {
      return this.transitionTo(CreatureState.ALERT);
    }

    return this.transitionTo(CreatureState.IDLE);
  }

  transitionTo(newState) {
    if (this.currentState === newState) return this.currentState;

    const fadeDuration = (newState === CreatureState.DEATH) ? 0.15 : 0.25;
    if (this.dispatcher && typeof this.dispatcher.crossFadeTo === "function") {
      this.dispatcher.crossFadeTo(newState, fadeDuration);
    }
    this.currentState = newState;
    return this.currentState;
  }
}

if (typeof window !== "undefined") {
  window.CreatureStateMachine = CreatureStateMachine;
  window.CreatureState = CreatureState;
}
