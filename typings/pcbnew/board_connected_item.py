from typing import Any
from board_item import BOARD_ITEM


# TODO
class BOARD_CONNECTED_ITEM(BOARD_ITEM):

    def GetNet(self) -> Any:
        ...

    def SetNet(self, aNetInfo) -> Any:
        ...

    def GetNetCode(self) -> Any:
        ...

    def SetNetCode(self, *args) -> Any:
        ...

    def GetNetname(self) -> Any:
        ...

    def GetNetnameMsg(self) -> Any:
        ...

    def GetShortNetname(self) -> Any:
        ...

    def GetUnescapedShortNetname(self) -> Any:
        ...

    def GetOwnClearance(self, aLayer, aSource=None) -> Any:
        ...

    def GetLocalClearanceOverrides(self, aSource) -> Any:
        ...

    def GetLocalClearance(self, aSource) -> Any:
        ...

    def GetEffectiveNetClass(self) -> Any:
        ...

    def GetNetClassName(self) -> Any:
        ...

    def SetLocalRatsnestVisible(self, aVisible) -> Any:
        ...

    def GetLocalRatsnestVisible(self) -> Any:
        ...
