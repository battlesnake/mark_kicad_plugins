from typing import Optional, final, Sequence
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

import pcbnew  # pyright: ignore

from .kicad_entities import Footprint, SIZE_SCALE


class ClonePlacementStrategySettings(ABC):

	@abstractmethod
	def is_valid(self) -> bool:
		pass


@final
@dataclass
class ClonePlacementRelativeStrategySettings(ClonePlacementStrategySettings):
	anchor: Optional[Footprint] = None

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
	sort: ClonePlacementGridSort = ClonePlacementGridSort.HIERARCHY
	flow: ClonePlacementGridFlow = ClonePlacementGridFlow.ROW
	main_interval: int = SIZE_SCALE
	wrap: bool = False
	wrap_at: int = 8
	cross_interval: int = SIZE_SCALE

	def is_valid(self) -> bool:
		return self.main_interval > 0 and \
				(not self.wrap or (self.wrap_at > 0 and self.cross_interval > 0))


class ClonePlacementStrategyType(Enum):
	RELATIVE = "relative"
	GRID = "grid"


@dataclass
class ClonePlacementSettings():
	strategy: ClonePlacementStrategyType = ClonePlacementStrategyType.RELATIVE

	relative: ClonePlacementRelativeStrategySettings = ClonePlacementRelativeStrategySettings()
	grid: ClonePlacementGridStrategySettings = ClonePlacementGridStrategySettings()

	def is_valid(self) -> bool:
		if self.strategy == ClonePlacementStrategyType.RELATIVE:
			return self.relative.is_valid()
		elif self.strategy == ClonePlacementStrategyType.GRID:
			return self.grid.is_valid()
		else:
			return False
