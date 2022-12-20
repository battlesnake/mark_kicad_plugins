import logging


class LoggingConfig():
	format = "%(asctime)s.%(msecs)03d %(name)s %(lineno)d %(levelname)s:%(message)s"
	datefmt = "%Y-%m-%d %H:%M:%S"
	level = logging.INFO
