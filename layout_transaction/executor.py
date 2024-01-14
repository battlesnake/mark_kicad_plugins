from typing import List, Optional, Sequence, Tuple
import logging

from pcbnew import BOARD

from .action import Action
from .linker import ScriptLinker
from .compiler import CompiledScript
from .transaction import TransactionObserver, TransactionState, TransactionProgress


logger = logging.getLogger(__name__)


VALID_STATE_TRANSITIONS: Sequence[Tuple[TransactionState, TransactionState]] = [
	(TransactionState.NOT_COMMITTED, TransactionState.COMMITTING),
	(TransactionState.COMMITTING, TransactionState.COMMITTED),
	(TransactionState.COMMITTING, TransactionState.COMMIT_FAILED),
	(TransactionState.COMMITTED, TransactionState.ROLLING_BACK),
	(TransactionState.COMMIT_FAILED, TransactionState.ROLLING_BACK),
	(TransactionState.ROLLING_BACK, TransactionState.ROLLBACK_FAILED),
	(TransactionState.ROLLING_BACK, TransactionState.NOT_COMMITTED),
]


class Executor():
	board: BOARD
	state: TransactionState
	transaction_observer: TransactionObserver
	commit_script: List[Action]
	rollback_script: List[Action]

	def __init__(self, board: BOARD, script: CompiledScript, transaction_observer: TransactionObserver):
		self.board = board
		self.state = TransactionState.NOT_COMMITTED
		self.transaction_observer = transaction_observer
		self.commit_script = ScriptLinker.link(board, script)

	def set_state(self, next_state: TransactionState):
		prev_state = self.state
		if (prev_state, next_state) not in VALID_STATE_TRANSITIONS:
			raise ValueError("Invalid state transition: %s -> %s", prev_state, next)
		logger.info("State transition: %s -> %s", prev_state.name, next_state.name)
		self.transaction_observer.state_changed(next_state)

	def set_progress(self, done: int, total: int):
		logger.info("Progress: %d/%d", done, total)
		self.transaction_observer.progress_changed(TransactionProgress(done, total))

	def execute_script(self, actions: Sequence[Action], reverse_actions: Optional[List[Action]]):
		action_count = len(actions)
		self.set_progress(0, action_count)
		for index, action in enumerate(actions):
			try:
				# Apply action
				logger.info("Executing action %s", action.__class__.__name__)
				reverse = action.execute(self.board)
				# Create reverse action
				if reverse_actions is not None:
					reverse_actions.append(reverse)
			except Exception as exc:
				logger.exception("Failed to execute action %s", action.__class__.__name__, exc_info=exc)
				raise
			self.set_progress(index + 1, action_count)

	def commit(self):
		self.rollback_script = []
		self.set_state(TransactionState.COMMITTING)
		try:
			self.execute_script(self.commit_script, self.rollback_script)
		except Exception as exc:
			logger.exception("Failed to commit transaction", exc_info=exc)
			self.set_state(TransactionState.COMMIT_FAILED)
			raise exc
		self.set_state(TransactionState.COMMITTED)

	def rollback(self):
		self.set_state(TransactionState.ROLLING_BACK)
		try:
			self.execute_script(list(reversed(self.rollback_script)), None)
		except Exception as exc:
			logger.exception("Failed to rollback transaction", exc_info=exc)
			self.set_state(TransactionState.ROLLBACK_FAILED)
			raise exc
		self.set_state(TransactionState.NOT_COMMITTED)
		self.rollback_script = []
