from typing import Callable, TypeVar
from .bored_user_entertainer import BoredUserEntertainer


ResultType = TypeVar("ResultType")


def spin_while(func: Callable[..., ResultType]) -> Callable[..., ResultType]:
	def wrapper(*args: ..., **kwargs: ...) -> ResultType:
		BoredUserEntertainer.start()
		try:
			return func(*args, **kwargs)
		finally:
			BoredUserEntertainer.stop()
	return wrapper
