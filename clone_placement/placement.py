from typing import final
from dataclasses import dataclass

from ..kicad_v8_model import Footprint

from ..geometry import Vector2, Angle


PlacementEntity = Footprint


@final
@dataclass(frozen=True)
class Placement():
	position: Vector2
	orientation: Angle
	flipped: bool

	@staticmethod
	def of(item: PlacementEntity) -> "Placement":
		if isinstance(item, Footprint):  # Also PAD, but we don't consider those yet
			return Placement(
				position=item.position,
				orientation=item.orientation,
				flipped=item.flipped,
			)
		else:
			raise TypeError()
