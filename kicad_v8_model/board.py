from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class BoardLayer(Enum):
	"""
	Lifted from Kicad official docs, canonical layer names
	Used here under Creative Commons Attribution License version 3.0 license
	"""
	F_Cu = "F.Cu"
	In1_Cu = "In1.Cu"
	In2_Cu = "In2.Cu"
	In3_Cu = "In3.Cu"
	In4_Cu = "In4.Cu"
	In5_Cu = "In5.Cu"
	In6_Cu = "In6.Cu"
	In7_Cu = "In7.Cu"
	In8_Cu = "In8.Cu"
	In9_Cu = "In9.Cu"
	In10_Cu = "In10.Cu"
	In11_Cu = "In11.Cu"
	In12_Cu = "In12.Cu"
	In13_Cu = "In13.Cu"
	In14_Cu = "In14.Cu"
	In15_Cu = "In15.Cu"
	In16_Cu = "In16.Cu"
	In17_Cu = "In17.Cu"
	In18_Cu = "In18.Cu"
	In19_Cu = "In19.Cu"
	In20_Cu = "In20.Cu"
	In21_Cu = "In21.Cu"
	In22_Cu = "In22.Cu"
	In23_Cu = "In23.Cu"
	In24_Cu = "In24.Cu"
	In25_Cu = "In25.Cu"
	In26_Cu = "In26.Cu"
	In27_Cu = "In27.Cu"
	In28_Cu = "In28.Cu"
	In29_Cu = "In29.Cu"
	In30_Cu = "In30.Cu"
	B_Cu = "B.Cu"
	B_Adhes = "B.Adhes"
	F_Adhes = "F.Adhes"
	B_Paste = "B.Paste"
	F_Paste = "F.Paste"
	B_SilkS = "B.SilkS"
	F_SilkS = "F.SilkS"
	B_Mask = "B.Mask"
	F_Mask = "F.Mask"
	Dwgs_User = "Dwgs.User"
	Cmts_User = "Cmts.User"
	Eco1_User = "Eco1.User"
	Eco2_User = "Eco2.User"
	Edge_Cuts = "Edge.Cuts"
	Margin = "Margin"
	F_CrtYd = "F.CrtYd"
	B_CrtYd = "B.CrtYd"
	F_Fab = "F.Fab"
	B_Fab = "B.Fab"
	User_1 = "User.1"
	User_2 = "User.2"
	User_3 = "User.3"
	User_4 = "User.4"
	User_5 = "User.5"
	User_6 = "User.6"
	User_7 = "User.7"
	User_8 = "User.8"
	User_9 = "User.9"

	def is_front(self):
		return self.value.startswith("F.")

	def is_back(self):
		return self.value.startswith("B.")

	def is_inner(self):
		return self.value.startswith("In")

	def is_user(self):
		return self.value.startswith("User.")

	@property
	def opposite(self):
		parts = self.value.split(".", maxsplit=2)
		if parts[0] == "F":
			return "B." + parts[1]
		if parts[0] == "B":
			return "F." + parts[1]
		raise ValueError("Opposite layer is not well-defined")

	@property
	def index(self):
		return self.id_map().index(self)

	@staticmethod
	def id_map() -> Sequence["BoardLayer"]:
		return [
			BoardLayer.F_Cu,
			BoardLayer.In1_Cu,
			BoardLayer.In2_Cu,
			BoardLayer.In3_Cu,
			BoardLayer.In4_Cu,
			BoardLayer.In5_Cu,
			BoardLayer.In6_Cu,
			BoardLayer.In7_Cu,
			BoardLayer.In8_Cu,
			BoardLayer.In9_Cu,
			BoardLayer.In10_Cu,
			BoardLayer.In11_Cu,
			BoardLayer.In12_Cu,
			BoardLayer.In13_Cu,
			BoardLayer.In14_Cu,
			BoardLayer.In15_Cu,
			BoardLayer.In16_Cu,
			BoardLayer.In17_Cu,
			BoardLayer.In18_Cu,
			BoardLayer.In19_Cu,
			BoardLayer.In20_Cu,
			BoardLayer.In21_Cu,
			BoardLayer.In22_Cu,
			BoardLayer.In23_Cu,
			BoardLayer.In24_Cu,
			BoardLayer.In25_Cu,
			BoardLayer.In26_Cu,
			BoardLayer.In27_Cu,
			BoardLayer.In28_Cu,
			BoardLayer.In29_Cu,
			BoardLayer.In30_Cu,
			BoardLayer.B_Cu,
			BoardLayer.B_Adhes,
			BoardLayer.F_Adhes,
			BoardLayer.B_Paste,
			BoardLayer.F_Paste,
			BoardLayer.B_SilkS,
			BoardLayer.F_SilkS,
			BoardLayer.B_Mask,
			BoardLayer.F_Mask,
			BoardLayer.Dwgs_User,
			BoardLayer.Cmts_User,
			BoardLayer.Eco1_User,
			BoardLayer.Eco2_User,
			BoardLayer.Edge_Cuts,
			BoardLayer.Margin,
			BoardLayer.B_CrtYd,
			BoardLayer.F_CrtYd,
			BoardLayer.B_Fab,
			BoardLayer.F_Fab,
			BoardLayer.User_1,
			BoardLayer.User_2,
			BoardLayer.User_3,
			BoardLayer.User_4,
			BoardLayer.User_5,
			BoardLayer.User_6,
			BoardLayer.User_7,
			BoardLayer.User_8,
			BoardLayer.User_9,
		]


@dataclass
class Layer():
	number: int
	name: str
	type: BoardLayer
