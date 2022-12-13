import pcbnew

from .mark_text import Plugin, PluginConfiguration


class MoveTextToDedicatedLayers(pcbnew.ActionPlugin):

	def defaults(self):
		self.name = "Text to dedicated layers"
		self.category = "Modify PCB"
		self.description = "Assign references and values to dedicated layers (which must be created beforehand: Refs, Values)"
		self.icon = "psygen.png"
		self.show_toolbar_button = True

	def Run(self):
		board = pcbnew.GetBoard()
		configuration = PluginConfiguration()
		plugin = Plugin(board, configuration)
		plugin.execute()
		pcbnew.Refresh()


MoveTextToDedicatedLayers().register()
