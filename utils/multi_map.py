from typing import Dict, Iterable, Optional, Generic, TypeVar, Set, Tuple, Iterator, Callable


KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


class MultiMap(Generic[KeyType, ValueType]):

    key_func: Optional[Callable[[ValueType], KeyType]]
    mapping: Dict[KeyType, Set[ValueType]]

    def __init__(self, key_func: Optional[Callable[[ValueType], KeyType]] = None):
        self.mapping = {}
        self.key_func = key_func

    @staticmethod
    def groupby(collection: Iterable[ValueType], key: Callable[[ValueType], KeyType]) -> "MultiMap[KeyType, ValueType]":
        result = MultiMap(key_func=key)
        for item in collection:
            result.add(item)
        return result

    def copy(self) -> "MultiMap[KeyType, ValueType]":
        result = MultiMap(key_func=self.key_func)
        for key, value in self:
            result[key] = value
        return result

    def __getitem__(self, key: KeyType) -> Set[ValueType]:
        return set(self.mapping.get(key, set()))

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        values: Set[ValueType]
        if key in self.mapping:
            values = self.mapping[key]
        else:
            values = set()
            self.mapping[key] = values
        values.add(value)

    def __contains__(self, key: KeyType) -> bool:
        return key in self.mapping

    def __iter__(self) -> Iterator[Tuple[KeyType, ValueType]]:
        for key, values in self.mapping.items():
            for value in values:
                yield key, value

    def keys(self) -> Iterator[KeyType]:
        yield from self.mapping.keys()

    def values(self) -> Iterator[ValueType]:
        for values in self.mapping.values():
            yield from values

    def pairs(self) -> Iterable[Tuple[KeyType, Set[ValueType]]]:
        return self.mapping.items()

    def groups(self) -> Iterable[Set[ValueType]]:
        return self.mapping.values()

    def add(self, value: ValueType):
        if self.key_func is None:
            raise KeyError("Key function has not been provided")
        self[self.key_func(value)] = value

    def invert(self) -> Dict[ValueType, KeyType]:
        return {
            value: key
            for key, value in self
        }
