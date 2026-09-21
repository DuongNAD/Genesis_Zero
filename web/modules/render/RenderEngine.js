/**
 * RenderEngine.js - WebGLRenderer lifecycle, Tone Mapping, Shadows, and Loop
 * Part of Genesis Zero Modular Architecture (Module 2: Rendering Engine).
 * Decoupled from simulation logic.
 * 100% Offline, Zero-CDN compliant.
 */

export class RenderEngine {
  constructor(containerElement, options = {}) {
    this.container = containerElement || (typeof document !== "undefined" ? document.body : null);
    this.options = options;
    this.renderCallbacks = [];
    this.clock = (typeof THREE !== "undefined") ? new THREE.Clock() : null;
    this.animationFrameId = null;
    this.composer = null;

    if (typeof THREE !== "undefined" && this.container) {
      this.initRenderer();
    }
  }

  initRenderer() {
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
      alpha: false
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(this.container.clientWidth || window.innerWidth, this.container.clientHeight || window.innerHeight);

    // Advanced Lighting & Soft Shadows
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Cinematic Tone Mapping
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;
    if (THREE.sRGBEncoding) {
      this.renderer.outputEncoding = THREE.sRGBEncoding;
    }

    if (this.container.appendChild && this.renderer.domElement) {
      this.container.appendChild(this.renderer.domElement);
    }

    this.setupResizeHandler();
    this.setupPMREM();
  }

  setupPMREM() {
    if (!this.renderer || !THREE.PMREMGenerator) return;
    this.pmremGenerator = new THREE.PMREMGenerator(this.renderer);
    this.pmremGenerator.compileEquirectangularShader();
  }

  generateIBLFromScene(scene) {
    if (!this.pmremGenerator || !scene) return null;
    const envMap = this.pmremGenerator.fromScene(scene).texture;
    scene.environment = envMap;
    return envMap;
  }

  setupResizeHandler() {
    this.resizeHandler = () => {
      if (!this.renderer || !this.container) return;
      const width = this.container.clientWidth || window.innerWidth;
      const height = this.container.clientHeight || window.innerHeight;
      this.renderer.setSize(width, height);
      if (this.camera) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
      }
      if (this.composer) {
        this.composer.setSize(width, height);
      }
    };
    window.addEventListener("resize", this.resizeHandler);
  }

  setCamera(camera) {
    this.camera = camera;
  }

  setScene(scene) {
    this.scene = scene;
  }

  onTick(callback) {
    this.renderCallbacks.push(callback);
  }

  start() {
    if (this.animationFrameId) return;

    const animate = () => {
      this.animationFrameId = requestAnimationFrame(animate);
      const delta = this.clock ? this.clock.getDelta() : 0.016;
      const elapsed = this.clock ? this.clock.getElapsedTime() : 0;

      for (let i = 0; i < this.renderCallbacks.length; i++) {
        this.renderCallbacks[i](delta, elapsed);
      }

      if (this.composer) {
        this.composer.render();
      } else if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    };

    animate();
  }

  stop() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  dispose() {
    this.stop();
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
    }
    if (this.pmremGenerator) {
      this.pmremGenerator.dispose();
    }
    if (this.renderer) {
      this.renderer.dispose();
    }
  }
}

if (typeof window !== "undefined") {
  window.RenderEngine = RenderEngine;
}
