from typing import Optional, final, Sequence, Iterator
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

import pcbnew  # pyright: ignore

from .kicad_entities import Footprint


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


class ClonePlacementGridFlow(Enum):
	ROW = "row"
	COLUMN = "column"


@final
@dataclass
class ClonePlacementGridStrategySettings(ClonePlacementStrategySettings):
	flow: ClonePlacementGridFlow = ClonePlacementGridFlow.ROW
	main_interval: int = 1000000
	wrap: bool = False
	wrap_at: int = 8
	cross_interval: int = 1000000

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

	def get_selected_strategy(self) -> ClonePlacementStrategySettings:
		if self.strategy == ClonePlacementStrategyType.RELATIVE:
			return self.relative
		elif self.strategy == ClonePlacementStrategyType.GRID:
			return self.grid
		else:
			raise ValueError()

	def is_valid(self) -> bool:
		return self.get_selected_strategy().is_valid()


@final
@dataclass
class Placement():
	x: int
	y: int
	angle: float

	@staticmethod
	def from_footprint(footprint: Footprint) -> "Placement":
		position = footprint.data.GetPosition().x
		return Placement(
			x=position.x,
			y=position.y,
			angle=footprint.data.GetOrientationDegrees(),
		)


class ClonePlacementStrategy(ABC, Iterator[Placement]):

	@abstractmethod
	def __next__(self) -> Placement:
		pass

	def get(self, settings: ClonePlacementStrategySettings, reference: Footprint, targets: Sequence[Footprint]) -> "ClonePlacementStrategy":
		if isinstance(settings, ClonePlacementRelativeStrategySettings):
			return ClonePlacementRelativeStrategy(targets)
		elif isinstance(settings, ClonePlacementGridStrategySettings):
			return ClonePlacementGridStrategy(settings, reference, targets)
		else:
			raise TypeError(type(settings))


@final
class ClonePlacementRelativeStrategy(ClonePlacementStrategy):

	def __init__(self, targets: Sequence[Footprint]):
		self.targets = targets.__iter__()

	def __next__(self) -> Placement:
		return Placement.from_footprint(next(self.targets))


@final
class ClonePlacementGridStrategy(ClonePlacementStrategy):

	def __init__(self, settings: ClonePlacementGridStrategySettings, reference: Footprint, targets: Sequence[Footprint]):
		self.reference = Placement.from_footprint(reference)
		self.targets = targets.__iter__()
		self.settings = settings
		self.main: int = 0
		self.cross: int = 0

	def __next__(self) -> Placement:
		next(self.targets)
		main, cross = self.main, self.cross
		main = main + 1
		if self.settings.wrap and main == self.settings.wrap_at:
			main = 0
			cross = cross + 1
		self.main, self.cross = main, cross
		dmain = main * self.settings.main_interval
		dcross = cross * self.settings.cross_interval
		if self.settings.flow == ClonePlacementGridFlow.ROW:
			dx, dy = dmain, dcross
		elif self.settings.flow == ClonePlacementGridFlow.COLUMN:
			dx, dy = dcross, dmain
		else:
			raise ValueError()
		return Placement(
			x=self.reference.x + dx,
			y=self.reference.y + dy,
			angle=self.reference.angle
		)
