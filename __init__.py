import logging
import os.path
import tempfile

from .error_handler import error_handler


def init_root_logger():
	for handler in logging.root.handlers[:]:
		logging.root.removeHandler(handler)
	logging.basicConfig(
		level=logging.DEBUG,
		filename=os.path.join(tempfile.gettempdir(), "mark-plugin-root.log"),
		filemode="w",
		encoding="utf-8",
		format="%(asctime)s %(name)s %(lineno)d:%(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)


@error_handler
def load_plugins():
	from .text_plugin_wrapper import TextPluginWrapper  # pyright: ignore
	from .clone_plugin_wrapper import ClonePluginWrapper  # pyright: ignore

	TextPluginWrapper().register()
	ClonePluginWrapper().register()


init_root_logger()
try:
	load_plugins()
except:
	# error_handler took care of reporting already
	pass
