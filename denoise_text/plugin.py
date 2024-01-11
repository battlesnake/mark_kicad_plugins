from enum import Enum
from typing import final, cast
from dataclasses import dataclass, field
import functools

import pcbnew
from pcbnew import BOX2I, FOOTPRINT, EDA_ANGLE, VECTOR2I, TENTHS_OF_A_DEGREE_T, PCB_TEXT

from ..utils.user_exception import UserException

from ..ui.bored_user_entertainer import BoredUserEntertainer

from ..kicad_v8_native_adapter import Plugin


@dataclass
class Point():
	x: float
	y: float


class LinearInterpolate():

	@staticmethod
	def scalar(a: float, b: float, i: float) -> float:
		return a + i * (b - a)

	@staticmethod
	def rectangle(rect: BOX2I, i: Point) -> Point:
		return Point(
			LinearInterpolate.scalar(rect.GetLeft(), rect.GetRight(), i.x),
			LinearInterpolate.scalar(rect.GetTop(), rect.GetBottom(), i.y)
		)

	@staticmethod
	def space(amount: float, i: float) -> float:
		return LinearInterpolate.scalar(-amount, amount, i)


class Anchor(Enum):

	C = Point(0.5, 0.5)

	N = Point(0.5, 0.0)
	W = Point(0.0, 0.5)
	S = Point(0.5, 1.0)
	E = Point(1.0, 0.5)

	NW = Point(0.0, 0.0)
	SW = Point(0.0, 1.0)
	SE = Point(1.0, 1.0)
	NE = Point(1.0, 0.0)


@dataclass(frozen=True, eq=True)
class LayerConfiguration():

	name: str

	color: str


@dataclass
class TextConfiguration():

	layer: LayerConfiguration

	anchor: Anchor = Anchor.C

	spacing: Point = field(default_factory=lambda: Point(-0.2, -0.2))

	width: float = 0.2
	height: float = 0.2

	thickness: float = 0.04

	bold: bool = False
	italic: bool = False

	upright: bool = True
	angle: float = 0.0
	angle_is_absolute: bool = True


@dataclass
class TextPluginConfiguration():

	reference: TextConfiguration = field(default_factory=lambda: TextConfiguration(
		layer=LayerConfiguration(name="Refs", color="#00FF20FF"),
		anchor=Anchor.N
	))

	value: TextConfiguration = field(default_factory=lambda: TextConfiguration(
		layer=LayerConfiguration(name="Values", color="#00D6FFFF"),
		anchor=Anchor.S
	))

	size_scale: int = 1000000
	angle_scale: int = 10


@final
class TextPlugin(Plugin):

	configuration = TextPluginConfiguration()

	def calc_length(self, value: float) -> int:
		return int(self.configuration.size_scale * value)

	def calc_angle(self, value: float) -> int:
		return int(self.configuration.angle_scale * value)

	@functools.cache
	def find_or_create_layer(self, layer_configuration: LayerConfiguration) -> int:
		layer_name = layer_configuration.name
		layer_id = self.board.GetLayerID(layer_name)
		if layer_id == -1:
			raise UserException(f"Layer \"{layer_name}\" not found in board, and I haven't implemented automatic setup of layers yet")
		return layer_id

	def process_text(self, text: PCB_TEXT, text_configuration: TextConfiguration) -> None:
		footprint = cast(FOOTPRINT, text.GetParentFootprint().Cast())

		text.SetLayer(self.find_or_create_layer(text_configuration.layer))

		text.SetVisible(True)

		text.SetKeepUpright(text_configuration.upright)

		text.SetTextWidth(self.calc_length(text_configuration.width))
		text.SetTextHeight(self.calc_length(text_configuration.height))
		text.SetTextThickness(self.calc_length(text_configuration.thickness))

		angle: int = self.calc_angle(text_configuration.angle)
		if text_configuration.angle_is_absolute:
			angle -= footprint.GetOrientation().AsTenthsOfADegree()
		text.SetTextAngle(EDA_ANGLE(angle, TENTHS_OF_A_DEGREE_T))

		text.SetBold(text_configuration.bold)
		text.SetItalic(text_configuration.italic)

		parent_box: BOX2I = footprint.GetBoundingBox(False, False)
		anchor = text_configuration.anchor.value
		anchor_pt = LinearInterpolate.rectangle(parent_box, anchor)
		anchor_pt.x += LinearInterpolate.space(self.calc_length(text_configuration.spacing.x), anchor.x)
		anchor_pt.y += LinearInterpolate.space(self.calc_length(text_configuration.spacing.y), anchor.y)
		text.SetPosition(VECTOR2I(
			int(anchor_pt.x),
			int(anchor_pt.y)
		))

	def process_footprint(self, footprint: FOOTPRINT) -> None:
		self.process_text(footprint.Reference(), self.configuration.reference)
		self.process_text(footprint.Value(), self.configuration.value)

	def process_board(self) -> None:
		for footprint in self.board.GetFootprints():
			self.process_footprint(footprint)

	def execute(self) -> None:
		self.process_board()

		BoredUserEntertainer.message("Refreshing pcbnew...")
		self.logger.info("Refreshing pcbnew")
		pcbnew.Refresh()
