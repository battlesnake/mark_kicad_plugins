from typing import TypeVar, Callable
from functools import wraps
import traceback
import logging

from .message_box import MessageBox


ReturnType = TypeVar("ReturnType")


def error_handler(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
	@wraps(func)
	def wrapper(*args: ..., **kwargs: ...) -> ReturnType:
		try:
			return func(*args, **kwargs)
		except Exception as error:
			diagnostic = "".join(traceback.TracebackException.from_exception(error).format())
			logger = logging.getLogger(f"error_handler @ {repr(func)}")
			logger.info("Operation failed: %s", diagnostic)
			MessageBox.alert(f"Operation failed: {error}\nSee log file for full call stack")
			raise error
	return wrapper
