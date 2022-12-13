from typing import Generic, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger

import pcbnew  # pyright: ignore


ConfigurationType = TypeVar("ConfigurationType")


@dataclass
class PluginInitParams(Generic[ConfigurationType]):
	board: pcbnew.BOARD
	configuration: ConfigurationType
	logger: Logger


class Plugin(ABC, Generic[ConfigurationType]):

	def __init__(self, init_params: PluginInitParams[ConfigurationType]):
		self.board = init_params.board
		self.configuration = init_params.configuration
		self.logger = init_params.logger

	@abstractmethod
	def execute(self) -> None:
		pass
