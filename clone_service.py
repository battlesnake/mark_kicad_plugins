from typing import Sequence, final, Optional
from logging import Logger
from dataclasses import dataclass

import pcbnew  # pyright: ignore

from .clone_settings import CloneSettings
from .kicad_entities import UuidPath
from .hierarchy import Hierarchy
from .placement import Placement
from .clone_placement_strategy import ClonePlacementStrategy, ClonePlacementStrategyType
from .string_utils import StringUtils
from .spinner import spin_while
from .bored_user_entertainer import BoredUserEntertainer
from .clone_transaction_builder import CloneTransactionBuilder
from .clone_transaction import CloneTransaction


@final
@dataclass(eq=False, repr=False, frozen=True)
class CloneSelection():
	source_footprints: Sequence[pcbnew.FOOTPRINT]
	source_tracks: Sequence[pcbnew.PCB_TRACK]
	source_drawings: Sequence[pcbnew.BOARD_ITEM]
	source_zones: Sequence[pcbnew.ZONE]


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

		pcbnew.Refresh()

	@spin_while
	def clone_subcircuits(self, logger: Logger, hierarchy: Hierarchy, selection: CloneSelection, settings: CloneSettings) -> None:

		logger = logger.getChild(type(self).__name__)

		BoredUserEntertainer.message("Preparing to clone")

		if settings.placement.strategy == ClonePlacementStrategyType.RELATIVE:
			source_reference_footprint = settings.placement.relative.anchor.data
		else:
			source_reference_footprint = selection.source_footprints[0]

		source_reference = hierarchy.get_footprint_by_pcb_path(source_reference_footprint.GetPath())
		logger.info("Source reference footprint: %s (%s)", source_reference.reference, source_reference.sheet_instance.name_path)

		selected_instances = settings.instances
		for instance in selected_instances:
			logger.info("Selected target sheet: %s", instance.name_path)
		selected_instance_paths = {
			instance.uuid_path
			for instance in selected_instances
		}

		logger.info("Unfiltered list of related footprints: %s", ", ".join(
			footprint.reference
			for footprint in hierarchy.symbol_instances[source_reference.symbol]
		))

		target_references = [
			footprint
			for footprint in hierarchy.symbol_instances[source_reference.symbol]
			if any(
				StringUtils.is_child_of(instance, footprint.path)
				for instance in selected_instance_paths
			)
		]
		for target in target_references:
			logger.info("Target reference footprints: %s", target.reference)

		source_reference_placement = Placement.of(source_reference.data)

		placement_strategy = ClonePlacementStrategy.get(
			settings=settings.placement,
			reference=source_reference,
			targets=target_references
		)

		# TODO: Option to clear target placement areas so we never create
		# overlaps

		transaction_builder = CloneTransactionBuilder()

		BoredUserEntertainer.message("Planning clone operation")

		for target_reference, target_reference_placement in placement_strategy:
			logger.info("Planning clone of subcircuit around %s", target_reference.reference)
			for source_footprint in selection.source_footprints:
				source_path = hierarchy.get_path_from_pcb_path(source_footprint.GetPath())
				target_reference_path = target_reference.path
				target_path = target_reference_path[:-1] + source_path[-1]
				source_footprint = hierarchy.footprints[source_path]
				target_footprint = hierarchy.footprints[target_path]
				logger.debug(f"Matched source %s to target %s", source_footprint, target_footprint)
				# Apply placement
				transaction_builder.add_item(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_footprint.data,
					target_item=target_footprint.data,
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
		pcbnew.Refresh()
