from typing import Union, overload


class _TENTHS_OF_A_DEGREE_T():
    ...


class _DEGREE_T():
    ...


TENTHS_OF_A_DEGREE_T = _TENTHS_OF_A_DEGREE_T()
DEGREE_T = _DEGREE_T()


EDA_ANGLE_T = Union[_TENTHS_OF_A_DEGREE_T, _DEGREE_T]


class EDA_ANGLE():

    @overload
    def __init__(self, aValue: float, aAngleType: EDA_ANGLE_T):
        ...

    @overload
    def __init__(self, aVector: "VECTOR2I"):
        ...

    @overload
    def __init__(self):
        ...

    def __init__(self, *args):
        ...

    def AsDegrees(self):
        ...

    def AsTenthsOfADegree(self) -> int:
        ...

    def AsRadians(self) -> float:
        ...

    def IsCardinal(self) -> float:
        ...

    def IsCardinal90(self) -> bool:
        ...

    def IsZero(self) -> bool:
        ...

    def IsHorizontal(self) -> bool:
        ...

    def IsVertical(self) -> bool:
        ...

    def IsParallelTo(self, aAngle: "EDA_ANGLE") -> bool:
        ...

    def Invert(self) -> "EDA_ANGLE":
        ...

    def Sin(self) -> float:
        ...

    def Cos(self) -> float:
        ...

    def Tan(self) -> float:
        ...

    def Normalize(self):
        ...

    def NormalizeNegative(self):
        ...

    def Normalize90(self):
        ...

    def Normalize180(self):
        ...

    def Normalize720(self):
        ...

    def KeepUpright(self):
        ...

    def __iadd__(self, aAngle: "EDA_ANGLE") -> "EDA_ANGLE":
        ...

    def __isub__(self, aAngle: "EDA_ANGLE") -> "EDA_ANGLE":
        ...

    def __add__(self, other: "EDA_ANGLE") -> "EDA_ANGLE":
        ...

    def __sub__(self, other: "EDA_ANGLE") -> "EDA_ANGLE":
        ...

    def __mul__(self, other: "EDA_ANGLE" | float | int) -> "EDA_ANGLE":
        ...

    def __rmul__(self, other: "EDA_ANGLE" | float | int) -> "EDA_ANGLE":
        ...

    def __truediv__(self, other: "EDA_ANGLE" | float | int) -> "EDA_ANGLE":
        ...

    @staticmethod
    def Arccos(x: float) -> "EDA_ANGLE":
        ...

    @staticmethod
    def Arcsin(x: float) -> "EDA_ANGLE":
        ...

    @staticmethod
    def Arctan(x: float) -> "EDA_ANGLE":
        ...

    @staticmethod
    def Arctan2(y: float, x: float) -> "EDA_ANGLE":
        ...

    DEGREES_TO_RADIANS: float

    m_Angle0: "EDA_ANGLE"
    m_Angle45: "EDA_ANGLE"
    m_Angle90: "EDA_ANGLE"
    m_Angle135: "EDA_ANGLE"
    m_Angle180: "EDA_ANGLE"
    m_Angle270: "EDA_ANGLE"
    m_Angle360: "EDA_ANGLE"


from .vector2i import VECTOR2I
