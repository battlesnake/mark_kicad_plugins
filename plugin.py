from typing import Generic, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger

import pcbnew  # pyright: ignore

from .configuration import ConfigurationType, ConfigurationInitParams


@dataclass
class PluginInitParams(Generic[ConfigurationType]):
	logger: Logger
	board: pcbnew.BOARD
	configuration: ConfigurationType


class Plugin(ABC, Generic[ConfigurationType]):

	def __init__(self, init_params: PluginInitParams[ConfigurationType]):
		self.board = init_params.board
		self.configuration = init_params.configuration
		self.logger = init_params.logger.getChild(self.__class__.__name__)

	@abstractmethod
	def execute(self) -> None:
		pass
