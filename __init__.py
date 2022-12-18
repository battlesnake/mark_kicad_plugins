from .error_handler import error_handler


@error_handler
def load_plugins():
	from .text_plugin_wrapper import TextPluginWrapper  # pyright: ignore
	from .clone_plugin_wrapper import ClonePluginWrapper  # pyright: ignore


load_plugins()
