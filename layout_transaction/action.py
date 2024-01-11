""" Actions implement commands """
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Sequence, Union
from uuid import UUID, uuid4

from pcbnew import EDA_ITEM, VECTOR2I, EDA_ANGLE_T
from pcbnew.board import BOARD


# Board item / action result / "pcbnew entity for internal use in executor"
ActionTarget = Union[EDA_ITEM, "Action"]


@dataclass(eq=False, frozen=False)
class Action(ABC):
	target: ActionTarget
	action_id: UUID = field(default_factory=uuid4, init=False)
	result: Optional[ActionTarget] = field(default=None, init=False)

	@abstractmethod
	def execute(self, board: BOARD):
		...

	@abstractmethod
	def create_inverse(self) -> "Action":
		...


@dataclass
class DeleteAction(Action):
	...


@dataclass
class SetPositionAction(Action):
	position: VECTOR2I


@dataclass
class SetOrientationAction(Action):
	orientation: EDA_ANGLE_T


@dataclass
class DisplaceAction(Action):
	displacement: VECTOR2I


@dataclass
class RotateAction(Action):
	rotation: EDA_ANGLE_T


@dataclass
class FlipAction(Action):
	...


@dataclass
class MoveToLayerAction(Action):
	layer: TODO_LAYER_ID_OR_REF


@dataclass
class CloneAction(Action):
	...


@dataclass
class InsertAction(Action):
	...


@dataclass
class GroupAction(Action):
	extra_items: Sequence[ActionTarget]  # "target" is added to this if not included


@dataclass
class UngroupAction(Action):
	group: ActionTarget
