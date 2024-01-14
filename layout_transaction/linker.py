from typing import Dict, List, cast
from uuid import UUID

from ..utils.json_types import JsonObject, JsonArray

from .compiler import CompiledCommand, CompiledScript

from .action import (
	Action,
	ActionTarget,
	DeleteAction,
	DisplaceAction,
	FlipAction,
	MoveToLayerAction,
	RotateAction,
	SetOrientationAction,
	SetPositionAction,
	CloneAction,
	GroupAction,
	UngroupAction,
)

from pcbnew import (
	BOARD,
	KIID,
	VECTOR2I,
	EDA_ANGLE,
	DEGREE_T,
)


class ScriptLinker():
	command_action_map: Dict[UUID, Action]

	def __init__(self, board: BOARD):
		self.command_action_map = {}
		self.board = board

	def get_target(self, target: JsonObject) -> ActionTarget:
		if target["type"] == "board_item":
			kiid = KIID(cast(str, target["id"]))
			item = self.board.GetItem(kiid)
			return item
		if target["type"] == "output":
			cid = self.command_action_map[UUID(cast(str, target["id"]))]
			return cid
		else:
			raise TypeError()

	@staticmethod
	def link(board: BOARD, script: CompiledScript):
		return ScriptLinker(board).translate_script(script)

	def translate_script(self, script: CompiledScript):
		result: List[Action] = []
		for command in script:
			command_id = UUID(cast(str, command["command_id"]))
			action = self.translate_command(command)
			self.command_action_map[command_id] = action
			result.append(action)
		return result

	def translate_command(self, command: CompiledCommand) -> Action:
		"""
		Use JSONs instead of Command objects, as we intend to move the clever
		parts of the plugin to a web-service sometime.
		Perhaps see if pydantic can be some help with this.
		"""
		command_type = cast(str, command["command_type"])
		target = self.get_target(cast(JsonObject, command["target"]))
		if command_type == "delete_command":
			return DeleteAction(target=target)
		elif command_type == "set_position_command":
			return SetPositionAction(
				target=target,
				position=VECTOR2I(**cast(JsonObject, command["position"])),
			)
		elif command_type == "set_orientation_command":
			return SetOrientationAction(
				target=target,
				orientation=EDA_ANGLE(cast(float, command["orientation"]), DEGREE_T),
			)
		elif command_type == "displace_command":
			return DisplaceAction(
				target=target,
				displacement=VECTOR2I(**cast(JsonObject, command["displacement"])),
			)
		elif command_type == "rotate_command":
			return RotateAction(
				target=target,
				rotation=EDA_ANGLE(cast(float, command["rotation"]), DEGREE_T),
			)
		elif command_type == "flip_command":
			return FlipAction(
				target=target,
			)
		elif command_type == "move_to_layer_command":
			return MoveToLayerAction(
				target=target,
				layer=cast(int, command["layer"]),
			)
		elif command_type == "clone_command":
			return CloneAction(
				target=target,
			)
		elif command_type == "group_command":
			return GroupAction(
				target=target,
				extra_items=[
					self.get_target(cast(JsonObject, item))
					for item in cast(JsonArray, command["extra_items"])
				]
			)
		elif command_type == "ungroup_command":
			return UngroupAction(
				target=target,
			)
		else:
			raise NotImplementedError()
