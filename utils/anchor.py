from enum import Enum

from utils.point import Point


class Anchor(Enum):

	C = Point(0.5, 0.5)

	N = Point(0.5, 0.0)
	W = Point(0.0, 0.5)
	S = Point(0.5, 1.0)
	E = Point(1.0, 0.5)

	NW = Point(0.0, 0.0)
	SW = Point(0.0, 1.0)
	SE = Point(1.0, 1.0)
	NE = Point(1.0, 0.0)

