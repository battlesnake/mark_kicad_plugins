from typing import final, Sequence, Iterator, Tuple, Callable, Dict, List
from abc import ABC, abstractmethod

from ..parse_v8 import Footprint

from ..utils.placement import Placement

from .placement_settings import ClonePlacementGridFlow, ClonePlacementGridSort, ClonePlacementGridStrategySettings, ClonePlacementRelativeStrategySettings, ClonePlacementStrategyType, ClonePlacementSettings


PlacementResult = Tuple[Footprint, Placement]


class ClonePlacementStrategy(ABC, Iterator[PlacementResult]):

	@abstractmethod
	def __next__(self) -> PlacementResult:
		pass

	@staticmethod
	def get(settings: ClonePlacementSettings, reference: Footprint, targets: Sequence[Footprint]) -> "ClonePlacementStrategy":
		if settings.strategy == ClonePlacementStrategyType.RELATIVE:
			return ClonePlacementRelativeStrategy(settings.relative, reference, targets)
		elif settings.strategy == ClonePlacementStrategyType.GRID:
			return ClonePlacementGridStrategy(settings.grid, reference, targets)
		else:
			raise ValueError(settings.strategy)


@final
class ClonePlacementRelativeStrategy(ClonePlacementStrategy):

	def __init__(self, settings: ClonePlacementRelativeStrategySettings, reference: Footprint, targets: Sequence[Footprint]):
		super().__init__()
		self.settings = settings
		self.targets = filter(lambda target: target != reference, targets)

	def __next__(self) -> PlacementResult:
		target = next(self.targets)
		placement = Placement.of(target.pcbnew_footprint)
		return target, placement


@final
class ClonePlacementGridStrategy(ClonePlacementStrategy):

	@staticmethod
	def compare_footprint_by_reference(footprint: Footprint) -> List[str | int]:
		""" Key-function for sorting footprints (number, then type) """
		number = int("".join(
			ch
			for ch in footprint.symbol_instance.reference.designator
			if ch.isdigit()
		) or "0")
		return [
			number,
			footprint.reference.designator
		]

	@staticmethod
	def compare_footprint_by_hierarchy(footprint: Footprint) -> List[str | int]:
		""" Key-function for sorting footprints """
		return list(footprint.symbol_instance.sheet.path)

	def __init__(self, settings: ClonePlacementGridStrategySettings, reference: Footprint, targets: Sequence[Footprint]):
		super().__init__()
		comparators: Dict[ClonePlacementGridSort, Callable[[Footprint], List[str | int]]] = {
				ClonePlacementGridSort.REFERENCE: self.compare_footprint_by_reference,
				ClonePlacementGridSort.HIERARCHY: self.compare_footprint_by_hierarchy,
		}
		self.reference = Placement.of(reference.data)
		self.targets = sorted(targets, key=comparators[settings.sort]).__iter__()
		self.settings = settings
		self.main: int = 0
		self.cross: int = 0

	def next_position(self) -> Tuple[int, int]:
		main, cross = self.main, self.cross
		result = main, cross
		main = main + 1
		if self.settings.wrap and main == self.settings.wrap_at:
			main = 0
			cross = cross + 1
		self.main, self.cross = main, cross
		return result

	def __next__(self) -> PlacementResult:
		target = next(self.targets)
		reference = self.reference
		main, cross = self.next_position()
		dmain = main * self.settings.main_interval
		dcross = cross * self.settings.cross_interval
		if self.settings.flow == ClonePlacementGridFlow.ROW:
			dx, dy = dmain, dcross
		elif self.settings.flow == ClonePlacementGridFlow.COLUMN:
			dx, dy = dcross, dmain
		else:
			raise ValueError()
		placement = Placement(
			x=reference.x + dx,
			y=reference.y + dy,
			angle=reference.angle,
			flipped=reference.flipped
		)
		return target, placement
