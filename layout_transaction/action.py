""" Actions implement commands """
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Sequence, Type, TypeVar, Union

from pcbnew import EDA_ITEM, VECTOR2I, EDA_ANGLE, BOARD, BOARD_ITEM, FOOTPRINT


# Board item / action result / "pcbnew entity for internal use in executor"
ActionTarget = Union[EDA_ITEM, "Action"]


EDA_ITEM_TYPE = TypeVar("EDA_ITEM_TYPE", bound=EDA_ITEM)


@dataclass(eq=False, frozen=False)
class Action(ABC):
	target: ActionTarget
	result: Optional[EDA_ITEM] = field(default=None, init=False)

	def resolve_target(
		self,
		expected_type: Type[EDA_ITEM_TYPE],
		target: Optional[ActionTarget] = None
	) -> EDA_ITEM_TYPE:
		if target is None:
			target = self.target
		elif isinstance(target, Action):
			target = target.result
		if isinstance(target, expected_type):
			return target
		else:
			raise TypeError()

	@abstractmethod
	def execute(self, board: BOARD) -> "Action":
		...


@dataclass
class DeleteAction(Action):
	...

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		board.Delete(target)
		return InsertAction(
			target=target,
		)


@dataclass
class SetPositionAction(Action):
	position: VECTOR2I

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		inverse = SetPositionAction(
			target=target,
			position=target.GetPosition()
		)
		target.SetPosition(self.position)
		return inverse


@dataclass
class SetOrientationAction(Action):
	orientation: EDA_ANGLE

	def execute(self, board: BOARD):
		target = self.resolve_target(FOOTPRINT)
		inverse = SetOrientationAction(
			target=target,
			orientation=target.GetOrientation()
		)
		target.SetOrientation(self.orientation)
		return inverse


@dataclass
class DisplaceAction(Action):
	displacement: VECTOR2I

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		inverse = SetPositionAction(
			target=target,
			position=target.GetPosition()
		)
		target.SetPosition(target.GetPosition() + self.displacement)
		return inverse


@dataclass
class RotateAction(Action):
	rotation: EDA_ANGLE

	def execute(self, board: BOARD):
		target = self.resolve_target(FOOTPRINT)
		inverse = SetOrientationAction(
			target=target,
			orientation=target.GetOrientation()
		)
		target.SetOrientation(target.GetOrientation() + self.rotation)
		return inverse


@dataclass
class FlipAction(Action):
	...

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		inverse = FlipAction(
			target=target,
		)
		target.Flip(target.GetPosition(), True)
		return inverse


@dataclass
class MoveToLayerAction(Action):
	layer: int

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		inverse = MoveToLayerAction(
			target=target,
			layer=target.GetLayer(),
		)
		target.SetLayer(self.layer)
		return inverse


@dataclass
class CloneAction(Action):
	...

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		result = target.Duplicate()
		inverse = DeleteAction(
			target=result,
		)
		self.result = result
		return inverse


@dataclass
class InsertAction(Action):
	...

	def execute(self, board: BOARD):
		target = self.resolve_target(BOARD_ITEM)
		board.Add(target)
		inverse = DeleteAction(
			target=target,
		)
		self.result = target
		return inverse


@dataclass
class GroupAction(Action):
	extra_items: Sequence[ActionTarget]  # "target" is added to this if not included explicitly

	def execute(self, board: BOARD):
		raise NotImplementedError()


@dataclass
class UngroupAction(Action):
	...

	def execute(self, board: BOARD):
		raise NotImplementedError()
