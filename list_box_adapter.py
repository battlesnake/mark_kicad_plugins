from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable, Sequence, List, cast

import wx


ValueType = TypeVar("ValueType")


class ListBoxAdapter(Generic[ValueType], ABC):

	def __init__(self, control: wx.ListBox):
		self.control = control
		control.Bind(event=wx.EVT_LISTBOX, handler=self.on_selected_change)

	def update_view(self) -> None:
		control = self.control
		items = self.get_items()
		# Items
		items_actual = control.GetItems()
		items_expect = [
			self.get_caption(item)
			for item in items
		]
		if items_actual != items_expect:
			control.Set(items_expect)
		for index, item in enumerate(items):
			control.SetClientData(index, item)
		# Selections
		selections_actual = set(
			cast(ValueType, control.GetClientData(index))
			for index in control.GetSelections()
		)
		selections_expect = set(self.get_selected())
		if selections_actual != selections_expect:
			for index, item in enumerate(items):
				selected_expect = item in selections_expect
				selected_actual = control.IsSelected(index)
				if selected_actual != selected_expect:
					if item in selections_expect:
						control.SetSelection(index)
					else:
						control.Deselect(index)

	def update_model(self) -> None:
		control = self.control
		selected = [
			cast(ValueType, control.GetClientData(index))
			for index in control.GetSelections()
		]
		self.set_selected(selected)

	###

	def on_selected_change(self, event: wx.Event) -> None:
		self.update_model()

	###

	@abstractmethod
	def get_items(self) -> List[ValueType]:
		pass

	@abstractmethod
	def get_caption(self, item: ValueType) -> str:
		pass

	@abstractmethod
	def get_selected(self) -> Iterable[ValueType]:
		pass

	@abstractmethod
	def set_selected(self, items: Sequence[ValueType]) -> None:
		pass


class StaticListBoxAdapter(Generic[ValueType], ListBoxAdapter[ValueType]):

	def __init__(self, control: wx.ListBox, items: Iterable[ValueType], selection: Iterable[ValueType]):
		super().__init__(control=control)
		self.items = list(items)
		self.selection = list(selection)
		self.update_view()

	def get_items(self) -> List[ValueType]:
		return self.items

	def get_caption(self, item: ValueType) -> str:
		return str(item)

	def get_selected(self) -> Iterable[ValueType]:
		return self.selection

	def set_selected(self, items: Sequence[ValueType]) -> None:
		self.selection = list(items)
		self.selection_changed()

	@abstractmethod
	def selection_changed(self) -> None:
		pass
