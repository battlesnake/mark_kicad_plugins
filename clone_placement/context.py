from dataclasses import dataclass
from typing import Mapping, Sequence

from .service import CloneSelection
from .settings import CloneSettings

from ..parse_v8 import Schematic, Footprint, SheetInstance


@dataclass
class TargetFootprint():
	base_sheet: SheetInstance
	footprint: Footprint


FootprintMapping = Mapping[Footprint, Sequence[TargetFootprint]]


@dataclass
class CloneContext():
	schematic: Schematic
	selection: CloneSelection
	settings: CloneSettings

	selected_footprints: Sequence[Footprint]
	source_sheet: SheetInstance
	footprint_mapping: FootprintMapping
