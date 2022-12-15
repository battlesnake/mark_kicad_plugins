from typing import Generic, cast

import wx

from .list_box_adapter import ListBoxAdapter, ListItemType


class ListBoxBinding(Generic[ListItemType]):

	def __init__(self, list_box: wx.ListBox, adapter: ListBoxAdapter[ListItemType]):
		self.list_box = list_box
		self.adapter = adapter
		list_box.Bind(event=wx.EVT_LISTBOX, handler=self.on_selected_change)

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
				selected_expect = item in list_box_selections_expect
				selected_actual = list_box.IsSelected(index)
				if selected_actual != selected_expect:
					if item in list_box_selections_expect:
						list_box.SetSelection(index)
					else:
						list_box.Deselect(index)

	def update_model(self) -> None:
		list_box = self.list_box
		adapter = self.adapter
		selected = [list_box.GetClientData(index) for index in list_box.GetSelections()]
		adapter.set_selected(selected)
		adapter.update()

	def update(self) -> None:
		self.update_view()
		self.update_model()

	def on_selected_change(self, event) -> None:
		self.update_model()
