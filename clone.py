from dataclasses import dataclass
from typing import List, TypeVar, Iterable, Union

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .clone_settings import CloneSettings, CloneSettingsDialog
from .hierarchy_parser import HierarchyParser, SheetInstance, SheetID


Board = pcbnew.BOARD
Footprint = pcbnew.FOOTPRINT
Track = pcbnew.PCB_TRACK
Via = pcbnew.PCB_VIA
Segment = Union[Track, Via]
Item = pcbnew.EDA_ITEM
Instance = str


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

	def get_instances(self, footprints: Iterable[Footprint]) -> Iterable[SheetInstance]:
		logger = self.logger
		board = self.board
		hierarchy = HierarchyParser(logger, board)
		hierarchy.parse()
		footprint_sheets = set(
			hierarchy.by_footprint[str(footprint.GetReference())]
			for footprint in footprints
		)

		for fp in footprints:
			logger.info(" - FP=%s, SHEET=%s", fp.GetReference(), hierarchy.by_footprint[str(fp.GetReference())])

		if not footprint_sheets:
			raise Exception("Failed to identify bounding sheet of selected footprints")
		bounding_sheet_path_chain = HierarchyParser.get_common_ancestor_of(
			sheet.path_chain()
			for sheet in footprint_sheets
		)
		if not bounding_sheet_path_chain:
			raise Exception("Bounding sheet is top-level sheet")
		bounding_sheet_path = bounding_sheet_path_chain[-1]
		return hierarchy.by_path[bounding_sheet_path]

	def execute(self) -> None:
		logger = self.logger
		board = self.board
		selected_footprints: List[Footprint] = self.filter_selected(board.Footprints())
		selected_items: List[Item] = \
				self.filter_selected(board.Footprints()) + \
				self.filter_selected(board.Tracks()) + \
				self.filter_selected(board.Drawings()) + \
				self.filter_selected(board.Zones())
		if not selected_footprints:
			raise ValueError("No footprints in selection")
		instances = self.get_instances(selected_footprints)
		settings_dialog = CloneSettingsDialog(selected_footprints, instances)
		if not settings_dialog.execute():
			return
