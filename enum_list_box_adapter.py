from typing import TypeVar, Generic, Iterable, Sequence, List, Callable, get_args, final, Type, Optional
from enum import Enum

from .list_box_adapter import ListBoxAdapter


EnumListItemType = TypeVar("EnumListItemType", bound=Enum)


@final
class SingleEnumListBoxAdapter(Generic[EnumListItemType], ListBoxAdapter[EnumListItemType]):

	def __init__(
		self,
		type: Type[EnumListItemType],
		update: Callable[[EnumListItemType], None],
		value: Optional[EnumListItemType] = None
	):
		self.type = type
		self.value = list(type)[0] if value is None else value
		self._update = update

	def get_items(self) -> List[EnumListItemType]:
		return list(self.type)

	def get_caption(self, item: EnumListItemType) -> str:
		return item.name

	def get_selected(self) -> Iterable[EnumListItemType]:
		return [self.value]

	def set_selected(self, items: Sequence[EnumListItemType]) -> None:
		self.value = items[0]

	def update(self):
		self._update(self.value)


@final
class MultipleEnumListBoxAdapter(Generic[EnumListItemType], ListBoxAdapter[EnumListItemType]):

	def __init__(
		self,
		type: Type[EnumListItemType],
		update: Callable[[Sequence[EnumListItemType]], None],
		value: Optional[Iterable[EnumListItemType]] = None
	):
		self.type = type
		self.value = [] if value is None else value
		self._update = update

	def get_items(self) -> List[EnumListItemType]:
		return list(self.type)

	def get_caption(self, item: EnumListItemType) -> str:
		return item.name

	def get_selected(self) -> Iterable[EnumListItemType]:
		return self.value

	def set_selected(self, items: Sequence[EnumListItemType]) -> None:
		self.value = items

	def update(self):
		self._update(list(self.value))
