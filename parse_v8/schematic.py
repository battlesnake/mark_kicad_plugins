from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, TypeVar

from ..utils.common_value import common_value
from ..utils.multi_map import MultiMap

from .entities import (
	ComponentReference,
	Schematic,
	SheetDefinition,
	SheetInstance,
	SymbolDefinition,
	SymbolInstance,
	ComponentDefinition,
	ComponentInstance,
	SymbolReference,
)

from .entity_path import EntityPath, EntityPathComponent
from .node import Node
from .selection import Selection
from .parser import Parser


logger = logging.getLogger(__name__)


@dataclass
class SheetMetadata():
	node: Node
	filename: str
	instances: List["SheetInstanceMetadata"]


@dataclass
class SymbolMetadata():
	node: Node
	instances: List["SymbolInstanceMetadata"]


@dataclass
class SheetInstanceMetadata():
	""" Intermediate data to help with loading stuff """
	node: Node
	id: EntityPathComponent
	path: EntityPath
	page: str
	name: str
	filename: str


@dataclass
class SymbolInstanceMetadata():
	""" Intermediate data to help with loading stuff """
	node: Node
	path: EntityPath
	designator: str
	unit: int


@dataclass
class ComponentDefinitionMetadata():
	""" Intermediate data to help with loading stuff """
	node: Node


@dataclass
class ComponentInstanceMetadata():
	""" Intermediate data to help with loading stuff """
	symbol_instance: SymbolInstance


# Schematic loader


