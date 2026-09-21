/**
 * SceneManager.js - Three.js Scene graph hierarchy, Groups, and Camera framing
 * Part of Genesis Zero Modular Architecture (Module 2: Rendering Engine).
 * 100% Offline, Zero-CDN compliant.
 */

export class SceneManager {
  constructor() {
    this.scene = null;
    this.dioramaGroup = null;
    this.faunaGroup = null;
    this.vfxGroup = null;
    this.weatherGroup = null;
    this.camera = null;

    if (typeof THREE !== "undefined") {
      this.initScene();
    }
  }

  initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x06080f);
    this.scene.fog = new THREE.Fog(0x06080f, 40, 180);

    // Modular Scene Groups
    this.dioramaGroup = new THREE.Group();
    this.dioramaGroup.name = "DioramaGroup";
    this.scene.add(this.dioramaGroup);

    this.faunaGroup = new THREE.Group();
    this.faunaGroup.name = "FaunaGroup";
    this.scene.add(this.faunaGroup);

    this.vfxGroup = new THREE.Group();
    this.vfxGroup.name = "VFXGroup";
    this.scene.add(this.vfxGroup);

    this.weatherGroup = new THREE.Group();
    this.weatherGroup.name = "WeatherGroup";
    this.scene.add(this.weatherGroup);

    this.setupCamera();
  }

  setupCamera() {
    const aspect = (typeof window !== "undefined") ? (window.innerWidth / window.innerHeight) : (16 / 9);
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
    // Default 3/4 Isometric diorama view
    this.camera.position.set(38, 42, 38);
    this.camera.lookAt(0, 0, 0);
  }

  setCameraPreset(presetName) {
    if (!this.camera) return;

    switch (presetName) {
      case "ISO_NE":
        this.camera.position.set(38, 42, 38);
        this.camera.lookAt(0, 0, 0);
        break;
      case "ISO_NW":
        this.camera.position.set(-38, 42, 38);
        this.camera.lookAt(0, 0, 0);
        break;
      case "TOP_DOWN":
        this.camera.position.set(0, 65, 0.1);
        this.camera.lookAt(0, 0, 0);
        break;
      case "CAVE_LEVEL":
        this.camera.position.set(0, -2, 18);
        this.camera.lookAt(0, -5, 0);
        break;
      default:
        this.camera.position.set(38, 42, 38);
        this.camera.lookAt(0, 0, 0);
        break;
    }
  }

  attachDioramaModel(model) {
    if (!model || !this.dioramaGroup) return;

    // Clear previous procedural placeholders if any
    while (this.dioramaGroup.children.length > 0) {
      this.dioramaGroup.remove(this.dioramaGroup.children[0]);
    }

    model.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    this.dioramaGroup.add(model);
  }
}

if (typeof window !== "undefined") {
  window.SceneManager = SceneManager;
}
