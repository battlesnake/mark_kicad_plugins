from typing import Set
from dataclasses import dataclass

from ..kicad_v8_model import SheetInstance

from .placement_settings import ClonePlacementSettings


@dataclass
class CloneSettings():
	instances: Set[SheetInstance]
	placement: ClonePlacementSettings

	def is_valid(self) -> bool:
		return bool(self.instances) and self.placement.is_valid()
