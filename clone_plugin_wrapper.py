from typing import final
from logging import Logger

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .plugin_wrapper import PluginWrapper
from .plugin_metadata import PluginMetadata
from .clone_plugin import ClonePlugin


@final
class ClonePluginWrapper(PluginWrapper):

	def create_plugin(self, logger: Logger, board: pcbnew.BOARD) -> Plugin:
		return ClonePlugin(logger, board)

	@staticmethod
	def get_metadata():
		return PluginMetadata(
			name="Clone subcircuit across sheet instances",
			description="Clones the selected subcircuit (including footprint placement, tracks, vias, drawings, zones) across to other instances of the sheet containing it",
		)


ClonePluginWrapper().register()
