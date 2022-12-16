from dataclasses import dataclass
from typing import List, TypeVar, Iterable, Optional

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .clone_settings import CloneSettings
from .clone_settings_dialog import CloneSettingsDialog
from .kicad_entities import  SheetInstance, Footprint, UuidPath
from .hierarchy_parser import HierarchyParser
from .string_utils import StringUtils
from .clone_placement import Placement


@dataclass
class ClonePluginConfiguration():

	pass


ItemType = TypeVar("ItemType", bound=pcbnew.EDA_ITEM)


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
		common_ancestor_uuid_chain = UuidPath.from_parts(StringUtils.get_common_ancestor_of(footprint_sheet_uuid_chains))
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
			hierarchy.footprints[UuidPath.from_kiid_path(footprint.GetPath())]
			for footprint in self.filter_selected(board.Footprints())
		]

	def get_settings(self, selected_footprints: Iterable[Footprint], instances: Iterable[SheetInstance]) -> Optional[CloneSettings]:
		settings_dialog = CloneSettingsDialog(
			logger=self.logger,
			footprints=selected_footprints,
			instances=instances,
			relations=self.hierarchy.relations,
		)
		if not settings_dialog.execute():
			return None
		return settings_dialog.settings

	def do_cloning(self) -> None:
		logger = self.logger
		board = self.board
		hierarchy = self.hierarchy
		settings = self.settings
		common_ancestor = self.common_ancestor

		reference = settings.placement.relative.anchor
		if reference is None:
			raise ValueError("No reference/anchor selected")

		targets = [
			footprint
			for footprint in hierarchy.symbol_instances[reference.symbol]
			if footprint != reference
		]
		# TODO filter by sheet instances selected in settings

		instances = settings.instances

		reference_placement = Placement.from_footprint(reference)

		placement_strategy = settings.placement.get_strategy(
			reference=reference,
			targets=targets
		)

		# TODO: Option to clear target placement area so we never create
		# overlaps

		for anchor, placement in placement_strategy:
			for source_footprint in self.filter_selected(board.Footprints()):
				# 1. get footprint path (sheet/sheet/.../footprint)
				# 2. replace footprint (last) part of reference footprint path with this footprint's path uuid
				# 3. resolve footprint from path
				# 4. apply placement
				source_path = UuidPath.from_kiid_path(source_footprint.GetPath())
				anchor_path = anchor.path
				target_path = UuidPath(list(anchor_path.value[:-1]) + [source_path.value[-1]])
				target_footprint = hierarchy.footprints[target_path]
				pass
			for source_track in self.filter_selected(board.Tracks()):
				# 1. Duplicate the track
				# 2. Apply placement
				pass
			for source_drawing in self.filter_selected(board.Drawings()):
				# 1. Duplicate the drawing
				# 2. Apply placement
				pass
			for source_zone in self.filter_selected(board.Zones()):
				# 1. Duplicate the zone
				# 2. Apply placement
				pass

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

		if (settings := self.get_settings(selected_footprints, instances)) is None:
			logger.error("Dialog rejected by user")
			return
		self.settings = settings

		self.do_cloning()
