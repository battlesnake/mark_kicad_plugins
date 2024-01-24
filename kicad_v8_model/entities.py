from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import re
from pathlib import Path

from .board import BoardLayer, Layer
from .entity_path import EntityPath, EntityPathComponent
from .entity_traits import HasArc, HasLine, HasPolygon, HasProperties, HasId, HasPath, Net, HasNet, HasLayer, HasPosition, HasOrientation
from .angle import Angle
from .vector2 import Vector2


# Many of the PCB-related dataclasses are incomplete, containing only what we
# currently need (or slightly more).


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
class SheetDefinition(HasId):
	""" Maps to one sheet file i.e. a kicad_sch """
	id: EntityPathComponent = field(compare=True, hash=True)
	version: str
	filename: str
	symbols: List["SymbolDefinition"] = field(repr=False)
	instances: List["SheetInstance"]

	def __str__(self):
		return Path(self.filename).stem


@dataclass
class SheetInstance(HasPath):
	""" Maps to an instance of a sheet within the sheet-hierarchy """
	path: EntityPath = field(compare=True, hash=True)
	definition: SheetDefinition
	name: str
	page: str
	parent: Optional["SheetInstance"] = field(repr=False)
	children: List["SheetInstance"] = field(repr=False)
	symbols: List["SymbolInstance"] = field(repr=False)

	def __str__(self):
		return f"{self.name}#{self.page}"


@dataclass
class SymbolDefinition(HasId):
	""" Maps to a symbol node in a sheet file """
	id: EntityPathComponent = field(compare=True, hash=True)
	sheet: SheetDefinition
	reference: SymbolReference  # Reference in own sheet file, not in schematic/layout
	instances: List["SymbolInstance"] = field(repr=False)
	component: "ComponentDefinition" = field(init=False, repr=False)

	def __str__(self):
		return f"{self.sheet}/{self.id}"

	def __hash__(self):
		return hash(self.id)


@dataclass
class SymbolInstance(HasPath):
	""" Maps to a symbol in an instance of a sheet in the sheet-hierarchy """
	path: EntityPath = field(compare=True, hash=True)
	sheet: SheetInstance
	definition: SymbolDefinition
	reference: SymbolReference
	component: "ComponentInstance" = field(init=False, repr=False)

	def __str__(self):
		return f"{self.sheet}/{self.reference}"

	def __hash__(self):
		return hash(self.path)


@dataclass
class Footprint(HasId, HasProperties, HasLayer, HasPosition, HasOrientation):
	id: EntityPathComponent = field(compare=True, hash=True)
	properties: Dict[str, str]
	layer: Layer
	locked: bool
	board_only: bool
	position: Vector2
	orientation: Angle
	symbol_path: EntityPath
	component: "ComponentInstance" = field(init=False, repr=False)

	def __str__(self):
		return f"{self.component.reference}"

	def __hash__(self):
		return hash(self.id)


@dataclass
class ComponentDefinition(HasProperties):
	properties: Dict[str, str]
	value: str
	units: List[SymbolDefinition] = field(repr=False)
	symbol_library_id: str
	in_bom: bool
	on_board: bool
	dnp: bool
	instances: List["ComponentInstance"] = field(repr=False)

	def __str__(self):
		return f"{self.symbol_library_id}({self.value})"

	def __hash__(self):
		return id(self)


@dataclass
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


@dataclass
class StraightRoute(HasId, HasPosition, HasLayer, HasNet, HasLine):
	id: EntityPathComponent = field(compare=True, hash=True)
	position: Vector2
	start: Vector2
	end: Vector2
	layer: Layer
	net: Net


@dataclass
class ArcRoute(HasId, HasPosition, HasLayer, HasNet, HasArc):
	id: EntityPathComponent = field(compare=True, hash=True)
	position: Vector2
	start: Vector2
	mid: Vector2
	end: Vector2
	layer: Layer
	net: Net


@dataclass
class PolygonRoute(HasId, HasPosition, HasLayer, HasNet, HasPolygon):
	id: EntityPathComponent = field(compare=True, hash=True)
	position: Vector2
	layer: Layer
	points: List[Vector2]
	net: Net


@dataclass
class Via(HasId, HasPosition, HasNet):
	id: EntityPathComponent = field(compare=True, hash=True)
	position: Vector2
	layers: Tuple[Layer, Layer]
	net: Net


@dataclass(repr=False, eq=False)
class Project():
	"""
	This has grown from a basic schematic relations parser to include board
	stuff too, perhaps rename from Schematic to Project?
	"""

	name: str = field(init=False)
	sheet_definitions: Dict[str, SheetDefinition] = field(init=False)
	sheet_instances: Dict[EntityPath, SheetInstance] = field(init=False)
	symbol_definitions: Dict[EntityPathComponent, SymbolDefinition] = field(init=False)
	symbol_instances: Dict[EntityPath, SymbolInstance] = field(init=False)
	component_definitions: List[ComponentDefinition] = field(init=False)
	component_instances: Dict[str, ComponentInstance] = field(init=False)
	root_sheet_instance: SheetInstance = field(init=False)
	root_sheet_definition: SheetDefinition = field(init=False)

	""" Eventually we will support multiple boards, even if Kicad won't """
	""" But for now, keep it as is currently required """
	layers: Dict[BoardLayer, Layer] = field(init=False)
	nets: Dict[int, Net] = field(init=False)
	footprints: Dict[EntityPathComponent, Footprint] = field(init=False)
	# Tracks, vias, zones, arcs
	# Don't differentiate between them until we need to
	tracks: Dict[EntityPathComponent, StraightRoute] = field(init=False)
	track_arcs: Dict[EntityPathComponent, ArcRoute] = field(init=False)
	zones: Dict[EntityPathComponent, PolygonRoute] = field(init=False)
	vias: Dict[EntityPathComponent, Via] = field(init=False)
