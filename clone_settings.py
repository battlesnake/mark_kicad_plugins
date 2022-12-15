from typing import List, Optional, Sequence, Set, Iterable
from dataclasses import dataclass
from enum import Enum

import pcbnew  # pyright: ignore

from .list_box_binding import ListBoxBinding
from .list_box_adapter import ListBoxAdapter
from .enum_list_box_adapter import SingleEnumListBoxAdapter
from .hierarchy_parser import SheetInstance, SheetID


Footprint = pcbnew.FOOTPRINT
Instance = SheetInstance


class ClonePositionStrategy(Enum):
	RELATIVE = "relative"
	HORIZONTAL = "horizontal"
	VERTICAL = "vertical"


@dataclass
class ClonePositionSettings():
	strategy: ClonePositionStrategy = ClonePositionStrategy.RELATIVE
	# main_interval: float = 1
	# wrap: bool = False
	# wrap_count: int = 8
	# cross_interval: float = 1


@dataclass
class CloneSettings():
	anchor: Optional[Footprint]
	instances: Set[Instance]
	positioning: ClonePositionSettings

	def is_valid(self) -> bool:
		return self.anchor is not None \
				and not not self.instances


class CloneSettingsDialog():

	def __init__(
		self,
		footprints: Iterable[Footprint],
		instances: Iterable[Instance],
		settings: Optional[CloneSettings] = None
	):
		self.footprints = sorted(footprints, key=lambda footprint: str(footprint.GetReference()))
		self.instances = sorted(instances, key=lambda instance: " / ".join(instance.name_chain()))
		if settings is None:
			settings = CloneSettings(
				anchor=None,
				instances=set(),
				positioning=ClonePositionSettings()
			)
		self.settings = settings

	def execute(self) -> bool:
		import wx
		from .wx_utils import WxUtils


		footprints = self.footprints
		instances: Iterable[Instance] = self.instances
		settings = self.settings

		if not footprints:
			raise ValueError("No footprints provided")

		if settings.anchor is None or settings.anchor not in footprints:
			settings.anchor = footprints[0]

		settings.instances = settings.instances.intersection(instances)

		class AnchorListBoxAdapter(ListBoxAdapter[Footprint]):
			def get_items(self): return footprints
			def get_caption(self, item: Footprint): return item.GetReference()
			def get_selected(self): return [settings.anchor]
			def set_selected(self, items: Sequence[Footprint]): settings.anchor = items[0] if items else None
			def update_model(self):
				ok_button.Enable(settings.is_valid())

		class InstancesListBoxAdapter(ListBoxAdapter[Instance]):
			def get_items(self): return instances
			def get_caption(self, item): return item
			def get_selected(self): return settings.instances
			def set_selected(self, items: Sequence[Instance]): settings.instances = set(items)
			def update_model(self):
				ok_button.Enable(settings.is_valid())

		def position_strategy_update_model(value: ClonePositionStrategy):
			settings.positioning.strategy = value

		def ok_button_click(event) -> None:
			dialog.set_result(True)
			frame.Close()

		dialog = WxUtils.dialog("Mark's clone plugin", False)

		with dialog as frame:

			message_text = wx.StaticText(frame, -1, "Clone settings")

			anchor_list_box = wx.ListBox(frame, -1, choices=[], style=wx.LB_SINGLE | wx.LB_SORT, size=(200, 300))
			anchor_binding = ListBoxBinding(anchor_list_box, AnchorListBoxAdapter())

			instances_list_box = wx.ListBox(frame, -1, choices=[], style=wx.LB_MULTIPLE | wx.LB_SORT, size=(500, 300))
			instances_binding = ListBoxBinding(instances_list_box, InstancesListBoxAdapter())

			position_strategy_list_box = wx.ListBox(frame, -1, choices=[], style=wx.LB_SINGLE)
			position_strategy_binding = ListBoxBinding(position_strategy_list_box, SingleEnumListBoxAdapter(ClonePositionStrategy.RELATIVE, position_strategy_update_model))

			ok_button = wx.Button(frame, -1, "Ok")
			frame.Bind(wx.EVT_BUTTON, ok_button_click, ok_button)

			"""
			Layout structure:
			 - vertical vbox:
				- spacer
				- caption
				- spacer
				- horizontal hbox:
				  - spacer
				  - vertical vbox:
					- text
					- anchor single-select list
				  - spacer
				  - vertical vbox:
					- text
					- instances multi-select list
				  - spacer
				  - vertical vbox:
					- text
					- position-strategy single-select list
					- TODO
				  - spacer
				- spacer
				- button
				- spacer
			"""

			pos_vbox = wx.BoxSizer(wx.VERTICAL)
			pos_vbox.Add(WxUtils.wrap_control_with_caption(position_strategy_list_box, "Positioning strategy", wx.ADJUST_MINSIZE))

			hbox = wx.BoxSizer(wx.HORIZONTAL)
			hbox.AddSpacer(10)
			hbox.Add(WxUtils.wrap_control_with_caption(anchor_list_box, "Select anchor", wx.EXPAND))
			hbox.AddSpacer(10)
			hbox.Add(WxUtils.wrap_control_with_caption(instances_list_box, "Select instances", wx.EXPAND))
			hbox.AddSpacer(10)
			hbox.Add(pos_vbox)
			hbox.AddSpacer(10)

			vbox = wx.BoxSizer(wx.VERTICAL)
			vbox.AddSpacer(10)
			vbox.Add(message_text, flag=wx.ADJUST_MINSIZE)
			vbox.AddSpacer(10)
			vbox.Add(hbox, flag=wx.EXPAND)
			vbox.AddSpacer(10)
			vbox.Add(ok_button, flag=wx.ADJUST_MINSIZE)
			vbox.AddSpacer(10)

			frame.SetSizer(vbox)
			vbox.Fit(frame)

			anchor_binding.update()

		return dialog.get_result()
