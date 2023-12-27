from typing import TypeVar, Sequence, Iterable
from functools import reduce


T = TypeVar("T")


class StringUtils():

	@staticmethod
	def is_child_of(parent: Sequence[T], child: Sequence[T]) -> bool:
		return len(parent) < len(child) and child[0:len(parent)] == parent

	@staticmethod
	def is_same_or_is_child_of(parent: Sequence[T], child: Sequence[T]) -> bool:
		return parent == child or StringUtils.is_child_of(parent, child)

	@staticmethod
	def get_common_ancestor_of(items: Iterable[Sequence[T]]) -> Sequence[T]:
		def reductor(a: Sequence[T], b: Sequence[T]) -> Sequence[T]:
			min_len = min(len(a), len(b))
			for index in range(0, min_len):
				if a[index] != b[index]:
					return a[0:index]
			return a[0:min_len]
		try:
			return reduce(reductor, items)
		except TypeError:
			raise ValueError("No values provided")
