from typing import Any
from .board_item import BOARD_ITEM
from .eda_text import EDA_TEXT


class PCB_TEXT(BOARD_ITEM, EDA_TEXT):

    def GetShownText(self, aDepth=0, aAllowExtraText=True) -> str:
        ...

    def Mirror(self, aCentre, aMirrorAroundXAxis) -> Any:
        ...

    def TextHitTest(self, *args) -> Any:
        ...

    def HitTest(self, *args) -> Any:
        ...

    def TransformTextToPolySet(self, aBuffer, aLayer, aClearance, aError, aErrorLoc) -> Any:
        ...

    def TransformShapeToPolygon(self, aBuffer, aLayer, aClearance, aError, aErrorLoc, aIgnoreLineWidth=False) -> Any:
        ...

    def GetEffectiveShape(self, *args) -> Any:
        ...

    def ViewGetLOD(self, aLayer, aView) -> Any:
        ...
