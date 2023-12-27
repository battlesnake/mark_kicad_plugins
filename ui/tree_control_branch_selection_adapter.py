from typing import List, Set, Generic, TypeVar, Iterable, Optional, Dict, Callable, Sequence, Any
from abc import ABC, abstractmethod
from enum import Enum
import wx
import wx.dataview

from .multi_map import MultiMap


ValueType = TypeVar("ValueType")


class TreeItemSelectionState(Enum):
	SELECTED = "selected"
	UNSELECTED = "unselected"
	PARTIAL_SELECTED = "partial_selected"


class TreeSelectionChangeMode(Enum):
	SINGLE = "recursive"
	PARALLEL = "parallel"


class TreeControlBranchSelectionAdapter(ABC, Generic[ValueType]):

	def __init__(
		self,
		items: Iterable[ValueType],
		get_parent: Callable[[ValueType], ValueType | None],
		control: wx.dataview.DataViewTreeCtrl,
		selection: Iterable[ValueType],
	):
		self.items = set(items)
		self.control = control
		self.selection = set(selection)
		self.view_map: Dict[ValueType, wx.dataview.DataViewItem] = {}
		self.icons: Dict[TreeItemSelectionState, str] = {
			TreeItemSelectionState.SELECTED: "●",
			TreeItemSelectionState.UNSELECTED: "○",
			TreeItemSelectionState.PARTIAL_SELECTED: "◐",
		}
		control.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_item_activated)

		self.relations = MultiMap[ValueType, ValueType]()
		queue: List[ValueType] = list(items)
		while queue:
			item = queue.pop()
			parent = get_parent(item)
			if parent is not None:
				self.relations[parent] = item
				if parent not in self.items:
					self.items.add(parent)
					queue.append(parent)
		self.parents = self.relations.invert()

		self.create_view_tree()

	###

	@abstractmethod
	def get_view_text(self, item: ValueType) -> str:
		# Text to display for item in UI
		pass

	@abstractmethod
	def get_item_type_key(self, item: ValueType) -> Any:
		# Value that identifies this item-type in the hierarchy, but but the
		# specific instance.  Used for parallel-selection (alt+click).
		pass

	@abstractmethod
	def get_item_sort_key(self, item: ValueType) -> Any:
		# Value for comparing items to sort them in the UI
		pass

	@abstractmethod
	def selection_changed(self):
		pass

	###

	def get_recursively(self, start: Iterable[ValueType], walker: Callable[[ValueType], Iterable[ValueType]], predicate: Callable[[ValueType], bool] = lambda _: True) -> Set[ValueType]:
		result: Set[ValueType] = set()
		queue: Set[ValueType] = set(start)
		while queue:
			items, queue = queue, set()
			for item in items:
				if predicate(item):
					result.add(item)
				queue.update(walker(item))
		return result

	def is_leaf(self, item: ValueType) -> bool:
		return not self.relations[item]

	def get_leaves(self, start: Iterable[ValueType]):
		return self.get_recursively(start, lambda item: self.relations[item], self.is_leaf)

	def get_downwards(self, start: Iterable[ValueType]) -> Set[ValueType]:
		return self.get_recursively(start, lambda item: self.relations[item])

	def get_upwards(self, start: Iterable[ValueType]) -> Set[ValueType]:
		return self.get_recursively(start, lambda item: [self.parents[item]] if item in self.parents else [])

	def get_parallel_items(self, items: Iterable[ValueType]) -> Set[ValueType]:
		names = {
			self.get_item_type_key(item)
			for item in items
		}
		return {
			item
			for item in self.items
			if self.get_item_type_key(item) in names
		}

	###

	def get_selection_state(self, item: ValueType) -> TreeItemSelectionState:
		leaves = self.get_leaves([item])
		selected_leaves = leaves.intersection(self.selection)
		if len(selected_leaves) == len(leaves):
			return TreeItemSelectionState.SELECTED
		if len(selected_leaves) == 0:
			return TreeItemSelectionState.UNSELECTED
		return TreeItemSelectionState.PARTIAL_SELECTED

	def get_iconised_view_text(self, item: ValueType) -> str:
		selection_state = self.get_selection_state(item)
		icon = self.icons[selection_state]
		text = self.get_view_text(item)
		return f"{icon}  {text}"

	def create_view_tree(self):
		root_node = wx.dataview.DataViewItem(0)
		self.create_view_branch(root_node, None)
		self.control.ExpandChildren(root_node)

	def create_view_branch(self, view_start: wx.dataview.DataViewItem, model_start: Optional[ValueType]):
		if model_start is None:
			items = [
				item
				for item in self.items
				if item not in self.parents
			]
			self.control.DeleteAllItems()
		else:
			items = [
				item
				for item in self.items
				if item in self.relations[model_start]
			]
			self.control.DeleteChildren(view_start)
		for model_item in sorted(items, key=self.get_item_sort_key):
			view_item: wx.dataview.DataViewItem
			if model_item in self.relations:
				view_item = self.control.AppendContainer(
					parent=view_start,
					text=self.get_iconised_view_text(model_item),
					data=model_item,
				)
			else:
				view_item = self.control.AppendItem(
					parent=view_start,
					text=self.get_iconised_view_text(model_item),
					data=model_item,
				)
			self.view_map[model_item] = view_item
			self.create_view_branch(view_item, model_item)
			self.control.Expand(view_item)

	def update_view_item(self, item: ValueType):
		self.control.SetItemText(self.view_map[item], self.get_iconised_view_text(item))

	def set_selected(self, items: Iterable[ValueType], state: bool, mode: TreeSelectionChangeMode):
		if mode == TreeSelectionChangeMode.PARALLEL:
			items = self.get_parallel_items(items)
		leaves = self.get_leaves(items)
		if state:
			self.selection.update(leaves)
		else:
			self.selection.difference_update(leaves)
		for item in self.get_upwards(items).union(self.get_downwards(items)):
			self.update_view_item(item)

	def toggle_selected(self, items: Sequence[ValueType], mode: TreeSelectionChangeMode):
		if not items:
			return
		new_state = self.get_selection_state(items[0]) != TreeItemSelectionState.SELECTED
		self.set_selected(items, new_state, mode)

	def on_item_activated(self, event: wx.Event):
		items: List[ValueType] = [
			self.control.GetItemData(selection)
			for selection in self.control.GetSelections()
		]
		if not items:
			return
		if wx.GetKeyState(wx.WXK_ALT):
			mode = TreeSelectionChangeMode.PARALLEL
		else:
			mode = TreeSelectionChangeMode.SINGLE
		self.toggle_selected(items, mode)
		self.selection_changed()
