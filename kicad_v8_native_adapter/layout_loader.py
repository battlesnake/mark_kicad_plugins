# Designed with intention that we can eventually totally decouple from Kicad,
# so that future developments can run outside of Kicad, or even use Kicad as a
# lower-layer for higher-level generation automation.
#
# At minimum, have the ability to run the plugins in a separate process from
# Kicad, with a thin "adapter" plugin to provide a socket-based interface.
#

import logging
from typing import List

from pcbnew import BOARD
from pcbnew import PCB_VIA

from ..utils.to_dict_strict import to_dict_strict

from ..kicad_v8_model import Graphic
from ..kicad_v8_model import BoardLayer
from ..kicad_v8_model import Layer
from ..kicad_v8_model import Vector2, Angle, Net, Route, Via
from ..kicad_v8_model import EntityPath, EntityPathComponent
from ..kicad_v8_model import Footprint, Project
from ..kicad_v8_model.layout_loader import BaseLayoutLoader


logger = logging.getLogger(__name__)


class PluginLayoutLoader(BaseLayoutLoader):

	def __init__(self, project: Project, board: BOARD):
		super().__init__(project)
		self.board = board

	@staticmethod
	def load(project: Project, board: BOARD):
		loader = PluginLayoutLoader(project, board)
		loader.read_nets()
		loader.read_layers()
		loader.read_routes()
		loader.read_vias()
		loader.read_footprints()
		loader.read_graphics()
		loader.get_result()

	def read_nets(self):
		board = self.board
		logger.info("Reading nets")
		nets_info = board.GetNetInfo()
		nets_count = nets_info.GetNetCount()
		nets: List[Net] = []
		for net_index in range(0, nets_count):
			net_info = nets_info.GetNetItem(net_index)
			net_id = net_info.GetNetCode()
			net_name = net_info.GetNetname()
			net = Net(
				net_id,
				net_name,
			)
			nets.append(net)
		self.nets = to_dict_strict(nets, lambda net: net.number)

	def read_layers(self):
		board = self.board
		logger.info("Reading layers")
		layers: List[Layer] = []
		layer_map = BoardLayer.id_map()
		for layer_index in range(0, 64):
			layer_name = board.GetLayerName(layer_index)
			if not layer_name:
				continue
			layer_type = layer_map[board.GetLayerType(layer_index)]
			layer = Layer(
				number=layer_index,
				name=layer_name,
				type=layer_type,
			)
			layers.append(layer)
		self.layers = to_dict_strict(layers, lambda layer: layer.type.value)

	def read_routes(self):
		# segment, zone, arc
		board = self.board
		logger.info("Reading routes")
		layer_map = to_dict_strict(self.layers.values(), lambda layer: layer.number)
		for track in board.GetTracks():
			if isinstance(track, PCB_VIA):
				continue
			id = EntityPathComponent.parse(str(track.m_Uuid))
			net = self.nets[track.GetNetCode()]
			layer_id = track.GetLayer()
			layer = layer_map[layer_id]
			route = Route(
				id=id,
				net=net,
				layer=layer,
			)
			self.routes.append(route)
		for zone in board.Zones():
			id = EntityPathComponent.parse(str(zone.m_Uuid))
			net = self.nets[zone.GetNetCode()]
			layer_id = zone.GetFirstLayer()  # Zones support multiple layers now!  TODO
			layer = layer_map[layer_id]
			route = Route(
				id=id,
				net=net,
				layer=layer,
			)
			self.routes.append(route)

	def read_vias(self):
		board = self.board
		logger.info("Reading vias")
		layer_map = to_dict_strict(self.layers.values(), lambda layer: layer.number)
		for track in board.GetTracks():
			if not isinstance(track, PCB_VIA):
				continue
			id = EntityPathComponent.parse(str(track.m_Uuid))
			net = self.nets[track.GetNetCode()]
			layer1_id = track.TopLayer()
			layer2_id = track.BottomLayer()
			layer1 = layer_map[layer1_id]
			layer2 = layer_map[layer2_id]
			via = Via(
				id=id,
				net=net,
				layers=(layer1, layer2),
			)
			self.vias.append(via)

	def read_footprints(self):
		board = self.board
		logger.info("Reading footprints")
		layer_map = to_dict_strict(self.layers.values(), lambda layer: layer.number)
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
				layer=layer_map[pcbnew_footprint.GetLayer()],
				id=EntityPathComponent.parse(pcbnew_footprint.GetFPIDAsString()),
				position=Vector2(position.x, position.y),
				orientation=Angle.from_degrees(angle),
				properties={
					key: value
					for key, value in pcbnew_footprint.GetProperties()
				},
				symbol_path=EntityPath.parse(pcbnew_footprint.GetPath().AsString()),
			)
			footprint.component = component_instance
			self.footprints.append(footprint)

	def read_graphics(self):
		board = self.board
		logger.info("Reading footprints")
		layer_map = to_dict_strict(self.layers.values(), lambda layer: layer.number)
		for pcbnew_graphic in board.Drawings():
			graphic_id = EntityPathComponent.parse(str(pcbnew_graphic.m_Uuid))
			layer_id = pcbnew_graphic.GetLayer()
			layer = layer_map[layer_id]
			graphic = Graphic(
				id=graphic_id,
				layer=layer,
			)
			self.graphics.append(graphic)
