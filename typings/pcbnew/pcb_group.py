from typing import Any

from .board_item import BOARD_ITEM


# TODO
class PCB_GROUP(BOARD_ITEM):

	def __init__(self, aParent) -> Any:
		...

	def GetName(self) -> Any:
		...

	def SetName(self, aName) -> Any:
		...

	def GetItems(self, *args) -> Any:
		...

	def AddItem(self, aItem) -> Any:
		...

	def RemoveItem(self, aItem) -> Any:
		...

	def RemoveAll(self) -> Any:
		...

	def SetLayerRecursive(self, aLayer, aDepth) -> Any:
		...

	def DeepClone(self) -> Any:
		...

	def DeepDuplicate(self) -> Any:
		...

	def HitTest(self, *args) -> Any:
		...

	def GetEffectiveShape(self, *args) -> Any:
		...

	def ViewGetLOD(self, aLayer, aView) -> Any:
		...

	def AddChildrenToCommit(self, aCommit) -> Any:
		...

	def RunOnChildren(self, aFunction) -> Any:
		...

	def RunOnDescendants(self, aFunction) -> Any:
		...
