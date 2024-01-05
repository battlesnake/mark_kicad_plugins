# Sheet-path, crude ripoff of xpath/css concepts

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union, overload

from ..parse_v8 import SheetDefinition
from ..parse_v8 import SheetInstance


SHEET_DELIMITER = "/"
INDEX_DELIMITER = "@"


@dataclass(frozen=True, eq=True)
class SpathComponent():
	value: SheetDefinition  # Need some way to incorporate index-addressed symbol unit as terminal item in path?
	index: Optional[int] = None

	def __str__(self):
		result = str(Path(self.value.filename).stem)
		if self.index is not None:
			result += INDEX_DELIMITER + str(self.index)
		return result

	def __lt__(self, other: "SpathComponent"):
		if self.value.filename < other.value.filename:
			return True
		if self.value.filename > other.value.filename:
			return False
		return (
			self.index is not None and
			other.index is not None and
			self.index < other.index
		)

	def __gt__(self, other: "SpathComponent"):
		return other < self


@dataclass(frozen=True)
class Spath():
	parts: Sequence[SpathComponent]

	def __str__(self):
		return SHEET_DELIMITER.join([
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

	@staticmethod
	def create(item: SheetInstance, root: SheetInstance) -> "Spath":
		parts: List[SpathComponent] = []
		it: SheetInstance = item
		while it != root:
			siblings = (
				[item]
				if it.parent is None else
				[
					sheet
					for sheet in it.parent.children
					if sheet.definition == it.definition
				]
			)
			if len(siblings) == 1:
				parts.append(SpathComponent(value=it.definition, index=None))
			else:
				parts.append(SpathComponent(value=it.definition, index=siblings.index(it)))
			if it.parent is None:
				raise ValueError()
			it = it.parent
		return Spath(parts=parts)

	def resolve(self, root: SheetInstance) -> SheetInstance:
		it: SheetInstance = root
		for part in self.parts:
			definition = part.value
			index = part.index
			siblings: List[SheetInstance] = [
				sheet
				for sheet in it.children
				if sheet.definition == definition
			]
			if index is None:
				if len(siblings) != 1:
					raise IndexError
				it = siblings[0]
			else:
				if index >= len(siblings):
					raise IndexError
				it = siblings[index]
		return it

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
