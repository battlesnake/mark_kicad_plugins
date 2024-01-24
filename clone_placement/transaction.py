from typing import Iterable, Union, final, List, Callable, overload
from abc import ABC
from math import copysign

from pcbnew import EDA_ANGLE, DEGREE_T, BOARD_ITEM, FOOTPRINT, VECTOR2I

from ..layout_transaction.command import CloneCommand, Command, DisplaceCommand, FlipCommand, MoveToLayerCommand, RotateCommand

from ..kicad_v8_model.angle import Angle
from ..kicad_v8_model.entities import ArcRoute, Footprint, PolygonRoute, StraightRoute, Via

from ..utils.kicad_units import RotationUnits
from ..utils.user_exception import UserException

from .placement import Placement


class CloneTransactionOperator(ABC):

	def __init__(self, source_reference_placement: Placement, target_reference_placement: Placement):
		self.source_reference_placement = source_reference_placement
		self.target_reference_placement = target_reference_placement
		self.rotation = (target_reference_placement.orientation - source_reference_placement.orientation).wrap()
		self.flip = target_reference_placement.flipped != source_reference_placement.flipped
		self.displacement = target_reference_placement.position - source_reference_placement.position

	@overload
	def apply(self, target_item: Footprint) -> Iterable[Command]:
		...

	@overload
	def apply(self, target_item: StraightRoute) -> Iterable[Command]:
		...

	@overload
	def apply(self, target_item: ArcRoute) -> Iterable[Command]:
		...

	@overload
	def apply(self, target_item: PolygonRoute) -> Iterable[Command]:
		...

	@overload
	def apply(self, target_item: Via) -> Iterable[Command]:
		...

	@overload
	def apply(self, target_item: CloneCommand) -> Iterable[Command]:
		...

	def apply(self, target_item: Union[Footprint, StraightRoute, ArcRoute, PolygonRoute, Via, CloneCommand]) -> Iterable[Command]:
		yield MoveToLayerCommand(target=target_item, layer=self.source_reference_placement.layer)
		# Assumes that target item is at same location/angle/side as source item
		yield DisplaceCommand(target=target_item, displacement=self.displacement)
		if self.flip:
			yield FlipCommand(target=target_item)
		if isinstance(target_item, Footprint):
			rotation = self.rotation.degrees
			if self.flip:
				source_angle = self.source_reference_placement.orientation.degrees
				target_angle = self.target_reference_placement.orientation.degrees
				flipped_angle = copysign(180 - abs(source_angle), source_angle)
				rotation = 180 - flipped_angle - target_angle
			rotation += (self.target_reference_placement.orientation - self.source_reference_placement.orientation).degrees
			yield RotateCommand(target=target_item, rotation=Angle.from_degrees(rotation))


@final
class CloneTransactionTransferFootprintPlacementOperator(CloneTransactionOperator):

	def __init__(self, source_reference_placement: Placement, target_reference_placement: Placement, source_footprint: FOOTPRINT, target_footprint: FOOTPRINT):
		super().__init__(source_reference_placement, target_reference_placement)
		self.original_placement = Placement.of(target_footprint)
		self.target_footprint = target_footprint
		self.current_placement = self.original_placement
		self.source_footprint_placement = Placement.of(source_footprint)

	def apply(self) -> None:
		# Place footprint at same position as source footprint, to satisfy
		# precondition for apply_displacement operator
		self.internal_place_footprint(self.source_footprint_placement)
		self.internal_apply_displacement(self.target_footprint)

	def revert(self) -> None:
		self.internal_place_footprint(self.original_placement)

	def internal_place_footprint(self, where: Placement):
		current = self.current_placement
		target_footprint = self.target_footprint
		target_footprint.SetPosition(where.position)
		target_footprint.SetOrientation(int(where.angle * RotationUnits.PER_DEGREE))
		if current.flipped != where.flipped:
			target_footprint.Flip(target_footprint.GetPosition(), False)
		self.current_placement = Placement.of(target_footprint)


@final
class CloneTransactionDuplicateAndTransferPlacementPlacementOperator(CloneTransactionOperator):

	def __init__(self, source_reference_placement: Placement, target_reference_placement: Placement, source_item: BOARD_ITEM):
		super().__init__(source_reference_placement, target_reference_placement)
		self.source_item = source_item
		self.target_item: BOARD_ITEM | None = None

	def apply(self) -> None:
		if self.target_item is not None:
			return
		source_item = self.source_item
		target_item = source_item.Duplicate()
		source_item.GetBoard().Add(target_item)
		self.target_item = target_item
		self.internal_apply_displacement(target_item)

	def revert(self) -> None:
		if self.target_item is None:
			return
		target_item = self.target_item
		self.target_item = None
		target_item.GetBoard().RemoveNative(target_item)


class CloneTransaction():

	def __init__(self):
		self.operators: List[CloneTransactionOperator] = []
		self.on_progress: Callable[[int, int], None] | None = None

	def add(self, operator: CloneTransactionOperator) -> None:
		self.operators.append(operator)

	def progress(self, step: int, count: int) -> None:
		if self.on_progress is not None:
			self.on_progress(step, count)

	def apply(self) -> None:
		try:
			for index, operator in enumerate(self.operators):
				self.progress(index, len(self.operators))
				operator.apply()
		except Exception as error:
			self.revert()
			raise UserException("Clone operation failed, partial changes reverted") from error

	def revert(self) -> None:
		for index, operator in enumerate(reversed(self.operators)):
			self.progress(index, len(self.operators))
			operator.revert()
