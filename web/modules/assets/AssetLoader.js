/**
 * AssetLoader.js - Asynchronous GLTFLoader wrapper with promise/caching
 * Part of Genesis Zero Modular Architecture (Module 1: Assets Management).
 * Decoupled from entity and simulation logic.
 * 100% Offline, Zero-CDN compliant.
 */

export class AssetLoader {
  constructor(options = {}) {
    this.options = options;
    this.cache = new Map();
    this.loader = (typeof THREE !== "undefined" && THREE.GLTFLoader)
      ? new THREE.GLTFLoader()
      : null;
  }

  async loadGLTF(url, fallbackCandidates = []) {
    if (this.cache.has(url)) {
      return this.cache.get(url);
    }

    if (!this.loader) {
      if (typeof THREE !== "undefined" && THREE.GLTFLoader) {
        this.loader = new THREE.GLTFLoader();
      } else {
        console.warn("[AssetLoader] THREE.GLTFLoader not available");
        return null;
      }
    }

    const candidates = [url, ...fallbackCandidates];

    for (const candidateUrl of candidates) {
      try {
        const gltf = await new Promise((resolve, reject) => {
          this.loader.load(
            candidateUrl,
            (loaded) => resolve(loaded),
            undefined,
            (err) => reject(err)
          );
        });

        if (gltf) {
          this.cache.set(url, gltf);
          return gltf;
        }
      } catch (e) {
        // Continue to next candidate
      }
    }

    console.warn(`[AssetLoader] Unable to load asset from candidates for: ${url}`);
    return null;
  }

  has(url) {
    return this.cache.has(url);
  }

  get(url) {
    return this.cache.get(url);
  }

  clear() {
    this.cache.clear();
  }
}

if (typeof window !== "undefined") {
  window.AssetLoader = AssetLoader;
}
