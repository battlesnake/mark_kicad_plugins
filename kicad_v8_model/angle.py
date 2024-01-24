from dataclasses import dataclass
from enum import Enum
import math


@dataclass
class AngleUnitInfo():
	radians: float
	circle: float


class AngleUnit(Enum):
	""" Enum value is unit size in radians """
	RADIANS = AngleUnitInfo(1, math.tau)
	DEGREES = AngleUnitInfo(math.pi / 180, 360)


@dataclass(frozen=True)
class Angle():
	""" Clockwise """

	value: float
	unit: AngleUnit

	@staticmethod
	def from_degrees(value: float):
		return Angle(value=value, unit=AngleUnit.DEGREES)

	@staticmethod
	def from_radians(value: float):
		return Angle(value=value, unit=AngleUnit.RADIANS)

	@staticmethod
	def from_fraction(value: float, unit: AngleUnit = AngleUnit.DEGREES):
		return Angle(value=unit.value.circle * value, unit=unit)

	def to_unit(self, unit: AngleUnit):
		if unit == self.unit:
			return self
		else:
			return Angle(self.value * self.unit.value.radians / unit.value.radians, unit=unit)

	def wrap(self):
		circle = self.unit.value.circle
		value = self.value % circle
		if value < 0:
			value += circle
		return Angle(value=value, unit=self.unit)

	@property
	def degrees(self):
		return self.to_unit(AngleUnit.DEGREES).value

	@property
	def radians(self):
		return self.to_unit(AngleUnit.RADIANS).value

	def __add__(self, other: "Angle"):
		return Angle(
			value=self.value + other.to_unit(self.unit).value,
			unit=self.unit,
		)

	def __sub__(self, other: "Angle"):
		return Angle(
			value=self.value - other.to_unit(self.unit).value,
			unit=self.unit,
		)

	def __mul__(self, other: float):
		return Angle(
			value=self.value * other,
			unit=self.unit,
		)

	def __div__(self, other: float):
		return Angle(
			value=self.value / other,
			unit=self.unit,
		)

	def __pos__(self):
		return Angle(
			value=self.value,
			unit=self.unit,
		)

	def __neg__(self):
		return Angle(
			value=-self.value,
			unit=self.unit,
		)

	def sin(self):
		return math.sin(self.radians)

	def cos(self):
		return math.cos(self.radians)

	def tan(self):
		return math.tan(self.radians)
