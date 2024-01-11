""" Defines commands that can be executed by the executor, commands are implemented by Actions """
from dataclasses import dataclass, field
from typing import Sequence, Union
from uuid import UUID, uuid4
from kicad_v8_model.angle import Angle

from kicad_v8_model.vector2 import Vector2

from ..kicad_v8_model import Layer
from ..kicad_v8_model import HasId


UniqueBoardItem = HasId


# Board item / action result / "pcbnew entity for internal use in executor"
CommandTarget = Union[UniqueBoardItem, "CloneCommand"]


@dataclass(eq=False, frozen=False)
class Command():
	target: CommandTarget
	command_id: UUID = field(default_factory=uuid4)


@dataclass
class DeleteCommand(Command):
	...


@dataclass
class SetPositionCommand(Command):
	position: Vector2


@dataclass
class SetOrientationCommand(Command):
	orientation: Angle


@dataclass
class DisplaceCommand(Command):
	displacement: Vector2


@dataclass
class RotateCommand(Command):
	rotation: Angle


@dataclass
class FlipCommand(Command):
	...


@dataclass
class MoveToLayerCommand(Command):
	layer: Layer


@dataclass
class CloneCommand(Command):
	...


@dataclass
class GroupCommand(Command):
	extra_items: Sequence[CommandTarget]  # "target" is added to this if not included


@dataclass
class UngroupCommand(Command):
	group: CommandTarget
