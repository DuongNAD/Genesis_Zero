# Genesis Zero — Telemetry Protocol Contract (v1.0)

**Document Version**: 1.0.0  
**Authoritative Subsystems**: `net/telemetry.py`, `net/match.py`, `net/routes_spectate.py`, `web/frame_history.js`  
**Security Classification**: Public Broadcast Protocol (No Secrets, Zero Information Leakage)

---

## 1. Overview & Architectural Principles

The Genesis Zero Telemetry Stream provides real-time, event-driven state replication for 2D/3D WebGL spectators (`web/watch3d.html`, `viewer.html`) and external analytical observers.

### Core Security & Privacy Invariants:
1. **Zero Hidden-Law Leakage**: During the `RUNNING` simulation phase, hidden laws governing physical phenomena are strictly masked. `LAW_FIRED` events transmit `"law": "?"` and hide effect descriptions until the official `REVEAL` phase.
2. **Zero Seed Exposure**: The internal world simulation seed (`world.seed`) and internal PRNG states are never broadcast across public telemetry envelopes.
3. **Bandwidth Optimization via Asymmetric Terrain Streaming**: The complete $24 \times 24$ terrain matrix (~3 KB) is transmitted **only once** on tick 0 or injected into the initial backlog frame of late-joining spectators. Subsequent tick frames carry empty or delta terrain structures.
4. **Offline Zero-CDN Operation**: All telemetry decoding and WebGL 3D rendering operate completely self-contained within local networks with no external CDN lookups.

---

## 2. Envelope Specification

Every JSON frame emitted by WebSocket `/v1/spectate` or HTTP `/v1/spectate/dossier` includes a top-level metadata envelope:

```json
{
  "schema_version": "1.0",
  "match_id": "m_00001"
}
```

- `schema_version` (string): Canonical schema semantic version (`"1.0"`).
- `match_id` (string): Unique identifier of the current match instance.

---

## 3. Real-Time Tick Frame Schema (`/v1/spectate`)

A tick frame is streamed once per simulation cycle over the WebSocket `/v1/spectate` endpoint.

### Schema:
```json
{
  "schema_version": "1.0",
  "match_id": "m_00001",
  "t": 42,
  "phase": "RUNNING",
  "w": 24,
  "h": 24,
  "map": "DONG_CO",
  "creatures": [
    {
      "id": "L1:0",
      "species": "L1",
      "domain": "CAN",
      "x": 12,
      "y": 8,
      "hp": 48.5,
      "e": 82.0,
      "e_max": 93.0,
      "alive": true,
      "feral": false,
      "tr": [4, 3, 1, 2, 1, 1],
      "features": ["DAO_HANG", "TREO_GIOI"],
      "gen": 0,
      "parent_id": null,
      "lineage": "L1:0",
      "d_tr": [0, 0, 0, 0, 0, 0],
      "age": 42
    }
  ],
  "plants": [[4, 6], [12, 18], [15, 3]],
  "corpses": [[9, 14]],
  "terrain_delta": [],
  "terrain": null,
  "weather": {
    "kind": "CLEAR",
    "illum": 1.0,
    "temp": 0.5,
    "diurnal": "DAY",
    "cycle_progress": 0.35,
    "passability_mod": 1.0,
    "stamina_cost_mod": 1.0
  },
  "events": [
    {
      "k": "EAT",
      "who": "L1:0",
      "pos": [4, 6],
      "fruit": "qua_do_mong"
    }
  ]
}
```

### Top-Level Fields:
| Field | Type | Description |
|---|---|---|
| `t` | `integer` | Simulation tick counter (0..N). |
| `phase` | `string` | Match lifecycle state: `"LOBBY"`, `"SEEDING"`, `"RUNNING"`, `"REVEAL"`, `"COOLDOWN"`. |
| `w` | `integer` | Torus grid width (default: 24). |
| `h` | `integer` | Torus grid height (default: 24). |
| `map` | `string` | Biome map name (e.g. `"DONG_CO"`, `"RUNG_RAM"`, `"HOANG_MAC"`). |
| `creatures` | `array` | Array of `CreatureTelemetry` records. |
| `plants` | `array[list[int, int]]` | Active fruit coordinates `[[x, y], ...]`. |
| `corpses` | `array[list[int, int]]` | Organic corpse coordinates `[[x, y], ...]`. |
| `terrain_delta`| `array` | List of modified terrain tiles (if any). |
| `terrain` | `array[string] \| null` | 24 rows of ASCII terrain codes (`P`: Plain, `W`: Water, `B`: Bush, `R`: Rock, `F`: Fire). Sent on tick 0 or first backlog frame. |
| `weather` | `object` | Environmental and diurnal weather indicators. |
| `events` | `array[object]` | Sanitized public events occurring during this tick. |

---

## 4. Organism State Specification (`CreatureTelemetry`)

Each creature in `creatures` conforms to `CreatureTelemetry`:

