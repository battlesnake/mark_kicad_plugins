from typing import final, List, Callable
from abc import ABC, abstractmethod
from math import copysign

import pcbnew  # pyright: ignore

from utils.kicad_units import RotationUnits
from utils.user_exception import UserException

from clone_placement.placement import Placement


class CloneTransactionOperator(ABC):

	def __init__(self, source_reference_placement: Placement, target_reference_placement: Placement):
		self.source_reference_placement: Placement = source_reference_placement
		self.target_reference_placement: Placement = target_reference_placement

	@abstractmethod
	def apply(self) -> None:
		pass

	@abstractmethod
	def revert(self) -> None:
		pass

	def internal_apply_displacement(self, target_item: pcbnew.BOARD_ITEM) -> None:
		# Assumes that target item is at same location/angle/side as source item
		def clamp_angle(angle: float):
			while angle > 180: angle -= 360
			while angle < -180: angle += 360
			return angle
		source_reference_placement = self.source_reference_placement
		target_reference_placement = self.target_reference_placement
		rotation = clamp_angle(target_reference_placement.angle - source_reference_placement.angle)
		flip = target_reference_placement.flipped != source_reference_placement.flipped
		target_item.Move(target_reference_placement.position - source_reference_placement.position)
		if flip:
			target_item.Flip(target_reference_placement.position, False)
			source_angle = source_reference_placement.angle
			flipped_angle = copysign(180 - abs(source_angle), source_angle)
			rotation = 180 - flipped_angle - target_reference_placement.angle
		rotation += target_reference_placement.angle - source_reference_placement.angle
		target_item.Rotate(target_reference_placement.position, int(rotation * RotationUnits.PER_DEGREE))


@final
class CloneTransactionTransferFootprintPlacementOperator(CloneTransactionOperator):

	def __init__(self, source_reference_placement: Placement, target_reference_placement: Placement, source_footprint: pcbnew.FOOTPRINT, target_footprint: pcbnew.FOOTPRINT):
		super().__init__(source_reference_placement, target_reference_placement)
		self.original_placement: Placement = Placement.of(target_footprint)
		self.target_footprint: pcbnew.FOOTPRINT = target_footprint
		self.current_placement: Placement = self.original_placement
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

	def __init__(self, source_reference_placement: Placement, target_reference_placement: Placement, source_item: pcbnew.BOARD_ITEM):
		super().__init__(source_reference_placement, target_reference_placement)
		self.source_item: pcbnew.BOARD_ITEM = source_item
		self.target_item: pcbnew.BOARD_ITEM | None = None

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
