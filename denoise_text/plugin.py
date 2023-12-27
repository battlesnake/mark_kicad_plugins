from typing import final, cast
from dataclasses import dataclass, field
import functools

import pcbnew  # pyright: ignore

from utils.point import Point
from utils.linear_interpolate import LinearInterpolate
from utils.anchor import Anchor
from utils.user_exception import UserException

from ui.bored_user_entertainer import BoredUserEntertainer

from denoise_text.plugin import Plugin


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
		layer_id = self.board.GetLayerID(cast(pcbnew.wxString, layer_name))
		if layer_id == -1:
			raise UserException(f"Layer \"{layer_name}\" not found in board, and I haven't implemented automatic setup of layers yet")
		return layer_id

	def process_text(self, text: pcbnew.PCB_FIELD, text_configuration: TextConfiguration) -> None:
		footprint = cast(pcbnew.FOOTPRINT, text.GetParentFootprint().Cast())

		text.SetLayer(self.find_or_create_layer(text_configuration.layer))

		text.SetVisible(True)

		text.SetKeepUpright(text_configuration.upright)

		text.SetTextWidth(self.calc_length(text_configuration.width))
		text.SetTextHeight(self.calc_length(text_configuration.height))
		text.SetTextThickness(self.calc_length(text_configuration.thickness))

		angle: int = self.calc_angle(text_configuration.angle)
		if text_configuration.angle_is_absolute:
			angle -= footprint.GetOrientation().AsTenthsOfADegree()
		text.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.TENTHS_OF_A_DEGREE_T))

		text.SetBold(text_configuration.bold)
		text.SetItalic(text_configuration.italic)

		parent_box: pcbnew.BOX2I = footprint.GetBoundingBox(False, False)
		anchor = text_configuration.anchor.value
		anchor_pt = LinearInterpolate.rectangle(parent_box, anchor)
		anchor_pt.x += LinearInterpolate.space(self.calc_length(text_configuration.spacing.x), anchor.x)
		anchor_pt.y += LinearInterpolate.space(self.calc_length(text_configuration.spacing.y), anchor.y)
		text.SetPosition(pcbnew.VECTOR2I(
			int(anchor_pt.x),
			int(anchor_pt.y)
		))

	def process_footprint(self, footprint: pcbnew.FOOTPRINT) -> None:
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