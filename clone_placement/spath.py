# Selector-path, crude ripoff of xpath/css concepts

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Sequence, TypeVar, Union, overload

from ..parse_v8 import SheetDefinition
from ..parse_v8 import SheetInstance
from ..parse_v8 import SymbolDefinition
from ..parse_v8 import SymbolInstance


SpathObject = Union[SheetDefinition, SymbolDefinition]
SpathTarget = Union[SheetInstance, SymbolInstance]
SpathTargetType = TypeVar("SpathTargetType", bound=SpathTarget)


def get_siblings_of_item_by_definition(item: SpathTargetType) -> Sequence[SpathTargetType]:
	if isinstance(item, SheetInstance):
		return (
			[item]
			if item.parent is None else
			[
				sheet
				for sheet in item.parent.children
				if sheet.definition == item.definition
			]
		)  # pyright: ignore
	elif isinstance(item, SymbolInstance):
		return (
			[
				symbol
				for symbol in item.sheet.symbols
				if symbol.definition == item.definition
			]
		)  # pyright: ignore
	else:
		raise TypeError()


def get_index_of_item_within_siblings_of_same_definition(item: SpathTarget) -> int:
	siblings = get_siblings_of_item_by_definition(item)
	return siblings.index(item)


def find_instance_of_item_by_index_within_siblings_of_same_definition(items: Sequence[SpathTargetType], definition: SpathObject, index: int) -> SpathTargetType:
	return [
		item
		for item in items
		if item.definition == definition
	][index]


@dataclass(frozen=True, eq=True)
class SpathComponent():
	"""
	Selector - specifies definition type

	Think like CSS:

		.definition:nth-child(index)

	"""
	definition: SpathObject
	index: int

	@property
	def name(self):
		if isinstance(self.definition, SheetDefinition):
			return str(Path(self.definition.filename).stem)
		elif isinstance(self.definition, SymbolDefinition):
			return str(self.definition.id)
		else:
			raise TypeError()

	def __str__(self):
		return f"{self.name}[{self.index}]"

	def __lt__(self, other: "SpathComponent"):
		if self.name < other.name:
			return True
		if self.name > other.name:
			return False
		return (
			self.index < other.index
		)

	def __gt__(self, other: "SpathComponent"):
		return other < self


@dataclass(frozen=True)
class Spath():
	"""
	Selector-path

	Think like a CSS selector:

		part1 > part2 > part3

	Where each part (component) is of the form:

		.definition:nth-child(index)

	"""
	parts: Sequence[SpathComponent]

	def __str__(self):
		return " > ".join([
			str(part)
			for part in self.parts
		])

	def __bool__(self):
		return bool(self.parts)

	def __iter__(self):
		return iter(self.parts)

	@overload
	def __getitem__(self, index_or_slice: int) -> SpathComponent:
		...

	@overload
	def __getitem__(self, index_or_slice: slice) -> "Spath":
		...

	def __getitem__(self, index_or_slice: Union[int, slice]) -> Union["Spath", SpathComponent]:
		if isinstance(index_or_slice, int):
			return self.parts[index_or_slice]
		else:
			return Spath(parts=self.parts[index_or_slice])

	def __len__(self):
		return len(self.parts)

	def __hash__(self):
		return hash(tuple(part for part in self.parts))

	def __eq__(self, other: Any):
		return (
			isinstance(other, Spath) and
			tuple(self.parts) == tuple(other.parts)
		)

	def __lt__(self, other: "Spath"):
		return list(self.parts) < list(other.parts)

	def __gt__(self, other: "Spath"):
		return list(self.parts) > list(other.parts)

	def startswith(self, prefix: "Spath"):
		return (
			len(self) >= len(prefix) and
			all(
				a == b
				for a, b in zip(self, prefix)
			)
		)

	def without_symbol(self):
		if isinstance(self.parts[-1].definition, SymbolDefinition):
			return Spath(parts=self.parts[:-1])
		else:
			return Spath(parts=self.parts)

	@staticmethod
	def create(item: SpathTarget, root: SheetInstance) -> "Spath":
		parts: List[SpathComponent] = []
		it: SheetInstance
		if isinstance(item, SheetInstance):
			it = item
		elif isinstance(item, SymbolInstance):
			it = item.sheet
		else:
			raise TypeError()
		while it != root:
			parts.append(
				SpathComponent(
					definition=it.definition,
					index=get_index_of_item_within_siblings_of_same_definition(it)
				)
			)
			if it.parent is None:
				raise ValueError()
			it = it.parent
		if isinstance(item, SymbolInstance):
			parts.append(
				SpathComponent(
					definition=item.definition,
					index=get_index_of_item_within_siblings_of_same_definition(item)
				)
			)
		return Spath(parts=parts)

	def resolve_sheet(self, root: SheetInstance) -> SheetInstance:
		it: SheetInstance = root
		for part in self.parts:
			if isinstance(part.definition, SymbolDefinition):
				break
			it = find_instance_of_item_by_index_within_siblings_of_same_definition(
				items=it.children,
				definition=part.definition,
				index=part.index,
			)
		return it

	def resolve_symbol(self, root: SheetInstance) -> SymbolInstance:
		sheet = self.resolve_sheet(root)
		symbol_part = self.parts[-1]
		symbol = find_instance_of_item_by_index_within_siblings_of_same_definition(
			items=sheet.symbols,
			definition=symbol_part.definition,
			index=symbol_part.index,
		)
		return symbol

	@overload
	def __add__(self, suffix: SpathComponent) -> "Spath":
		...

	@overload
	def __add__(self, suffix: Sequence[SpathComponent]) -> "Spath":
		...

	@overload
	def __add__(self, suffix: "Spath") -> "Spath":
		...

	def __add__(self, suffix: Union[SpathComponent, "Spath", Sequence[SpathComponent]]) -> "Spath":
		""" Concatenate """
		if isinstance(suffix, SpathComponent):
			return self + [suffix]
		else:
			return Spath(parts=list(self) + list(suffix))

	def __and__(self, other: "Spath") -> "Spath":
		""" Common prefix """
		prefix: List[SpathComponent] = []
		for a, b in zip(self, other):
			if a == b:
				prefix += [a]
			else:
				break
		return Spath(prefix)
