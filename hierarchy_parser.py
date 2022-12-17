from typing import Optional, Dict, cast
from dataclasses import dataclass, field
from logging import Logger
from uuid import UUID
from pathlib import Path
import os.path

import pcbnew  # pyright: ignore

from .multi_map import MultiMap
from .kicad_sexp_parser import KicadSexpParser
from .kicad_entities import Filename, UuidPath, SheetTemplate, SheetInstance, Symbol, Footprint


ROOT_UUID = UUID(bytes=b"\0" * 16)


@dataclass(repr=False)
class Hierarchy():

	templates: Dict[Filename, SheetTemplate] = field(default_factory=lambda:{})

	instances: Dict[UuidPath, SheetInstance] = field(default_factory=lambda:{})
	relations: MultiMap[SheetInstance, SheetInstance] = field(default_factory=lambda:MultiMap())
	root: SheetInstance = field(default_factory=lambda:cast(SheetInstance, None))

	symbols: Dict[UUID, Symbol] = field(default_factory=lambda:{})
	footprints: Dict[UuidPath, Footprint] = field(default_factory=lambda:{})
	symbol_instances: MultiMap[Symbol, Footprint] = field(default_factory=lambda:MultiMap())


class HierarchyParser():

	logger: Logger
	board: pcbnew.BOARD

	result: Hierarchy

	def __init__(self, logger: Logger, board: pcbnew.BOARD):
		self.logger = logger.getChild(self.__class__.__name__)
		self.board = board

	def fail(self, message, *args):
		self.logger.error(message, *args)
		return Exception("Hierarchy parser failed", message, *args)

	def parse_schematics(self, parent_filename: str) -> None:
		# Parse the parent schematic
		logger = self.logger
		templates = self.result.templates
		logger.info("Parsing schematic %s", parent_filename)
		root_node = KicadSexpParser().parse_file(parent_filename)
		uuid = UUID(hex=root_node.kicad_sch.uuid.values[0])
		template = SheetTemplate(filename=parent_filename, root_node=root_node, uuid=uuid)
		templates[parent_filename] = template
		# Iterate over child schematics
		for sheet_node in root_node.kicad_sch["sheet"]:
			properties = {
				property.values[0]: property.values[1:]
				for property in sheet_node["property"]
			}
			filename = properties["Sheet file"][0]
			path_from_base = os.path.join(os.path.dirname(filename), filename)
			# Recurse if schematic not already loaded
			if path_from_base not in templates:
				self.parse_schematics(path_from_base)

	def parse_sheet_instances(self, parent_instance: SheetInstance) -> None:
		# Iterate over child sheets
		logger = self.logger
		templates = self.result.templates
		instances = self.result.instances
		relations = self.result.relations
		logger.info("Parsing sheet instance %s", parent_instance.name_path)
		root_node = parent_instance.template.root_node
		for sheet_node in root_node.kicad_sch["sheet"]:
			properties = {
				property.values[0]: property.values[1:]
				for property in sheet_node["property"]
			}
			uuid = UUID(hex=sheet_node.uuid.values[0])
			name = properties["Sheet name"][0]
			filename = properties["Sheet file"][0]
			path_from_base = os.path.join(os.path.dirname(filename), filename)
			template = templates[path_from_base]
			instance = SheetInstance(uuid=uuid, name=name, template=template, parent=parent_instance)
			if instance.uuid_path in instances:
				raise self.fail("Duplicate sheet instance: %s", instance.uuid_path)
			instances[instance.uuid_path] = instance
			relations[parent_instance] = instance
			# Recurse
			self.parse_sheet_instances(instance)

	def build_sheet_hierarchy(self) -> None:
		logger = self.logger
		templates = self.result.templates
		instances = self.result.instances
		logger.info("Building sheet hierarchy")
		# Estimate filename for schematic
		base_filename = Path(str(self.board.GetFileName())).stem
		schematic_filename = f"{base_filename}.kicad_sch"
		# Recursively parse schematics
		self.parse_schematics(schematic_filename)
		# Create root sheet instance
		root_template = templates[schematic_filename]
		root_instance = SheetInstance(
			uuid=ROOT_UUID,
			name=base_filename,
			template=root_template,
			parent=None,
		)
		instances[root_instance.uuid_path] = root_instance 
		self.root = root_instance
		# Recursively parse sheet instances
		self.parse_sheet_instances(root_instance)

	def read_symbols(self) -> None:
		logger = self.logger
		instances = self.result.instances
		footprints = self.result.footprints
		symbols = self.result.symbols
		logger.info("Parsing symbols")
		for symbol_instance in self.root.template.root_node.kicad_sch.symbol_instances["path"]:
			path = UuidPath.of(symbol_instance.values[0])
			reference = symbol_instance.reference.values[0]
			unit = int(symbol_instance.unit.values[0])
			value = symbol_instance.value.values[0]
			uuid = path[-1]
			sheet_instance_uuid = path[:-1]
			try:
				sheet_instance = instances[sheet_instance_uuid]
			except KeyError:
				raise self.fail("Failed to find sheet instance \"%s\" for symbol %s:%s", sheet_instance_uuid, reference, unit)
			symbol = Symbol(path=path, uuid=uuid, reference=reference, unit=unit, value=value, sheet_instance=sheet_instance)
			if path in footprints:
				raise self.fail("Duplicate symbol: %s", path)
			symbols[uuid] = symbol

	def read_footprints(self) -> None:
		logger = self.logger
		symbols = self.result.symbols
		footprints = self.result.footprints
		symbol_instances = self.result.symbol_instances
		logger.info("Parsing footprints")
		for footprint in self.board.Footprints():
			path = UuidPath.of(footprint.GetPath())
			reference = str(footprint.GetReference())
			value = str(footprint.GetValue())
			try:
				symbol = symbols[path[-1]]
			except KeyError:
				logger.warn("Failed to match footprint to a symbol: %s (%s)", reference, path)
				continue
			footprint = Footprint(path=path, reference=reference, value=value, symbol=symbol, data=footprint)
			if path in footprints:
				raise self.fail("Duplicate footprint: %s", path)
			footprints[path] = footprint
			symbol_instances[symbol] = footprint

	def parse(self) -> Hierarchy:
		self.result = Hierarchy()
		self.build_sheet_hierarchy()
		self.read_symbols()
		self.read_footprints()
		return self.result
