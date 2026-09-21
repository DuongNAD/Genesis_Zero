/**
 * AudioSynthesizer.js - Procedural Web Audio API sound synthesizer
 * Part of Genesis Zero Modular Architecture (Module: Audio Subsystem).
 * Generates movement, shockwave, death, reproduce, and weather audio in-browser.
 * Zero external audio files (.mp3/.wav/.ogg). 100% Offline, Zero-CDN compliant.
 */

export class AudioSynthesizer {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.compressor = null;
    this.isMuted = false;
    this.volume = 0.7;
    this.isUnlocked = false;

    // Throttle timestamps to prevent voice starvation
    this.lastMoveSoundTime = 0;
    this.lastCombatHitTime = 0;

    this.initAudioContext();
  }

  initAudioContext() {
    if (typeof window === "undefined") return;

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    try {
      this.ctx = new AudioContextClass();

      // DynamicsCompressor in master chain with threshold -6 dB
      this.compressor = this.ctx.createDynamicsCompressor();
      this.compressor.threshold.setValueAtTime(-6, this.ctx.currentTime);
      this.compressor.knee.setValueAtTime(12, this.ctx.currentTime);
      this.compressor.ratio.setValueAtTime(4, this.ctx.currentTime);
      this.compressor.attack.setValueAtTime(0.003, this.ctx.currentTime);
      this.compressor.release.setValueAtTime(0.25, this.ctx.currentTime);

      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.volume, this.ctx.currentTime);

      // Standard mixing topology: Voices -> Compressor -> MasterGain -> Destination
      this.compressor.connect(this.masterGain);
      this.masterGain.connect(this.ctx.destination);
    } catch (e) {
      console.warn("[AudioSynthesizer] AudioContext init failed:", e);
    }
  }

  unlockAudio() {
    if (!this.ctx) {
      this.initAudioContext();
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().then(() => {
        this.isUnlocked = true;
      }).catch(() => {});
    } else {
      this.isUnlocked = true;
    }
  }

  setVolume(val) {
    this.volume = Math.max(0, Math.min(1, val));
    if (this.masterGain && this.ctx) {
      const targetGain = this.isMuted ? 0 : this.volume;
      this.masterGain.gain.setValueAtTime(targetGain, this.ctx.currentTime);
    }
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    this.setVolume(this.volume);
    return this.isMuted;
  }

  playMoveSound(domain = "CAN") {
    if (!this.ctx || this.isMuted) return;

    // Cooldown check: 70ms movement sound throttling
    const nowMs = (typeof performance !== "undefined" && performance.now) ? performance.now() : Date.now();
    if (nowMs - this.lastMoveSoundTime < 70) return;
    this.lastMoveSoundTime = nowMs;

    this.unlockAudio();

    try {
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      let stopOffset = 0.18;
      if (domain === "NUOC") {
        // Water ripple swish
        osc.type = "sine";
        osc.frequency.setValueAtTime(180, t);
        osc.frequency.exponentialRampToValueAtTime(80, t + 0.12);
        gain.gain.setValueAtTime(0.08, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
        gain.gain.setValueAtTime(0, t + 0.12);
        stopOffset = 0.14;
      } else if (domain === "TROI") {
        // Air swoosh
        osc.type = "triangle";
        osc.frequency.setValueAtTime(320, t);
        osc.frequency.exponentialRampToValueAtTime(220, t + 0.16);
        gain.gain.setValueAtTime(0.06, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.16);
        gain.gain.setValueAtTime(0, t + 0.16);
        stopOffset = 0.18;
      } else {
        // Ground step thud
        osc.type = "triangle";
        osc.frequency.setValueAtTime(120, t);
        osc.frequency.exponentialRampToValueAtTime(45, t + 0.08);
        gain.gain.setValueAtTime(0.12, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);
        gain.gain.setValueAtTime(0, t + 0.08);
        stopOffset = 0.10;
      }

      osc.connect(gain);
      gain.connect(this.compressor || this.masterGain);

      osc.onended = () => {
        try {
          if (typeof osc.disconnect === "function") osc.disconnect();
          if (typeof gain.disconnect === "function") gain.disconnect();
        } catch (_) {}
      };

      osc.start(t);
      osc.stop(t + stopOffset);
    } catch (_) {}
  }

  playLawFired() {
    if (!this.ctx || this.isMuted) return;
    this.unlockAudio();

    try {
      const t = this.ctx.currentTime;
      // Harmonic golden chord
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, t + idx * 0.05);
        gain.gain.setValueAtTime(0.15, t + idx * 0.05);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.8);
        gain.gain.setValueAtTime(0, t + 0.81);

        osc.connect(gain);
        gain.connect(this.compressor || this.masterGain);

        osc.onended = () => {
          try {
            if (typeof osc.disconnect === "function") osc.disconnect();
            if (typeof gain.disconnect === "function") gain.disconnect();
          } catch (_) {}
        };

        osc.start(t + idx * 0.05);
        osc.stop(t + 0.85);
      });
    } catch (_) {}
  }

  playDeath() {
    if (!this.ctx || this.isMuted) return;
    this.unlockAudio();

    try {
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(260, t);
      osc.frequency.exponentialRampToValueAtTime(40, t + 0.45);

      gain.gain.setValueAtTime(0.18, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.45);
      gain.gain.setValueAtTime(0, t + 0.46);

      osc.connect(gain);
      gain.connect(this.compressor || this.masterGain);

      osc.onended = () => {
        try {
          if (typeof osc.disconnect === "function") osc.disconnect();
          if (typeof gain.disconnect === "function") gain.disconnect();
        } catch (_) {}
      };

      osc.start(t);
      osc.stop(t + 0.46);
    } catch (_) {}
  }

  playReproduce() {
    if (!this.ctx || this.isMuted) return;
    this.unlockAudio();

    try {
      const t = this.ctx.currentTime;
      [440, 554.37, 659.25, 880].forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, t + idx * 0.06);
        gain.gain.setValueAtTime(0.12, t + idx * 0.06);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + idx * 0.06 + 0.25);
        gain.gain.setValueAtTime(0, t + idx * 0.06 + 0.26);

        osc.connect(gain);
        gain.connect(this.compressor || this.masterGain);

        osc.onended = () => {
          try {
            if (typeof osc.disconnect === "function") osc.disconnect();
            if (typeof gain.disconnect === "function") gain.disconnect();
          } catch (_) {}
        };

        osc.start(t + idx * 0.06);
        osc.stop(t + idx * 0.06 + 0.26);
      });
    } catch (_) {}
  }

  playWeatherShift() {
    if (!this.ctx || this.isMuted) return;
    this.unlockAudio();

    try {
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(90, t);
      osc.frequency.linearRampToValueAtTime(280, t + 0.6);
      osc.frequency.linearRampToValueAtTime(110, t + 1.2);

      gain.gain.setValueAtTime(0.08, t);
      gain.gain.linearRampToValueAtTime(0.16, t + 0.6);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 1.2);
      gain.gain.setValueAtTime(0, t + 1.21);

      osc.connect(gain);
      gain.connect(this.compressor || this.masterGain);

      osc.onended = () => {
        try {
          if (typeof osc.disconnect === "function") osc.disconnect();
          if (typeof gain.disconnect === "function") gain.disconnect();
        } catch (_) {}
      };

      osc.start(t);
      osc.stop(t + 1.25);
    } catch (_) {}
  }

  playCombatHit() {
    if (!this.ctx || this.isMuted) return;

    // Cooldown check: 50ms combat hit throttling
    const nowMs = (typeof performance !== "undefined" && performance.now) ? performance.now() : Date.now();
    if (nowMs - this.lastCombatHitTime < 50) return;
    this.lastCombatHitTime = nowMs;

    this.unlockAudio();

    try {
      const t = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "square";
      osc.frequency.setValueAtTime(160, t);
      osc.frequency.exponentialRampToValueAtTime(30, t + 0.1);

      gain.gain.setValueAtTime(0.2, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);
      gain.gain.setValueAtTime(0, t + 0.11);

      osc.connect(gain);
      gain.connect(this.compressor || this.masterGain);

      osc.onended = () => {
        try {
          if (typeof osc.disconnect === "function") osc.disconnect();
          if (typeof gain.disconnect === "function") gain.disconnect();
        } catch (_) {}
      };

      osc.start(t);
      osc.stop(t + 0.12);
    } catch (_) {}
  }

  dispose() {
    try {
      if (this.masterGain && typeof this.masterGain.disconnect === "function") {
        this.masterGain.disconnect();
      }
      if (this.compressor && typeof this.compressor.disconnect === "function") {
        this.compressor.disconnect();
      }
      if (this.ctx && typeof this.ctx.close === "function" && this.ctx.state !== "closed") {
        this.ctx.close().catch(() => {});
      }
    } catch (_) {}
    this.ctx = null;
    this.masterGain = null;
    this.compressor = null;
    this.isUnlocked = false;
  }
}

export const globalAudio = new AudioSynthesizer();

if (typeof window !== "undefined") {
  window.AudioSynthesizer = AudioSynthesizer;
  window.globalAudio = globalAudio;
}
