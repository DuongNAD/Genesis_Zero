/**
 * SpatialSynchronizer.js - Interpolation, Yaw Slerp, and Toroidal World Wrapping
 * Part of Genesis Zero Modular Architecture (Module 3: Entity & Creature Logic).
 * 100% Offline, Zero-CDN compliant.
 */

export class SpatialSynchronizer {
  static getDomainElevation(domain) {
    if (domain === "NUOC") return -0.15; // Submerged in river/lake basin
    if (domain === "TROI") return 2.80;  // Soaring aloft in sky tier
    return 0.12;                         // Terrestrial ground tier
  }

  static interpolate(entity, targetX, targetZ, targetElev, targetYaw, delta, gridW = 32, gridH = 32, isInstant = false) {
    if (!entity) return;

    if (isInstant) {
      entity.currX = targetX;
      entity.currY = targetElev;
      entity.currZ = targetZ;
      entity.currYaw = targetYaw;
      if (entity.group) {
        entity.group.position.set(targetX, targetElev, targetZ);
        entity.group.rotation.y = targetYaw;
      }
      return;
    }

    const dx = targetX - entity.currX;
    const dz = targetZ - entity.currZ;

    // Toroidal world grid wrapping detection: avoid lerping across entire diorama
    if (Math.abs(dx) > gridW / 2 || Math.abs(dz) > gridH / 2) {
      entity.currX = targetX;
      entity.currZ = targetZ;
    } else {
      const lerpFactor = Math.min(1.0, delta * 10.0);
      entity.currX += dx * lerpFactor;
      entity.currZ += dz * lerpFactor;
    }

    const elevFactor = Math.min(1.0, delta * 8.0);
    entity.currY += (targetElev - entity.currY) * elevFactor;

    // Yaw shortest angular distance slerp
    let dyaw = targetYaw - entity.currYaw;
    while (dyaw > Math.PI) dyaw -= Math.PI * 2;
    while (dyaw < -Math.PI) dyaw += Math.PI * 2;
    entity.currYaw += dyaw * Math.min(1.0, delta * 12.0);

    if (entity.group) {
      entity.group.position.set(entity.currX, entity.currY, entity.currZ);
      entity.group.rotation.y = entity.currYaw;
    }
  }
}

if (typeof window !== "undefined") {
  window.SpatialSynchronizer = SpatialSynchronizer;
}
