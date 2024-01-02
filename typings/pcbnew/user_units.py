from typing import Literal


USER_UNITS_INCH = 0
USER_UNITS_MILLIMETRE = 1
USER_UNITS_MIL = 5


UserUnitsType = Literal[0] | Literal[1] | Literal[5]


def GetUserUnits() -> UserUnitsType:
	...
