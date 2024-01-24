from typing import final
from dataclasses import dataclass

from ..kicad_v8_model import Footprint, Vector2, Angle, Layer


PlacementEntity = Footprint


@final
@dataclass(frozen=True)
class Placement():
	position: Vector2
	orientation: Angle
	flipped: bool
	layer: Layer

	@staticmethod
	def of(item: PlacementEntity) -> "Placement":
		if isinstance(item, Footprint):  # Also PAD, but we don't consider those yet
			return Placement(
				position=item.position,
				orientation=item.orientation,
				flipped=not item.layer.type.is_front(),
				layer=item.layer,
			)
		else:
			raise TypeError()
