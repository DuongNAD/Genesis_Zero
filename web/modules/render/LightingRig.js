/**
 * LightingRig.js - Advanced Lighting Pipeline and Soft Shadow Maps
 * Part of Genesis Zero Modular Architecture (Module 2: Rendering Engine).
 * Directional sun, Hemisphere skylight, Ambient/Point fill, and PCFSoftShadowMap.
 * Decoupled from simulation logic and creature traits.
 * 100% Offline, Zero-CDN compliant.
 */

export class LightingRig {
  constructor(scene) {
    this.scene = scene;
    this.sunLight = null;
    this.hemiLight = null;
    this.ambientLight = null;
    this.cavernPointLight = null;

    if (this.scene && typeof THREE !== "undefined") {
      this.setupLighting();
    }
  }

  setupLighting() {
    // 1. Hemisphere Light: Natural skylight-to-ground bounce fill
    this.hemiLight = new THREE.HemisphereLight(0xbfdbfe, 0x1e293b, 0.75);
    this.hemiLight.position.set(0, 50, 0);
    this.scene.add(this.hemiLight);

    // 2. Directional Sun Light with High-Resolution Soft Shadows
    this.sunLight = new THREE.DirectionalLight(0xfff7ed, 1.35);
    this.sunLight.position.set(30, 48, 22);
    this.sunLight.castShadow = true;

    // Advanced PCFSoftShadowMap Configuration (2048x2048, bias -0.0003)
    this.sunLight.shadow.mapSize.width = 2048;
    this.sunLight.shadow.mapSize.height = 2048;
    this.sunLight.shadow.camera.near = 0.5;
    this.sunLight.shadow.camera.far = 160;
    this.sunLight.shadow.camera.left = -35;
    this.sunLight.shadow.camera.right = 35;
    this.sunLight.shadow.camera.top = 35;
    this.sunLight.shadow.camera.bottom = -35;
    this.sunLight.shadow.bias = -0.0003;

    this.scene.add(this.sunLight);

    // 3. Ambient Light for deep shadow and cavern base illumination
    this.ambientLight = new THREE.AmbientLight(0x0f172a, 0.45);
    this.scene.add(this.ambientLight);

    // 4. Point Light for Subterranean Karst Cave Glow
    this.cavernPointLight = new THREE.PointLight(0x00e676, 1.2, 30);
    this.cavernPointLight.position.set(0, -6, 0);
    this.scene.add(this.cavernPointLight);
  }

  lerpLighting(targetSunColor, targetSunIntensity, targetAmbientColor, targetHemiSky, targetHemiGround, factor = 0.05) {
    if (this.sunLight && targetSunColor) {
      this.sunLight.color.lerp(targetSunColor, factor);
      if (typeof targetSunIntensity === "number") {
        this.sunLight.intensity += (targetSunIntensity - this.sunLight.intensity) * factor;
      }
    }
    if (this.ambientLight && targetAmbientColor) {
      this.ambientLight.color.lerp(targetAmbientColor, factor);
    }
    if (this.hemiLight) {
      if (targetHemiSky) this.hemiLight.color.lerp(targetHemiSky, factor);
      if (targetHemiGround) this.hemiLight.groundColor.lerp(targetHemiGround, factor);
    }
  }

  setSunPosition(x, y, z) {
    if (this.sunLight) {
      this.sunLight.position.set(x, y, z);
    }
  }
}

if (typeof window !== "undefined") {
  window.LightingRig = LightingRig;
}
