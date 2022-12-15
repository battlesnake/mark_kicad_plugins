from typing import Generic, final
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import logging
import sys
import os
import os.path

import pcbnew  # pyright: ignore

from .configuration import ConfigurationType, ConfigurationInitParams
from .plugin import Plugin, PluginInitParams
from .plugin_metadata import PluginMetadata


class PluginWrapper(pcbnew.ActionPlugin, Generic[ConfigurationType]):

	@abstractmethod
	def create_configuration(self, init_params: ConfigurationInitParams) -> ConfigurationType:
		pass

	@abstractmethod
	def create_plugin(self, init_params: PluginInitParams) -> Plugin[ConfigurationType]:
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
		self.icon = metadata.icon
		self.show_toolbar_button = metadata.show_toolbar_button

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
			board = pcbnew.GetBoard()
			filename = os.path.abspath(board.GetFileName())

			logger.info("Entering project directory")
			os.chdir(os.path.dirname(filename))

			logger.info("Initialising log sinks")
			self.init_log_sink(os.path.dirname(filename))

			logger.info("Platform: %s", sys.platform)
			logger.info("Python version: %s", sys.version)
			logger.info("KiCad build version: %s", pcbnew.GetBuildVersion())

			logger.info("Filename: %s", filename)
			logger.info("Metadata: %s", asdict(self.get_metadata()))

			logger.info("Creating configuration")
			configuration = self.create_configuration(ConfigurationInitParams(logger=logger))

			logger.info("Configuration: %s", asdict(configuration))

			logger.info("Creating plugin instance")
			plugin = self.create_plugin(PluginInitParams(logger=logger, board=board, configuration=configuration))

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
