from dataclasses import dataclass
import math

from .angle import Angle


@dataclass(frozen=True)
class Vector2():
	""" Origin is top-left: x+ across, y+ down """

	x: float
	y: float

	@staticmethod
	def ZERO():
		return Vector2(0, 0)

	def __add__(self, other: "Vector2"):
		return Vector2(
			x=self.x + other.x,
			y=self.y + other.y,
		)

	def __sub__(self, other: "Vector2"):
		return Vector2(
			x=self.x - other.x,
			y=self.y - other.y,
		)

	def __mul__(self, scale: float):
		return Vector2(
			x=self.x * scale,
			y=self.y * scale,
		)

	def __truediv__(self, scale: float):
		return Vector2(
			x=self.x / scale,
			y=self.y / scale,
		)

	def __pos__(self):
		return Vector2(
			x=self.x,
			y=self.y,
		)

	def __neg__(self):
		return Vector2(
			x=-self.x,
			y=-self.y,
		)

	def hadamard(self, other: "Vector2"):
		""" Hadamard product """
		return Vector2(
			x=self.x * other.x,
			y=self.y * other.y,
		)

	def dot(self, other: "Vector2"):
		return (
			self.x * other.x +
			self.y * other.y
		)

	def length(self):
		return math.hypot(self.x, self.y)

	def unit(self):
		return self / self.length()

	def rotate(self, angle: Angle):
		cs = angle.cos()
		sn = angle.sin()
		x = self.x
		y = self.y
		return Vector2(
			x=x * cs - y * sn,
			y=x * sn + y * cs,
		)
