from typing import Optional, Sequence, Set, Iterable, List
from dataclasses import dataclass
from enum import Enum
from logging import Logger

import wx

import pcbnew  # pyright: ignore

from .wx_utils import WxUtils
from .list_box_binding import ListBoxBinding
from .list_box_adapter import ListBoxAdapter
from .enum_list_box_adapter import SingleEnumListBoxAdapter
from .hierarchy_parser import SheetInstance, Footprint
from .string_utils import StringUtils


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
	anchor: Footprint
	instances: Set[SheetInstance]
	positioning: ClonePositionSettings

	def is_valid(self) -> bool:
		return self.anchor is not None \
				and not not self.instances


class CloneSettingsDialog():

	def __init__(
		self,
		logger: Logger,
		footprints: Iterable[Footprint],
		instances: Iterable[SheetInstance],
		settings: Optional[CloneSettings] = None
	):
		self.logger = logger
		if not footprints:
			raise ValueError("No footprints provided")
		self.footprints = sorted(footprints, key=lambda footprint: footprint.reference)
		self.instances = sorted(instances, key=lambda instance: instance.name_path)
		if settings is None:
			settings = CloneSettings(
				anchor=self.footprints[0],
				instances=set(),
				positioning=ClonePositionSettings()
			)
		self.settings = settings

	def execute(self) -> bool:
		logger = self.logger
		footprints = self.footprints
		instances: List[SheetInstance] = self.instances
		settings = self.settings

		settings.instances = set(instances)

		class AnchorListBoxAdapter(ListBoxAdapter[Footprint]):
			def get_items(self): return footprints
			def get_caption(self, item: Footprint): return f"{item.reference} ({item.value})"
			def get_selected(self): return [settings.anchor]
			def set_selected(self, items: Sequence[Footprint]): settings.anchor = items[0]
			def update(self): ok_button.Enable(settings.is_valid())

		class InstancesListBoxAdapter(ListBoxAdapter[SheetInstance]):
			def __init__(self):
				self.prev_selection: Set[SheetInstance] = settings.instances
			def get_items(self): return instances
			def get_caption(self, item: SheetInstance): return item.name_path
			def get_selected(self): return settings.instances
			def set_selected(self, items: Sequence[SheetInstance]):
				settings.instances = set(items)
				self.update_hierarchical_selection()
			def update(self): ok_button.Enable(settings.is_valid())
			def update_hierarchical_selection(self):
				prev_selection = self.prev_selection
				selection = settings.instances
				selected: Set[SheetInstance] = selection.difference(prev_selection)
				deselected: Set[SheetInstance] = prev_selection.difference(selection)
				to_select: Set[SheetInstance] = set()
				to_deselect: Set[SheetInstance] = set()
				for instance in instances:
					for item in deselected:
						if StringUtils.is_child_of(instance.uuid_chain, item.uuid_chain):
							to_deselect.add(instance)
					for item in selected:
						if StringUtils.is_child_of(item.uuid_chain, instance.uuid_chain):
							to_select.add(instance)
				to_select.difference_update(selection)
				to_deselect.intersection_update(selection)
				if not to_select and not to_deselect:
					self.prev_selection = set(settings.instances)
					return
				result = settings.instances.difference(to_deselect).union(to_select)
				settings.instances = result
				self.prev_selection = result
				instances_binding.update_view()

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
			position_strategy_binding = ListBoxBinding(position_strategy_list_box, SingleEnumListBoxAdapter(ClonePositionStrategy, position_strategy_update_model))

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
			hbox.Add(WxUtils.wrap_control_with_caption(instances_list_box, "Select instances to clone to", wx.EXPAND))
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
			instances_binding.update()
			position_strategy_binding.update()

		return dialog.get_result()
