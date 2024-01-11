from dataclasses import dataclass, field
from typing import Dict, Protocol, runtime_checkable

from .board import Layer
from .entity_path import EntityPath, EntityPathComponent


@runtime_checkable
class HasProperties(Protocol):
	properties: Dict[str, str]


@runtime_checkable
class HasId(Protocol):
	id: EntityPathComponent = field(compare=True, hash=True)


@runtime_checkable
class HasPath(Protocol):
	path: EntityPath = field(compare=True, hash=True)


@runtime_checkable
class OnBoard(Protocol):
	layer: Layer


@runtime_checkable
class HasNet(Protocol):
	net: "Net"


@dataclass
class Net():
	""" In this file to avoid circular dependency if we put it in entities """
	""" TODO: Fix this, move layout entities to anther place separate from schematic stuff """
	number: int = field(compare=True, hash=True)
	name: str
