# Designed with intention that we can eventually totally decouple from Kicad,
# so that future developments can run outside of Kicad, or even use Kicad as a
# lower-layer for higher-level generation automation.
#
# At minimum, have the ability to run the plugins in a separate process from
# Kicad, with a thin "adapter" plugin to provide a socket-based interface.
#

import logging

from pcbnew import BOARD

from ..kicad_v8_model.entity_path import EntityPath, EntityPathComponent
from ..kicad_v8_model.entities import Footprint, Project
from ..kicad_v8_model.layout_loader import BaseLayoutLoader


logger = logging.getLogger(__name__)


class PluginLayoutLoader(BaseLayoutLoader):

	@staticmethod
	def load(project: Project, board: BOARD):
		loader = PluginLayoutLoader(project)
		loader.read_footprints(board)
		loader.get_result()

	def read_footprints(self, board: BOARD):
		logger.info("Reading footprints")
		schematic = self.project
		for pcbnew_footprint in board.Footprints():
			reference = pcbnew_footprint.GetReference()
			logger.info("Reading footprint %", reference)
			component_instance = schematic.component_instances[reference]
			position = pcbnew_footprint.GetPosition()
			angle = pcbnew_footprint.GetOrientationDegrees()
			footprint = Footprint(
				locked=pcbnew_footprint.IsLocked(),
				board_only=pcbnew_footprint.IsBoardOnly(),
				placement_layer=pcbnew_footprint.GetLayerName(),
				id=EntityPathComponent.parse(pcbnew_footprint.GetFPIDAsString()),
				placement_x=position.x,
				placement_y=position.y,
				placement_angle=angle,
				properties={
					key: value
					for key, value in pcbnew_footprint.GetProperties()
				},
				symbol_path=EntityPath.parse(pcbnew_footprint.GetPath().AsString()),
			)
			footprint.component = component_instance
			self.footprints.append(footprint)
