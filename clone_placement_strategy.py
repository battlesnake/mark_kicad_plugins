from typing import Optional, final, Sequence, Iterator, Tuple, Callable, Dict, TypeVar, cast, overload, List
from abc import ABC, abstractmethod
from math import copysign
from dataclasses import dataclass, field

import pcbnew  # pyright: ignore

from .kicad_units import RotationUnits
from .kicad_entities import Footprint
from .placement import Placement
from .clone_placement_settings import ClonePlacementGridFlow, ClonePlacementGridSort, ClonePlacementGridStrategySettings, ClonePlacementRelativeStrategySettings, ClonePlacementStrategyType, ClonePlacementSettings, ClonePlacementGridStrategySettings


PlacementResult = Tuple[Footprint, Placement]


ItemType = TypeVar("ItemType", bound=pcbnew.BOARD_ITEM)


@dataclass
class ClonePlacementChangeLog():
	created_items: List[pcbnew.BOARD_ITEM] = field(default_factory=lambda:[], hash=False, compare=False, repr=False)
	original_placements: List[Tuple[pcbnew.FOOTPRINT, Placement]] = field(default_factory=lambda:[], hash=False, compare=False, repr=False)

	def undo(self) -> None:
		for created_item in self.created_items:
			created_item.GetBoard().RemoveNative(created_item)
		for footprint, original_placement in self.original_placements:
			footprint.SetPosition(original_placement.position)
			footprint.SetOrientationDegrees(original_placement.angle)
			if footprint.IsFlipped() != original_placement.flipped:
				footprint.Flip(footprint.GetPosition(), False)


class ClonePlacementStrategy(ABC, Iterator[PlacementResult]):

	def __init__(self):
		self.change_log = ClonePlacementChangeLog()

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

	@staticmethod
	def internal_apply_placement(
		source_reference: Placement,
		target_reference: Placement,
		target_item: pcbnew.BOARD_ITEM,
	) -> None:
		# Assumes that target item is at same location/angle/side as source item
		def clamp_angle(angle: float):
			while angle > 180: angle -= 360
			while angle < -180: angle += 360
			return angle
		rotation = clamp_angle(target_reference.angle - source_reference.angle)
		flip = target_reference.flipped != source_reference.flipped
		target_item.Move(target_reference.position - source_reference.position)
		if flip:
			target_item.Flip(target_reference.position, False)
			source_angle = source_reference.angle
			flipped_angle = copysign(180 - abs(source_angle), source_angle)
			rotation = 180 - flipped_angle - target_reference.angle
		rotation += target_reference.angle - source_reference.angle
		target_item.Rotate(target_reference.position, int(rotation * RotationUnits.PER_DEGREE))

	@staticmethod
	def internal_transfer_footprint_placement(source: pcbnew.FOOTPRINT, target: pcbnew.FOOTPRINT) -> None:
		# Satisfy pre-condition for internal_apply_placement
		target.SetPosition(source.GetPosition())
		target.SetOrientation(source.GetOrientation())
		if target.IsFlipped() != source.IsFlipped():
			target.Flip(target.GetPosition(), False)

	@overload
	def apply_placement(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: pcbnew.BOARD_ITEM,
	) -> None: ...

	@overload
	def apply_placement(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: pcbnew.FOOTPRINT,
		target_item: pcbnew.FOOTPRINT,
	) -> None: ...

	def apply_placement(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: ItemType,
		target_item: Optional[ItemType] = None,
	) -> None:
		if target_item is None and not isinstance(source_item, pcbnew.FOOTPRINT):
			target_item = cast(ItemType, source_item.Duplicate())
			source_item.GetBoard().Add(target_item)
			self.change_log.created_items.append(target_item)
			return ClonePlacementStrategy.internal_apply_placement(source_reference, target_reference, target_item)
		elif isinstance(target_item, pcbnew.FOOTPRINT) and isinstance(source_item, pcbnew.FOOTPRINT):
			self.change_log.original_placements.append((target_item, Placement.of(target_item)))
			ClonePlacementStrategy.internal_transfer_footprint_placement(source_item, target_item)
			return ClonePlacementStrategy.internal_apply_placement(source_reference, target_reference, target_item)
		else:
			raise ValueError()


@final
class ClonePlacementRelativeStrategy(ClonePlacementStrategy):

	def __init__(self, settings: ClonePlacementRelativeStrategySettings, reference: Footprint, targets: Sequence[Footprint]):
		super().__init__()
		self.settings = settings
		self.targets = filter(lambda target: target != reference, targets)

	def __next__(self) -> PlacementResult:
		target = next(self.targets)
		placement = Placement.of(target.data)
		return target, placement


@final
class ClonePlacementGridStrategy(ClonePlacementStrategy):

	@staticmethod
	def compare_footprint_by_reference(footprint: Footprint) -> List[str | int]:
		ref = int("".join([
			ch
			for ch in footprint.reference
			if ch.isdigit()
		]) + "0")
		return [ref, footprint.reference]

	@staticmethod
	def compare_footprint_by_hierarchy(footprint: Footprint) -> List[str | int]:
		return list(footprint.sheet_instance.name_chain)

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
