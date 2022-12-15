from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable, Sequence, List, Optional


ListItemType = TypeVar("ListItemType")


class ListBoxAdapter(Generic[ListItemType], ABC):

	@abstractmethod
	def get_items(self) -> List[ListItemType]:
		pass

	@abstractmethod
	def get_caption(self, item: ListItemType) -> str:
		pass

	@abstractmethod
	def get_selected(self) -> Iterable[ListItemType]:
		pass

	@abstractmethod
	def set_selected(self, items: Sequence[ListItemType]) -> None:
		pass

	@abstractmethod
	def update(self) -> None:
		pass
