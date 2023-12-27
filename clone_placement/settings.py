from typing import Set
from dataclasses import dataclass

import pcbnew  # pyright: ignore

from schematic import SheetInstance
from clone_placement.placement_settings import ClonePlacementSettings


@dataclass
class CloneSettings():
	instances: Set[SheetInstance]
	placement: ClonePlacementSettings

	def is_valid(self) -> bool:
		return bool(self.instances) and self.placement.is_valid()
