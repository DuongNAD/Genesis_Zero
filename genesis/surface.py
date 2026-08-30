"""Genesis Zero — surface: Ánh xạ lớp quả sang bề mặt quan sát được."""

from __future__ import annotations

import random
from dataclasses import dataclass

from genesis import law_config


@dataclass(frozen=True)
class SurfaceMap:
    cls_to_surface: dict[str, str]  # "FRUIT_A" -> "quả đỏ tròn"

    def surface_of(self, cls: str) -> str:
        return self.cls_to_surface[cls]

    def class_of(self, surface: str) -> str | None:
        for k, v in self.cls_to_surface.items():
            if v == surface:
                return k
        return None


def roll_surface_map(rng: random.Random) -> SurfaceMap:
    """Tạo SurfaceMap ngẫu nhiên bằng cách hoán vị danh sách bề mặt."""
    surfaces = [f"quả {c} {s}" for c, s in law_config.FRUIT_SURFACES]
    shuffled = list(surfaces)
    rng.shuffle(shuffled)
    cls_names = [f"FRUIT_{chr(ord('A') + i)}" for i in range(law_config.FRUIT_KINDS)]
    cls_to_surface = dict(zip(cls_names, shuffled))
    return SurfaceMap(cls_to_surface=cls_to_surface)
