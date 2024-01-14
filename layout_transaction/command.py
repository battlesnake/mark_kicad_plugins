""" Defines commands that can be executed by the executor, commands are implemented by Actions """
from dataclasses import asdict, dataclass, field
from typing import Sequence, Union
from uuid import UUID, uuid4

from ..kicad_v8_model import Vector2, HasId, Angle, Layer
from ..utils.json_types import JsonObject
from ..utils.case_converter import CaseConverter


UniqueBoardItem = HasId


# Board item / action result / "pcbnew entity for internal use in executor"
CommandTarget = Union[UniqueBoardItem, "CloneCommand"]


@dataclass(eq=False, frozen=False)
class Command():
	target: CommandTarget
	command_id: UUID = field(default_factory=uuid4, init=False)
	command_type: str = field(init=False)

	def __post_init__(self):
		self.command_type = CaseConverter.pascal_to_snake(self.__class__.__name__)

	@staticmethod
	def serialise_command_target(target: CommandTarget) -> JsonObject:
		if isinstance(target, UniqueBoardItem):
			return {
				"type": "board_item",
				"id": str(target.id),
			}
		elif isinstance(target, Command):
			return {
				"type": "output",
				"id": str(target.command_id),
			}
		else:
			raise TypeError()

	def serialise(self) -> JsonObject:
		return {
			"id": str(self.command_id),
			"type": self.command_type,
			"target": Command.serialise_command_target(self.target),
		}


@dataclass
class DeleteCommand(Command):
	...


@dataclass
class SetPositionCommand(Command):
	position: Vector2

	def serialise(self) -> JsonObject:
		dto = super().serialise()
		dto.update({
			"position": asdict(self.position),
		})
		return dto


@dataclass
class SetOrientationCommand(Command):
	orientation: Angle

	def serialise(self) -> JsonObject:
		dto = super().serialise()
		dto.update({
			"orientation": self.orientation.degrees,
		})
		return dto


@dataclass
class DisplaceCommand(Command):
	displacement: Vector2

	def serialise(self) -> JsonObject:
		dto = super().serialise()
		dto.update({
			"displacement": asdict(self.displacement),
		})
		return dto


@dataclass
class RotateCommand(Command):
	rotation: Angle

	def serialise(self) -> JsonObject:
		dto = super().serialise()
		dto.update({
			"rotation": self.rotation.degrees,
		})
		return dto


@dataclass
class FlipCommand(Command):
	...


@dataclass
class MoveToLayerCommand(Command):
	layer: Layer

	def serialise(self) -> JsonObject:
		dto = super().serialise()
		dto.update({
			"layer": self.layer.type.index,
		})
		return dto


@dataclass
class CloneCommand(Command):
	...


@dataclass
class GroupCommand(Command):
	extra_items: Sequence[CommandTarget]  # "target" is added to this if not included explicitly

	def serialise(self) -> JsonObject:
		dto = super().serialise()
		dto.update({
			"extra_items": [
				Command.serialise_command_target(item)
				for item in self.extra_items
			],
		})
		return dto


@dataclass
class UngroupCommand(Command):
	...
