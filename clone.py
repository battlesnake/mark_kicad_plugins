from dataclasses import dataclass
from enum import Enum
import functools

import pcbnew


# Wanted to add support for having project-local YAML file with the
# configuration so that projects could override the defaults.
#
# But it seems Python still lacks any decent support for easy round-trip
# (de)serialisation, and isn't even close to what C# had 12 years ago.
#
# So let's leave a hardcoded configuration for now.


@dataclass
class Point():
	x: float = 0
	y: float = 0


class LinearInterpolate():

	@staticmethod
	def float(a: float, b: float, i: float) -> float:
		return a + i * (b - a)

	@staticmethod
	def rectangle(rect: pcbnew.EDA_RECT, i: Point) -> Point:
		return Point(
			LinearInterpolate.float(rect.GetLeft(), rect.GetRight(), i.x),
			LinearInterpolate.float(rect.GetTop(), rect.GetBottom(), i.y)
		)

	@staticmethod
	def space(amount: float, i: float) -> float:
		return LinearInterpolate.float(-amount, amount, i)


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

	spacing: Point = Point(-0.2, -0.2)

	width: float = 0.2
	height: float = 0.2

	thickness: float = 0.04

	bold: bool = False
	italic: bool = False

	upright: bool = True
	angle: float = 0.0
	angle_is_absolute: bool = True


@dataclass
class PluginConfiguration():

	reference: TextConfiguration = TextConfiguration(
		layer=LayerConfiguration(name="Refs", color="#00FF20FF"),
		anchor=Anchor.N
	)

	value: TextConfiguration = TextConfiguration(
		layer=LayerConfiguration(name="Values", color="#00D6FFFF"),
		anchor=Anchor.S
	)

	size_scale: int = 1000000
	angle_scale: int = 10


class Plugin():

	def __init__(self, board: pcbnew.BOARD, configuration: PluginConfiguration):
		self.board = board
		self.configuration = configuration

	def calc_length(self, value: float) -> int:
		return int(self.configuration.size_scale * value)

	def calc_angle(self, value: float) -> int:
		return int(self.configuration.angle_scale * value)

	@functools.cache
	def find_or_create_layer(self, layer_configuration: LayerConfiguration) -> int:
		layer_name = layer_configuration.name
		layer_id = self.board.GetLayerID(layer_name)
		if layer_id == -1:
			raise ValueError(f"Layer \"{layer_name}\" not found in board, and I haven't implemented automatic setup of layers yet")
		return layer_id

	def process_text(self, text: pcbnew.PCB_TEXT, text_configuration: TextConfiguration) -> None:
		footprint = text.GetParentFootprint().Cast()

		text.SetLayer(self.find_or_create_layer(text_configuration.layer))

		text.SetVisible(True)

		text.SetKeepUpright(text_configuration.upright)

		text.SetTextWidth(self.calc_length(text_configuration.width))
		text.SetTextHeight(self.calc_length(text_configuration.height))
		text.SetTextThickness(self.calc_length(text_configuration.thickness))

		angle = self.calc_angle(text_configuration.angle)
		if text_configuration.angle_is_absolute:
			angle -= footprint.GetOrientation()
		text.SetTextAngle(angle)

		text.SetBold(text_configuration.bold)
		text.SetItalic(text_configuration.italic)

		parent_box = footprint.GetBoundingBox(False, False)
		anchor = text_configuration.anchor.value
		anchor_pt = LinearInterpolate.rectangle(parent_box, anchor)
		anchor_pt.x += LinearInterpolate.space(self.calc_length(text_configuration.spacing.x), anchor.x)
		anchor_pt.y += LinearInterpolate.space(self.calc_length(text_configuration.spacing.y), anchor.y)
		text.SetPosition(pcbnew.wxPoint(
			anchor_pt.x,
			anchor_pt.y
		))

	def process_footprint(self, footprint: pcbnew.FOOTPRINT) -> None:
		self.process_text(footprint.Reference(), self.configuration.reference)
		self.process_text(footprint.Value(), self.configuration.value)

	def process_board(self) -> None:
		for footprint in self.board.GetFootprints():
			self.process_footprint(footprint)

	def execute(self) -> None:
		self.process_board()