| Canonical Field | Type | Description | Legacy Alias |
|---|---|---|---|
| `id` | `string` | Unique organism identifier (e.g. `"L1:0"`). | — |
| `species` | `string` | Species classification (e.g. `"L1"`, `"L2"`). | `species_id` |
| `domain` | `string` | Ecological stratum: `"CAN"` (Terrestrial), `"THUY"` (Aquatic), `"KHONG"` (Aerial). | — |
| `x` | `integer` | Horizontal grid coordinate $[0, w-1]$. | — |
| `y` | `integer` | Vertical grid coordinate $[0, h-1]$. | — |
| `hp` | `float` | Current health points (rounded to 1 decimal). | — |
| `e` | `float` | Current energy reserve (rounded to 1 decimal). | `energy` |
| `e_max` | `float` | Maximum energy capacity based on traits. | — |
| `alive` | `boolean` | True if creature is alive; False if deceased this tick. | — |
| `feral` | `boolean` | True if external controller timed out / defaulted to feral reflex. | — |
| `tr` | `list[int]` | 6 numeric traits: `[brain, attack, armor, speed, sense, stomach]`. | `traits` |
| `features` | `list[str]` | Biological and anatomical trait adaptations. | — |
| `gen` | `integer` | Generational index ($0$ for founders, $\ge 1$ for offspring). | `generation` |
| `parent_id` | `str \| null` | Identifier of maternal parent organism. | — |
| `lineage` | `string` | Root progenitor lineage ancestor ID. | `lineage_id` |
| `d_tr` | `list[int]` | Delta trait variance relative to founder baseline: `tr - founder_tr`. | `dt_traits` |
| `age` | `integer` | Lifetime survival duration in simulation ticks. | — |

---

## 5. Dossier Specification (`/v1/spectate/dossier`)

The HTTP endpoint `/v1/spectate/dossier` returns detailed species rosters, population counts, and inferred law hypotheses.

### Dual-Key Compatibility Guarantee:
To guarantee seamless backward compatibility with legacy 2D visualizers and external monitoring scripts, `/v1/spectate/dossier` provides both canonical keys and legacy aliases:
- Both `e` and `energy` are provided for energy level.
- Both `tr` and `traits` are provided for 6-trait vectors.
- Both `d_tr` and `dt_traits` are provided for trait shift deltas.

```json
{
  "schema_version": "1.0",
  "match_id": "m_00001",
  "phase": "RUNNING",
  "tick": 42,
  "species": [
    {
      "species": "L1",
      "founder_traits": [4, 3, 1, 2, 1, 1],
      "features": ["DAO_HANG", "TREO_GIOI"],
      "creatures_count": 3,
      "alive_count": 3,
      "max_gen": 1
    }
  ],
  "creatures": [
    {
      "id": "L1:0",
      "species": "L1",
      "domain": "CAN",
      "x": 12, "y": 8, "hp": 48.5,
      "e": 82.0, "energy": 82.0,
      "e_max": 93.0,
      "alive": true, "feral": false,
      "tr": [4, 3, 1, 2, 1, 1], "traits": [4, 3, 1, 2, 1, 1],
      "d_tr": [0, 0, 0, 0, 0, 0], "dt_traits": [0, 0, 0, 0, 0, 0],
      "features": ["DAO_HANG", "TREO_GIOI"],
      "gen": 0, "parent_id": null, "lineage": "L1:0", "age": 42,
      "inferred_rules": [
        {
          "text": "KHI ăn quả tím dẹt THÌ tăng sức",
          "conf": 4,
          "written_at": 18,
          "source": "self",
          "status": "Giả thuyết chưa xác minh"
        }
      ]
    }
  ]
}
```

---

## 6. Public Simulation Events

Public events in `events` notify spectators of visible actions and reactions:

| Event Kind `k` | Key Properties | Description |
|---|---|---|
| `"MOVE"` | `who`, `from`, `to` | Organism repositioned on grid. |
| `"EAT"` | `who`, `pos`, `fruit` | Organism consumed plant fruit. |
| `"DRINK"` | `who`, `pos` | Organism drank from fresh water tile. |
| `"ATTACK"` | `who`, `target`, `damage` | Organism attacked another creature. |
| `"SPEAK"` | `who`, `signal`, `text` | In-world speech signal emission. |
| `"REPRODUCE"`| `who`, `offspring_id`, `gen` | Organism reproduced offspring. |
| `"DEATH"` | `who`, `pos`, `cause` | Organism died (exhaustion, combat, poison). |
| `"LAW_FIRED"`| `who`, `pos`, `law` | Physical law triggered (`law: "?"` during RUNNING). |

---

## 7. Versioning & Evolution Guidelines

1. **Additive Compatibility**: Adding new fields to `CreatureTelemetry`, `weather`, or `events` does NOT increment the schema major version.
2. **Deprecation Path**: Any field planned for deprecation will retain both the canonical key and its legacy alias for a minimum of 2 major release cycles.
3. **Client Conformance**: Client decoders should parse using canonical keys first (`e`, `tr`, `d_tr`), falling back to aliases (`energy`, `traits`, `dt_traits`) when interfacing with legacy replay logs.
