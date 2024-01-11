from typing import Callable, Dict, Iterable, TypeVar


Key = TypeVar("Key")
Value = TypeVar("Value")


def to_dict_strict(items: Iterable[Value], key_func: Callable[[Value], Key]) -> Dict[Key, Value]:
	result: Dict[Key, Value] = {}
	for item in items:
		key = key_func(item)
		if key in result:
			raise KeyError("Duplicate key", key, type(key), type(item), repr(result[key]), repr(item))
		result[key] = item
	return result
