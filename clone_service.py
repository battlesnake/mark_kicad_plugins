from typing import Sequence, final, Optional
from logging import Logger
from dataclasses import dataclass

import pcbnew  # pyright: ignore

from .clone_settings import CloneSettings
from .kicad_entities import UuidPath
from .hierarchy import Hierarchy
from .placement import Placement
from .clone_placement_strategy import ClonePlacementStrategy, ClonePlacementChangeLog
from .string_utils import StringUtils


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
		self.change_log: ClonePlacementChangeLog | None = None

	def can_revert(self) -> bool:
		return self.change_log is not None

	def revert_clone(self) -> None:
		if self.change_log is None:
			return
		self.change_log.undo()
		self.change_log = None

	def clone_subcircuits(self, logger: Logger, hierarchy: Hierarchy, selection: CloneSelection, settings: CloneSettings) -> None:

		logger = logger.getChild(type(self).__name__)

		source_reference = hierarchy.footprints[UuidPath.of(selection.source_footprints[0].GetPath())]
		logger.info("Source reference footprint: %s (%s)", source_reference.reference, source_reference.symbol.sheet_instance.name_path)

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
			if footprint != source_reference
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

		for target_reference, target_reference_placement in placement_strategy:
			logger.info("Rendering target subcircuit around %s", target_reference.reference)
			for source_footprint in selection.source_footprints:
				source_path = UuidPath.of(source_footprint.GetPath())
				target_reference_path = target_reference.path
				target_path = target_reference_path[:-1] + source_path[-1]
				source_footprint = hierarchy.footprints[source_path]
				target_footprint = hierarchy.footprints[target_path]
				logger.debug(f"Matched source %s to target %s", source_footprint, target_footprint)
				# Apply placement
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_footprint.data,
					target_item=target_footprint.data,
				)
			for source_track in selection.source_tracks:
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_track,
				)
			for source_drawing in selection.source_drawings:
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_drawing,
				)
			for source_zone in selection.source_zones:
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_zone,
				)

		self.change_log = placement_strategy.change_log
