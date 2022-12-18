from typing import List, TypeVar, Iterable, Optional, final

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .clone_settings import CloneSettings
from .clone_settings_dialog import CloneSettingsDialog
from .kicad_entities import SheetInstance, Footprint, UuidPath
from .hierarchy_parser import HierarchyParser
from .string_utils import StringUtils
from .placement import Placement
from .clone_placement_strategy import ClonePlacementStrategy


ItemType = TypeVar("ItemType", bound=pcbnew.BOARD_ITEM)


@final
class ClonePlugin(Plugin):

	@staticmethod
	def filter_selected(items: Iterable[ItemType]) -> List[ItemType]:
		return [
			item
			for item in items
			if item.IsSelected()
		]

	@staticmethod
	def path_to_str(path: pcbnew.KIID_PATH) -> str:
		return "".join(f"/{uuid.AsString()}" for uuid in path)

	def get_common_ancestor(self, footprints: Iterable[Footprint]) -> SheetInstance:
		hierarchy = self.hierarchy
		footprint_sheet_uuid_chains = set(
			footprint.symbol.sheet_instance.uuid_chain
			for footprint in footprints
		)
		common_ancestor_uuid_chain = UuidPath.of(StringUtils.get_common_ancestor_of(footprint_sheet_uuid_chains))
		return hierarchy.instances[common_ancestor_uuid_chain]

	def get_peers_and_parents(self, ancestor: SheetInstance) -> Iterable[SheetInstance]:
		hierarchy = self.hierarchy
		return [
			sheet_instance
			for sheet_instance in hierarchy.instances.values()
			if StringUtils.is_same_or_is_child_of(sheet_instance.template_uuid_chain, ancestor.template_uuid_chain)
			if sheet_instance != ancestor
		]

	def get_selected_footprints(self) -> List[Footprint]:
		board = self.board
		hierarchy = self.hierarchy
		return [
			hierarchy.footprints[UuidPath.of(footprint.GetPath())]
			for footprint in self.filter_selected(board.Footprints())
		]

	def get_settings(self, selected_footprints: Iterable[Footprint], instances: Iterable[SheetInstance]) -> Optional[CloneSettings]:
		settings_dialog = CloneSettingsDialog(
			logger=self.logger,
			footprints=selected_footprints,
			instances=instances,
			relations=self.hierarchy.relations,
		)
		return settings_dialog.execute()

	def do_cloning(self) -> None:
		logger = self.logger
		board = self.board
		hierarchy = self.hierarchy
		settings = self.settings
		common_ancestor = self.common_ancestor

		self.logger.info("Common ancestor sheet of all selected footprints: %s", common_ancestor.name_path)

		source_reference = settings.placement.relative.anchor
		if source_reference is None:
			raise ValueError("No reference/anchor selected")
		self.logger.info("Source reference: %s (%s)", source_reference.reference, source_reference.symbol.sheet_instance.name_path)

		selected_instances = settings.instances
		for instance in selected_instances:
			self.logger.info("Targets sheet: %s", instance.name_path)
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

		source_footprints = self.filter_selected(board.Footprints())
		source_tracks = self.filter_selected(board.Tracks())
		source_drawings = self.filter_selected(board.Drawings())
		source_zones = self.filter_selected(board.Zones())

		# TODO: Option to clear target placement areas so we never create
		# overlaps

		for target_reference, target_reference_placement in placement_strategy:
			self.logger.info("Rendering target subcircuit around %s", target_reference.reference)
			for source_footprint in source_footprints:
				# 1. get footprint path (sheet/sheet/.../footprint)
				# 2. replace footprint (last) part of reference footprint path with this footprint's path uuid
				# 3. resolve footprint from path
				# 4. apply placement
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
			for source_track in source_tracks:
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_track,
				)
			for source_drawing in source_drawings:
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_drawing,
				)
			for source_zone in source_zones:
				placement_strategy.apply_placement(
					source_reference=source_reference_placement,
					target_reference=target_reference_placement,
					source_item=source_zone,
				)

		pcbnew.Refresh()

		from .message_box import MessageBox
		MessageBox.alert("will undo after")

		change_log = placement_strategy.change_log

		change_log.undo()

		pcbnew.Refresh()

	def execute(self) -> None:
		logger = self.logger
		board = self.board

		hierarchy = HierarchyParser(logger, board).parse()
		self.hierarchy = hierarchy

		selected_footprints = self.get_selected_footprints()
		if not selected_footprints:
			logger.error("No footprints selected")
			raise ValueError("No footprints in selection")

		self.common_ancestor = self.get_common_ancestor(selected_footprints)

		instances = self.get_peers_and_parents(self.common_ancestor)

		settings = self.get_settings(selected_footprints, instances)
		if settings is None:
			logger.error("Dialog rejected by user")
			return
		self.settings = settings

		self.do_cloning()
