/**
 * MaterialLibrary.js - PBR Materials, Triplanar Terrain, and Optical Water Shaders
 * Part of Genesis Zero Modular Architecture (Module 2: Rendering Engine).
 * 100% Offline, Zero-CDN compliant.
 */

export class MaterialLibrary {
  static createPBRWaterMaterial(color = 0x0077b6, opacity = 0.85) {
    if (typeof THREE === "undefined") return null;

    return new THREE.MeshPhysicalMaterial({
      color: color,
      transparent: true,
      opacity: opacity,
      roughness: 0.03,
      metalness: 0.1,
      transmission: 0.7,
      ior: 1.333,
      reflectivity: 0.5,
      depthWrite: false
    });
  }

  static createSlopeTerrainMaterial() {
    if (typeof THREE === "undefined") return null;

    return new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.92,
      metalness: 0.05,
      flatShading: false
    });
  }

  static createCavernRockMaterial() {
    if (typeof THREE === "undefined") return null;

    return new THREE.MeshStandardMaterial({
      color: 0x35302c,
      roughness: 0.92,
      metalness: 0.08
    });
  }

  static createBioluminescentMaterial(color = 0x00e676, intensity = 2.5) {
    if (typeof THREE === "undefined") return null;

    return new THREE.MeshStandardMaterial({
      color: color,
      emissive: new THREE.Color(color),
      emissiveIntensity: intensity,
      roughness: 0.2,
      metalness: 0.0
    });
  }

  static createCreaturePBRMaterial(baseColor, emissiveColor = 0x000000) {
    if (typeof THREE === "undefined") return null;

    return new THREE.MeshStandardMaterial({
      color: baseColor,
      roughness: 0.45,
      metalness: 0.15,
      emissive: new THREE.Color(emissiveColor),
      emissiveIntensity: 1.0,
      shadowSide: THREE.DoubleSide
    });
  }
}

if (typeof window !== "undefined") {
  window.MaterialLibrary = MaterialLibrary;
}
