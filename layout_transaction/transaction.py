from dataclasses import field
from enum import Enum
from typing import Sequence

from layout_transaction.command import Command


class TransactionState(Enum):
	"""
	Terminals:
		RF
	Transitions:
		NC -> C
		C -> NC
		NC -> CF
		CF -> NC
		C -> RF
	"""
	NOT_COMMITTED = "not committed"
	COMMITTED = "committed"
	COMMIT_FAILED = "commit failed"
	ROLLBACK_FAILED = "rollback failed"



class Transaction():
	script: Sequence[Command]
	state: TransactionState = field(default=TransactionState.NOT_COMMITTED, init=False)
