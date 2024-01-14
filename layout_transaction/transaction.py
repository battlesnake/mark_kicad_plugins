from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class TransactionState(Enum):
	NOT_COMMITTED = "not committed"
	COMMITTING = "committing"
	COMMITTED = "committed"
	COMMIT_FAILED = "commit failed"
	ROLLING_BACK = "rolling back"
	ROLLBACK_FAILED = "rollback failed"


@dataclass
class TransactionProgress():
	done: int
	total: int
	message: str = field(default="")


class TransactionObserver(ABC):

	@abstractmethod
	def state_changed(self, state: TransactionState):
		...

	@abstractmethod
	def progress_changed(self, progress: TransactionProgress):
		...
