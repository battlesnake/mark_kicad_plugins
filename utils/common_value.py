import logging
from typing import Callable, Iterable, Optional, TypeVar


logger = logging.getLogger(__name__)


T = TypeVar("T")
U = TypeVar("U")


def common_value(items: Iterable[T], mapping: Callable[[T], U], default_value: Optional[U] = None) -> U:
	values = {
		mapping(item)
		for item in items
	}
	if len(values) == 0:
		if default_value is None:
			raise ValueError("Unable to extract value from set, set is empty")
		else:
			logger.warn("Unable to extract value from set, set is empty")
			return default_value
	elif len(values) == 1:
		return next(iter(values))
	else:
		raise ValueError("Unable to extract value from set, multiple different values found for same key")
