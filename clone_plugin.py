import pcbnew

from .clone import Plugin, PluginConfiguration


class CloneSubcircuitAcrossSheetInstances(pcbnew.ActionPlugin):

	def defaults(self):
		self.name = "Clone subcircuit across sheet instances"
		self.category = "Modify PCB"
		self.description = "Clones the selected subcircuit footprint relative positions, tracks, vias across to other instances of the sheet containing it"
		self.icon = "psygen.png"
		self.show_toolbar_button = True

	def Run(self):
		board = pcbnew.GetBoard()
		configuration = PluginConfiguration()
		plugin = Plugin(board, configuration)
		plugin.execute()
		pcbnew.Refresh()


CloneSubcircuitAcrossSheetInstances().register()
