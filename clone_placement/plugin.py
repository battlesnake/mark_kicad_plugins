from typing import List, TypeVar, Iterable, final
from functools import reduce
from math import ceil

import pcbnew  # pyright: ignore

from ..utils.kicad_units import UserUnits, SizeUnits
from ..utils.user_exception import UserException
from ..utils.string_utils import StringUtils

from ..parse_v8 import SheetInstance, Footprint, EntityPath, SchematicParser

from ..plugin import Plugin

from .service import CloneSelection
from .settings_controller import CloneSettingsController
from .settings_view import CloneSettingsView
from .settings import CloneSettings
from .placement_settings import ClonePlacementGridFlow, ClonePlacementGridSort, ClonePlacementGridStrategySettings, ClonePlacementRelativeStrategySettings, ClonePlacementSettings, ClonePlacementStrategyType


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

	def get_common_ancestor_of_footprints(self, footprints: Iterable[Footprint]) -> SheetInstance:
		hierarchy = self.hierarchy
		footprint_sheet_uuid_paths = set(
			footprint.sheet_instance.uuid_path
			for footprint in footprints
		)
		common_ancestor_uuid_path = EntityPath.parse(StringUtils.get_common_ancestor_of(footprint_sheet_uuid_paths))
		return hierarchy.instances[common_ancestor_uuid_path]

	def get_selected_footprints(self) -> List[Footprint]:
		board = self.board
		hierarchy = self.hierarchy
		return [
			hierarchy.get_footprint_by_pcb_path(footprint.GetPath())
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
			hierarchy.get_footprint_by_pcb_path(footprint.GetPath())
			for footprint in selection.source_footprints
		]
		if not selected_footprints:
			logger.error("No footprints selected")
			raise UserException("No footprints in selection")

		selected_footprints_common_ancestor = self.get_common_ancestor_of_footprints(selected_footprints)
		self.logger.info("Common ancestor sheet of all selected footprints: %s", selected_footprints_common_ancestor.name_path)

		reference_footprint = selected_footprints[0]
		reference_symbol = reference_footprint.symbol
		reference_instance = reference_footprint.sheet_instance

		self.logger.info("Reference footprint: %s", reference_footprint.reference)
		self.logger.info("Reference footprint's symbol's sheet instance: %s", reference_instance.name_path)

		common_ancestor_up_levels = len(reference_instance.uuid_path) - len(selected_footprints_common_ancestor.uuid_path)

		self.logger.info("Levels from reference footprint's sheet instance to common ancestor of all selected footprints: %s", common_ancestor_up_levels)

		peer_footprints = hierarchy.symbol_instances[reference_symbol]

		self.logger.info("Peer footprints: %s", ", ".join(symbol.reference for symbol in peer_footprints))

		relevant_sheet_instances = [
			hierarchy.instances[footprint.path[:-1]]
			for footprint in peer_footprints
		]

		for instance in relevant_sheet_instances:
			self.logger.debug("Peer sheet instances: %s", instance.name_path)

		subcircuit_root_sheet_instances = set(
			hierarchy.instances[
				instance.uuid_path[0:-common_ancestor_up_levels]
				if common_ancestor_up_levels > 0
				else instance.uuid_path
			]
			for instance in relevant_sheet_instances
		)

		for sheet_instance in subcircuit_root_sheet_instances:
			self.logger.info("Sheet instance we can clone to: %s", sheet_instance.name_path)

		selected_footprint_bboxes = [
			footprint.data.GetBoundingBox(True, True)
			for footprint in selected_footprints
		]

		selected_footprint_bbox_coords = [
			(bbox.GetLeft(), bbox.GetTop(), bbox.GetRight(), bbox.GetBottom())
			for bbox in selected_footprint_bboxes
			if bbox.GetWidth() > 0 and bbox.GetHeight() > 0
		]

		selected_subcircuit_bbox = reduce(
			lambda a, b: (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])),
			selected_footprint_bbox_coords
		)

		selection_bbox_width = selected_subcircuit_bbox[2] - selected_subcircuit_bbox[0]
		selection_bbox_height = selected_subcircuit_bbox[3] - selected_subcircuit_bbox[1]

		self.logger.info("Selection bounding-box: %sx%s", selection_bbox_width, selection_bbox_height)

		user_unit = UserUnits(pcbnew.GetUserUnits())
		length_unit = int({
			UserUnits.INCH: SizeUnits.PER_INCH / 10,
			UserUnits.MILLIMETRE: SizeUnits.PER_MILLIMETRE,
			UserUnits.MIL: SizeUnits.PER_MIL * 100,
		}[user_unit])

		selection_size = (
			length_unit * ceil(1 + 1.2 * selection_bbox_width / length_unit),
			length_unit * ceil(1 + 1.2 * selection_bbox_height / length_unit),
		)

		settings = CloneSettings(
			instances=set(subcircuit_root_sheet_instances),
			placement=ClonePlacementSettings(
				strategy=ClonePlacementStrategyType.RELATIVE,
				relative=ClonePlacementRelativeStrategySettings(
					anchor=selected_footprints[0],
				),
				grid=ClonePlacementGridStrategySettings(
					sort=ClonePlacementGridSort.HIERARCHY,
					flow=ClonePlacementGridFlow.ROW,
					main_interval=selection_size[0],
					cross_interval=selection_size[1],
					length_unit=user_unit,
					wrap=False,
					wrap_at=8,
				),
			)
		)

		settings_controller = CloneSettingsController(logger, board, hierarchy, selection)

		view = CloneSettingsView(
			logger=logger,
			instances=sorted(subcircuit_root_sheet_instances, key=lambda instance: instance.name_path), 
			footprints=sorted(selected_footprints, key=lambda footprint: footprint.reference),
			controller=settings_controller,
			settings=settings,
		)
		view.execute()
