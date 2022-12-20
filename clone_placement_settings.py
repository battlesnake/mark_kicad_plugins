from typing import final
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

import pcbnew  # pyright: ignore

from .kicad_units import UserUnits
from .kicad_entities import Footprint


class ClonePlacementStrategySettings(ABC):

	@abstractmethod
	def is_valid(self) -> bool:
		pass


@final
@dataclass
class ClonePlacementRelativeStrategySettings(ClonePlacementStrategySettings):
	anchor: Footprint

	def is_valid(self) -> bool:
		return self.anchor is not None


class ClonePlacementGridSort(Enum):
	REFERENCE = "reference"
	HIERARCHY = "hierarchy"


class ClonePlacementGridFlow(Enum):
	ROW = "row"
	COLUMN = "column"


@final
@dataclass
class ClonePlacementGridStrategySettings(ClonePlacementStrategySettings):
	sort: ClonePlacementGridSort
	flow: ClonePlacementGridFlow
	length_unit: UserUnits
	main_interval: int
	cross_interval: int
	wrap: bool
	wrap_at: int

	def is_valid(self) -> bool:
		return self.main_interval > 0 and \
				(not self.wrap or (self.wrap_at > 0 and self.cross_interval > 0))


class ClonePlacementStrategyType(Enum):
	RELATIVE = "relative"
	GRID = "grid"


@dataclass
class ClonePlacementSettings():
	strategy: ClonePlacementStrategyType

	relative: ClonePlacementRelativeStrategySettings
	grid: ClonePlacementGridStrategySettings

	def is_valid(self) -> bool:
		if self.strategy == ClonePlacementStrategyType.RELATIVE:
			return self.relative.is_valid()
		elif self.strategy == ClonePlacementStrategyType.GRID:
			return self.grid.is_valid()
		else:
			return False
