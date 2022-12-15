from dataclasses import dataclass
from typing import List, TypeVar, Iterable

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .clone_settings import CloneSettings, CloneSettingsDialog
from .kicad_entities import  SheetInstance, Footprint, UuidPath
from .hierarchy_parser import HierarchyParser, Hierarchy
from .string_utils import StringUtils


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

	def get_instances(self, hierarchy: Hierarchy, footprints: Iterable[Footprint]) -> Iterable[SheetInstance]:
		footprint_sheet_uuid_chains = set(
			footprint.symbol.sheet_instance.uuid_chain
			for footprint in footprints
		)
		common_ancestor_uuid_chain = UuidPath.from_parts(StringUtils.get_common_ancestor_of(footprint_sheet_uuid_chains))
		common_ancestor = hierarchy.instances[common_ancestor_uuid_chain]
		return [
			sheet_instance
			for sheet_instance in hierarchy.instances.values()
			if StringUtils.is_same_or_is_child_of(sheet_instance.template_uuid_chain, common_ancestor.template_uuid_chain)
			if sheet_instance != common_ancestor
		]

	def execute(self) -> None:
		logger = self.logger
		board = self.board
		
		hierarchy = HierarchyParser(logger, board).parse()

		selected_footprints: List[Footprint] = [
			hierarchy.footprints[UuidPath.from_kiid_path(footprint.GetPath())]
			for footprint in self.filter_selected(board.Footprints())
		]
		if not selected_footprints:
			logger.error("No footprints selected")
			raise ValueError("No footprints in selection")

		instances = self.get_instances(hierarchy, selected_footprints)

		settings_dialog = CloneSettingsDialog(logger, selected_footprints, instances)
		if not settings_dialog.execute():
			logger.error("Dialog rejected by user")
			return

		selected_items: List[pcbnew.EDA_ITEM] = \
				self.filter_selected(board.Footprints()) + \
				self.filter_selected(board.Tracks()) + \
				self.filter_selected(board.Drawings()) + \
				self.filter_selected(board.Zones())
