from typing import final
from logging import Logger

import pcbnew  # pyright: ignore

from plugin.plugin import Plugin
from plugin.plugin_wrapper import PluginWrapper
from plugin.plugin_metadata import PluginMetadata

from denoise_text.text_plugin import TextPlugin


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
