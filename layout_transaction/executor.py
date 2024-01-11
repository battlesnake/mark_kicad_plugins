from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence, cast
import logging
from uuid import UUID

from .transaction import Transaction


logger = logging.getLogger(__name__)


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


class Executor():
	transaction: Transaction
	board: BOARD
	compiler: ScriptCompiler
	on_progress: Callable[[int, int], None]
	state: TransactionState

	def __init__(self, transaction: Transaction, board: BOARD):
		self.transaction = transaction
		self.board = board
		self.on_progress = lambda done, total: None
		self.state = TransactionState.NOT_COMMITTED
		self.element_map = {}

	def get_target(self, target: CommandTarget) -> ActionTarget:
		if isinstance(target, EntityPathComponent):
			kiid = KIID(str(target))
			item = self.board.GetItem(kiid)
			return item
		if isinstance(target, UniqueBoardItem):
			entity_id = target.id
			kiid = KIID(str(entity_id))
			item = self.board.GetItem(kiid)
			return item
		elif isinstance(target, Command):
			item = self.element_map[target.command_id]
			return item
		else:
			raise TypeError()

	def execute_script(self, actions: Sequence[Action], reverse_actions: Optional[List[Action]]):
		action_count = len(actions)
		self.on_progress(0, action_count)
		for index, action in enumerate(actions):
			try:
				# Apply action
				reverse = self.execute_command(action)
				# Create reverse action
				if reverse_actions is not None:
					reverse_actions.append(reverse)
			except Exception as exc:
				logger.exception("Failed to execute action %s", action.__class__.__name__, exc_info=exc)
				raise
			self.on_progress(index + 1, action_count)

	def commit(self):
		if self.state != TransactionState.NOT_COMMITTED:
			raise RuntimeError("Invalid state transition for transaction", self.state)
		self.element_map = {}
		self.reverse_actions = []
		try:
			self.execute_script(self.transaction.actions, self.reverse_actions)
		except Exception as exc:
			logger.exception("Failed to commit transaction", exc_info=exc)
			self.state = TransactionState.COMMIT_FAILED
			raise exc
		self.state = TransactionState.COMMITTED

	def rollback(self):
		if self.state not in (TransactionState.COMMIT_FAILED, TransactionState.COMMITTED):
			raise RuntimeError("Invalid state transition for transaction", self.state)
		try:
			self.execute_script(list(reversed(self.reverse_actions)), None)
		except Exception as exc:
			logger.exception("Failed to rollback transaction", exc_info=exc)
			self.state = TransactionState.ROLLBACK_FAILED
			raise exc
		self.state = TransactionState.NOT_COMMITTED
		self.reverse_actions = []
		self.element_map = {}

	def compile(self, command: Command) -> Action:
		...

	def execute_command(self, action: Action) -> Action:
		board = self.board
		if isinstance(action, InsertAction):
			""" Hacky """
			item = cast(BOARD_ITEM, action.target)
			board.Add(item)
			self.element_map[id(action)] = item
			return DeleteAction(target=action)
		item = self.get_target(action.target)
		# Ideally we'd use visitor pattern for executing action, and have
		# proper type-checks and casts done per action in some declarative way.
		# But for python reasons we'll do it this way instead.
		board_item = cast(BOARD_ITEM, item)
		footprint = cast(FOOTPRINT, item)
		if isinstance(action, DeleteAction):
			board.Delete(board_item)
			self.element_map[id(action)] = board_item
			return InsertAction(target=action)
		elif isinstance(action, SetPositionAction):
			position = Vector2(x=item.GetPosition().x, y=item.GetPosition().y)
			item.SetPosition(VECTOR2I(int(action.position.x), int(action.position.y)))
			return SetPositionAction(target=action.target, position=position)
		elif isinstance(action, SetOrientationAction):
			orientation = Angle(footprint.GetOrientation().AsDegrees(), AngleUnit.DEGREES)
			footprint.SetOrientation(EDA_ANGLE(action.orientation.degrees * 10, TENTHS_OF_A_DEGREE_T))
			return SetOrientationAction(target=action.target, orientation=orientation)
		elif isinstance(action, DisplaceAction):
			position = Vector2(x=item.GetPosition().x, y=item.GetPosition().y)
			board_item.Move(VECTOR2I(int(action.displacement.x), int(action.displacement.y)))
			return SetPositionAction(target=action.target, position=position)
		elif isinstance(action, RotateAction):
			orientation = Angle(footprint.GetOrientation().AsDegrees(), AngleUnit.DEGREES)
			board_item.Rotate(item.GetPosition(), EDA_ANGLE(action.rotation.degrees * 10, TENTHS_OF_A_DEGREE_T))
			return SetOrientationAction(target=action.target, orientation=orientation)
		elif isinstance(action, FlipAction):
			board_item.Flip(item.GetPosition(), True)
			return FlipAction(target=action.target)
		elif isinstance(action, MoveToLayerAction):
			layer = board_item.GetLayer()
			board_item.SetLayer(...)
			return MoveToLayerAction(target=action.target, layer=layer)
		elif isinstance(action, CloneAction):
			copy = item.Clone()
			self.element_map[id(action)] = copy
			return DeleteAction(target=action)
		elif isinstance(action, InsertAction):
			""" Handled above """
			raise Exception("Should not get here")
		elif isinstance(action, GroupAction):
			""" TODO """
			return UngroupAction(...)
		elif isinstance(action, UngroupAction):
			""" TODO """
			return GroupAction(...)
		else:
			raise NotImplementedError()
