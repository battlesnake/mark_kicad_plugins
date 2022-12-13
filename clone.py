from dataclasses import dataclass
from typing import List, TypeVar, Iterable, Union
import functools

import pcbnew  # pyright: ignore

from .plugin import Plugin
from .choice_box import ChoiceBox


@dataclass
class ClonePluginConfiguration():

	pass


ItemType = TypeVar("ItemType", bound=pcbnew.EDA_ITEM)


class ClonePlugin(Plugin):

	def get_anchor_footprint(self, footprints: List[pcbnew.FOOTPRINT]) -> pcbnew.FOOTPRINT:
		names = [str(footprint.GetReference()) for footprint in footprints]
		anchor = ChoiceBox(
			title="Select anchor component",
			message="This component's counterparts in other instances of the sheet will be used as anchors in the PCB layout for rebuilding the subcircuit around",
			choices=names,
			multiple=False
		).execute()
		if anchor is None:
			raise ValueError("No anchor footprint selected")
		return footprints[anchor[0]]

	@staticmethod
	def filter_selected(items: Iterable[ItemType]) -> List[ItemType]:
		return [
			item
			for item in items
			if item.IsSelected()
		]

	def execute(self) -> None:
		board = self.board
		footprints: List[pcbnew.FOOTPRINT] \
				= self.filter_selected(board.GetFootprints())
		if not footprints:
			raise ValueError("No footprints in selection")
		tracks: List[Union[pcbnew.PCB_TRACK, pcbnew.PCB_VIA]] \
				= self.filter_selected(board.GetTracks())
		anchor = self.get_anchor_footprint(footprints)
