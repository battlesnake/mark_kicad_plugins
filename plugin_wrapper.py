from typing import final, Optional, cast
from abc import ABC, abstractmethod
from dataclasses import asdict
import logging
from logging import Logger
import sys
import os
import os.path

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .plugin_metadata import PluginMetadata


class PluginWrapper(pcbnew.ActionPlugin, ABC):

	def __init__(self, test_board: Optional[pcbnew.BOARD] = None):
		super().__init__()
		self.test_board = test_board
	
	@abstractmethod
	def create_plugin(self, logger: Logger, board: pcbnew.BOARD) -> Plugin:
		pass

	@staticmethod
	@abstractmethod
	def get_metadata() -> PluginMetadata:
		pass

	@final
	def defaults(self) -> None:
		metadata = self.get_metadata()
		self.name = metadata.name
		self.description = metadata.description
		self.category = metadata.category
		self.icon_file_name = metadata.icon
		self.dark_icon_file_name = metadata.icon
		self.show_toolbar_button = metadata.show_toolbar_button

	@final
	def init_log_sink(self, path: str):
		for handler in logging.root.handlers[:]:
			logging.root.removeHandler(handler)
		logging.basicConfig(level=logging.DEBUG,
			filename=os.path.join(path, f"plugin-{self.__class__.__name__}.log"),
			filemode="w",
			format="%(asctime)s %(name)s %(lineno)d:%(message)s",
			datefmt="%Y-%m-%d %H:%M:%S"
		)

	@final
	def Run(self) -> None:

		logger = logging.getLogger(self.__class__.__name__)

		try:

			logger.info("Getting board")
			board = cast(Optional[pcbnew.BOARD], pcbnew.GetBoard()) if self.test_board is None else self.test_board
			if board is None:
				raise Exception("Failed to determine board")
			filename = os.path.abspath(str(board.GetFileName()))

			logger.info("Entering project directory")
			os.chdir(os.path.dirname(filename))

			logger.info("Initialising log sinks")
			self.init_log_sink(os.path.dirname(filename))

			logger.info("Platform: %s", sys.platform)
			logger.info("Python version: %s", sys.version)
			logger.info("KiCad build version: %s", pcbnew.GetBuildVersion())

			logger.info("Filename: %s", filename)
			logger.info("Metadata: %s", asdict(self.get_metadata()))

			logger.info("Instantiating plugin")
			plugin = self.create_plugin(logger, board)
			logger.info("Plugin: %s", plugin.__class__.__name__)

			logger.info("Executing plugin")
			plugin.execute()

			logger.info("Refreshing pcbnew")
			pcbnew.Refresh()

			logger.info("Done")

		except Exception as error:

			logger.exception(error)

			raise

		finally:

			logger.info("End")
