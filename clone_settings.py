from typing import Set
from dataclasses import dataclass

import pcbnew  # pyright: ignore

from .kicad_entities import SheetInstance
from .clone_placement_settings import ClonePlacementSettings


@dataclass
class CloneSettings():
	instances: Set[SheetInstance]
	placement: ClonePlacementSettings

	def is_valid(self) -> bool:
		return bool(self.instances) and self.placement.is_valid()
