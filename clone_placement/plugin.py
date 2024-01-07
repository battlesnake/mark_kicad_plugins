from pathlib import Path
from typing import List, Set, TypeVar, Iterable, final
from functools import reduce
from math import ceil

from pcbnew import GetUserUnits, BOARD_ITEM

from ..utils.kicad_units import UserUnits, SizeUnits
from ..utils.user_exception import UserException

from ..parse_v8 import EntityPath, SchematicLoader, Schematic

from ..plugin import Plugin

from .context import CloneContext, TargetFootprint
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


T = TypeVar("T")


def unique_list(items: Iterable[T]) -> List[T]:
	result: List[T] = []
	have_already: Set[T] = set()
	for item in items:
		if item in have_already:
			continue
		result.append(item)
		have_already.add(item)
	return result


@final
class ClonePlugin(Plugin):

	"""
	Given sheet definitions: a, b, c, d, e

	Where the hierarchy is: a>b>2(c>d>2(e))

	i.e. the instances are:
		a
		a.b
		a.b.c[0]
		a.b.c[0].d.e[0]
		a.b.c[0].d.e[1]
		a.b.c[1]
		a.b.c[1].d.e[0]
		a.b.c[1].d.e[1]

	And the relevant symbols in each sheet are:
		e[0]: sa sb ta
		e[1]: sc
		d: sd

	And all of those symbols from sheets under c[0] are selected

	The following prefixes exist:

		Selection common prefix:
			a.b.c[0].d

		All instances common prefix:
			a.b

		Instance prefixes:
			a.b.c[0].d
			a.b.c[1].d

		Relative symbol paths:
			e[0].s[0]
			e[0].s[1]
			e[0].t[0]
			s[1].s[0]
			s[0]

		Mappings from source to target(s):
			sa: a.b.c[1].d.e[0].s[0]
			sb: a.b.c[1].d.e[0].s[1]
			ta: a.b.c[1].d.e[0].t[0]
			sc: a.b.c[1].d.e[1].s[0]
			sd: a.b.c[1].d.s[0]
	"""

	schematic: Schematic

	@staticmethod
	def filter_selected(items: Iterable[ItemType]) -> List[ItemType]:
		return [
			item
			for item in items
			if item.IsSelected()
		]

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

		logger.info("Selected footprints (%d):", len(selected_footprints))
		for footprint in selected_footprints:
			logger.info(" * %s", footprint.component_instance.reference)

		selected_symbol_spaths = set(
			Spath.create(unit.sheet, schematic.root_sheet_instance)
			for footprint in selected_footprints
			for unit in footprint.component_instance.units
		)
		logger.info("Selected symbol spaths:")
		for spath in selected_symbol_spaths:
			logger.info(" * %s", spath)

		selected_symbols_base_spath = reduce(Spath.__and__, selected_symbol_spaths).without_symbol()
		logger.info("Selection prefix spath: %s", selected_symbols_base_spath)
		assert len(selected_symbols_base_spath) > 0

		source_sheet = selected_symbols_base_spath.resolve_sheet(schematic.root_sheet_instance)

		selected_symbols_relative_spaths = [
			path[len(selected_symbols_base_spath):]
			for path in selected_symbol_spaths
		]
		logger.info("Paths to selected footprints, relative to selection prefix:")
		for spath in selected_symbols_relative_spaths:
			logger.info(" * %s", spath)

		reference_symbol_instances = selected_footprints[0].component_instance.units[0].definition.instances

		reference_symbol_instances_spaths = [
			Spath.create(symbol, schematic.root_sheet_instance)
			for symbol in reference_symbol_instances
		]

		instances_prefix_spaths = [
			instance_spath[0:len(selected_symbols_base_spath)]
			for instance_spath in reference_symbol_instances_spaths
		]

		footprint_mapping = {
			source_footprint: [
				TargetFootprint(
					base_sheet=instance_prefix_spath.resolve_sheet(schematic.root_sheet_instance),
					footprint=target_spath.resolve_symbol(schematic.root_sheet_instance).component.footprint
				)
				for instance_prefix_spath in instances_prefix_spaths
				for target_spath in (
					(
						instance_prefix_spath + source_spath[len(selected_symbols_base_spath):]
					),
				)
			]
			for source_footprint in selected_footprints
			for source_spath in (
				Spath.create(
					source_footprint.component_instance.units[0],
					schematic.root_sheet_instance
				),
			)
		}

		logger.info("Footprint mappings:")
		for source, targets in footprint_mapping.items():
			logger.info(" * %s", source.component_instance.reference)
			for target in targets:
				logger.info("    - %s", target.footprint.component_instance.reference)

		base_sheets = [
			instance_prefix_spath.resolve_sheet(schematic.root_sheet_instance)
			for instance_prefix_spath in instances_prefix_spaths
			if instance_prefix_spath != selected_symbols_base_spath
		]

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
			instances=set(base_sheets),
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

		context = CloneContext(
			schematic=schematic,
			selection=selection,
			settings=settings,
			selected_footprints=selected_footprints,
			source_sheet=source_sheet,
			footprint_mapping=footprint_mapping,
		)

		settings_controller = CloneSettingsController(
			logger=logger,
			board=board,
			context=context,
		)

		view = CloneSettingsView(
			logger=logger,
			context=context,
			controller=settings_controller,
		)
		view.execute()
