from typing import Sequence

from ..utils.json_types import JsonObject
from .command import Command


Script = Sequence[Command]
CompiledCommand = JsonObject
CompiledScript = Sequence[CompiledCommand]


class ScriptCompiler():

	def __init__(self):
		...

	def encode_commands(self, script: Script) -> CompiledScript:
		return [
			command.serialise()
			for command in script
		]

	@staticmethod
	def compile(script: Script):
		return ScriptCompiler().encode_commands(script)
