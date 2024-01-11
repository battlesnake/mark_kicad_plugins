from abc import ABC, abstractmethod
from logging import Logger

import pcbnew  # pyright: ignore


class Plugin(ABC):

	def __init__(self, logger: Logger, board: pcbnew.BOARD):
		self.logger = logger.getChild(type(self).__name__)
		self.board = board

	@abstractmethod
	def execute(self) -> None:
		pass
