from typing import Optional, Sequence, Iterable, overload, final, Union
from dataclasses import dataclass, field
from uuid import UUID
from functools import cached_property

import pcbnew  # pyright: ignore

from .kicad_sexp_parser import KicadSexpNode


SIZE_SCALE: int = 1000000
ROTATION_SCALE: int = 10


Filename = str
Reference = str


@final
@dataclass(frozen=True, eq=True)
class UuidPath(Sequence[UUID]):
	value: Sequence[UUID]

	@overload
	def __getitem__(self, index: int) -> UUID: ...

	@overload
	def __getitem__(self, index: slice) -> "UuidPath": ...

	def __getitem__(self, index: int | slice) -> Union[UUID, "UuidPath"]:
		if isinstance(index, int):
			return self.value[index]
		elif isinstance(index, slice):
			return UuidPath.of(self.value[index])
		else:
			raise ValueError(index)

	def __len__(self) -> int:
		return len(self.value)

	@overload
	def __add__(self, value: UUID) -> "UuidPath": ...

	@overload
	def __add__(self, value: Sequence[UUID]) -> "UuidPath": ...

	def __add__(self, value: UUID | Sequence[UUID]) -> "UuidPath":
		if isinstance(value, UUID):
			return UuidPath.of(list(self.value) + [value])
		elif isinstance(value, Sequence):
			return UuidPath.of(list(self.value) + list(value))
		else:
			raise ValueError(value)

	@overload
	@staticmethod
	def of(value: Iterable[UUID]) -> "UuidPath": ...

	@overload
	@staticmethod
	def of(value: pcbnew.KIID_PATH) -> "UuidPath": ...

	@overload
	@staticmethod
	def of(value: str) -> "UuidPath": ...

	@staticmethod
	def of(value: Iterable[UUID] | pcbnew.KIID_PATH | str) -> "UuidPath":
		if isinstance(value, pcbnew.KIID_PATH):
			return UuidPath.of(
				UUID(hex=str(item.AsString()))
				for item in value
			)
		elif isinstance(value, str):
			return UuidPath.of(
				UUID(hex=part)
				for index, part in enumerate(value.split("/"))
				if not (index == 0 and not part)
			)
		elif isinstance(value, Iterable):
			return UuidPath(value=tuple(value))
		else:
			raise ValueError()

	def __repr__(self) -> str:
		return "/" + "/".join(str(part) for part in self.value)

	def __str__(self) -> str:
		return repr(self)


@dataclass(frozen=True, eq=True)
class SheetTemplate():
	uuid: UUID
	filename: Filename = field(hash=False, compare=False)
	root_node: KicadSexpNode = field(hash=False, compare=False, repr=False)


@dataclass(frozen=True, eq=True)
class SheetInstance():
	uuid: UUID
	name: str = field(hash=False, compare=False)

	template: SheetTemplate = field(hash=False, compare=False)

	parent: Optional["SheetInstance"]

	def __str__(self) -> str:
		return self.name_path

	@cached_property
	def uuid_path(self) -> UuidPath:
		return UuidPath.of(self.uuid_chain)

	@cached_property
	def template_uuid_path(self) -> UuidPath:
		return UuidPath.of(self.template_uuid_chain)

	@cached_property
	def name_path(self) -> str:
		return " / ".join(self.name_chain)

	@cached_property
	def uuid_chain(self) -> Sequence[UUID]:
		if self.parent is None:
			return []
		else:
			return list(self.parent.uuid_chain) + [self.uuid]

	@cached_property
	def template_uuid_chain(self) -> Sequence[UUID]:
		# Omit for root
		if self.parent is None:
			return []
		else:
			return list(self.parent.template_uuid_chain) + [self.template.uuid]

	@cached_property
	def name_chain(self) -> Sequence[str]:
		if self.parent is None:
			return [self.name]
		else:
			return list(self.parent.name_chain) + [self.name]


@dataclass(frozen=True, eq=True)
class Symbol():
	path: UuidPath
	uuid: UUID
	reference: Reference
	unit: int
	value: str

	sheet_instance: SheetInstance = field(hash=False, compare=False)

	def __str__(self) -> str:
		return f"{self.reference}:{self.unit} ({self.value})"


@dataclass(frozen=True, eq=True)
class Footprint():
	path: UuidPath
	reference: Reference
	value: str

	symbol: Symbol = field(hash=False, compare=False, repr=False)

	data: pcbnew.FOOTPRINT = field(hash=False, compare=False, repr=False)

	def __str__(self) -> str:
		return f"{self.reference} ({self.value})"
