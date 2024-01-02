import logging
import os.path
import tempfile

from .utils.error_handler import error_handler
from .utils.logging_config import LoggingConfig


def init_root_logger():
	logging.basicConfig(
		level=LoggingConfig.level,
		filename=os.path.join(tempfile.gettempdir(), "mark-plugin-root.log"),
		filemode="w",
		encoding="utf-8",
		format=LoggingConfig.format,
		datefmt=LoggingConfig.datefmt,
		force=True
	)


@error_handler
def load_plugins():
	from .denoise_text.plugin_wrapper import TextPluginWrapper  # pyright: ignore
	from .clone_placement.plugin_wrapper import ClonePluginWrapper  # pyright: ignore

	TextPluginWrapper().register()
	ClonePluginWrapper().register()


init_root_logger()
try:
	# Test if running in Kicad
	import pcbnew  # pyright: ignore
	load_plugins()
except ModuleNotFoundError:
	# Not running in pcbnew, skip
	pass
except:  # pyright: ignore
	# Running in pcbnew, re-raise
	raise
