from typing import Any

from eda_item import EDA_ITEM
from eda_text import EDA_TEXT


# TOOD
class FP_TEXT(EDA_ITEM, EDA_TEXT):

    def GetParentAsString(self) -> Any:
        ...

    def KeepUpright(self, aOldOrientation, aNewOrientation) -> Any:
        ...

    def IsParentFlipped(self) -> Any:
        ...

    def Mirror(self, aCentre, aMirrorAroundXAxis) -> Any:
        ...

    def SetType(self, aType) -> Any:
        ...

    def GetType(self) -> Any:
        ...

    def SetPos0(self, aPos) -> Any:
        ...

    def GetPos0(self) -> Any:
        ...

    def GetLength(self) -> Any:
        ...

    def SetDrawCoord(self) -> Any:
        ...

    def SetLocalCoord(self) -> Any:
        ...

    def TextHitTest(self, *args) -> Any:
        ...

    def HitTest(self, *args) -> Any:
        ...

    def TransformTextToPolySet(self, aBuffer, aLayer, aClearance, aError, aErrorLoc) -> Any:
        ...

    def GetEffectiveShape(self, *args) -> Any:
        ...

    def GetShownText(self, aDepth=0, aAllowExtraText=True) -> Any:
        ...

    def ViewGetLOD(self, aLayer, aView) -> Any:
        ...
