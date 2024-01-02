from pathlib import Path
from typing import List, TypeVar, Iterable, final
from functools import reduce
from math import ceil

from pcbnew import GetUserUnits, BOARD_ITEM

from ..utils.kicad_units import UserUnits, SizeUnits
from ..utils.user_exception import UserException

from ..parse_v8 import SheetInstance, Footprint, EntityPath, SchematicLoader, Schematic, Layout, LayoutLoader

from ..plugin import Plugin

from .service import CloneSelection
from .settings_controller import CloneSettingsController
from .settings_view import CloneSettingsView
from .settings import CloneSettings
from .placement_settings import (
	ClonePlacementGridFlow,
	ClonePlacementGridSort,
	ClonePlacementGridStrategySettings,
	ClonePlacementRelativeStrategySettings,
	ClonePlacementSettings,
	ClonePlacementStrategyType,
)

ItemType = TypeVar("ItemType", bound=BOARD_ITEM)


@final
class ClonePlugin(Plugin):

	schematic: Schematic
	layout: Layout

	@staticmethod
	def filter_selected(items: Iterable[ItemType]) -> List[ItemType]:
		return [
			item
			for item in items
			if item.IsSelected()
		]

	def get_common_ancestor_of_footprints(self, footprints: Iterable[Footprint]) -> SheetInstance:
		footprint_sheet_paths = [
			symbol_instance.sheet.path
			for footprint in footprints
			for symbol_instance in footprint.component_instance.units
		]
		assert footprint_sheet_paths
		common_prefix: EntityPath = footprint_sheet_paths[0]
		for path in footprint_sheet_paths:
			common_prefix = common_prefix & path
		return self.schematic.sheet_instances[common_prefix]

	def get_selected_footprints(self) -> List[Footprint]:
		return [
			self.layout.footprints[EntityPath.parse(footprint.GetPath())]
			for footprint in self.filter_selected(self.board.Footprints())
		]

	def execute(self) -> None:
		logger = self.logger
		board = self.board

		try:
			board_file = board.GetFileName()
			logger.info("Board path: %s", board_file)
			schematic_file = str(Path(board_file).with_suffix(".kicad_sch"))
			logger.info("Assumed schematic path: %s", schematic_file)
			schematic = SchematicLoader.load(schematic_file)
			layout = LayoutLoader.load(board, schematic)
		except Exception as error:
			raise UserException("Failed to parse board / schematic structure") from error
		self.schematic = schematic

		selection = CloneSelection(
			source_footprints=self.filter_selected(board.Footprints()),
			source_tracks=self.filter_selected(board.Tracks()),
			source_drawings=self.filter_selected(board.Drawings()),
			source_zones=self.filter_selected(board.Zones()),
		)

		selected_footprints = [
			layout.footprints[EntityPath.parse(footprint.GetPath())]
			for footprint in selection.source_footprints
		]
		if not selected_footprints:
			logger.error("No footprints selected")
			raise UserException("No footprints in selection")

		selected_footprints_common_ancestor = self.get_common_ancestor_of_footprints(selected_footprints)
		self.logger.info("Common ancestor sheet of all selected footprints: %s", selected_footprints_common_ancestor)

		reference_footprint = selected_footprints[0]
		reference_symbols = reference_footprint.component_instance.units
		if len(reference_symbols) > 1:
			raise UserException("Reference footprint has corresponding multiple schematic units, this is currently not supported")
		reference_sheets = [
			symbol.sheet
			for symbol in reference_symbols
		]
		if len(reference_sheets) > 1:
			raise UserException("Reference symbol is spread over several sheets, this currently is not supported")
		reference_symbol = reference_symbols[0]
		reference_sheet = reference_sheets[0]

		self.logger.info("Reference footprint: %s", reference_footprint.component_instance)
		self.logger.info("Reference footprint's symbol's sheet instance: %s", reference_sheet)

		common_ancestor_up_levels = len(reference_sheet.path) - len(selected_footprints_common_ancestor.path)

		self.logger.info("Levels from reference footprint's sheet instance to common ancestor of all selected footprints: %s", common_ancestor_up_levels)

		peer_symbols = reference_symbol.definition.instances

		self.logger.info("Peer footprints: %s", ", ".join(str(symbol.reference) for symbol in peer_symbols))

		relevant_sheet_instances = [
			peer_symbol.sheet
			for peer_symbol in peer_symbols
		]

		for instance in relevant_sheet_instances:
			self.logger.debug("Peer sheet instances: %s", instance)

		subcircuit_root_sheet_instances = set(
			schematic.sheet_instances[
				sheet.path[0:len(sheet.path) - common_ancestor_up_levels]
			]
			for sheet in relevant_sheet_instances
		)

		for sheet_instance in subcircuit_root_sheet_instances:
			self.logger.info("Sheet instance we can clone to: %s", sheet_instance)

		selected_footprint_bboxes = [
			footprint.pcbnew_footprint.GetBoundingBox(True, True)
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

		user_unit = UserUnits(GetUserUnits())
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

		settings_controller = CloneSettingsController(logger, board, schematic, selection)

		view = CloneSettingsView(
			logger=logger,
			instances=sorted(
				subcircuit_root_sheet_instances,
				key=lambda instance: instance.path,
			),
			footprints=sorted(
				selected_footprints,
				key=lambda footprint: footprint.component_instance.reference,
			),
			controller=settings_controller,
			settings=settings,
		)
		view.execute()
