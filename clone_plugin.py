from typing import List, TypeVar, Iterable, final

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .kicad_entities import SheetInstance, Footprint, UuidPath
from .hierarchy_parser import HierarchyParser
from .hierarchy_logger import HierarchyLogger
from .string_utils import StringUtils
from .clone_placement_strategy import ClonePlacementChangeLog
from .clone_service import CloneSelection
from .clone_settings_controller import CloneSettingsController
from .clone_settings_view import CloneSettingsView, CloneSettingsViewDomain
from .user_exception import UserException


ItemType = TypeVar("ItemType", bound=pcbnew.BOARD_ITEM)


@final
class ClonePlugin(Plugin):

	change_log: ClonePlacementChangeLog | None = None

	@staticmethod
	def path_to_str(path: pcbnew.KIID_PATH) -> str:
		return "".join(f"/{uuid.AsString()}" for uuid in path)

	@staticmethod
	def filter_selected(items: Iterable[ItemType]) -> List[ItemType]:
		return [
			item
			for item in items
		if item.IsSelected()
	]

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
			for footprint in self.filter_selected(board.Footprints())
		]

	def execute(self) -> None:
		logger = self.logger
		board = self.board

		try:
			hierarchy = HierarchyParser(logger, board).parse()
		except Exception as error:
			raise UserException("Failed to parse board / schematic structure") from error
		self.hierarchy = hierarchy

		HierarchyLogger(logger).log_all(hierarchy)

		selection = CloneSelection(
			source_footprints=self.filter_selected(board.Footprints()),
			source_tracks=self.filter_selected(board.Tracks()),
			source_drawings=self.filter_selected(board.Drawings()),
			source_zones=self.filter_selected(board.Zones()),
		)

		selected_footprints = [
			hierarchy.footprints[UuidPath.of(footprint.GetPath())]
			for footprint in selection.source_footprints
		]
		if not selected_footprints:
			logger.error("No footprints selected")
			raise UserException("No footprints in selection")

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

		settings_controller = CloneSettingsController(logger, board, hierarchy, selection)

		view = CloneSettingsView(logger, settings_domain, settings_controller)
		view.execute()
