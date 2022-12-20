from typing import TypeVar, Optional
from typing_extensions import overload

import pcbnew  # pyright: ignore

from .placement import Placement
from .clone_transaction import CloneTransaction, CloneTransactionDuplicateAndTransferPlacementPlacementOperator, CloneTransactionTransferFootprintPlacementOperator


ItemType = TypeVar("ItemType", bound=pcbnew.BOARD_ITEM)


class CloneTransactionBuilder():

	def __init__(self):
		self.transaction = CloneTransaction()

	@overload
	def add_item(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: pcbnew.BOARD_ITEM,
	) -> None: ...

	@overload
	def add_item(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: pcbnew.FOOTPRINT,
		target_item: pcbnew.FOOTPRINT,
	) -> None: ...

	def add_item(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: ItemType,
		target_item: Optional[ItemType] = None,
	) -> None:
		if target_item is None and not isinstance(source_item, pcbnew.FOOTPRINT):
			self.transaction.add(CloneTransactionDuplicateAndTransferPlacementPlacementOperator(
				source_reference,
				target_reference,
				source_item,
			))
		elif isinstance(target_item, pcbnew.FOOTPRINT) and isinstance(source_item, pcbnew.FOOTPRINT):
			self.transaction.add(CloneTransactionTransferFootprintPlacementOperator(
				source_reference,
				target_reference,
				source_item,
				target_item,
			))
		else:
			raise ValueError()

	def build(self) -> CloneTransaction:
		return self.transaction
