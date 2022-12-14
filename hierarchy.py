from typing import Dict, cast
from dataclasses import dataclass, field
from uuid import UUID

import pcbnew  # pyright: ignore

from .multi_map import MultiMap
from .kicad_entities import Filename, UuidPath, SheetTemplate, SheetInstance, Symbol, Footprint


@dataclass(repr=False)
class Hierarchy():

	templates: Dict[Filename, SheetTemplate] = field(default_factory=lambda:{})

	instances: Dict[UuidPath, SheetInstance] = field(default_factory=lambda:{})
	relations: MultiMap[SheetInstance, SheetInstance] = field(default_factory=lambda:MultiMap())
	root: SheetInstance = field(default_factory=lambda:cast(SheetInstance, None))

	symbols: Dict[UUID, Symbol] = field(default_factory=lambda:{})
	footprints: Dict[UuidPath, Footprint] = field(default_factory=lambda:{})
	symbol_instances: MultiMap[Symbol, Footprint] = field(default_factory=lambda:MultiMap())
