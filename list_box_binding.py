from typing import Generic, cast

import wx

from .list_box_adapter import ListBoxAdapter, ListItemType


class ListBoxBinding(Generic[ListItemType]):

	def __init__(self, list_box: wx.ListBox, adapter: ListBoxAdapter[ListItemType]):
		self.list_box = list_box
		self.adapter = adapter
		cast(wx.Frame, wx.GetTopLevelParent(list_box)).Bind(
			wx.EVT_LIST_ITEM_SELECTED,
			list_box,
			self.on_event
		)
		self.update_view()

	def update_view(self) -> None:
		list_box = self.list_box
		adapter = self.adapter
		items = adapter.get_items()
		list_box_items_actual = list_box.GetItems()
		list_box_items_expect = [adapter.get_caption(item) for item in items]
		if list_box_items_actual != list_box_items_expect:
			list_box.Set(list_box_items_expect)
		for index, item in enumerate(items):
			list_box.SetClientData(index, item)
		list_box_selections_actual = set(
			cast(ListItemType, list_box.GetClientData(index))
			for index in list_box.GetSelections()
		)
		list_box_selections_expect = set(adapter.get_selected())
		if list_box_selections_actual != list_box_selections_expect:
			for index, item in enumerate(items):
				if item in list_box_selections_expect:
					list_box.SetSelection(index)
				else:
					list_box.Deselect(index)

	def update_model(self) -> None:
		list_box = self.list_box
		adapter = self.adapter
		selected = [list_box.GetClientData(index) for index in list_box.GetSelections()]
		adapter.set_selected(selected)
		adapter.update_model()

	def update(self) -> None:
		self.update_view()
		self.update_model()

	def on_event(self, event) -> None:
		self.update_model()
