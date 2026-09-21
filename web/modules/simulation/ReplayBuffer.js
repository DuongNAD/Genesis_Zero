/**
 * ReplayBuffer.js - Ring buffer and timeline scrubber for match telemetry ticks
 * Part of Genesis Zero Modular Architecture (Module: Simulation Adapter).
 * 100% Offline, Zero-CDN compliant.
 */

export const MAX_HISTORY = 1200;

export class ReplayBuffer {
  constructor(capacity = MAX_HISTORY) {
    this.capacity = capacity;
    this.historyBuffer = [];
    this.isPaused = false;
    this.playbackSpeed = 1;
    this.scrubTick = 0;
    this.isLive = true;
    this.latestTick = 0;
  }

  push(frame) {
    if (!frame) return;

    if (typeof frame.t === "number" && Number.isFinite(frame.t)) {
      const len = this.historyBuffer.length;
      if (len === 0 || this.historyBuffer[len - 1].t <= frame.t) {
        this.historyBuffer.push(frame);
      } else {
        // Insert in chronological sorted order
        let insertIdx = len - 1;
        while (
          insertIdx >= 0 &&
          typeof this.historyBuffer[insertIdx].t === "number" &&
          this.historyBuffer[insertIdx].t > frame.t
        ) {
          insertIdx--;
        }
        this.historyBuffer.splice(insertIdx + 1, 0, frame);
      }

      this.latestTick = Math.max(this.latestTick, frame.t);
      if (this.isLive && frame.t >= this.latestTick) {
        this.scrubTick = frame.t;
      }
    } else {
      this.historyBuffer.push(frame);
    }

    if (this.historyBuffer.length > this.capacity) {
      this.historyBuffer.shift();
    }
  }

  getFrameByTick(tick) {
    for (let i = this.historyBuffer.length - 1; i >= 0; i--) {
      if (this.historyBuffer[i].t === tick) {
        return this.historyBuffer[i];
      }
    }
    return null;
  }

  renderHistoricalFrame(tick, callback) {
    const frame = this.getFrameByTick(tick);
    if (frame && typeof callback === "function") {
      callback(frame, true); // isInstant = true
    }
    return frame;
  }

  goToLive() {
    this.isLive = true;
    this.isPaused = false;
    this.scrubTick = this.latestTick;
  }

  seek(tick) {
    this.scrubTick = Math.max(0, Math.min(tick, this.latestTick));
    this.isLive = (this.scrubTick >= this.latestTick);
  }

  setSpeed(speed) {
    this.playbackSpeed = speed;
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    if (!this.isPaused && this.scrubTick >= this.latestTick) {
      this.isLive = true;
    }
  }

  clear() {
    this.historyBuffer = [];
    this.scrubTick = 0;
    this.latestTick = 0;
    this.isLive = true;
    this.isPaused = false;
  }
}

if (typeof window !== "undefined") {
  window.ReplayBuffer = ReplayBuffer;
  window.MAX_HISTORY = MAX_HISTORY;
}
