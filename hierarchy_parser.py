from typing import Optional, Dict, Sequence, Iterable
from dataclasses import dataclass, field
from logging import Logger
from functools import cached_property
from uuid import UUID
from pathlib import Path
import os.path

import pcbnew  # pyright: ignore

from .multi_map import MultiMap
from .kicad_sexp_parser import KicadSexpParser, KicadSexpNode


Filename = str
Reference = str


ROOT_UUID = UUID(bytes=b"\0" * 16)


@dataclass(frozen=True, eq=True)
class UuidPath():
	value: Sequence[UUID]

	@staticmethod
	def from_parts(parts: Iterable[UUID]) -> "UuidPath":
		return UuidPath(value=tuple(parts))

	@staticmethod
	def from_kiid_path(kiid_path: pcbnew.KIID_PATH) -> "UuidPath":
		return UuidPath.from_parts(
			UUID(hex=str(item.AsString()))
			for item in kiid_path
		)

	@staticmethod
	def from_str(path: str) -> "UuidPath":
		return UuidPath.from_parts(
			UUID(hex=part)
			for index, part in enumerate(path.split("/"))
			if not (index == 0 and not part)
		)

	def __repr__(self) -> str:
		return "/" + "/".join(str(part) for part in self.value)

	def __str__(self) -> str:
		return repr(self)


@dataclass(frozen=True, eq=True)
class SheetTemplate():
	uuid: UUID
	filename: Filename
	root_node: KicadSexpNode = field(hash=False)


@dataclass(frozen=True, eq=True)
class SheetInstance():
	uuid: UUID
	name: str

	template: SheetTemplate = field(hash=False)

	parent: Optional["SheetInstance"] = field(hash=False)

	@cached_property
	def uuid_path(self) -> UuidPath:
		return UuidPath.from_parts(self.uuid_chain)

	@cached_property
	def template_uuid_path(self) -> UuidPath:
		return UuidPath.from_parts(self.template_uuid_chain)

	@cached_property
	def name_path(self) -> str:
		return " / ".join(self.name_chain)

	@cached_property
	def uuid_chain(self) -> Sequence[UUID]:
		if self.parent is None:
			return tuple()
		else:
			return tuple(list(self.parent.uuid_chain) + [self.uuid])

	@cached_property
	def template_uuid_chain(self) -> Sequence[UUID]:
		# Omit for root
		if self.parent is None:
			return tuple()
		else:
			return tuple(list(self.parent.template_uuid_chain) + [self.template.uuid])

	@cached_property
	def name_chain(self) -> Sequence[str]:
		if self.parent is None:
			return tuple([self.name])
		else:
			return tuple(list(self.parent.name_chain) + [self.name])


@dataclass(frozen=True, eq=True)
class Symbol():
	path: UuidPath
	uuid: UUID
	reference: Reference
	unit: int
	value: str

	sheet_instance: SheetInstance = field(hash=False)


@dataclass(frozen=True, eq=True)
class Footprint():
	path: UuidPath
	reference: Reference
	value: str

	symbol: Symbol = field(hash=False)


