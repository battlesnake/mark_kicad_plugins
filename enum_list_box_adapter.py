from typing import TypeVar, Generic, Iterable, Sequence, List, Callable
from enum import Enum

from .list_box_adapter import ListBoxAdapter


EnumListItemType = TypeVar("EnumListItemType", bound=Enum)


class SingleEnumListBoxAdapter(Generic[EnumListItemType], ListBoxAdapter[EnumListItemType]):

	def __init__(self, value: EnumListItemType, update_model: Callable[[EnumListItemType], None]):
		self.value = value
		self._update_model = update_model

	def get_items(self) -> List[EnumListItemType]:
		return list(self.__args__[0])

	def get_caption(self, item: EnumListItemType) -> str:
		return item.name

	def get_selected(self) -> Iterable[EnumListItemType]:
		return [self.value]

	def set_selected(self, items: Sequence[EnumListItemType]) -> None:
		self.value = items[0]

	def update_model(self):
		self._update_model(self.value)


class MultipleEnumListBoxAdapter(Generic[EnumListItemType], ListBoxAdapter[EnumListItemType]):

	def __init__(self, value: Iterable[EnumListItemType], update_model: Callable[[Sequence[EnumListItemType]], None]):
		self.value = value
		self._update_model = update_model

	def get_items(self) -> List[EnumListItemType]:
		return list(self.__args__[0])

	def get_caption(self, item: EnumListItemType) -> str:
		return item.name

	def get_selected(self) -> Iterable[EnumListItemType]:
		return self.value

	def set_selected(self, items: Sequence[EnumListItemType]) -> None:
		self.value = items

	def update_model(self):
		self._update_model(list(self.value))
