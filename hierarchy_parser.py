from typing import Any
from logging import Logger
from uuid import UUID
from pathlib import Path
import os.path

import pcbnew  # pyright: ignore

from .kicad_sexp_parser import KicadSexpParser
from .kicad_entities import UuidPath, SheetTemplate, SheetInstance, Symbol, Footprint
from .hierarchy import Hierarchy


class HierarchyParser():

	logger: Logger
	board: pcbnew.BOARD
	project_name: str

	result: Hierarchy

	root: SheetInstance

	def __init__(self, logger: Logger, board: pcbnew.BOARD):
		self.logger = logger.getChild(type(self).__name__)
		self.board = board
		self.project_name = Path(str(board.GetFileName())).stem

	def fail(self, message: str, *args: Any):
		self.logger.error(message, *args)
		return Exception("Hierarchy parser failed", message, *args)

	def parse_schematics(self, parent_filename: str) -> None:
		# Parse the parent schematic
		logger = self.logger
		templates = self.result.templates
		logger.debug("Parsing schematic %s", parent_filename)
		root_node = KicadSexpParser().parse_file(parent_filename)
		uuid = UUID(hex=root_node.kicad_sch.uuid.values[0])
		logger.info("Schematic sheet UUID: %s", uuid)
		templates[parent_filename] = SheetTemplate(
			filename=parent_filename,
			root_node=root_node,
			uuid=uuid
		)
		# Iterate over child schematics
		for sheet_node in root_node.kicad_sch["sheet"]:
			filename = sheet_node.query_child_field("property", 0, "Sheetfile", 1)
			if filename is None:
				raise ValueError()
			path_from_base = os.path.join(os.path.dirname(filename), filename)
			logger.debug(" - Sheet %s", path_from_base)
			# Recurse if schematic not already loaded
			if path_from_base not in templates:
				self.parse_schematics(path_from_base)

	def parse_sheet_instances(self, parent_instance: SheetInstance) -> None:
		# Iterate over child sheets
		logger = self.logger
		templates = self.result.templates
		instances = self.result.instances
		relations = self.result.relations
		logger.debug("Parsing sheet instance %s", parent_instance.name_path)
		root_node = parent_instance.template.root_node
		for sheet_node in root_node.kicad_sch["sheet"]:
			uuid = UUID(hex=sheet_node.uuid.values[0])
			name = sheet_node.query_child_field("property", 0, "Sheetname", 1)
			if name is None:
				raise ValueError()
			filename = sheet_node.query_child_field("property", 0, "Sheetfile", 1)
			if filename is None:
				raise ValueError()
			logger.debug(" - Sheet instance %s (%s) / %s", name, filename, uuid)
			path_from_base = os.path.join(os.path.dirname(filename), filename)
			template = templates[path_from_base]
			instance = SheetInstance(uuid=uuid, name=name, template=template, parent=parent_instance)
			if instance.uuid_path in instances:
				raise self.fail("Duplicate sheet instance: %s", instance.uuid_path)
			logger.debug(" - Sheet UUID path: %s", instance.uuid_path)
			instances[instance.uuid_path] = instance
			relations[parent_instance] = instance
			# Recurse
			self.parse_sheet_instances(instance)

	def build_sheet_hierarchy(self) -> None:
		logger = self.logger
		templates = self.result.templates
		instances = self.result.instances
		logger.debug("Building sheet hierarchy")
		# Estimate filename for schematic
		schematic_filename = f"{self.project_name}.kicad_sch"
		# Recursively parse schematics
		self.parse_schematics(schematic_filename)
		# Create root sheet instance
		root_template = templates[schematic_filename]
		root_instance = SheetInstance(
			uuid=UUID(hex=root_template.root_node.kicad_sch.uuid.values[0]),
			name=self.project_name,
			template=root_template,
			parent=None,
		)
		instances[root_instance.uuid_path] = root_instance
		self.result.root = root_instance
		# Recursively parse sheet instances
		self.parse_sheet_instances(root_instance)
		logger.info("Read total %d sheet instances", len(instances))

	def read_symbols(self) -> None:
		logger = self.logger
		templates = self.result.templates
		instances = self.result.instances
		footprints = self.result.footprints
		symbols = self.result.symbols
		logger.debug("Parsing symbols")
		for template in templates.values():
			for symbol_template in template.root_node.kicad_sch["symbol"]:
				uuid = UUID(hex=symbol_template.uuid.values[0])
				reference = symbol_template.query_child_field("property", 0, "Reference", 1)
				if reference is None:
					raise ValueError()
				value = symbol_template.query_child_field("property", 0, "Value", 1)
				if value is None:
					raise ValueError()
				unit = int(symbol_template.unit.values[0])
				symbol = Symbol(
					uuid=uuid,
					path=UuidPath.of([uuid]),
					reference=reference,
					unit=unit,
					value=value,
					sheet_template=template,
					sheet_instance=None,
				)
				symbols[uuid] = symbol
				logger.info("> Symbol %s id %s", reference, uuid)
				for project_symbol_instances in symbol_template.instances.query_children("project", 0, self.project_name):
					for symbol_instance in project_symbol_instances["path"]:
						path = UuidPath.of(symbol_instance.values[0])
						reference = symbol_instance.reference.values[0]
						unit = int(symbol_instance.unit.values[0])
						uuid = path[-1]
						sheet_instance_uuid = path[:-1]
						logger.debug(" - Symbol %s (%s)", reference, value)
						try:
							sheet_instance = instances[sheet_instance_uuid]
						except KeyError:
							raise self.fail("Failed to find sheet instance \"%s\" for symbol %s:%s", sheet_instance_uuid, reference, unit)
						symbol = Symbol(
							uuid=uuid,
							path=path,
							reference=reference,
							unit=unit,
							value=value,
							sheet_template=template,
							sheet_instance=sheet_instance,
						)
						if path in footprints:
							raise self.fail("Duplicate symbol: %s", path)
						symbols[uuid] = symbol
						logger.info("> Symbol %s path %s", reference, path)
		logger.info("Read total %d symbols", len(symbols))

	def read_footprints(self) -> None:
		logger = self.logger
		symbols = self.result.symbols
		footprints = self.result.footprints
		symbol_instances = self.result.symbol_instances
		sheet_instances = self.result.instances
		logger.debug("Parsing footprints")
		for footprint in self.board.Footprints():
			reference = str(footprint.GetReference())
			value = str(footprint.GetValue())
			logger.debug(" - Footprint %s (%s)", reference, value)
			path = self.result.get_path_from_pcb_path(footprint.GetPath())
			try:
				sheet_instance = sheet_instances[path[:-1]]
			except KeyError:
				logger.warn("Failed to match footprint to a sheet instance: %s (%s)", reference, path)
				continue
			try:
				symbol = symbols[path[-1]]
			except KeyError:
				logger.warn("Failed to match footprint to a symbol: %s (%s)", reference, path)
				continue
			footprint = Footprint(
				path=path,
				reference=reference,
				value=value,
				symbol=symbol,
				sheet_instance=sheet_instance,
				data=footprint,
			)
			if path in footprints:
				raise self.fail("Duplicate footprint: %s", path)
			footprints[path] = footprint
			symbol_instances[symbol] = footprint
		logger.info("Read total %d footprints", len(footprints))

	def parse(self) -> Hierarchy:
		self.result = Hierarchy()
		self.build_sheet_hierarchy()
		self.read_symbols()
		self.read_footprints()
		return self.result
