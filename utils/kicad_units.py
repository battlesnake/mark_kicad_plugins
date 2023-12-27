from enum import Enum


class UserUnits(Enum):  # pcbnew.GetUserUnits()
	INCH = 0
	MILLIMETRE = 1
	MIL = 5

	def get_abbreviation(self) -> str:
		return {
			UserUnits.INCH: "in",
			UserUnits.MILLIMETRE: "mm",
			UserUnits.MIL: "mil",
		}[self]


class SizeUnits():
	PER_INCH: int = 25400000
	PER_MILLIMETRE: int = 1000000
	PER_MIL: int = 25400

	@staticmethod
	def get(unit: UserUnits) -> int:
		return {
			UserUnits.INCH: SizeUnits.PER_INCH,
			UserUnits.MILLIMETRE: SizeUnits.PER_MILLIMETRE,
			UserUnits.MIL: SizeUnits.PER_MIL,
		}[unit]


class RotationUnits():
	PER_DEGREE: int = 10
