from typing import Set
from dataclasses import dataclass

from ..parse_v8 import SheetInstance

from .placement_settings import ClonePlacementSettings


@dataclass
class CloneSettings():
	instances: Set[SheetInstance]
	placement: ClonePlacementSettings

	def is_valid(self) -> bool:
		return bool(self.instances) and self.placement.is_valid()
