from pcbnew.eda_angle import EDA_ANGLE
from .vector2i import VECTOR2I
from .pcb_track import PCB_TRACK


class PCB_ARC(PCB_TRACK):

	def SetMid(self, aMid: VECTOR2I):
		...

	def GetMid(self) -> VECTOR2I:
		...

	def GetRadius(self) -> float:
		...

	def GetAngle(self) -> EDA_ANGLE:
		...

	def GetArcAngleStart(self) -> EDA_ANGLE:
		...

	def GetArcAngleEnd(self) -> EDA_ANGLE:
		...

	def HitTest(self, *args) -> bool:
		...

	def IsCCW(self) -> bool:
		...

	def GetEffectiveShape(self, *args) -> Any:  #"SHAPE":
		...

