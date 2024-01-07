from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import re
from pathlib import Path

from parse_v8.entity_path import EntityPath, EntityPathComponent


COMPONENT_REFERENCE_VALIDATOR = re.compile(r"^(#?[A-Z]+)([0-9]+)$")


@dataclass(kw_only=True, frozen=True, eq=True)
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


@dataclass(kw_only=True, frozen=True, eq=True)
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


@dataclass(kw_only=True)
class SheetDefinition():
	""" Maps to one sheet file i.e. a kicad_sch """
	id: EntityPathComponent = field(compare=True, hash=True)
	version: str
	filename: str
	symbols: List["SymbolDefinition"] = field(repr=False)
	instances: List["SheetInstance"]

	def __str__(self):
		return Path(self.filename).stem


@dataclass(kw_only=True)
class SheetInstance():
	""" Maps to an instance of a sheet within the sheet-hierarchy """
	definition: SheetDefinition
	path: EntityPath = field(compare=True, hash=True)
	name: str
	page: str
	parent: Optional["SheetInstance"] = field(repr=False)
	children: List["SheetInstance"] = field(repr=False)
	symbols: List["SymbolInstance"] = field(repr=False)

	def __str__(self):
		return f"{self.name}#{self.page}"


@dataclass(kw_only=True)
class SymbolDefinition():
	""" Maps to a symbol node in a sheet file """
	sheet: SheetDefinition
	id: EntityPathComponent
	reference: SymbolReference  # Reference in own sheet file, not in schematic/layout
	instances: List["SymbolInstance"] = field(repr=False)
	component: "ComponentDefinition" = field(init=False, repr=False)

	def __str__(self):
		return f"{self.sheet}/{self.id}"

	def __hash__(self):
		return hash(self.id)


@dataclass(kw_only=True)
class SymbolInstance():
	""" Maps to a symbol in an instance of a sheet in the sheet-hierarchy """
	sheet: SheetInstance
	definition: SymbolDefinition
	path: EntityPath
	reference: SymbolReference
	component: "ComponentInstance" = field(init=False, repr=False)

	def __str__(self):
		return f"{self.sheet}/{self.reference}"

	def __hash__(self):
		return hash(self.path)


@dataclass(kw_only=True)
class Footprint():
	locked: bool
	board_only: bool
	placement_layer: str
	id: EntityPathComponent = field(hash=True, compare=True)
	placement_x: float
	placement_y: float
	placement_angle: float
	properties: Dict[str, str]
	symbol_path: EntityPath
	component: "ComponentInstance" = field(init=False, repr=False)

	def __str__(self):
		return f"{self.component.reference}"

	def __hash__(self):
		return hash(self.id)


@dataclass(kw_only=True)
class ComponentDefinition():
	value: str
	units: List[SymbolDefinition] = field(repr=False)
	properties: Dict[str, str]
	symbol_library_id: str
	in_bom: bool
	on_board: bool
	dnp: bool
	instances: List["ComponentInstance"] = field(repr=False)

	def __str__(self):
		return f"{self.symbol_library_id}({self.value})"

	def __hash__(self):
		return id(self)


@dataclass(kw_only=True)
class ComponentInstance():
	""" Maps to a physical component i.e. a footprint on the PCB """
	""" (or in some cases, virtual components e.g. for power symbols) """
	definition: ComponentDefinition
	reference: ComponentReference = field(hash=True, compare=True)
	units: List[SymbolInstance] = field(repr=False)
	footprint: Footprint = field(init=False)

	def __str__(self):
		return f"{self.reference}"

	def __hash__(self):
		return hash(self.reference)


@dataclass(kw_only=True, repr=False, eq=False)
class Project():
	"""
	This has grown from a basic schematic relations parser to include board
	stuff too, perhaps rename from Schematic to Project?
	"""

	sheet_definitions: Dict[str, SheetDefinition] = field(default_factory=dict)
	sheet_instances: Dict[EntityPath, SheetInstance] = field(default_factory=dict)
	symbol_definitions: Dict[EntityPathComponent, SymbolDefinition] = field(default_factory=dict)
	symbol_instances: Dict[EntityPath, SymbolInstance] = field(default_factory=dict)
	component_definitions: List[ComponentDefinition] = field(default_factory=list)
	component_instances: Dict[str, ComponentInstance] = field(default_factory=dict)
	root_sheet_instance: SheetInstance = field(init=False)
	root_sheet_definition: SheetDefinition = field(init=False)

	""" Eventually we will support multiple boards, even if Kicad won't """
	""" But for now, keep it as is currently required """
	footprints: Dict[EntityPathComponent, Footprint] = field(default_factory=dict)
