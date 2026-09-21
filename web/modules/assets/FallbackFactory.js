/**
 * FallbackFactory.js - Procedural mesh fallback generators when GLB assets fail
 * Part of Genesis Zero Modular Architecture (Module 1: Assets Management).
 * 100% Offline, Zero-CDN compliant.
 */

export class FallbackFactory {
  static createFallbackCreature(c) {
    if (typeof THREE === "undefined") return null;

    const t = (c && c.tr) ? c.tr : [2, 2, 2, 2, 2, 2];
    const domain = (c && c.domain) ? c.domain : (c && c.d) ? c.d : "CAN";
    const stomachR = 0.13 + (t[5] || 2) * 0.032;
    const speedZ = 1.0 + (t[3] || 2) * 0.14;

    const g = new THREE.Group();
    if (c && c.id) g.userData.creatureId = c.id;

    // PBR Material with roughness and metalness
    const mat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      roughness: 0.45,
      metalness: 0.15,
      shadowSide: THREE.DoubleSide
    });

    if (domain === "NUOC") {
      const bodyGeo = new THREE.ConeGeometry(stomachR, 0.44 * speedZ, 12);
      const mesh = new THREE.Mesh(bodyGeo, mat);
      mesh.rotation.x = Math.PI / 2;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      g.add(mesh);
    } else if (domain === "TROI") {
      const bodyGeo = new THREE.SphereGeometry(stomachR * 0.9, 10, 8);
      const mesh = new THREE.Mesh(bodyGeo, mat);
      mesh.scale.set(0.85, 0.8, 1.3 * speedZ);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      g.add(mesh);
    } else {
      const bodyGeo = new THREE.BoxGeometry(stomachR * 1.5, stomachR * 1.2, 0.4 * speedZ);
      const mesh = new THREE.Mesh(bodyGeo, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      g.add(mesh);
    }

    return g;
  }

  static createFallbackTerrain(w = 32, h = 32) {
    if (typeof THREE === "undefined") return null;
    const geo = new THREE.PlaneGeometry(w, h, 32, 32);
    const mat = new THREE.MeshStandardMaterial({
      color: 0x223322,
      roughness: 0.9,
      metalness: 0.05
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    mesh.receiveShadow = true;
    return mesh;
  }
}

if (typeof window !== "undefined") {
  window.FallbackFactory = FallbackFactory;
}
