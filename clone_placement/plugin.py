from pathlib import Path
from typing import List, TypeVar, Iterable, final
from functools import reduce
from math import ceil

from pcbnew import GetUserUnits, BOARD_ITEM

from ..utils.kicad_units import UserUnits, SizeUnits
from ..utils.user_exception import UserException

from ..parse_v8 import SheetInstance, Footprint, EntityPath, SchematicLoader, Schematic

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
from .spath import Spath

ItemType = TypeVar("ItemType", bound=BOARD_ITEM)


@final
class ClonePlugin(Plugin):

	schematic: Schematic

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
		assert footprint_sheet_paths, "No footprints provided"
		common_prefix = reduce(EntityPath.__and__, footprint_sheet_paths)
		assert common_prefix, "No valid common ancestor of provided footprints/symbol-units"
		return self.schematic.sheet_instances[common_prefix]

	def execute(self) -> None:
		logger = self.logger
		board = self.board

		try:
			board_file = board.GetFileName()
			logger.info("Board path: %s", board_file)
			schematic_file = str(Path(board_file).with_suffix(".kicad_sch"))
			logger.info("Assumed schematic path: %s", schematic_file)
			schematic = SchematicLoader.load(schematic_file, board)
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
			schematic.footprints[EntityPath.parse(footprint.GetPath())]
			for footprint in selection.source_footprints
		]
		if not selected_footprints:
			logger.error("No footprints selected")
			raise UserException("No footprints in selection")

		selected_units = [
			unit
			for footprint in selected_footprints
			for unit in footprint.component_instance.units
		]
		logger.info("Total selected footprints: %d", len(selected_footprints))
		logger.info("Total selected units: %d", len(selected_units))

		selected_unit_sheet_paths = [
			Spath.create(unit.sheet, schematic.root_sheet_instance)
			for unit in selected_units
		]

		selected_prefix = reduce(Spath.__and__, selected_unit_sheet_paths)
		logger.info("Selection prefix: %s", selected_prefix)
		assert len(selected_prefix) > 0

		selected_unit_relative_paths = [
			path[len(selected_prefix):]
			for path in selected_unit_sheet_paths
		]
		logger.info("Paths to selected footprints, relative to selection prefix:")
		for path in sorted(set(selected_unit_relative_paths)):
			logger.info(" * %s", path)

		selected_footprints_common_ancestor = self.get_common_ancestor_of_footprints(selected_footprints)
		self.logger.info("Common ancestor sheet of all selected footprints: %s", selected_footprints_common_ancestor)

		reference_footprint = selected_footprints[0]
		logger.info("Taking %s to be reference footprint for now", reference_footprint.component_instance.reference)

		reference_unit = reference_footprint.component_instance.units[0]
		logger.info("Reference instance of symbol-unit: %s", reference_unit.reference)

		sibling_unit_paths = [
			Spath.create(unit.sheet, schematic.root_sheet_instance)
			for unit in reference_unit.definition.instances
		]
		assert len(set(sibling_unit_paths)) == len(sibling_unit_paths)

		sibling_unit_base_paths = [
			path[0:len(selected_prefix)]
			for path in sibling_unit_paths
		]
		assert selected_prefix in sibling_unit_base_paths
		logger.info("Sibling unit base paths:")
		for path in sorted(set(sibling_unit_base_paths)):
			logger.info(" * %s", path)

		sibling_groups = [
			[
				(base_path + relative_path).resolve(root=schematic.root_sheet_instance)
				for relative_path in selected_unit_relative_paths
			]
			for base_path in sibling_unit_base_paths
			if base_path != selected_prefix
		]

		reference_sibling_footprints = [
			instance.component.footprint
			for instance in reference_unit.definition.instances
			if instance != reference_unit
		]
		logger.info("Sibling footprints:")
		for footprint in reference_sibling_footprints:
			logger.info(" * %s", footprint.component_instance.reference)

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
			instances=set(peer_sheet_instances),
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
				peer_sheet_instances,
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
