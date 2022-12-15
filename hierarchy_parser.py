from typing import List, Optional, Iterator, Dict, Set, Sequence, Iterable
from dataclasses import dataclass
from logging import Logger
from functools import reduce

import pcbnew  # pyright: ignore


Board = pcbnew.BOARD
Footprint = pcbnew.FOOTPRINT


@dataclass
class SheetID():
	value: Sequence[str]

	def __hash__(self) -> int:
		return hash(tuple(self.value))

	def __eq__(self, other: "SheetID") -> bool:
		return self.value == other.value

	def __bool__(self) -> bool:
		return bool(self.value)

	def __len__(self) -> int:
		return len(self.value)

	def __str__(self) -> str:
		return " / ".join(self.value)

	def prefix(self, end: int) -> "SheetID":
		return SheetID(value=self.value[0:end])

@dataclass
class SheetTemplate():
	path: str


@dataclass
class SheetInstance():
	id: SheetID
	name: str
	path: str

	footprints: Dict[str, Footprint]

	parent: Optional["SheetInstance"]
	children: Set["SheetInstance"]
	level: int

	def __hash__(self) -> int:
		return hash(self.id)

	def __eq__(self, other: "SheetInstance") -> bool:
		return self.id == other.id

	def __str__(self) -> str:
		return str(self.id)

	def name_chain(self) -> Sequence[str]:
		parts: List[str] = []
		sheet = self
		while sheet is not None:
			parts.append(sheet.name)
			sheet = sheet.parent
		return list(reversed(parts))

	def path_chain(self) -> Sequence[str]:
		parts: List[str] = []
		sheet = self
		while sheet is not None:
			parts.append(sheet.path)
			sheet = sheet.parent
		return list(reversed(parts))

	def get_all_footprints(self) -> Iterator[Footprint]:
		yield from self.footprints.values()
		for sheet in self.children:
			yield from sheet.get_all_footprints()


class HierarchyParser():

	logger: Logger
	board: Board
	by_id: Dict[SheetID, SheetInstance]
	by_footprint: Dict[str, SheetInstance]
	by_path: Dict[str, Set[SheetInstance]]
	root: Optional[SheetInstance]

	def __init__(self, logger: Logger, board: Board):
		self.logger = logger
		self.board = board
		self.by_id = {}
		self.by_footprint = {}
		self.by_path = {}
		self.root = None

	def fail(self, message, *args):
		self.logger.error(message, *args)
		return Exception("Hierarchy parser failed", message, *args)

	def get_sheet_instance_id_from_footprint(self, footprint: Footprint) -> Optional[SheetID]:
		return SheetID(value=[
			level.AsString()
			for level in footprint.GetPath()
		])

	def find_or_create_sheet_instance_from_footprint(self, footprint: Footprint) -> Optional[SheetInstance]:
		sheet_id = self.get_sheet_instance_id_from_footprint(footprint)
		if sheet_id is None:
			self.logger.debug("Failed to find sheet ID for footprint %s", footprint.GetReference())
			return None
		if sheet_id in self.by_id:
			return self.by_id[sheet_id]
		try:
			sheet_name = footprint.GetProperty("Sheetname")
			sheet_path = footprint.GetProperty("Sheetfile")
			if any(value is None for value in (sheet_name, sheet_path)):
				raise KeyError()
		except KeyError:
			self.logger.warn("Failed to get sheet info for footprint %s", footprint.GetReference())
			return None
		sheet = SheetInstance(
			id=sheet_id,
			name=str(sheet_name),
			path=str(sheet_path),
			footprints={},
			parent=None,
			children=set(),
			level=len(sheet_id),
		)
		self.by_id[sheet_id] = sheet
		return sheet

	def discover_sheets(self) -> None:
		for footprint in self.board.GetFootprints():
			self.logger.debug("Resolving sheet for footprint %s", footprint.GetReference())
			sheet = self.find_or_create_sheet_instance_from_footprint(footprint)
			reference = str(footprint.GetReference())
			if reference in self.by_footprint:
				raise self.fail("Duplicate footprint reference \"%s\"", reference)
			if sheet is not None:
				sheet.footprints[reference] = footprint
				self.by_footprint[reference] = sheet
				path = sheet.path
				if path in self.by_path:
					self.by_path[path].add(sheet)
				else:
					path_sheets = { sheet }
					self.by_path[path] = path_sheets

	def find_parent_sheet_instance(self, sheet: SheetInstance, create: bool = False) -> Optional[SheetInstance]:
		logger = self.logger
		id = sheet.id
		if not id:
			return None
		parent_id = id.prefix(-1)
		parent_sheet = self.by_id.get(parent_id)
		if parent_sheet:
			return parent_sheet
		msg_args = ("Failed to find parent sheet \"%s\" for sheet \"%s\" with name \"%s\" and path \"%s\"", parent_id, id, sheet.name, sheet.path)
		if create:
			logger.info(*msg_args)
		else:
			raise self.fail(*msg_args)
		parent_sheet = SheetInstance(
			id=parent_id,
			name="(unknown)",
			path="(unknown)",
			footprints={},
			parent=None,
			children=set(),
			level=sheet.level - 1
		)
		self.by_id[parent_id] = parent_sheet
		self.find_parent_sheet_instance(parent_sheet, True)
		return parent_sheet

	def build_tree(self) -> None:
		for sheet in list(self.by_id.values()):
			self.find_parent_sheet_instance(sheet, True)
		for sheet in self.by_id.values():
			parent_sheet = self.find_parent_sheet_instance(sheet)
			if not parent_sheet:
				continue
			sheet.parent = parent_sheet
			parent_sheet.children.add(sheet)
		roots = [
			sheet
			for sheet in self.by_id.values()
			if sheet.level == 0
		]
		if len(roots) == 0:
			raise self.fail("Failed to find root sheet")
		if len(roots) > 1:
			raise self.fail("Multiple root sheets")
		self.root = roots[0]

	def parse(self) -> None:
		self.discover_sheets()
		self.build_tree()

	@staticmethod
	def is_child_of(parent: List[str], child: List[str]) -> bool:
		return len(parent) < len(child) and child[0:len(parent)] == parent

	@staticmethod
	def get_common_ancestor_of(items: Iterable[Sequence[str]]) -> Sequence[str]:
		def reductor(a: Sequence[str], b: Sequence[str]) -> Sequence[str]:
			result: List[str] = []
			for index in range(0, min(len(a), len(b))):
				if a[index] != b[index]:
					break
				result.append(a[index])
			return result
		try:
			return reduce(reductor, items)
		except TypeError:
			raise ValueError("No values provided")
