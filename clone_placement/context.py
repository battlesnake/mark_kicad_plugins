from dataclasses import dataclass
from typing import Mapping, Sequence

from .service import CloneSelection
from .settings import CloneSettings

from ..kicad_v8_model import Project, Footprint, SheetInstance


@dataclass
class TargetFootprint():
	base_sheet: SheetInstance
	footprint: Footprint


FootprintMapping = Mapping[Footprint, Sequence[TargetFootprint]]


@dataclass
class CloneContext():
	project: Project
	selection: CloneSelection
	settings: CloneSettings

	selected_footprints: Sequence[Footprint]
	source_sheet: SheetInstance
	footprint_mapping: FootprintMapping
