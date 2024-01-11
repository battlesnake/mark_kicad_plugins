from functools import reduce
from typing import final, Sequence, Iterator, Tuple, Callable, Dict, List
from abc import ABC, abstractmethod

from ..geometry import Vector2
from ..kicad_v8_model import Footprint, EntityPath, Project

from .placement import Placement
from .placement_settings import ClonePlacementGridFlow, ClonePlacementGridSort, ClonePlacementGridStrategySettings, ClonePlacementRelativeStrategySettings, ClonePlacementStrategyType, ClonePlacementSettings


PlacementResult = Tuple[Footprint, Placement]


class ClonePlacementStrategy(ABC, Iterator[PlacementResult]):

	@abstractmethod
	def __next__(self) -> PlacementResult:
		pass

	@staticmethod
	def get(project: Project, settings: ClonePlacementSettings, reference: Footprint, targets: Sequence[Footprint]) -> "ClonePlacementStrategy":
		if settings.strategy == ClonePlacementStrategyType.RELATIVE:
			return ClonePlacementRelativeStrategy(settings.relative, reference, iter(targets))
		elif settings.strategy == ClonePlacementStrategyType.GRID:
			return ClonePlacementGridStrategy(project, settings.grid, reference, iter(targets))
		else:
			raise ValueError(settings.strategy)


@final
class ClonePlacementRelativeStrategy(ClonePlacementStrategy):

	def __init__(
		self,
		settings: ClonePlacementRelativeStrategySettings,
		reference: Footprint,
		targets: Iterator[Footprint],
	):
		super().__init__()
		self.settings = settings
		self.targets = filter(lambda target: target != reference, targets)

	def __next__(self) -> PlacementResult:
		target = next(self.targets)
		placement = Placement.of(target)
		return target, placement


@final
class ClonePlacementGridStrategy(ClonePlacementStrategy):

	def __init__(
		self,
		project: Project,
		settings: ClonePlacementGridStrategySettings,
		reference: Footprint,
		targets: Iterator[Footprint],
	):
		super().__init__()
		comparators: Dict[ClonePlacementGridSort, Callable[[Footprint], List[str | int]]] = {
			ClonePlacementGridSort.REFERENCE: self.compare_footprint_by_reference,
			ClonePlacementGridSort.HIERARCHY: self.compare_footprint_by_hierarchy,
		}
		self.reference = Placement.of(reference)
		self.targets = sorted(targets, key=comparators[settings.sort]).__iter__()
		self.project = project
		self.settings = settings
		self.main: int = 0
		self.cross: int = 0

	def compare_footprint_by_reference(self, footprint: Footprint) -> List[str | int]:
		""" Key-function for sorting footprints (number, then type) """
		number = int("".join(
			ch
			for ch in footprint.component.reference.designator
			if ch.isdigit()
		) or "0")
		return [
			number,
			footprint.component.reference.designator
		]

	def compare_footprint_by_hierarchy(self, footprint: Footprint) -> List[str | int]:
		""" Key-function for sorting footprints """
		result: List[str] = []
		sheets = [
			unit.sheet
			for unit in footprint.component.units
		]
		sheet_paths = [
			sheet.path
			for sheet in sheets
		]
		common_sheet_path = reduce(EntityPath.__and__, sheet_paths)
		# TODO fix
		common_sheet = self.project.sheet_instances[common_sheet_path]
		while common_sheet is not None:
			result.append(common_sheet.name)
			common_sheet = common_sheet.parent
		return list(reversed(result))

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
			position=reference.position + Vector2(dx, dy),
			orientation=reference.orientation,
			flipped=reference.flipped
		)
		return target, placement
