(function (root) {
  "use strict";
  const LEGACY_MATCH_ID = "legacy";
  const matchIdOf = (id) => typeof id === "string" && id.trim() ? id : LEGACY_MATCH_ID;

  function normalizeCreature(c) {
    if (c.species_id === undefined && c.generation === undefined &&
        c.energy === undefined && c.energy_max === undefined &&
        c.traits === undefined && c.dt_traits === undefined) return c;
    return Object.assign({}, c, {
      species: c.species_id ?? c.species ?? (c.id || "").split(":")[0],
      gen: c.generation ?? c.gen ?? 0,
      e: c.e ?? c.energy ?? 0,
      e_max: c.energy_max ?? c.e_max ?? c.traits?.energy_max ?? 1,
      tr: c.tr ?? (Array.isArray(c.traits) ? c.traits : undefined),
      d_tr: c.d_tr ?? c.dt_traits,
    });
  }

  class FrameHistory {
    constructor({ maxFrames = 1200, maxMatches = 2 } = {}) {
      if (!Number.isInteger(maxFrames) || maxFrames < 1 ||
          !Number.isInteger(maxMatches) || maxMatches < 1) {
        throw new RangeError("History limits must be positive integers");
      }
      this.maxFrames = maxFrames;
      this.maxMatches = maxMatches;
      this.matches = new Map();
      this.matchId = null;
      this.listeners = new Set();
    }
    onMatchChanged(listener) {
      this.listeners.add(listener);
      return () => this.listeners.delete(listener);
    }
    frames(matchId = this.matchId) {
      return this.matches.get(matchIdOf(matchId))?.frames ?? [];
    }
    getFrame(matchId, t) {
      return this.matches.get(matchIdOf(matchId))?.byTick.get(t) ?? null;
    }
    nearestFrame(matchId, t) {
      if (!Number.isFinite(t)) return null;
      return this.frames(matchId).reduce((best, f) =>
        !best || Math.abs(f.t - t) < Math.abs(best.t - t) ? f : best, null);
    }
    add(raw) {
      if (!raw || !Number.isInteger(raw.t) || raw.t < 0) return null;
      const matchId = matchIdOf(raw.match_id);
      const previous = this.matchId;
      const changed = previous !== matchId;
      // A retained, completed partition must never reactivate from a late packet.
      if (changed && this.matches.has(matchId)) return null;
      if (!this.matches.has(matchId)) {
        this.matches.set(matchId, { frames: [], byTick: new Map(), terrain: null });
      }
      const partition = this.matches.get(matchId);
      if (raw.terrain ?? raw.surface_map) partition.terrain = raw.terrain ?? raw.surface_map;
      const frame = Object.assign({}, raw, {
        match_id: matchId, schema_version: raw.schema_version ?? "legacy",
        terrain: raw.terrain ?? partition.terrain,
        creatures: (raw.creatures ?? []).map(normalizeCreature),
      });
      const old = partition.byTick.get(frame.t);
      if (old) partition.frames[partition.frames.indexOf(old)] = frame;
      else {
        const frames = partition.frames;
        if (!frames.length || frames[frames.length - 1].t < frame.t) frames.push(frame);
        else {
          let lo = 0, hi = frames.length;
          while (lo < hi) {
            const mid = (lo + hi) >>> 1;
            if (frames[mid].t < frame.t) lo = mid + 1;
            else hi = mid;
          }
          frames.splice(lo, 0, frame);
        }
      }
      partition.byTick.set(frame.t, frame);
      while (partition.frames.length > this.maxFrames) {
        partition.byTick.delete(partition.frames.shift().t);
      }
      this.matchId = matchId;
      while (this.matches.size > this.maxMatches) {
        this.matches.delete(this.matches.keys().next().value);
      }
      if (changed) for (const listener of this.listeners) listener(matchId, previous);
      return frame;
    }
  }
  const api = { FrameHistory, matchIdOf, normalizeCreature, LEGACY_MATCH_ID };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GenesisTelemetry = api;
})(typeof window !== "undefined" ? window : globalThis);
