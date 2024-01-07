from typing import final
from logging import Logger

from pcbnew import BOARD, Refresh as RefreshView

from ..utils.error_handler import error_handler

from .context import CloneContext
from .settings import CloneSettings
from .service import CloneService


@final
class CloneSettingsController():

	def __init__(
		self,
		logger: Logger,
		board: BOARD,
		context: CloneContext,
	):
		self.logger = logger.getChild(type(self).__name__)
		self.board = board
		self.context = context
		self.is_preview = False
		self.service = CloneService.get()

	def revert(self) -> None:
		self.service.revert_clone()
		self.is_preview = False

	def clone(self, settings: CloneSettings) -> None:
		self.service.clone_subcircuits(
			self.logger,
			self.context,
			settings,
		)

	def refresh_view(self):
		RefreshView()

	@error_handler
	def has_preview(self) -> bool:
		return self.is_preview

	@error_handler
	def apply_preview(self, settings: CloneSettings) -> None:
		self.logger.info("Command: Apply preview")
		self.revert()
		self.clone(settings)
		self.is_preview = True
		self.refresh_view()

	@error_handler
	def clear_preview(self) -> None:
		self.logger.info("Command: Clear preview")
		if self.is_preview:
			self.revert()
		self.refresh_view()

	@error_handler
	def can_undo(self) -> bool:
		return self.service.can_revert()

	@error_handler
	def apply(self, settings: CloneSettings) -> None:
		self.logger.info("Command: Apply")
		self.revert()
		self.clone(settings)
		self.refresh_view()

	@error_handler
	def undo(self) -> None:
		self.logger.info("Command: Undo")
		self.revert()
		self.is_preview = False
		self.refresh_view()
