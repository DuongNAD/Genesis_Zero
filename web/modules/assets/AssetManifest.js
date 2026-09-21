/**
 * AssetManifest.js - Central catalog of 3D Models, Dioramas, Flora, and Audio
 * Part of Genesis Zero Modular Architecture (Module 1: Assets Management).
 * 100% Offline, Zero-CDN compliant.
 */

export const CREATURE_ASSET_REGISTRY = {
  "sand_skink":       { code: "L1", domain: "CAN",  path: "assets/creatures/sand_skink.glb", name: "Sand Skink" },
  "snow_ferret":      { code: "L2", domain: "CAN",  path: "assets/creatures/snow_ferret.glb", name: "Snow Ferret" },
  "alpine_ibex":      { code: "L3", domain: "CAN",  path: "assets/creatures/alpine_ibex.glb", name: "Alpine Ibex" },
  "meadow_hare":      { code: "L4", domain: "CAN",  path: "assets/creatures/meadow_hare.glb", name: "Meadow Hare" },
  "marsh_croc":       { code: "L5", domain: "CAN",  path: "assets/creatures/marsh_croc.glb", name: "Marsh Croc" },
  "abyssal_hunter":   { code: "W1", domain: "NUOC", path: "assets/creatures/abyssal_hunter.glb", name: "Abyssal Hunter" },
  "storm_eagle":      { code: "A1", domain: "TROI", path: "assets/creatures/storm_eagle.glb", name: "Storm Eagle" },
  "armored_sentinel": { code: "S1", domain: "CAN",  path: "assets/creatures/armored_sentinel.glb", name: "Armored Sentinel" },
  "giant_tarantula":  { code: "B1", domain: "CAN",  path: "assets/creatures/giant_tarantula.glb", name: "Giant Tarantula" },
  "carnivore_apex":   { code: "X1", domain: "CAN",  path: "assets/creatures/carnivore_apex.glb", name: "Carnivore Apex" },
};

export const MAP_ASSET_REGISTRY = {
  "master_diorama": {
    path: "assets/blender_map/ecosystem_map.glb",
    fallbackPaths: [
      "../assets/blender_map/ecosystem_map.glb",
      "/assets/blender_map/ecosystem_map.glb",
      "assets/blender_map/ecosystem_map.glb"
    ],
    name: "Master Ecosystem Diorama",
    hasKarstCave: true,
    hasHydrology: true,
    hasRockCrags: true
  },
  "manifest": {
    path: "assets/map_manifest.json"
  }
};

export const FLORA_ASSET_REGISTRY = {
  "canopy_tree":       { category: "canopy_trees", path: "assets/flora/canopy_trees/" },
  "understory_shrub":  { category: "understory_shrubs", path: "assets/flora/understory_shrubs/" },
  "aquatic_plant":     { category: "aquatic_wetland", path: "assets/flora/aquatic_wetland/" },
  "cave_mushroom":     { category: "cave_bioluminescent", path: "assets/flora/cave_bioluminescent/" }
};

if (typeof window !== "undefined") {
  window.CREATURE_ASSET_REGISTRY = CREATURE_ASSET_REGISTRY;
  window.MAP_ASSET_REGISTRY = MAP_ASSET_REGISTRY;
  window.FLORA_ASSET_REGISTRY = FLORA_ASSET_REGISTRY;
}
