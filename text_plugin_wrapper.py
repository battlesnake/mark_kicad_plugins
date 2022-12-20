from typing import final
from logging import Logger

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .plugin_wrapper import PluginWrapper
from .plugin_metadata import PluginMetadata
from .text_plugin import TextPlugin


@final
class TextPluginWrapper(PluginWrapper):

	def create_plugin(self, logger: Logger, board: pcbnew.BOARD) -> Plugin:
		return TextPlugin(logger, board)

	@staticmethod
	def get_metadata():
		return PluginMetadata(
			name="Text to dedicated layers",
			description="Assign references and values to dedicated layers (which must be created beforehand: Refs, Values)",
			icon="footprint1.svg",
		)
