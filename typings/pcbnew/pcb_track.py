from typing import Any

from .board_connected_item import BOARD_CONNECTED_ITEM


# TODO
class PCB_TRACK(BOARD_CONNECTED_ITEM):

	def Mirror(self, aCentre, aMirrorAroundXAxis) -> Any:
		...

	def SetWidth(self, aWidth) -> Any:
		...

	def GetWidth(self) -> Any:
		...

	def SetEnd(self, aEnd) -> Any:
		...

	def GetEnd(self) -> Any:
		...

	def SetStart(self, aStart) -> Any:
		...

	def GetStart(self) -> Any:
		...

	def SetEndX(self, aX) -> Any:
		...

	def SetEndY(self, aY) -> Any:
		...

	def GetEndX(self) -> Any:
		...

	def GetEndY(self) -> Any:
		...

	def GetEndPoint(self, aEndPoint) -> Any:
		...

	def GetLength(self) -> Any:
		...

	def TransformShapeToPolygon(self, aBuffer, aLayer, aClearance, aError, aErrorLoc, ignoreLineWidth=False) -> Any:
		...

	def GetEffectiveShape(self, *args) -> Any:
		...

	def IsPointOnEnds(self, point, min_dist=0) -> Any:
		...

	def IsNull(self) -> Any:
		...

	def HitTest(self, *args) -> Any:
		...

	def ApproxCollinear(self, aTrack) -> Any:
		...

	def GetWidthConstraint(self, aSource) -> Any:
		...

	def ViewGetLOD(self, aLayer, aView) -> Any:
		...

	def GetCachedLOD(self) -> Any:
		...

	def SetCachedLOD(self, aLOD) -> Any:
		...

	def GetCachedScale(self) -> Any:
		...

	def SetCachedScale(self, aScale) -> Any:
		...
