from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable, List, cast

import wx


ValueType = TypeVar("ValueType")


class ChoiceAdapter(Generic[ValueType], ABC):

	def __init__(self, control: wx.Choice):
		self.control = control
		control.Bind(event=wx.EVT_CHOICE, handler=self.on_selected_change)

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
		selection_actual = cast(ValueType, control.GetClientData(control.GetSelection()))
		selection_expect = self.get_selected()
		if selection_actual != selection_expect:
			for index, item in enumerate(items):
				if item == selection_expect:
					control.SetSelection(index)
					break

	def update_model(self) -> None:
		control = self.control
		selected = cast(ValueType, control.GetClientData(control.GetSelection()))
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
	def get_selected(self) -> ValueType:
		pass

	@abstractmethod
	def set_selected(self, item: ValueType) -> None:
		pass


class StaticChoiceAdapter(Generic[ValueType], ChoiceAdapter[ValueType]):

	def __init__(self, control: wx.Choice, items: Iterable[ValueType], selection: ValueType):
		super().__init__(control=control)
		self.items = list(items)
		self.selection = selection
		self.update_view()

	def get_items(self) -> List[ValueType]:
		return self.items

	def get_caption(self, item: ValueType) -> str:
		return str(item)

	def get_selected(self) -> ValueType:
		return self.selection

	def set_selected(self, item: ValueType) -> None:
		self.selection = item
		self.selection_changed()

	@abstractmethod
	def selection_changed(self) -> None:
		pass
