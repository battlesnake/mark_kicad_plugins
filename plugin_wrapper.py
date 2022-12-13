from typing import Generic, final
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import logging

import pcbnew  # pyright: ignore

from .plugin import Plugin, PluginInitParams, ConfigurationType
from .plugin_metadata import PluginMetadata


class PluginWrapper(pcbnew.ActionPlugin, Generic[ConfigurationType]):

	@abstractmethod
	def create_configuration(self) -> ConfigurationType:
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

	@final
	def Run(self) -> None:
		logger = logging.Logger("mark_plugin_wrapper")

		try:

			logger.info("Getting board")
			board = pcbnew.GetBoard()

			logger.info("Creating configuration")
			configuration = self.create_configuration()

			logger.info("Filename: %s", board.GetFileName())
			logger.info("Metadata: %s", asdict(self.get_metadata()))
			logger.info("Configuration: %s", asdict(configuration))

			logger.info("Creating plugin instance")
			init_params = PluginInitParams(board=board, configuration=configuration, logger=logger)
			plugin = self.create_plugin(init_params)

			logger.info("Plugin: %s", plugin.__class__.__name__)

			logger.info("Executing plugin")
			plugin.execute()

			logger.info("Refreshing pcbnew")
			pcbnew.Refresh()

			logger.info("Done")

		except Exception as error:

			logger.exception(error)

		finally:

			logger.info("End")
