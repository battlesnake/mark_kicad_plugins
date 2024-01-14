from typing import Any
from .board_item import BOARD_ITEM
from .netinfo import NETINFO_ITEM


# TODO
class BOARD_CONNECTED_ITEM(BOARD_ITEM):

    def GetNet(self) -> NETINFO_ITEM:
        ...

    def SetNet(self, aNetInfo: NETINFO_ITEM) -> Any:
        ...

    def GetNetCode(self) -> int:
        ...

    def SetNetCode(self, code: int) -> Any:
        ...

    def GetNetname(self) -> str:
        ...

    def GetNetnameMsg(self) -> Any:
        ...

    def GetShortNetname(self) -> str:
        ...

    def GetUnescapedShortNetname(self) -> str:
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