class SchematicLoader():
	schematic: Schematic
	filename: str
	project: str
	schematic_loader: Callable[[str], Selection]

	# use filename instead of id, there is significant risk of copy/paste
	# hierarchical sheets causing UUID clashes
	sheet_metadata: Dict[str, SheetMetadata]
	symbol_metadata: Dict[EntityPathComponent, SymbolMetadata]
	component_definition_metadata: Dict[EntityPathComponent, ComponentDefinitionMetadata]
	component_instance_metadata: Dict[EntityPath, ComponentInstanceMetadata]

	sheet_definitions: List[SheetDefinition]
	sheet_instances: List[SheetInstance]
	symbol_definitions: List[SymbolDefinition]
	symbol_instances: List[SymbolInstance]
	component_definitions: List[ComponentDefinition]
	component_instances: List[ComponentInstance]

	root_sheet_definition: SheetDefinition
	root_sheet_instance: SheetInstance

	@staticmethod
	def load(schematic: Schematic, filename: str):
		schematic_loader = SchematicLoader(schematic, filename)
		schematic_loader.read_schematic()
		schematic_loader.get_result()

	def __init__(self, schematic: Schematic, filename: str, schematic_loader: Optional[Callable[[str], Selection]] = None):
		self.schematic = schematic
		if schematic_loader is None:
			schematic_loader = Parser().parse_file
		self.filename = os.path.join(os.path.curdir, filename)
		self.project = Path(filename).stem
		self.schematic_loader = schematic_loader
		self.sheet_metadata = {}
		self.symbol_metadata = {}
		self.component_definition_metadata = {}
		self.component_instance_metadata = {}
		self.sheet_definitions = []
		self.sheet_instances = []
		self.symbol_definitions = []
		self.symbol_instances = []
		self.component_definitions = []
		self.component_instances = []

	def read_schematic(self):
		self.read_sheet_definitions()
		self.read_sheet_instances()
		self.read_symbol_definitions()
		self.read_symbol_instances()
		self.read_component_definitions()
		self.read_component_instances()

	def get_result(self):

		Key = TypeVar("Key")
		Value = TypeVar("Value")

		def to_dict(items: Sequence[Value], key_func: Callable[[Value], Key]) -> Dict[Key, Value]:
			result: Dict[Key, Value] = {}
			for item in items:
				key = key_func(item)
				if key in result:
					raise KeyError("Duplicate key", key, type(key), type(item), repr(result[key]), repr(item))
				result[key] = item
			return result

		schematic = self.schematic
		schematic.sheet_definitions = to_dict(self.sheet_definitions, lambda item: item.filename)
		schematic.sheet_instances = to_dict(self.sheet_instances, lambda item: item.path)
		schematic.symbol_definitions = to_dict(self.symbol_definitions, lambda item: item.id)
		schematic.symbol_instances = to_dict(self.symbol_instances, lambda item: item.path)
		schematic.component_definitions = self.component_definitions
		schematic.component_instances = to_dict(self.component_instances, lambda item: item.reference.designator)
		schematic.root_sheet_definition = self.root_sheet_definition
		schematic.root_sheet_instance = self.root_sheet_instance

	def read_sheet_definitions(self):
		logger.info("Reading sheet definition")

		def read_sheet_definition(filename: str):
			if already_loaded := next(
				(
					item
					for item in self.sheet_definitions
					if item.filename == filename
				),
				None
			):
				return already_loaded
			logger.info("Reading schematic: %s", filename)
			node = self.schematic_loader(filename).kicad_sch
			sheet_id = EntityPathComponent.parse(node.uuid[0])
			version = node.version[0]
			sheet_definition = SheetDefinition(
				id=sheet_id,
				version=version,
				filename=filename,
				symbols=[],
				instances=[],
			)
			sheet_instances = [
				SheetInstanceMetadata(
					node=~node,
					id=EntityPathComponent.parse(inner_sheet_node.uuid[0]),
					path=EntityPath.parse(inner_path_node[0]) + EntityPathComponent.parse(inner_sheet_node.uuid[0]),
					page=inner_path_node.page[0],
					name=inner_sheet_node.property.filter(0, "Sheetname")[1],
					filename=os.path.join(
						os.path.dirname(filename),
						inner_sheet_node.property.filter(0, "Sheetfile")[1],
					),
				)
				for inner_sheet_node in node.sheet
				for inner_path_node in inner_sheet_node.instances.project.filter(0, self.project).path
			]
			self.sheet_definitions.append(sheet_definition)
			self.sheet_metadata[filename] = SheetMetadata(
				node=~node,
				filename=filename,
				instances=sheet_instances,
			)
			for sheet_instance in sheet_instances:
				read_sheet_definition(sheet_instance.filename)
			return sheet_definition

		self.root_sheet_definition = read_sheet_definition(self.filename)

	def read_sheet_instances(self):
		logger.info("Reading sheet instances")
		root_path = EntityPath([self.root_sheet_definition.id])
		logger.info("Reading sheet instance: %s / %s", self.project, root_path)
		root_sheet_definition_node = Selection([self.sheet_metadata[self.root_sheet_definition.filename].node])
		self.root_sheet_instance = SheetInstance(
			definition=self.root_sheet_definition,
			path=root_path,
			name=self.project,
			page=root_sheet_definition_node.sheet_instances.path.page[0],
			parent=None,
			children=[],
			symbols=[],
		)
		self.sheet_instances.append(self.root_sheet_instance)

		def instantiante_inner_sheets(parent: SheetInstance):
			for metadata in self.sheet_metadata[parent.definition.filename].instances:
				if not metadata.path.startswith(parent.path):
					continue
				logger.info("Reading sheet instance: %s / %s", metadata.name, metadata.path)
				definition = next(
					item
					for item in self.sheet_definitions
					if item.filename == metadata.filename
				)
				sheet_instance = SheetInstance(
					definition=definition,
					path=metadata.path,
					name=metadata.name,
					page=metadata.page,
					parent=parent,
					children=[],
					symbols=[],
				)
				self.sheet_instances.append(sheet_instance)
				parent.children.append(sheet_instance)
				definition.instances.append(sheet_instance)
				instantiante_inner_sheets(sheet_instance)

		instantiante_inner_sheets(self.root_sheet_instance)

	def read_symbol_definitions(self):
		logger.info("Reading symbol definitions")
		for sheet_definition in self.sheet_definitions:
			sheet_node = Selection([self.sheet_metadata[sheet_definition.filename].node])
			for symbol_node in sheet_node.symbol:
				symbol_id = EntityPathComponent.parse(symbol_node.uuid[0])
				symbol_library_id = symbol_node.lib_id[0]
				designator = symbol_node.property.filter(0, "Reference")[1]
				value = symbol_node.property.filter(0, "Value")[1]
				unit = int(symbol_node.unit[0])
				logger.info("Reading symbol definition: %s / %s / %s", symbol_id, symbol_library_id, value)
				library_info = sheet_node.lib_symbols.symbol.filter(0, symbol_library_id)
				multi_unit = len([
					...
					for symbol in library_info.symbol
					for unit in symbol[0].split("_")[-2]
					if unit != "0"
				]) > 1
				symbol_definition = SymbolDefinition(
					sheet=sheet_definition,
					id=symbol_id,
					reference=SymbolReference(
						designator=designator,
						unit=unit,
						multi_unit=multi_unit,
					),
					instances=[],
				)
				self.symbol_definitions.append(symbol_definition)
				sheet_definition.symbols.append(symbol_definition)
				assert symbol_id not in self.symbol_metadata
				self.symbol_metadata[symbol_definition.id] = SymbolMetadata(
					node=~symbol_node,
					instances=[
						SymbolInstanceMetadata(
							node=~symbol_node,
							path=EntityPath.parse(path_node[0]) + symbol_id,
							designator=path_node.reference[0],
							unit=int(path_node.unit[0]),
						)
						for path_node in symbol_node.instances.project.filter(0, self.project).path
					],
				)
				self.component_definition_metadata[symbol_definition.id] = ComponentDefinitionMetadata(
					node=~symbol_node,
				)

	def read_symbol_instances(self):
		logger.info("Reading symbol instances")
		sheet_map = {
			item.path: item
			for item in self.sheet_instances
		}
		for symbol_definition in self.symbol_definitions:
			metadata = self.symbol_metadata[symbol_definition.id]
			for symbol_instance_metadata in metadata.instances:
				symbol_reference = SymbolReference(
					designator=symbol_instance_metadata.designator,
					unit=symbol_instance_metadata.unit,
					multi_unit=symbol_definition.reference.multi_unit,
				)
				logger.info("Reading symbol instance: %s", symbol_reference)
				sheet_instance = sheet_map[symbol_instance_metadata.path[:-1]]
				symbol_instance = SymbolInstance(
					definition=symbol_definition,
					path=symbol_instance_metadata.path,
					reference=symbol_reference,
					sheet=sheet_instance,
				)
				self.component_instance_metadata[symbol_instance_metadata.path] = ComponentInstanceMetadata(
					symbol_instance=symbol_instance,
				)
				self.symbol_instances.append(symbol_instance)
				sheet_instance.symbols.append(symbol_instance)
				symbol_definition.instances.append(symbol_instance)

	def read_component_definitions(self):
		for units in MultiMap.groupby(
			self.symbol_definitions,
			lambda symbol_definition: symbol_definition.reference.designator,
		).groups():
			nodes = [
				Selection([self.component_definition_metadata[unit.id].node])
				for unit in units
			]
			symbol_library_id = common_value(nodes, lambda node: node.lib_id[0])
			in_bom = common_value(nodes, lambda node: node.in_bom[0] == "yes")
			on_board = common_value(nodes, lambda node: node.on_board[0] == "yes")
			dnp = common_value(nodes, lambda node: node.dnp[0] == "yes")
			value = common_value(nodes, lambda node: node.property.filter(0, "Value")[0])
			properties = {
				name: common_value(nodes, lambda node: node.property.filter(0, name)[1])
				for name in (
					property_node[0]
					for property_node in nodes[0].property
				)
			}
			component_definition = ComponentDefinition(
				units=list(units),
				properties=properties,
				symbol_library_id=symbol_library_id,
				in_bom=in_bom,
				on_board=on_board,
				dnp=dnp,
				value=value,
				instances=[],
			)
			self.component_definitions.append(component_definition)
			for unit in units:
				unit.component = component_definition

	def read_component_instances(self):
		for units in MultiMap.groupby(self.symbol_instances, lambda symbol_instance: symbol_instance.reference.designator).groups():
			component_definition = common_value(units, lambda unit: unit.definition.component)
			designator = next(iter(units)).reference.designator  # Same for all since it was the groupby key
			reference = ComponentReference(
				designator=designator,
			)
			component_instance = ComponentInstance(
				units=list(units),
				definition=component_definition,
				reference=reference,
			)
			self.component_instances.append(component_instance)
			component_definition.instances.append(component_instance)
			for unit in units:
				unit.component = component_instance
