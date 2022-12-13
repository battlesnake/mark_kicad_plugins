from .plugin_wrapper import PluginWrapper
from .plugin_metadata import PluginMetadata
from .text import TextPlugin, TextPluginConfiguration


class TextPluginWrapper(PluginWrapper[TextPluginConfiguration]):

	def create_configuration(self):
		return TextPluginConfiguration()

	def create_plugin(self, init_params):
		return TextPlugin(init_params)

	@staticmethod
	def get_metadata():
		return PluginMetadata(
			name="Text to dedicated layers",
			description="Assign references and values to dedicated layers (which must be created beforehand: Refs, Values)",
		)


TextPluginWrapper().register()
