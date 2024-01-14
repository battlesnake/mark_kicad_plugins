from dataclasses import dataclass
from typing import Iterator, List, Optional, Sequence, Set

from .node import Node


@dataclass
class Selection():
    nodes: List[Node]

    def _get_one(self) -> Node:
        if not self.nodes:
            raise KeyError("No nodes in selection")
        if len(self.nodes) > 1:
            raise KeyError("Multiple nodes in selection")
        return self.nodes[0]

    def __invert__(self):
        """ Deference if a single node is selected """
        return self._get_one()

    @property
    def keys(self) -> Set[str]:
        return set(
            node.key
            for node in self.nodes
        )

    @property
    def key(self) -> str:
        return self._get_one().key

    @property
    def values(self) -> Sequence[str]:
        return self._get_one().values

    @property
    def children(self) -> Sequence[Node]:
        return self._get_one().children

    @property
    def first(self) -> "Selection":
        return Selection([self.nodes[0]])

    def children_by_key(self, key: str) -> "Selection":
        """ Filter children by key """
        nodes = [
            child
            for node in self.nodes
            for child in node.children
            if child.key == key
        ]
        return Selection(nodes)

    def value_by_index(self, index: int, default: Optional[str] = None) -> str:
        """ Get value by index """
        try:
            return self._get_one().values[index]
        except IndexError:
            if default is not None:
                return default
            else:
                raise

    def filter(self, field: int, value: str) -> "Selection":
        """ Filter selection by field value """
        filtered_nodes = [
            node
            for node in self.nodes
            if len(node.values) > field
            if node.values[field] == value
        ]
        return Selection(filtered_nodes)

    def __getitem__(self, index: int) -> str:
        return self.value_by_index(index)

    def __getattr__(self, key: str) -> "Selection":
        return self.children_by_key(key)

    def __bool__(self):
        return bool(self.nodes)

    def __iter__(self) -> Iterator["Selection"]:
        return (
            Selection([node])
            for node in self.nodes
        )

    def __len__(self):
        return len(self.nodes)

    def __str__(self):
        indent = "  "

        def stringify(node: Node, level: int) -> List[str]:
            return (
                [
                    (indent * level) + " ".join([node.key] + list(node.values)),
                ] + [
                    line
                    for child in node.children
                    for line in stringify(child, level + 1)
                ]
            )

        return "\n".join([
            line
            for node in self.nodes
            for line in stringify(node, 0)
        ])

    def __add__(self, other: "Selection"):
        """ Merge selections (no deduplication) """
        return Selection(self.nodes + other.nodes)
