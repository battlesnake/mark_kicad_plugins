from typing import Sequence, overload

from .kicad_t import KICAD_T
from .vector2i import VECTOR2I
from .box2i import BOX2I


EDA_ITEM_FLAGS = int


class EDA_ITEM():

    def Type(self) -> KICAD_T:
        ...

    def GetParent(self) -> "EDA_ITEM":
        ...

    def SetParent(self, aParent: "EDA_ITEM") -> None:
        ...

    def IsModified(self) -> bool:
        ...

    def IsNew(self) -> bool:
        ...

    def IsMoving(self) -> bool:
        ...

    def IsSelected(self) -> bool:
        ...

    def IsEntered(self) -> bool:
        ...

    def IsBrightened(self) -> bool:
        ...

    def IsRollover(self) -> bool:
        ...

    def SetSelected(self) -> None:
        ...

    def SetBrightened(self) -> None:
        ...

    def ClearSelected(self) -> None:
        ...

    def ClearBrightened(self) -> None:
        ...

    def SetModified(self) -> None:
        ...

    def GetState(self, type: EDA_ITEM_FLAGS) -> int:
        ...

    def SetState(self, type: EDA_ITEM_FLAGS, state: bool) -> None:
        ...

    def GetStatus(self) -> EDA_ITEM_FLAGS:
        ...

    def SetStatus(self, aStatus: EDA_ITEM_FLAGS) -> None:
        ...

    def SetFlags(self, aMask: EDA_ITEM_FLAGS) -> None:
        ...

    def XorFlags(self, aMask: EDA_ITEM_FLAGS) -> None:
        ...

    def ClearFlags(self, flags: EDA_ITEM_FLAGS) -> None:
        ...

    def GetFlags(self) -> EDA_ITEM_FLAGS:
        ...

    def HasFlag(self, aFlag: EDA_ITEM_FLAGS) -> bool:
        ...

    def GetEditFlags(self) -> EDA_ITEM_FLAGS:
        ...

    def ClearTempFlags(self) -> None:
        ...

    def ClearEditFlags(self) -> None:
        ...

    def RenderAsBitmap(self, aWorldScale: float) -> bool:
        ...

    def SetIsShownAsBitmap(self, aBitmap: bool) -> None:
        ...

    def IsShownAsBitmap(self) -> bool:
        ...

    def IsType(self, aScanTypes: Sequence[KICAD_T]) -> bool:
        ...

    def SetForceVisible(self, aEnable: bool):
        ...

    def IsForceVisible(self) -> bool:
        ...

    def GetMsgPanelInfo(self, aFrame, aList):
        ...

    def GetFriendlyName(self) -> "wxString":
        ...

    @overload
    def HitTest(self, aPosition: VECTOR2I, aAccuracy: int = 0) -> bool:
        ...

    @overload
    def HitTest(self, aRect: BOX2I, aContained: bool, aAccuracy: int = 0) -> bool:
        ...

    def GetBoundingBox(self) -> BOX2I:
        ...

    def GetPosition(self) -> VECTOR2I:
        ...

    def SetPosition(self, aPos: VECTOR2I) -> None:
        ...

    def GetFocusPosition(self) -> VECTOR2I:
        ...

    def GetSortPosition(self) -> VECTOR2I:
        ...

    def Clone(self) -> "EDA_ITEM":
        ...

    def Visit(self, inspector, testData, aScanTypes):
        ...

    def GetClass(self):
        ...

    def GetTypeDesc(self) -> "wxString":
        ...

    def GetItemDescription(self, aUnitsProvider) -> "wxString":
        ...

    def GetMenuImage(self):
        ...

    def Matches(self, aSearchData, aAuxData):
        ...

    def Replace(self, *args):
        ...

    def IsReplaceable(self) -> bool:
        ...

    def __lt__(self, aItem: "EDA_ITEM") -> bool:
        ...

    def ViewBBox(self) -> BOX2I:
        ...

    def ViewGetLayers(self, aLayers: Sequence[int], aCount: int):
        ...
