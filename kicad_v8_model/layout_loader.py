import logging
from typing import Dict, List, Type

from ..utils.to_dict_strict import to_dict_strict

from .angle import Angle
from .vector2 import Vector2

from .parser import Parser, FastParser
from .entities import ArcRoute, Footprint, PolygonRoute, Project, StraightRoute, Via
from .entity_path import EntityPath, EntityPathComponent
from .entity_traits import Net
from .board import BoardLayer, Layer
from .selection import Selection


logger = logging.getLogger(__name__)


class BaseLayoutLoader():
	project: Project
	layers: Dict[str, Layer]
	nets: Dict[int, Net]
	footprints: List[Footprint]
	tracks: List[StraightRoute]
	track_arcs: List[ArcRoute]
	zones: List[PolygonRoute]
	vias: List[Via]

	def __init__(self, project: Project):
		self.project = project
		self.layers = {}
		self.nets = {}
		self.footprints = []
		self.tracks = []
		self.track_arcs = []
		self.zones = []
		self.vias = []

	def get_result(self):
		project = self.project
		project.layers = to_dict_strict(self.layers.values(), lambda layer: layer.type)
		project.nets = self.nets
		project.footprints = to_dict_strict(self.footprints, lambda footprint: footprint.id)
		project.tracks = to_dict_strict(self.tracks, lambda route: route.id)
		project.track_arcs = to_dict_strict(self.track_arcs, lambda route: route.id)
		project.zones = to_dict_strict(self.zones, lambda route: route.id)
		project.vias = to_dict_strict(self.vias, lambda via: via.id)


class LayoutLoader(BaseLayoutLoader):

	parser_class: Type[Parser] = FastParser

	@staticmethod
	def load(project: Project, filename: str):
		loader = LayoutLoader(project, filename)
		loader.get_result()

	def __init__(self, project: Project, filename: str):
		super().__init__(project)
		pcb_node = self.parser_class().parse_file(filename).kicad_pcb
		self.read_nets(pcb_node.net)
		self.read_layers(pcb_node.layers)
		self.read_footprints(pcb_node.footprint)
		self.read_tracks(pcb_node.segment)
		self.read_track_arcs(pcb_node.arc)
		self.read_track_zones(pcb_node.zone)
		self.read_vias(pcb_node.via)
		# self.read_graphics(
		# 	pcb_node.gr_text +
		# 	pcb_node.gr_text_box +
		# 	pcb_node.gr_line +
		# 	pcb_node.gr_rect +
		# 	pcb_node.gr_circle +
		# 	pcb_node.gr_arc +
		# 	pcb_node.gr_poly +
		# 	pcb_node.bezier
		# )
		self.get_result()

	def read_nets(self, net_nodes: Selection):
		nets: List[Net] = []
		for net_node in net_nodes:
			net_id = int(net_node[0])
			net_name = net_node[1]
			net = Net(
				number=net_id,
				name=net_name,
			)
			nets.append(net)
		self.nets = to_dict_strict(nets, lambda net: net.number)

	def read_layers(self, layers_node: Selection):
		layers: List[Layer] = []
		layer_map = BoardLayer.id_map()
		for layer in layers_node.children:
			layer_id = int(layer.key)
			layer_name = " ".join(layer.values)  # pyright: ignore
			layer_type = layer_map[layer_id]
			layer = Layer(
				number=layer_id,
				name=layer_name,
				type=layer_type,
			)
			layers.append(layer)
		self.layers = to_dict_strict(layers, lambda layer: layer.type.value)

	def _vector(self, node: Selection, index: int = 0):
		x = int(float(node[index]) * 1e6)
		y = int(float(node[index + 1]) * 1e6)
		return Vector2(
			x=x,
			y=y,
		)

	def _angle(self, node: Selection, index: int = 2):
		angle = float(node.value_by_index(index, "0"))
		return Angle.from_degrees(angle)

	def read_footprints(self, footprint_nodes: Selection):
		project = self.project
		component_instances = {
			unit.path: component_instance
			for component_instance in project.component_instances.values()
			for unit in component_instance.units
		}
		root_sheet_id = project.root_sheet_definition.id
		for footprint_node in footprint_nodes:
			locked = "locked" in footprint_node.values
			layer_name = footprint_node.layer[0]
			footprint_id = EntityPathComponent.parse(footprint_node.uuid[0])
			position = self._vector(footprint_node.at)
			angle = self._angle(footprint_node.at)
			properties = {
				property_node[0]: property_node[1]
				for property_node in footprint_node.property
			}
			symbol_path = root_sheet_id + EntityPath.parse(footprint_node.path[0])
			if footprint_node.attr:
				board_only = "board_only" in footprint_node.attr.values
			else:
				board_only = False
			layer = self.layers[layer_name]
			footprint = Footprint(
				locked=locked,
				board_only=board_only,
				layer=layer,
				id=footprint_id,
				position=position,
				orientation=angle,
				properties=properties,
				symbol_path=symbol_path,
			)
			if not board_only:
				footprint.component = component_instances[symbol_path]
				self.footprints.append(footprint)

	def read_tracks(self, track_nodes: Selection):
		for track_node in track_nodes:
			id = EntityPathComponent.parse(track_node.uuid[0])
			net = self.nets[int(track_node.net[0])]
			start = self._vector(track_node.start)
			end = self._vector(track_node.end)
			layer_name = track_node.layer[0]
			layer = self.layers[layer_name]
			position = start
			track = StraightRoute(
				id=id,
				position=position,
				start=start,
				end=end,
				net=net,
				layer=layer,
			)
			self.tracks.append(track)

	def read_track_arcs(self, track_arc_nodes: Selection):
		for track_arc_node in track_arc_nodes:
			id = EntityPathComponent.parse(track_arc_node.uuid[0])
			net = self.nets[int(track_arc_node.net[0])]
			start = self._vector(track_arc_node.start)
			mid = self._vector(track_arc_node.mid)
			end = self._vector(track_arc_node.end)
			layer_name = track_arc_node.layer[0]
			layer = self.layers[layer_name]
			position = start
			track_arc = ArcRoute(
				id=id,
				position=position,
				start=start,
				mid=mid,
				end=end,
				net=net,
				layer=layer,
			)
			self.track_arcs.append(track_arc)

	def read_track_zones(self, zone_nodes: Selection):
		for zone_node in zone_nodes:
			id = EntityPathComponent.parse(zone_node.uuid[0])
			net = self.nets[int(zone_node.net[0])]
			points = [
				self._vector(point_node)
				for point_node in zone_node.polygon.pts.xy
			]
			layer_name = zone_node.layer[0]
			layer = self.layers[layer_name]
			position = points[0]
			zone = PolygonRoute(
				id=id,
				position=position,
				points=points,
				net=net,
				layer=layer,
			)
			self.zones.append(zone)

	def read_vias(self, via_nodes: Selection):
		for via_node in via_nodes:
			id = EntityPathComponent.parse(via_node.uuid[0])
			net = self.nets[int(via_node.net[0])]
			position = self._vector(via_node.at)
			layer1_name = via_node.layers[0]
			layer2_name = via_node.layers[1]
			layer1 = self.layers[layer1_name]
			layer2 = self.layers[layer2_name]
			via = Via(
				id=id,
				position=position,
				net=net,
				layers=(layer1, layer2),
			)
			self.vias.append(via)
