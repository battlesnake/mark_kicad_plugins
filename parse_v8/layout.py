import logging
from typing import List

from .parser import Parser
from .entities import Footprint, Schematic
from .entity_path import EntityPath, EntityPathComponent
from .selection import Selection


logger = logging.getLogger(__name__)


class BaseLayoutLoader():
	schematic: Schematic
	footprints: List[Footprint]

	def __init__(self, schematic: Schematic):
		self.schematic = schematic
		self.footprints = []

	def get_result(self):
		self.schematic.footprints = {
			footprint.id: footprint
			for footprint in self.footprints
		}


class LayoutLoader(BaseLayoutLoader):

	def __init__(self, schematic: Schematic, filename: str):
		super().__init__(schematic)
		pcb_node = Parser().parse_file(filename)
		self.read_footprints(pcb_node)
		self.get_result()

	def read_footprints(self, pcb_node: Selection):
		node = pcb_node.kicad_pcb
		schematic = self.schematic
		component_instances = {
			unit.path: component_instance
			for component_instance in schematic.component_instances.values()
			for unit in component_instance.units
		}
		for footprint_node in node.footprint:
			locked = "locked" in footprint_node.values
			placement_layer = footprint_node.layer[0]
			footprint_id = EntityPathComponent.parse(footprint_node.tstamp[0])
			placement_x = float(footprint_node.at[0])
			placement_y = float(footprint_node.at[1])
			placement_angle = float(footprint_node.at[2])
			properties = {
				property_node[0]: property_node[1]
				for property_node in footprint_node.property
			}
			symbol_path = EntityPath.parse(footprint_node.path[0])
			if footprint_node.attr:
				board_only = "board_only" in footprint_node.attr.values
			else:
				board_only = False
			footprint = Footprint(
				locked=locked,
				board_only=board_only,
				placement_layer=placement_layer,
				id=footprint_id,
				placement_x=placement_x,
				placement_y=placement_y,
				placement_angle=placement_angle,
				properties=properties,
				symbol_path=symbol_path,
			)
			if not board_only:
				footprint.component = component_instances[symbol_path]
				self.footprints.append(footprint)
