from typing import List, TypeVar, Iterable, final, Sequence
from logging import Logger
from dataclasses import dataclass

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .clone_settings import CloneSettings
from .clone_settings_view import CloneSettingsView, CloneSettingsController, CloneSettingsViewDomain
from .kicad_entities import SheetInstance, Footprint, UuidPath
from .hierarchy_parser import HierarchyParser, Hierarchy
from .string_utils import StringUtils
from .placement import Placement
from .clone_placement_strategy import ClonePlacementStrategy, ClonePlacementChangeLog
from .hierarchy_logger import HierarchyLogger


ItemType = TypeVar("ItemType", bound=pcbnew.BOARD_ITEM)


settings_view: CloneSettingsView | None = None
change_log: ClonePlacementChangeLog | None = None


def filter_selected(items: Iterable[ItemType]) -> List[ItemType]:
	return [
		item
		for item in items
	if item.IsSelected()
]


@dataclass(eq=False, repr=False, frozen=True)
class CloneSelection():
	source_footprints: Sequence[pcbnew.FOOTPRINT]
	source_tracks: Sequence[pcbnew.PCB_TRACK]
	source_drawings: Sequence[pcbnew.BOARD_ITEM]
	source_zones: Sequence[pcbnew.ZONE]


@final
class ClonePluginController(CloneSettingsController):

	def __init__(self, logger: Logger, board: pcbnew.BOARD, hierarchy: Hierarchy, selection: CloneSelection):
		self.logger = logger
		self.board = board
		self.hierarchy = hierarchy
		self.selection = selection
		self.is_preview = False

	def revert(self) -> None:
		global change_log
		if change_log is None:
			return
		change_log.undo()
		change_log = None
		self.is_preview = False

	def has_preview(self) -> bool:
		return self.is_preview

	def apply_preview(self, settings: CloneSettings) -> None:
		self.logger.info("Command: Apply preview")
		self.revert()
		self.clone_subcircuits(settings)
		self.is_preview = True
		pcbnew.Refresh()

	def clear_preview(self) -> None:
		self.logger.info("Command: Clear preview")
		if self.is_preview:
			self.revert()
		pcbnew.Refresh()

	def can_undo(self) -> bool:
		return change_log is not None

	def apply(self, settings: CloneSettings) -> None:
		self.logger.info("Command: Apply")
		self.revert()
		self.clone_subcircuits(settings)
		pcbnew.Refresh()

	def undo(self) -> None:
		self.logger.info("Command: Undo")
		self.revert()
		pcbnew.Refresh()

	def clone_subcircuits(self, settings: CloneSettings) -> None:
		logger = self.logger
		hierarchy = self.hierarchy
		selection = self.selection

		source_reference = hierarchy.footprints[UuidPath.of(selection.source_footprints[0].GetPath())]
		self.logger.info("Source reference: %s (%s)", source_reference.reference, source_reference.symbol.sheet_instance.name_path)

		selected_instances = settings.instances
		for instance in selected_instances:
			self.logger.info("Target sheet: %s", instance.name_path)
		selected_instance_paths = {
			instance.uuid_chain
			for instance in selected_instances
		}

		targets = [
			footprint
			for footprint in hierarchy.symbol_instances[source_reference.symbol]
			if footprint != source_reference
			if footprint.path[:-1] in selected_instance_paths
		]
		for target in targets:
			self.logger.info("Targets: %s", target.reference)

		source_reference_placement = Placement.of(source_reference.data)

		placement_strategy = ClonePlacementStrategy.get(
			settings=settings.placement,
			reference=source_reference,
			targets=targets
		)

		# TODO: Option to clear target placement areas so we never create
		# overlaps

		for target_reference, target_reference_placement in placement_strategy:
			self.logger.info("Rendering target subcircuit around %s", target_reference.reference)
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


@final
class ClonePlugin(Plugin):

	change_log: ClonePlacementChangeLog | None = None

	@staticmethod
	def path_to_str(path: pcbnew.KIID_PATH) -> str:
		return "".join(f"/{uuid.AsString()}" for uuid in path)

	def get_common_ancestor_of_footprints(self, footprints: Iterable[Footprint]) -> SheetInstance:
		hierarchy = self.hierarchy
		footprint_sheet_uuid_paths = set(
			footprint.symbol.sheet_instance.uuid_path
			for footprint in footprints
		)
		common_ancestor_uuid_path = UuidPath.of(StringUtils.get_common_ancestor_of(footprint_sheet_uuid_paths))
		return hierarchy.instances[common_ancestor_uuid_path]

	def get_selected_footprints(self) -> List[Footprint]:
		board = self.board
		hierarchy = self.hierarchy
		return [
			hierarchy.footprints[UuidPath.of(footprint.GetPath())]
			for footprint in filter_selected(board.Footprints())
		]

	def execute(self) -> None:
		logger = self.logger
		board = self.board

		hierarchy = HierarchyParser(logger, board).parse()
		self.hierarchy = hierarchy

		HierarchyLogger(logger).log_all(hierarchy)

		selection = CloneSelection(
			source_footprints=filter_selected(board.Footprints()),
			source_tracks=filter_selected(board.Tracks()),
			source_drawings=filter_selected(board.Drawings()),
			source_zones=filter_selected(board.Zones()),
		)

		selected_footprints = [
			hierarchy.footprints[UuidPath.of(footprint.GetPath())]
			for footprint in selection.source_footprints
		]
		if not selected_footprints:
			logger.error("No footprints selected")
			raise ValueError("No footprints in selection")

		selected_footprints_common_ancestor = self.get_common_ancestor_of_footprints(selected_footprints)
		self.logger.info("Common ancestor sheet of all selected footprints: %s", selected_footprints_common_ancestor.name_path)

		reference_footprint = selected_footprints[0]
		reference_symbol = reference_footprint.symbol
		reference_instance = reference_symbol.sheet_instance

		self.logger.info("Reference footprint: %s", reference_footprint.reference)
		self.logger.info("Reference footprint's symbol's sheet instance: %s", reference_instance.name_path)

		common_ancestor_up_levels = len(reference_instance.uuid_path) - len(selected_footprints_common_ancestor.uuid_path)

		self.logger.info("Levels from reference footprint's sheet instance to common ancestor of all selected footprints: %s", common_ancestor_up_levels)

		peer_footprints = hierarchy.symbol_instances[reference_symbol]

		self.logger.info("Peer footprints: %s", ", ".join(symbol.reference for symbol in peer_footprints))

		peer_instances = [
			hierarchy.instances[footprint.path[:-1]]
			for footprint in peer_footprints
			if footprint != reference_footprint
		]

		for instance in peer_instances:
			self.logger.info("Peer sheet instances: %s", instance.name_path)

		target_instances = set(
			hierarchy.instances[
				instance.uuid_path[0:-common_ancestor_up_levels]
				if common_ancestor_up_levels > 0
				else instance.uuid_path
			]
			for instance in peer_instances
			if instance != reference_instance
		)

		for instance in target_instances:
			self.logger.info("Instance we can clone to: %s", instance.name_path)

		settings_domain = CloneSettingsViewDomain(
			instances=sorted(target_instances, key=lambda instance: instance.name_path),
			footprints=sorted(selected_footprints, key=lambda footprint: footprint.reference),
		)
		settings_controller = ClonePluginController(logger, board, hierarchy, selection)

		global settings_view
		if settings_view is not None:
			settings_view.Destroy()
			settings_view = None
		settings_view = CloneSettingsView(logger, settings_domain, settings_controller)
		settings_view.Show()
