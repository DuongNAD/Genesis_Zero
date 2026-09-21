/**
 * CreatureOverlay.js - Visual indicators, HP/Energy bars, and inspection tags
 * Part of Genesis Zero Modular Architecture (Module 3: Entity & Creature Logic).
 * 100% Offline, Zero-CDN compliant.
 */

export class CreatureOverlay {
  static createSelectionRing(radius = 0.4) {
    if (typeof THREE === "undefined") return null;

    const ringGeo = new THREE.RingGeometry(radius * 0.85, radius, 24);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.8
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.02;
    return ring;
  }

  static updateEnergyGlow(materials, energyRatio, isNight = false) {
    if (!materials) return;
    const glowIntensity = isNight ? 1.8 * energyRatio : 0.8 * energyRatio;

    for (const mat of materials) {
      if (mat.emissive) {
        mat.emissiveIntensity = glowIntensity;
      }
    }
  }

  static formatCreatureStats(c) {
    if (!c) return "";
    const hp = c.hp || 0;
    const energy = c.e || 0;
    const gen = c.gen || 0;
    return `HP: ${hp} | E: ${energy} | Gen: ${gen}`;
  }
}

if (typeof window !== "undefined") {
  window.CreatureOverlay = CreatureOverlay;
}
