from typing import Sequence, final, Optional

from logging import Logger
from dataclasses import dataclass

from pcbnew import FOOTPRINT, PCB_TRACK, BOARD_ITEM, ZONE, Refresh as RefreshView

from ..ui.spinner import spin_while
from ..ui.bored_user_entertainer import BoredUserEntertainer

from .context import CloneContext
from .placement import Placement
from .placement_strategy import ClonePlacementStrategy, ClonePlacementStrategyType
from .transaction_builder import CloneTransactionBuilder
from .transaction import CloneTransaction


@final
@dataclass(eq=False, repr=False, frozen=True)
class CloneSelection():
	source_footprints: Sequence[FOOTPRINT]
	source_tracks: Sequence[PCB_TRACK]
	source_drawings: Sequence[BOARD_ITEM]
	source_zones: Sequence[ZONE]


@final
class CloneService():

	_inst: Optional["CloneService"] = None

	@staticmethod
	def get() -> "CloneService":
		if CloneService._inst is None:
			CloneService._inst = CloneService()
		return CloneService._inst

	def __init__(self):
		self.transaction: CloneTransaction | None = None

	def can_revert(self) -> bool:
		return self.transaction is not None

	@spin_while
	def revert_clone(self) -> None:
		if self.transaction is None:
			return

		BoredUserEntertainer.message("Reverting changes...")
		self.transaction.revert()
		self.transaction = None

		RefreshView()

	@spin_while
	def clone_subcircuits(
		self,
		logger: Logger,
		context: CloneContext,
	) -> None:

		logger = logger.getChild(type(self).__name__)

		BoredUserEntertainer.message("Preparing to clone")

		settings = context.settings
		source_footprints = context.selected_footprints
		selection = context.selection
		footprint_mapping = context.footprint_mapping

		"""
		It's safe to assume that a footprint in source list corresponds to
		footprints at same index in each target list.
		"""
		source_footprints = list(context.footprint_mapping.keys())

		if settings.placement.strategy == ClonePlacementStrategyType.RELATIVE:
			assert settings.placement.relative.anchor is not None
			source_reference = settings.placement.relative.anchor
		else:
			source_reference = source_footprints[0]
		logger.info(
			"Source reference footprint: %s",
			source_reference.component.reference,
		)

		source_reference_placement = Placement.of(source_reference)

		placement_strategy = ClonePlacementStrategy.get(
			project=context.project,
			settings=settings.placement,
			reference=source_reference,
			targets=[
				target.footprint
				for target in footprint_mapping[source_reference]
				if target.base_sheet in settings.instances
			],
		)

		# TODO: Option to clear target placement areas so we never create
		# overlaps

		transaction_builder = CloneTransactionBuilder()

		BoredUserEntertainer.message("Planning clone operation")

		for target_reference, target_reference_placement in placement_strategy:
			logger.info("Planning clone of subcircuit around %s", target_reference.component.reference)
			for source_index, source_footprint in enumerate(source_footprints):
				target_footprint_mapping = footprint_mapping[source_footprint][source_index]
				target_footprint = target_footprint_mapping.footprint
				logger.debug("Matched source %s to target %s", source_footprint, target_footprint)
				if target_footprint_mapping.base_sheet not in settings.instances:
					logger.debug("Sheet deselected, skipping footprint")
					continue
				transaction_builder.add_item(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_footprint.pcbnew_footprint,
					target_item=target_footprint.pcbnew_footprint,
				)
			for source_track in selection.source_tracks:
				transaction_builder.add_item(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_track,
				)
			for source_drawing in selection.source_drawings:
				transaction_builder.add_item(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_drawing,
				)
			for source_zone in selection.source_zones:
				transaction_builder.add_item(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_zone,
				)

		self.transaction = transaction_builder.build()
		self.transaction.on_progress = BoredUserEntertainer.progress

		BoredUserEntertainer.message("Executing clone operation")
		self.transaction.apply()

		BoredUserEntertainer.message("Refreshing pcbnew...")
		logger.info("Refreshing pcbnew")
		RefreshView()
