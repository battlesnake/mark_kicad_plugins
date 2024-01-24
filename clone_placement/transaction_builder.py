from typing import List, TypeVar, Optional
from typing_extensions import overload

import pcbnew

from kicad_v8_model.vector2 import Vector2
from layout_transaction.command import DisplaceCommand, FlipCommand, RotateCommand

from ..kicad_v8_model import Footprint
from ..layout_transaction import Command, CommandTarget  # pyright: ignore

from .placement import Placement
from .transaction import CloneTransaction, CloneTransactionDuplicateAndTransferPlacementPlacementOperator, CloneTransactionTransferFootprintPlacementOperator


ItemType = TypeVar("ItemType", bound=pcbnew.BOARD_ITEM)


class CloneTransactionBuilder():

	transaction: List[Command]

	def __init__(self):
		self.transaction = []

	def generate_placement_commands(
		self,
		source_reference: Placement,
		target_reference: Placement,
		target: CommandTarget,
	):
		rotation = (target_reference.orientation - source_reference.orientation).wrap()
		flip = target_reference.flipped != source_reference.flipped
		displacement = target_reference.position - source_reference.position
		if displacement != Vector2.ZERO():
			yield DisplaceCommand(
				target=target,
				displacement=displacement,
			)
		if rotation != 0:
			yield RotateCommand(
				target=target,
				rotation=rotation,
			)
		if flip:
			yield FlipCommand(
				target=target,
			)

	def add_route(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: ItemType,
	) -> None:
		self.transaction.add(CloneTransactionDuplicateAndTransferPlacementPlacementOperator(
			source_reference,
			target_reference,
			source_item,
		))

	def add_footprint(
		self,
		source_reference: Placement,
		target_reference: Placement,
		source_item: Footprint,
		target_item: Footprint,
	):
		self.transaction.add(CloneTransactionTransferFootprintPlacementOperator(
			source_reference,
			target_reference,
			source_item,
			target_item,
		))

	def build(self) -> CloneTransaction:
		return self.transaction