class HierarchyParser():

	logger: Logger
	board: pcbnew.BOARD
	base_path: str

	templates: Dict[Filename, SheetTemplate]

	instances: Dict[UuidPath, SheetInstance]
	relations: MultiMap[SheetInstance, SheetInstance]
	root: SheetInstance

	symbols: Dict[UuidPath, Symbol]
	footprints: Dict[UuidPath, Footprint]

	def __init__(self, logger: Logger, board: Optional[pcbnew.BOARD] = None):
		self.logger = logger
		self.board = pcbnew.GetBoard() if board is None else board
		self.base_path = os.path.dirname(str(self.board.GetFileName()))
		self.schematics = {}
		self.templates = {}
		self.instances = {}
		self.relations = MultiMap()
		self.root = None  # pyright: ignore
		self.symbols = {}
		self.footprints = {}
		logger.info("Base path: %s", self.base_path)

	def fail(self, message, *args):
		self.logger.error(message, *args)
		return Exception("Hierarchy parser failed", message, *args)

	def parse_schematics(self, parent_filename: str) -> None:
		# Parse the parent schematic
		self.logger.info("Parsing schematic %s", parent_filename)
		root_node = KicadSexpParser().parse_file(parent_filename)
		uuid = UUID(hex=root_node.kicad_sch.uuid.values[0])
		template = SheetTemplate(filename=parent_filename, root_node=root_node, uuid=uuid)
		self.templates[parent_filename] = template
		# Iterate over child schematics
		for sheet_node in root_node.kicad_sch["sheet"]:
			properties = {
				property.values[0]: property.values[1:]
				for property in sheet_node["property"]
			}
			filename = properties["Sheet file"][0]
			path_from_base = os.path.join(os.path.dirname(filename), filename)
			# Recurse if schematic not already loaded
			if path_from_base not in self.templates:
				self.parse_schematics(path_from_base)

	def parse_sheet_instances(self, parent_instance: SheetInstance) -> None:
		# Iterate over child sheets
		self.logger.info("Parsing sheet instance %s", parent_instance.name_path)
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
			template = self.templates[path_from_base]
			instance = SheetInstance(uuid=uuid, name=name, template=template, parent=parent_instance)
			if instance.uuid_path in self.instances:
				raise self.fail("Duplicate sheet instance: %s", instance.uuid_path)
			self.instances[instance.uuid_path] = instance
			self.relations[parent_instance] = instance
			# Recurse
			self.parse_sheet_instances(instance)

	def build_sheet_hierarchy(self) -> None:
		self.logger.info("Building sheet hierarchy")
		# Estimate filename for schematic
		base_filename = Path(str(self.board.GetFileName())).stem
		schematic_filename = f"{base_filename}.kicad_sch"
		# Recursively parse schematics
		self.parse_schematics(schematic_filename)
		# Create root sheet instance
		root_template = self.templates[schematic_filename]
		root_instance = SheetInstance(
			uuid=ROOT_UUID,
			name=base_filename,
			template=root_template,
			parent=None,
		)
		self.instances[root_instance.uuid_path] = root_instance 
		self.root = root_instance
		# Recursively parse sheet instances
		self.parse_sheet_instances(root_instance)

	def read_symbols(self) -> None:
		self.logger.info("Parsing symbols")
		for symbol_instance in self.root.template.root_node.kicad_sch.symbol_instances["path"]:
			path = UuidPath.from_str(symbol_instance.values[0])
			reference = symbol_instance.reference.values[0]
			unit = int(symbol_instance.unit.values[0])
			value = symbol_instance.value.values[0]
			uuid = path.value[-1]
			sheet_instance_uuid = UuidPath.from_parts(path.value[:-1])
			try:
				sheet_instance = self.instances[sheet_instance_uuid]
			except KeyError:
				raise self.fail("Failed to find sheet instance \"%s\" for symbol %s:%s", sheet_instance_uuid, reference, unit)
			symbol = Symbol(path=path, uuid=uuid, reference=reference, unit=unit, value=value, sheet_instance=sheet_instance)
			if path in self.footprints:
				raise self.fail("Duplicate symbol: %s", path)
			self.symbols[path] = symbol

	def read_footprints(self) -> None:
		self.logger.info("Parsing footprints")
		for footprint in self.board.Footprints():
			path = UuidPath.from_kiid_path(footprint.GetPath())
			reference = str(footprint.GetReference())
			value = str(footprint.GetValue())
			try:
				symbol = self.symbols[path]
			except KeyError:
				self.logger.warn("Failed to match footprint to a symbol: %s (%s)", reference, path)
				continue
			footprint = Footprint(path=path, reference=reference, value=value, symbol=symbol)
			if path in self.footprints:
				raise self.fail("Duplicate footprint: %s", path)
			self.footprints[path] = footprint

	def parse(self) -> None:
		self.build_sheet_hierarchy()
		self.read_symbols()
		self.read_footprints()
