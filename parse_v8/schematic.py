"""
This has grown from a basic schematic relations parser to include board stuff
too, perhaps rename from Schematic to Project?
"""

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import re
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from .pcbnew_imports import FOOTPRINT, BOARD

from ..utils.common_value import common_value
from ..utils.multi_map import MultiMap

from .entity_path import EntityPath, EntityPathComponent
from .node import Node
from .selection import Selection
from .parser import Parser


logger = logging.getLogger(__name__)


# User-friendly symbol / component references


COMPONENT_REFERENCE_VALIDATOR = re.compile(r"^(#?[A-Z]+)([0-9]+)$")


@dataclass(frozen=True, eq=True)
class ComponentReference():
	""" Reference for one physical component (i.e. all units) """

	designator: str

	def __post_init__(self):
		if not COMPONENT_REFERENCE_VALIDATOR.match(self.designator):
			raise ValueError("Invalid component reference", self.designator)

	def __str__(self):
		return self.designator

	@property
	def type(self):
		match = COMPONENT_REFERENCE_VALIDATOR.match(self.designator)
		assert match is not None
		return match.group(1)

	@property
	def number(self):
		match = COMPONENT_REFERENCE_VALIDATOR.match(self.designator)
		assert match is not None
		return int(match.group(2))

	@property
	def _sort_key(self) -> Tuple[str, int, int]:
		return (self.type, self.number, 0)

	def __gt__(self, other: "ComponentReference") -> bool:
		return self._sort_key > other._sort_key

	def __lt__(self, other: "ComponentReference") -> bool:
		return not (self > other)


@dataclass(frozen=True, eq=True)
class SymbolReference(ComponentReference):
	""" Reference for a logical symbol (i.e. one unit of a physical component) """

	unit: int
	multi_unit: bool

	def __str__(self):
		if not self.multi_unit:
			return self.designator
		unit = self.unit
		unit -= 1
		parts: List[str] = []
		while unit > 0 or not parts:
			parts += [chr(ord("A") + unit % 26)]
			unit //= 26
		return self.designator + "".join(reversed(parts))

	@property
	def _sort_key(self):
		return (self.type, self.number, self.unit)


@dataclass
class SheetDefinition():
	""" Maps to one sheet file i.e. a kicad_sch """
	id: EntityPathComponent = field(compare=True, hash=True)
	version: str
	filename: str
	symbols: List["SymbolDefinition"] = field(repr=False)
	instances: List["SheetInstance"]


@dataclass
class SheetInstance():
	""" Maps to an instance of a sheet within the sheet-hierarchy """
	definition: SheetDefinition
	path: EntityPath = field(compare=True, hash=True)
	name: str
	page: str
	parent: Optional["SheetInstance"] = field(repr=False)
	children: List["SheetInstance"] = field(repr=False)
	symbols: List["SymbolInstance"] = field(repr=False)


@dataclass
class SymbolDefinition():
	""" Maps to a symbol node in a sheet file """
	sheet: SheetDefinition
	id: EntityPathComponent
	reference: SymbolReference  # Reference in own sheet file, not in schematic/layout
	instances: List["SymbolInstance"] = field(repr=False)
	component: "ComponentDefinition" = field(init=False, repr=False)

	def __hash__(self):
		return hash(self.id)


@dataclass
class SymbolInstance():
	""" Maps to a symbol in an instance of a sheet in the sheet-hierarchy """
	sheet: SheetInstance
	definition: SymbolDefinition
	path: EntityPath
	reference: SymbolReference
	component: "ComponentInstance" = field(init=False, repr=False)

	def __hash__(self):
		return hash(self.path)


@dataclass
class Footprint():
	path: EntityPath
	pcbnew_footprint: FOOTPRINT
	component_instance: "ComponentInstance"


@dataclass
class ComponentDefinition():
	value: str
	units: List[SymbolDefinition] = field(repr=False)
	properties: Dict[str, str]
	library_id: str
	in_bom: bool
	on_board: bool
	dnp: bool
	instances: List["ComponentInstance"] = field(repr=False)

	def __hash__(self):
		return id(self)


@dataclass
class ComponentInstance():
	""" Maps to a physical component i.e. a footprint on the PCB """
	""" (or in some cases, virtual components e.g. for power symbols) """
	definition: ComponentDefinition
	reference: ComponentReference
	units: List[SymbolInstance] = field(repr=False)
	footprint: Footprint = field(init=False)

	def __hash__(self):
		return hash(self.reference)


# Internal metadata classes to store temporary info and relations while reading


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


# Schematic scope


SchematicEntity = Union[SheetInstance, SymbolInstance, ComponentInstance]
SchematicEntityType = Type[SchematicEntity]


@dataclass
class Schematic():
	sheet_definitions: Dict[str, SheetDefinition]
	sheet_instances: Dict[EntityPath, SheetInstance]
	symbol_definitions: Dict[EntityPathComponent, SymbolDefinition]
	symbol_instances: Dict[EntityPath, SymbolInstance]
	component_definitions: List[ComponentDefinition]
	component_instances: Dict[str, ComponentInstance]
	footprints: Dict[EntityPath, Footprint]


# Schematic loader


class SchematicLoader():
	filename: str
	project: str
	schematic_loader: Callable[[str], Selection]

	# use filename, there is significant risk of copy/paste hierarchical sheets
	# causing UUID clashes
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
	footprints: List[Footprint]

	root_sheet_definition: SheetDefinition
	root_sheet_instance: SheetInstance

	@staticmethod
	def load(filename: str, board: Optional[BOARD] = None):
		sheet_loader = Parser().parse_file
		schematic_loader = SchematicLoader(filename, sheet_loader)
		schematic_loader.read_schematic()
		if board is not None:
			schematic_loader.read_footprints(board)
		return schematic_loader.get_result()

	def __init__(self, filename: str, schematic_loader: Callable[[str], Selection]):
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
		self.footprints = []

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

		return Schematic(
			sheet_definitions=to_dict(self.sheet_definitions, lambda item: item.filename),
			sheet_instances=to_dict(self.sheet_instances, lambda item: item.path),
			symbol_definitions=to_dict(self.symbol_definitions, lambda item: item.id),
			symbol_instances=to_dict(self.symbol_instances, lambda item: item.path),
			component_definitions=self.component_definitions,
			component_instances=to_dict(self.component_instances, lambda item: item.reference.designator),
			footprints=to_dict(self.footprints, lambda footprint: footprint.path),
		)

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
				library_id = symbol_node.lib_id[0]
				designator = symbol_node.property.filter(0, "Reference")[1]
				value = symbol_node.property.filter(0, "Value")[1]
				unit = int(symbol_node.unit[0])
				logger.info("Reading symbol definition: %s / %s / %s", symbol_id, library_id, value)
				library_info = sheet_node.lib_symbols.symbol.filter(0, library_id)
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
			library_id = common_value(nodes, lambda node: node.lib_id[0])
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
				library_id=library_id,
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

	def read_footprints(self, board: BOARD):
		logger.info("Reading footprints")
		component_instances = {
			component_instance.reference.designator: component_instance
			for component_instance in self.component_instances
		}
		for pcbnew_footprint in board.Footprints():
			reference = pcbnew_footprint.GetReference()
			logger.info("Reading footprint %", reference)
			component_instance = component_instances[reference]
			footprint = Footprint(
				path=EntityPath.parse(pcbnew_footprint.GetPath()),
				pcbnew_footprint=pcbnew_footprint,
				component_instance=component_instance,
			)
			self.footprints.append(footprint)
