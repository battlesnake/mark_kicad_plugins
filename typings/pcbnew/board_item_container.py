from board_item import BOARD_ITEM


class BOARD_ITEM_CONTAINER(BOARD_ITEM):

    def	__init__ (self, *args, **kwargs):
        ...

    def AddNative(self, *args):
        ...

    def RemoveNative(self, *args):
        ...

    def DeleteNative(self, aItem: "BOARD_ITEM"):
        ...

    def GetZoneSettings(self) -> "ZONE_SETTINGS":
        ...

    def SetZoneSettings(self, aSettings: "ZONE_SETTINGS"):
        ...

    def	Add(self, item):
        ...

    def	Remove(self, item):
        ...

    def	Delete(self, item):
        ...
