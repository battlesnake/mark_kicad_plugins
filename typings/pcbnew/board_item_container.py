from .board_item import BOARD_ITEM


class BOARD_ITEM_CONTAINER(BOARD_ITEM):

    def GetZoneSettings(self) -> "ZONE_SETTINGS":
        ...

    def SetZoneSettings(self, aSettings: "ZONE_SETTINGS") -> None:
        ...

    def Add(self, item: BOARD_ITEM) -> None:
        ...

    def Remove(self, item: BOARD_ITEM) -> None:
        ...

    def Delete(self, item: BOARD_ITEM) -> None:
        ...
