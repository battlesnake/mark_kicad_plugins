import pcbnew  # pyright: ignore

from .point import Point

class LinearInterpolate():

	@staticmethod
	def scalar(a: float, b: float, i: float) -> float:
		return a + i * (b - a)

	@staticmethod
	def rectangle(rect: pcbnew.BOX2I, i: Point) -> Point:
		return Point(
			LinearInterpolate.scalar(rect.GetLeft(), rect.GetRight(), i.x),
			LinearInterpolate.scalar(rect.GetTop(), rect.GetBottom(), i.y)
		)

	@staticmethod
	def space(amount: float, i: float) -> float:
		return LinearInterpolate.scalar(-amount, amount, i)
