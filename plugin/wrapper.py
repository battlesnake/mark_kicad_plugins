from typing import final, Optional
from abc import ABC, abstractmethod
from dataclasses import asdict
import logging
from logging import Logger
import sys
import os
import os.path

import pcbnew  # pyright: ignore
from pcbnew import BOARD, ActionPlugin

from .plugin import Plugin
from .metadata import PluginMetadata

from ..utils.error_handler import error_handler, LoggedException
from ..utils.logging_config import LoggingConfig

from ..ui.spinner import spin_while
from ..ui.bored_user_entertainer import BoredUserEntertainer


class PluginWrapper(ActionPlugin, ABC):

	def __init__(self, test_board: Optional[BOARD] = None):
		super().__init__()
		self.test_board = test_board

	@abstractmethod
	def create_plugin(self, logger: Logger, board: BOARD) -> Plugin:
		pass

	@staticmethod
	@abstractmethod
	def get_metadata() -> PluginMetadata:
		pass

	@final
	def defaults(self) -> None:
		def icon_path(name: str) -> str:
			return os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon", name)
		metadata = self.get_metadata()
		self.name = metadata.name
		self.description = metadata.description
		self.category = metadata.category
		self.icon_file_name = icon_path(metadata.icon)
		self.dark_icon_file_name = icon_path(metadata.icon)
		self.show_toolbar_button = metadata.show_toolbar_button

	@final
	def init_log_sink(self):
		logger = logging.getLogger(type(self).__name__)
		logger.setLevel(logging.DEBUG)
		handler = logging.FileHandler(
			filename=os.path.abspath(f"mark-plugin-{type(self).__name__}.log"),
			mode="w",
			encoding="utf-8",
		)
		formatter = logging.Formatter(
			fmt=LoggingConfig.format,
			datefmt=LoggingConfig.datefmt,
		)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.setLevel(LoggingConfig.level)
		return logger

	@final
	def Run(self) -> None:
		board = pcbnew.GetBoard() if self.test_board is None else self.test_board
		if board is None:
			raise Exception("Failed to determine board")
		filename = os.path.abspath(str(board.GetFileName()))
		os.chdir(os.path.dirname(filename))
		logger = self.init_log_sink()
		try:
			self.execute(logger, board, filename)
		except LoggedException:
			pass

	@error_handler
	@spin_while
	def execute(self, logger: Logger, board: BOARD, filename: str) -> None:
		BoredUserEntertainer.message("Inspecting environment...")
		logger.info("Platform: %s", sys.platform)
		logger.info("Python version: %s", sys.version)
		logger.info("KiCad build version: %s", pcbnew.GetBuildVersion())

		logger.info("Filename: %s", filename)
		logger.info("Metadata: %s", asdict(self.get_metadata()))

		BoredUserEntertainer.message("Starting plugin...")
		logger.info("Instantiating plugin")
		plugin = self.create_plugin(logger, board)
		logger.info("Plugin: %s", plugin.__class__.__name__)

		BoredUserEntertainer.message("Executing plugin...")
		logger.info("Executing plugin")
		plugin.execute()

		logger.info("Done")
