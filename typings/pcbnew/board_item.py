from typing import Sequence

from eda_item import EDA_ITEM


class BOARD_ITEM(EDA_ITEM):

    def __init__ (self, *args, **kwargs):
        ...

    def SetParentGroup(self, aGroup: "PCB_GROUP") -> None:
        ...

    def GetParentGroup(self) -> "PCB_GROUP":
        ...

    def GetX(self) -> int:
        ...

    def GetY(self) -> int:
        ...

    def GetCenter(self) -> "wxPoint":
        ...

    def SetX(self, aX: int) -> None:
        ...

    def SetY(self, aY: int) -> None:
        ...

    def IsConnected(self) -> bool:
        ...

    def IsOnCopperLayer(self) -> bool:
        ...

    def GetEffectiveShape(self, *args) -> "Shape":
        ...

    def GetParent(self) -> "BOARD_ITEM_CONTAINER":
        ...

    def GetParentFootprint(self) -> "BOARD_ITEM_CONTAINER":
        ...

    def GetLayer(self) -> "PCB_LAYER_ID":
        ...

    def GetLayerSet(self) -> "LSET":
        ...

    def SetLayerSet(self, aLayers: "LSET") -> None:
        ...

    def SetLayer(self, aLayer: "PCB_LAYER_ID") -> None:
        ...

    def Duplicate(self) -> "BOARD_ITEM":
        ...

    def SwapData(self, aImage: "BOARD_ITEM") -> None:
        ...

    def IsOnLayer(self, aLayer: "PCB_LAYER_ID") -> bool:
        ...

    def IsTrack(self) -> bool:
        ...

    def IsLocked(self) -> bool:
        ...

    def SetLocked(self, aLocked: bool) -> None:
        ...

    def DeleteStructure(self) -> None:
        ...

    def Move(self, *args) -> None:
        ...

    def Rotate(self, *args) -> None:
        ...

    def Flip(self, *args) -> None:
        ...

    def GetBoard(self, *args) -> "BOARD":

        def GetLayerName(self) -> "wxString":
            ...

    def ViewGetLayers(self, aLayers: Sequence[int], aCount: int) -> None:
        ...

    def TransformShapeWithClearanceToPolygon(self, aCornerBuffer: "SHAPE_POLY_SET", aLayer: "PCB_LAYER_ID", aClearanceValue: int, aError: int, aErrorLoc: "ERROR_LOC", ignoreLineWidth: bool = False) -> None:
        ...

    def	Cast(self):
        ...

    def	Duplicate(self):
        ...

    def	SetPos(self, p):
        ...

    def	SetStartEnd(self, start, end):
        ...