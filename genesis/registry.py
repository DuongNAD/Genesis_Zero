"""Genesis Zero — registry: quản lý định nghĩa loài động (SpeciesRegistry)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from genesis import config
from genesis.traits import Traits, founder_traits


@dataclass
class SpeciesSpec:
    """Đặc tả một loài trong thế giới Genesis."""

    species_id: str
    display_name: str
    persona: str
    traits: Traits
    pop: int
    slots: list[int] = field(default_factory=list)
    client_id: str | None = None
    model_name: str | None = None
    endpoint: str | None = None
    is_bot: bool = False
    is_feral: bool = False


class SpeciesRegistry:
    """Sổ đăng ký các loài tham gia thế giới."""

    def __init__(self, specs: list[SpeciesSpec] | None = None) -> None:
        self._species: dict[str, SpeciesSpec] = {}
        self._counts: dict[str, int] = {}
        if specs:
            for s in specs:
                self.add(s)

    def add(self, spec: SpeciesSpec) -> list[str]:
        """Thêm hoặc cập nhật đặc tả loài, sinh danh sách creature_id dạng '{species_id}:{n}'."""
        start_idx = self._counts.get(spec.species_id, 0)
        ids = [f"{spec.species_id}:{start_idx + i}" for i in range(spec.pop)]
        self._counts[spec.species_id] = start_idx + spec.pop
        self._species[spec.species_id] = spec
        return ids

    def remove(self, species_id: str) -> None:
        """Xoá một loài khỏi sổ đăng ký."""
        self._species.pop(species_id, None)

    def mark_feral(self, species_id: str, feral: bool = True) -> None:
        """Đánh dấu loài chạy ở chế độ hoang dã (feral)."""
        if species_id in self._species:
            self._species[species_id].is_feral = feral

    def __iter__(self) -> Iterator[SpeciesSpec]:
        """Duyệt các loài theo thứ tự CỐ ĐỊNH (sắp xếp tăng dần theo species_id)."""
        for sp_id in sorted(self._species.keys()):
            yield self._species[sp_id]

    def __len__(self) -> int:
        return len(self._species)

    def __contains__(self, species_id: str) -> bool:
        return species_id in self._species

    def __getitem__(self, species_id: str) -> SpeciesSpec:
        return self._species[species_id]

    def get(self, species_id: str, default: Any = None) -> SpeciesSpec | None:
        return self._species.get(species_id, default)


def registry_from_config(cfg: Any = config) -> SpeciesRegistry:
    """Nạp SpeciesRegistry từ cấu hình (Lab mode).

    Không hardcode tên loài, đọc động từ cfg.POPULATION và cfg.FOUNDERS.
    """
    registry = SpeciesRegistry()
    for species_id, pop in cfg.POPULATION.items():
        traits = founder_traits(species_id)
        endpoint_info = getattr(cfg, "SPECIES_ENDPOINTS", {}).get(species_id, {})
        endpoint_url = endpoint_info.get("url") if isinstance(endpoint_info, dict) else None
        slots = endpoint_info.get("slots", []) if isinstance(endpoint_info, dict) else []
        spec = SpeciesSpec(
            species_id=species_id,
            display_name=species_id,
            persona=f"Species {species_id}",
            traits=traits,
            pop=pop,
            slots=slots,
            client_id=getattr(cfg, "LOG_FIELDS_EXTRA", {}).get("client_id"),
            model_name=getattr(cfg, "LOG_FIELDS_EXTRA", {}).get("model_name"),
            endpoint=endpoint_url,
            is_bot=False,
            is_feral=False,
        )
        registry.add(spec)
    return registry


from_config = registry_from_config
