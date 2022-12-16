from typing import Optional, Sequence, Iterable
from dataclasses import dataclass, field
from uuid import UUID
from functools import cached_property

import pcbnew  # pyright: ignore

from .kicad_sexp_parser import KicadSexpNode


SIZE_SCALE: int = 1000000


Filename = str
Reference = str


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

	def __str__(self) -> str:
		return self.name_path

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

	def __str__(self) -> str:
		return f"{self.reference}:{self.unit} ({self.value})"


@dataclass(frozen=True, eq=True)
class Footprint():
	path: UuidPath
	reference: Reference
	value: str

	symbol: Symbol = field(hash=False)

	data: pcbnew.FOOTPRINT = field(hash=False, compare=False, repr=False)

	def __str__(self) -> str:
		return f"{self.reference} ({self.value})"
