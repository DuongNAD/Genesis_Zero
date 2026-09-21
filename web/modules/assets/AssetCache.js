/**
 * AssetCache.js - In-memory model caching with SkeletonUtils.clone for SkinnedMesh armatures
 * Part of Genesis Zero Modular Architecture (Module 1: Assets Management).
 * Enables independent animations on cloned rigged creature models.
 * 100% Offline, Zero-CDN compliant.
 */

import { CREATURE_ASSET_REGISTRY } from "./AssetManifest.js";

export class AssetCache {
  constructor(loader) {
    this.loader = loader;
    this.speciesPrototypes = new Map(); // code -> GLTF object
    this.cloner = (typeof THREE !== "undefined" && THREE.SkeletonUtils && THREE.SkeletonUtils.clone)
      ? THREE.SkeletonUtils.clone
      : null;
  }

  setCloner(clonerFn) {
    this.cloner = clonerFn;
  }

  async preloadCreature(speciesKey) {
    const entry = this.resolveRegistryEntry(speciesKey);
    if (!entry) return null;

    if (this.speciesPrototypes.has(entry.code)) {
      return this.speciesPrototypes.get(entry.code);
    }

    const fallbackPaths = [
      `../${entry.path}`,
      `/${entry.path}`,
      entry.path
    ];

    const gltf = await this.loader.loadGLTF(entry.path, fallbackPaths);
    if (gltf) {
      this.speciesPrototypes.set(entry.code, gltf);
    }
    return gltf;
  }

  resolveRegistryEntry(speciesKey) {
    if (!speciesKey) return null;
    const str = String(speciesKey).toLowerCase();

    // 1. Direct key match
    if (CREATURE_ASSET_REGISTRY[str]) return CREATURE_ASSET_REGISTRY[str];

    // 2. Code match (e.g. "L1", "W1", "A1")
    for (const entry of Object.values(CREATURE_ASSET_REGISTRY)) {
      if (entry.code.toLowerCase() === str) return entry;
    }

    // 3. Substring match
    for (const [key, entry] of Object.entries(CREATURE_ASSET_REGISTRY)) {
      if (str.includes(key) || str.includes(entry.code.toLowerCase()) || (entry.name && str.includes(entry.name.toLowerCase()))) {
        return entry;
      }
    }

    return null;
  }

  async getCreatureInstance(speciesId, fallbackBuilder) {
    const entry = this.resolveRegistryEntry(speciesId);

    if (entry) {
      let proto = this.speciesPrototypes.get(entry.code);
      if (!proto) {
        proto = await this.preloadCreature(entry.code);
      }

      if (proto && proto.scene) {
        const cloner = this.cloner || (typeof THREE !== "undefined" && THREE.SkeletonUtils && THREE.SkeletonUtils.clone);
        let clonedScene;
        if (cloner) {
          clonedScene = cloner(proto.scene);
        } else {
          clonedScene = proto.scene.clone(true);
        }

        return {
          scene: clonedScene,
          animations: proto.animations || [],
          isRigged: true,
          entry
        };
      }
    }

    // Fallback procedural builder
    if (typeof fallbackBuilder === "function") {
      const fallbackMesh = fallbackBuilder(speciesId);
      return {
        scene: fallbackMesh,
        animations: [],
        isRigged: false,
        entry: null
      };
    }

    return null;
  }
}

if (typeof window !== "undefined") {
  window.AssetCache = AssetCache;
}
