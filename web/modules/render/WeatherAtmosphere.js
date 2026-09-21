/**
 * WeatherAtmosphere.js - Dynamic Procedural Particles & Weather Atmosphere Transitions
 * Part of Genesis Zero Modular Architecture (Module 2: Rendering Engine).
 * 100% Offline, Zero-CDN compliant.
 */

export class WeatherAtmosphere {
  constructor(scene) {
    this.scene = scene;
    this.weatherGroup = new THREE.Group();
    if (this.scene) this.scene.add(this.weatherGroup);

    this.rainParticles = null;
    this.solarParticles = null;
    this.sporeParticles = null;
    this.magneticParticles = null;

    this.targetFogColor = new THREE.Color(0x06080f);
    this.targetSunColor = new THREE.Color(0xfff7ed);
    this.targetSunIntensity = 1.35;
    this.targetAmbientColor = new THREE.Color(0x0f172a);

    this.initParticles();
  }

  initParticles() {
    if (typeof THREE === "undefined") return;

    // 1. Rain Particles (800 particles)
    const rainCount = 800;
    const rainGeo = new THREE.BufferGeometry();
    const rainPositions = new Float32Array(rainCount * 3);
    for (let i = 0; i < rainCount; i++) {
      rainPositions[i * 3] = (Math.random() - 0.5) * 60;
      rainPositions[i * 3 + 1] = Math.random() * 40;
      rainPositions[i * 3 + 2] = (Math.random() - 0.5) * 60;
    }
    rainGeo.setAttribute("position", new THREE.BufferAttribute(rainPositions, 3));
    const rainMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.15,
      transparent: true,
      opacity: 0.65
    });
    this.rainParticles = new THREE.Points(rainGeo, rainMat);
    this.rainParticles.visible = false;
    this.weatherGroup.add(this.rainParticles);

    // 2. Solar Flare Particles (400 particles)
    const solarCount = 400;
    const solarGeo = new THREE.BufferGeometry();
    const solarPositions = new Float32Array(solarCount * 3);
    for (let i = 0; i < solarCount; i++) {
      solarPositions[i * 3] = (Math.random() - 0.5) * 60;
      solarPositions[i * 3 + 1] = Math.random() * 35;
      solarPositions[i * 3 + 2] = (Math.random() - 0.5) * 60;
    }
    solarGeo.setAttribute("position", new THREE.BufferAttribute(solarPositions, 3));
    const solarMat = new THREE.PointsMaterial({
      color: 0xf59e0b,
      size: 0.28,
      transparent: true,
      opacity: 0.8
    });
    this.solarParticles = new THREE.Points(solarGeo, solarMat);
    this.solarParticles.visible = false;
    this.weatherGroup.add(this.solarParticles);

    // 3. Toxic Spores Particles (500 particles)
    const sporeCount = 500;
    const sporeGeo = new THREE.BufferGeometry();
    const sporePositions = new Float32Array(sporeCount * 3);
    for (let i = 0; i < sporeCount; i++) {
      sporePositions[i * 3] = (Math.random() - 0.5) * 55;
      sporePositions[i * 3 + 1] = Math.random() * 25;
      sporePositions[i * 3 + 2] = (Math.random() - 0.5) * 55;
    }
    sporeGeo.setAttribute("position", new THREE.BufferAttribute(sporePositions, 3));
    const sporeMat = new THREE.PointsMaterial({
      color: 0x10b981,
      size: 0.2,
      transparent: true,
      opacity: 0.75
    });
    this.sporeParticles = new THREE.Points(sporeGeo, sporeMat);
    this.sporeParticles.visible = false;
    this.weatherGroup.add(this.sporeParticles);

    // 4. Magnetic Shift Particles (300 particles)
    const magCount = 300;
    const magGeo = new THREE.BufferGeometry();
    const magPositions = new Float32Array(magCount * 3);
    for (let i = 0; i < magCount; i++) {
      magPositions[i * 3] = (Math.random() - 0.5) * 50;
      magPositions[i * 3 + 1] = Math.random() * 30;
      magPositions[i * 3 + 2] = (Math.random() - 0.5) * 50;
    }
    magGeo.setAttribute("position", new THREE.BufferAttribute(magPositions, 3));
    const magMat = new THREE.PointsMaterial({
      color: 0x8b5cf6,
      size: 0.22,
      transparent: true,
      opacity: 0.7
    });
    this.magneticParticles = new THREE.Points(magGeo, magMat);
    this.magneticParticles.visible = false;
    this.weatherGroup.add(this.magneticParticles);
  }

  animateWeatherParticles(time = 0) {
    if (this.rainParticles && this.rainParticles.visible) {
      const pos = this.rainParticles.geometry.attributes.position.array;
      for (let i = 1; i < pos.length; i += 3) {
        pos[i] -= 0.65;
        if (pos[i] < -2) pos[i] = 38;
      }
      this.rainParticles.geometry.attributes.position.needsUpdate = true;
    }

    if (this.solarParticles && this.solarParticles.visible) {
      const pos = this.solarParticles.geometry.attributes.position.array;
      for (let i = 0; i < pos.length; i += 3) {
        pos[i + 1] -= 0.12;
        pos[i] += Math.sin(time * 0.002 + pos[i + 1]) * 0.03;
        if (pos[i + 1] < -2) pos[i + 1] = 35;
      }
      this.solarParticles.geometry.attributes.position.needsUpdate = true;
    }

    if (this.sporeParticles && this.sporeParticles.visible) {
      const pos = this.sporeParticles.geometry.attributes.position.array;
      for (let i = 0; i < pos.length; i += 3) {
        pos[i] += Math.sin(time * 0.001 + pos[i + 1]) * 0.02;
        pos[i + 1] += Math.cos(time * 0.0012 + pos[i]) * 0.02;
        if (pos[i + 1] < -2) pos[i + 1] = 25;
        if (pos[i + 1] > 26) pos[i + 1] = 0;
      }
      this.sporeParticles.geometry.attributes.position.needsUpdate = true;
    }

    if (this.magneticParticles && this.magneticParticles.visible) {
      const pos = this.magneticParticles.geometry.attributes.position.array;
      for (let i = 0; i < pos.length; i += 3) {
        pos[i] += (Math.random() - 0.5) * 0.06;
        pos[i + 2] += (Math.random() - 0.5) * 0.06;
      }
      this.magneticParticles.geometry.attributes.position.needsUpdate = true;
    }
  }

  updateWeatherAtmosphere(kind, diurnal = "DAY") {
    const isNight = (diurnal === "NIGHT");

    // Hide all weather particle systems by default
    if (this.rainParticles) this.rainParticles.visible = false;
    if (this.solarParticles) this.solarParticles.visible = false;
    if (this.sporeParticles) this.sporeParticles.visible = false;
    if (this.magneticParticles) this.magneticParticles.visible = false;

    switch (kind) {
      case "SPORE_STORM":
        if (this.sporeParticles) this.sporeParticles.visible = true;
        this.targetFogColor.setHex(0x0a1f14);
        this.targetSunColor.setHex(0x34d399);
        this.targetSunIntensity = 0.9;
        this.targetAmbientColor.setHex(0x064e3b);
        break;

      case "SOLAR_FLARE":
        if (this.solarParticles) this.solarParticles.visible = true;
        this.targetFogColor.setHex(0x2d1203);
        this.targetSunColor.setHex(0xf59e0b);
        this.targetSunIntensity = 1.8;
        this.targetAmbientColor.setHex(0x78350f);
        break;

      case "MAGNETIC_SHIFT":
        if (this.magneticParticles) this.magneticParticles.visible = true;
        this.targetFogColor.setHex(0x1e112a);
        this.targetSunColor.setHex(0xa855f7);
        this.targetSunIntensity = 1.0;
        this.targetAmbientColor.setHex(0x4c1d95);
        break;

      case "CLEAR":
      default:
        if (isNight) {
          this.targetFogColor.setHex(0x030712);
          this.targetSunColor.setHex(0x38bdf8);
          this.targetSunIntensity = 0.25;
          this.targetAmbientColor.setHex(0x020617);
        } else {
          this.targetFogColor.setHex(0x06080f);
          this.targetSunColor.setHex(0xfff7ed);
          this.targetSunIntensity = 1.35;
          this.targetAmbientColor.setHex(0x0f172a);
        }
        break;
    }

    if (isNight) {
      this.targetSunIntensity *= 0.3;
    }
  }
}

if (typeof window !== "undefined") {
  window.WeatherAtmosphere = WeatherAtmosphere;
}
