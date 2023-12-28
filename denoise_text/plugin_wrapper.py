from typing import final
from logging import Logger

import pcbnew  # pyright: ignore

from ..plugin import Plugin
from ..plugin import PluginWrapper
from ..plugin import PluginMetadata

from .plugin import TextPlugin


@final
class TextPluginWrapper(PluginWrapper):

	def create_plugin(self, logger: Logger, board: pcbnew.BOARD) -> Plugin:
		return TextPlugin(logger, board)

	@staticmethod
	def get_metadata():
		return PluginMetadata(
			name="Text to dedicated layers",
			description="Assign references and values to dedicated layers (which must be created/named beforehand: Refs, Values)",
			icon="footprint1.svg",
		)
