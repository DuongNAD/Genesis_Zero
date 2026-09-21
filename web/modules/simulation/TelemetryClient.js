/**
 * TelemetryClient.js - WebSocket receiver for /v1/spectate & offline mock simulation
 * Part of Genesis Zero Modular Architecture (Module: Simulation Adapter).
 * 100% Offline, Zero-CDN compliant.
 */

export class TelemetryClient {
  constructor(endpoint = "/v1/spectate", options = {}) {
    this.endpoint = endpoint;
    this.options = options;
    this.ws = null;
    this.reconnectTimer = null;
    this.frameCallbacks = [];
    this.statusCallbacks = [];
    this.isConnected = false;
    this.retryDelay = 1000;
    this.isManuallyClosed = false;
  }

  onFrame(cb) {
    this.frameCallbacks.push(cb);
  }

  onStatus(cb) {
    this.statusCallbacks.push(cb);
  }

  connect() {
    if (typeof window === "undefined" || typeof WebSocket === "undefined") return;

    this.isManuallyClosed = false;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws && (this.ws.readyState === 0 || this.ws.readyState === 1)) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8000";
    const wsUrl = `${protocol}//${host}${this.endpoint}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.retryDelay = 1000;
        this.notifyStatus("CONNECTED");
        console.log("[TelemetryClient] Connected to:", wsUrl);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          for (let i = 0; i < this.frameCallbacks.length; i++) {
            this.frameCallbacks[i](data);
          }
        } catch (err) {
          console.warn("[TelemetryClient] Invalid frame JSON:", err);
        }
      };

      this.ws.onerror = () => {
        this.notifyStatus("ERROR");
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.notifyStatus("DISCONNECTED");
        if (!this.isManuallyClosed) {
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      if (!this.isManuallyClosed) {
        this.scheduleReconnect();
      }
    }
  }

  notifyStatus(status) {
    for (let i = 0; i < this.statusCallbacks.length; i++) {
      this.statusCallbacks[i](status);
    }
  }

  scheduleReconnect() {
    if (this.isManuallyClosed || this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.isManuallyClosed) return;
      this.retryDelay = Math.min(this.retryDelay * 1.5, 10000);
      this.connect();
    }, this.retryDelay);
  }

  disconnect() {
    this.isManuallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
      try {
        this.ws.close();
      } catch (_) {}
      this.ws = null;
    }
    const wasConnected = this.isConnected;
    this.isConnected = false;
    if (wasConnected) {
      this.notifyStatus("DISCONNECTED");
    }
  }
}

if (typeof window !== "undefined") {
  window.TelemetryClient = TelemetryClient;
}
