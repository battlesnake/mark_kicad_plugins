from typing import Dict, Union
from .board_item import BOARD_ITEM


class NETINFO_ITEM(BOARD_ITEM):

    def GetNetname(self) -> str:
        ...

    def GetNetCode(self) -> int:
        ...


class NETNAMES_MAP():

    def asdict(self) -> Dict[str, NETINFO_ITEM]:
        ...


class NETCODES_MAP():

    def asdict(self) -> Dict[int, NETINFO_ITEM]:
        ...


class NETINFO_LIST():

    def GetNetCount(self) -> int:
        ...

    def GetNetItem(self, item: Union[int, str]) -> NETINFO_ITEM:
        ...

    def GetParent(self) -> "BOARD":
        ...

    def NetsByName(self) -> NETNAMES_MAP:
        ...

    def NetsByNetcode(self) -> NETCODES_MAP:
        ...


from .board import BOARD
