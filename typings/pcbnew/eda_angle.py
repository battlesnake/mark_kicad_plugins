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

    def AsTenthsOfADegree(self):
        ...

    def AsRadians(self):
        ...

    def IsCardinal(self):
        ...

    def IsCardinal90(self):
        ...

    def IsZero(self):
        ...

    def IsHorizontal(self):
        ...

    def IsVertical(self):
        ...

    def IsParallelTo(self, aAngle: "EDA_ANGLE"):
        ...

    def Invert(self):
        ...

    def Sin(self):
        ...

    def Cos(self):
        ...

    def Tan(self):
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

    def __iadd__(self, aAngle: "EDA_ANGLE"):
        ...

    def __isub__(self, aAngle: "EDA_ANGLE"):
        ...

    def __add__(self, other: "EDA_ANGLE"):
        ...

    def __sub__(self, other: "EDA_ANGLE"):
        ...

    def __mul__(self, other: "EDA_ANGLE"):
        ...

    def __rmul__(self, other: "EDA_ANGLE"):
        ...

    def __truediv__(self, other: "EDA_ANGLE"):
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
