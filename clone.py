from dataclasses import dataclass
import functools

import pcbnew  # pyright: ignore

from .plugin import Plugin


@dataclass
class ClonePluginConfiguration():

	pass


class ClonePlugin(Plugin):

	def execute(self) -> None:
		pass
