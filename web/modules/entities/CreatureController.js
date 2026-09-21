/**
 * CreatureController.js - Organism Registry, Spawning, State Management, and Animation
 * Part of Genesis Zero Modular Architecture (Module 3: Entity & Creature Logic).
 * 100% Offline, Zero-CDN compliant.
 */

import { AnimationDispatcher } from "./AnimationDispatcher.js";
import { CreatureStateMachine } from "./CreatureStateMachine.js";
import { SpatialSynchronizer } from "./SpatialSynchronizer.js";

export class CreatureController {
  constructor(sceneGroup, assetCache, fallbackBuilder) {
    this.parentGroup = sceneGroup;
    this.assetCache = assetCache;
    this.fallbackBuilder = fallbackBuilder;
    this.entities = new Map(); // id -> EntityObject
  }

  async spawnCreature(c) {
    if (!c || !c.id) return null;
    const speciesId = c.species || c.sp || (c.tr ? `L${c.tr[0]}` : "L1");

    let instance = null;
    if (this.assetCache && typeof this.assetCache.getCreatureInstance === "function") {
      instance = await this.assetCache.getCreatureInstance(speciesId, this.fallbackBuilder);
    } else if (typeof this.fallbackBuilder === "function") {
      const fallbackMesh = this.fallbackBuilder(c);
      instance = { scene: fallbackMesh, animations: [], isRigged: false };
    }

    if (!instance || !instance.scene) return null;

    const group = new THREE.Group();
    group.name = `Creature_${c.id}`;
    group.add(instance.scene);

    if (this.parentGroup) {
      this.parentGroup.add(group);
    }

    // Configure shadows on all meshes
    group.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    const dispatcher = new AnimationDispatcher(instance.scene, instance.animations || []);
    const stateMachine = new CreatureStateMachine(dispatcher);

    const targetElev = SpatialSynchronizer.getDomainElevation(c.domain || "CAN");
    const targetX = (c.x !== undefined ? c.x : 0) + 0.5;
    const targetZ = (c.y !== undefined ? c.y : 0) + 0.5;

    group.position.set(targetX, targetElev, targetZ);

    const entity = {
      id: c.id,
      group,
      sceneInstance: instance.scene,
      dispatcher,
      stateMachine,
      isRigged: instance.isRigged,
      currX: targetX,
      currY: targetElev,
      currZ: targetZ,
      currYaw: 0,
      targetX,
      targetY: targetElev,
      targetZ,
      targetYaw: 0,
      data: c,
      alive: Boolean(c.alive)
    };

    this.entities.set(c.id, entity);
    return entity;
  }

  updateFromTick(creatureData, events = [], isInstant = false) {
    if (!creatureData || !creatureData.id) return;

    let entity = this.entities.get(creatureData.id);
    if (!entity) {
      this.spawnCreature(creatureData);
      return;
    }

    entity.data = creatureData;
    entity.alive = Boolean(creatureData.alive);

    // Evaluate state machine with safe events array
    if (entity.stateMachine) {
      entity.stateMachine.evaluateState(creatureData, Array.isArray(events) ? events : []);
    }

    // Update target coordinates with NaN/undefined guards
    const rawX = (typeof creatureData.x === "number" && !Number.isNaN(creatureData.x))
      ? creatureData.x
      : (entity.currX !== undefined ? entity.currX - 0.5 : 0);
    const rawZ = (typeof creatureData.y === "number" && !Number.isNaN(creatureData.y))
      ? creatureData.y
      : (entity.currZ !== undefined ? entity.currZ - 0.5 : 0);

    const targetX = rawX + 0.5;
    const targetZ = rawZ + 0.5;
    const targetElev = SpatialSynchronizer.getDomainElevation(creatureData.domain || "CAN");

    const dx = targetX - entity.currX;
    const dz = targetZ - entity.currZ;

    if (Math.abs(dx) > 0.05 || Math.abs(dz) > 0.05) {
      entity.targetYaw = Math.atan2(dx, dz);
    }

    entity.targetX = targetX;
    entity.targetY = targetElev;
    entity.targetZ = targetZ;

    if (isInstant) {
      SpatialSynchronizer.interpolate(entity, targetX, targetZ, targetElev, entity.targetYaw, 1.0, 32, 32, true);
    }
  }

  update(delta) {
    for (const [, entity] of this.entities) {
      // 1. Update skeletal animation mixer
      if (entity.dispatcher) {
        entity.dispatcher.update(delta);
      }

      // 2. Smooth spatial interpolation
      SpatialSynchronizer.interpolate(
        entity,
        entity.targetX,
        entity.targetZ,
        entity.targetY,
        entity.targetYaw,
        delta
      );
    }
  }

  despawnCreature(id) {
    const entity = this.entities.get(id);
    if (!entity) return;

    if (entity.dispatcher) {
      entity.dispatcher.dispose();
    }
    if (this.parentGroup && entity.group) {
      this.parentGroup.remove(entity.group);
    }
    this.entities.delete(id);
  }

  clear() {
    for (const id of [...this.entities.keys()]) {
      this.despawnCreature(id);
    }
  }
}

if (typeof window !== "undefined") {
  window.CreatureController = CreatureController;
}
