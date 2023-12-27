from typing import TypeVar, Callable
from functools import wraps
import traceback
import logging

from ui.message_box import MessageBox

from utils.user_exception import UserException


ReturnType = TypeVar("ReturnType")


class LoggedException(Exception):
	pass


def error_handler(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
	@wraps(func)
	def wrapper(*args: ..., **kwargs: ...) -> ReturnType:
		try:
			try:
				return func(*args, **kwargs)
			except LoggedException:
				raise
			except UserException:
				raise
			except Exception as error:
				raise UserException("Unexpected error occurred") from error
		except LoggedException:
			raise
		except UserException as error:
			diagnostic = "".join(traceback.TracebackException.from_exception(error).format())
			if "logger" in kwargs:
				logger = kwargs["logger"]
			else:
				logger = logging.getLogger(f"error_handler @ {repr(func)}")
			logger.error("Operation failed: %s", diagnostic)
			MessageBox.alert(f"Operation failed: {error.message}\n\nFor more information, check the log-files in your project directory or temp directory for more information")
			raise LoggedException() from error
	return wrapper
