from .plugin_wrapper import PluginWrapper
from .plugin_metadata import PluginMetadata
from .clone import ClonePlugin, ClonePluginConfiguration


class ClonePluginWrapper(PluginWrapper[ClonePluginConfiguration]):

	def create_configuration(self, init_params):
		return ClonePluginConfiguration()

	def create_plugin(self, init_params):
		return ClonePlugin(init_params)

	@staticmethod
	def get_metadata():
		return PluginMetadata(
			name="Clone subcircuit across sheet instances",
			description="Clones the selected subcircuit footprint relative positions, tracks, vias across to other instances of the sheet containing it",
		)


ClonePluginWrapper().register()
