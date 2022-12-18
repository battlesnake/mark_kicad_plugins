import traceback

try:
	from .text_plugin_wrapper import TextPluginWrapper  # pyright: ignore
	from .clone_plugin_wrapper import ClonePluginWrapper  # pyright: ignore
except Exception as error:
	from .message_box import MessageBox
	diagnostic = "".join(traceback.TracebackException.from_exception(error).format())
	MessageBox.alert(diagnostic)
