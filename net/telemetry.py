"""Public telemetry contract. Additive changes retain the schema major version."""

from __future__ import annotations

from dataclasses import astuple
from typing import TYPE_CHECKING, TypedDict

from genesis import config

if TYPE_CHECKING:
    from genesis.creature import Creature
    from net.match import MatchRunner

SCHEMA_VERSION = "1.0"


class CreatureTelemetry(TypedDict):
    """Allowlisted viewer fields; never include hidden law or seed identifiers."""

    id: str
    species: str
    domain: str
    x: int
    y: int
    hp: float
    e: float
    e_max: float
    alive: bool
    feral: bool
    tr: list[int]
    features: list[str]
    gen: int
    parent_id: str | None
    lineage: str
    d_tr: list[int]
    age: int


def creature_telemetry(runner: MatchRunner, creature: Creature) -> CreatureTelemetry:
    """Serialize current body traits using the same contract for frame and dossier."""
    traits = list(astuple(creature.traits))
    founder = config.FOUNDERS.get(creature.species, traits)
    features = list(creature.features)
    if not features and runner.world is not None:
        kit = runner.world.kits.get(creature.species)
        if kit is not None:
            features = list(kit.keys)
    return {
        "id": creature.id,
        "species": creature.species,
        "domain": config.SPECIES_DOMAIN.get(creature.species, "CAN"),
        "x": creature.pos[0],
        "y": creature.pos[1],
        "hp": round(creature.hp, 1),
        "e": round(creature.energy, 1),
        "e_max": round(creature.traits.energy_max, 1),
        "alive": creature.alive,
        "feral": any(
            reg.species_id == creature.species and runner.is_feral(cid)
            for cid, reg in runner.registrations.items()
        ),
        "tr": traits,
        "features": features,
        "gen": creature.generation,
        "parent_id": creature.parent_id,
        "lineage": creature.lineage_id or creature.id,
        "d_tr": [value - baseline for value, baseline in zip(traits, founder)],
        "age": creature.age,
    }


def envelope(match_id: str) -> dict[str, str]:
    """Metadata only: never include the hidden seed or law identifiers."""
    return {"schema_version": SCHEMA_VERSION, "match_id": match_id}

