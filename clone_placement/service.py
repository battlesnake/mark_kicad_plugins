from typing import Sequence, final, Optional

from logging import Logger
from dataclasses import dataclass

from pcbnew import FOOTPRINT, PCB_TRACK, BOARD_ITEM, ZONE, Refresh as RefreshView

from ..parse_v8 import Schematic, EntityPath

from ..ui.spinner import spin_while
from ..ui.bored_user_entertainer import BoredUserEntertainer

from .settings import CloneSettings
from .placement import Placement
from .placement_strategy import ClonePlacementStrategy, ClonePlacementStrategyType
from .transaction_builder import CloneTransactionBuilder
from .transaction import CloneTransaction
from .spath import Spath


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
		schematic: Schematic,
		selection: CloneSelection,
		settings: CloneSettings
	) -> None:

		logger = logger.getChild(type(self).__name__)

		BoredUserEntertainer.message("Preparing to clone")

		source_footprints = [
			schematic.footprints[EntityPath.parse(footprint.GetPath())]
			for footprint in selection.source_footprints
		]

		if settings.placement.strategy == ClonePlacementStrategyType.RELATIVE:
			assert settings.placement.relative.anchor is not None
			source_reference = settings.placement.relative.anchor
		else:
			source_reference = source_footprints[0]
		logger.info(
			"Source reference footprint: %s",
			source_reference.component_instance.reference,
		)

		source_units = [
			unit
			for footprint in source_footprints
			for unit in footprint.component_instance.units
		]
		logger.info("Total source footprints: %d", len(source_footprints))
		logger.info("Total source units: %d", len(source_units))

		source_unit_sheet_paths = [
			Spath.create(unit.sheet, schematic.root_sheet_instance)
			for unit in source_units
		]
		source_prefix = reduce(Spath.__and__, source_unit_sheet_paths)
		logger.info("Source prefix: %s", source_prefix)

		source_unit_relative_paths = [
			path[len(source_prefix):]
			for path in source_unit_sheet_paths
		]
		logger.info("Paths to source footprints, relative to source prefix:")
		for path in sorted(set(source_unit_relative_paths)):
			logger.info(" * %s", path)

		selected_instances = settings.instances
		for instance in selected_instances:
			logger.info("Selected target sheet: %s", instance.path)
		selected_instance_paths = {
			instance.path
			for instance in selected_instances
		}

		other_instances = [
			instance
			for instance in source_reference.component_instance.units[0].definition.instances
		]

		logger.info("Unfiltered list of related footprints: %s", ", ".join(
			str(instance.component.reference)
			for instance in other_instances
		))

		target_references = [
			other_instance.component.footprint
			for other_instance in other_instances
			if any(
				other_instance.path.startswith(instance)
				for instance in selected_instance_paths
			)
		]
		for target in target_references:
			logger.info("Target reference footprints: %s", target.component_instance.reference)

		source_reference_placement = Placement.of(source_reference.pcbnew_footprint)

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
			logger.info("Planning clone of subcircuit around %s", target_reference.component_instance.reference)
			for source_footprint in selection.source_footprints:
				# TODO: Proper MultiMaps for each component, we can't just do
				# prefix matching if the subcircuit is spread over several
				# sheets.  We don't need to care about multi-unit, just match
				# the sheets for the first unit - since all units map to the
				# same footprint anyway.
				source_path = schematic.footprints[EntityPath.parse(source_footprint.GetPath())].component_instance.units[0].path
				# TODO: Adjust the -1 to be -n, as we may need to splice in a
				# few levels of sheets too
				target_reference_path = target_reference.path
				target_path = target_reference_path[:-1] + source_path[-1]
				source_footprint = schematic.footprints[source_path]
				target_footprint = schematic.footprints[target_path]
				logger.debug("Matched source %s to target %s", source_footprint, target_footprint)
				# Apply placement
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
