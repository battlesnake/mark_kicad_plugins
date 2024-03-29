from typing import Union, overload


class VECTOR2I():

    x: int
    y: int

    @overload
    def __init__(self):
        ...

    @overload
    def __init__(self, aPoint: "wxPoint"):
        ...

    @overload
    def __init__(self, aSize: "wxSize"):
        ...

    @overload
    def __init__(self, x: int, y: int):
        ...

    @overload
    def __init__(self, aVec: "VECTOR2I"):
        ...

    def __init__(self, *args):
        ...

    def getWxPoint(self) -> "wxPoint":
        ...

    def getWxSize(self) -> "wxSize":
        ...

    def EuclideanNorm(self) -> float:
        ...

    def SquaredEuclideanNorm(self) -> int:
        ...

    def Perpendicular(self) -> "VECTOR2I":
        ...

    def Resize(self, aNewLength: int) -> "VECTOR2I":
        ...

    def Format(self) -> str:
        ...

    def Cross(self, aVector: "VECTOR2I") -> "VECTOR2I":
        ...

    def Dot(self, aVector: "VECTOR2I") -> int:
        ...

    def __add__(self, aVector: "VECTOR2I") -> "VECTOR2I":
        ...

    def __imul__(self, aVector: "VECTOR2I") -> "VECTOR2I":
        ...

    def __iadd__(self, aVector: "VECTOR2I") -> "VECTOR2I":
        ...

    def __sub__(self, aVector: "VECTOR2I") -> "VECTOR2I":
        ...

    def __isub__(self, aVector: "VECTOR2I") -> "VECTOR2I":
        ...

    def __neg__(self) -> "VECTOR2I":
        ...

    def __mul__(self, aVector: Union[int, "VECTOR2I"]) -> "VECTOR2I":
        ...

    def __truediv__(self, aVector: Union[int, "VECTOR2I"]) -> "VECTOR2I":
        ...

    def __eq__(self, aVector: "VECTOR2I") -> bool:
        ...

    def __ne__(self, aVector: "VECTOR2I") -> bool:
        ...

    def __lt__(self, aVector: "VECTOR2I") -> bool:
        ...

    def __le__(self, aVector: "VECTOR2I") -> bool:
        ...

    def __gt__(self, aVector: "VECTOR2I") -> bool:
        ...

    def __ge__(self, aVector: "VECTOR2I") -> bool:
        ...

    def Set(self, x: int, y: int) -> None:
        ...

    # def Get(self) -> t:

    def __str__(self) -> str:
        ...

    def __repr__(self) -> str:
        ...

    def __len__(self) -> float:
        ...

    def __getitem__(self, index: int) -> int:
        ...

    def __setitem__(self, index: int, val: int) -> int:
        ...

    def __nonzero__(self) -> bool:
        ...
