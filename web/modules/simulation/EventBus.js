/**
 * EventBus.js - Decoupled Pub-Sub Event Broker for Genesis Zero
 * Part of Genesis Zero Modular Architecture (Module: Simulation Adapter).
 * 100% Offline, Zero-CDN compliant.
 */

export class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const list = this.listeners.get(event);
    const idx = list.indexOf(callback);
    if (idx !== -1) list.splice(idx, 1);
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return;
    const list = this.listeners.get(event).slice();
    for (let i = 0; i < list.length; i++) {
      try {
        list[i](data);
      } catch (err) {
        console.error(`[EventBus] Error in listener for ${event}:`, err);
      }
    }
  }

  clear() {
    this.listeners.clear();
  }
}

export const globalEventBus = new EventBus();

if (typeof window !== "undefined") {
  window.EventBus = EventBus;
  window.globalEventBus = globalEventBus;
}
