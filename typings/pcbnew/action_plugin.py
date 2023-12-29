from typing import Any

from .kicad_plugin import KicadPlugin


class ActionPlugin(KicadPlugin):

	def __init__(self):
		...

	def defaults(self) -> Any:
		...

	def GetName(self) -> str:
		...

	def GetCategoryName(self) -> str:
		...

	def GetDescription(self) -> str:
		...

	def GetShowToolbarButton(self) -> bool:
		...

	def GetIconFileName(self, dark: bool) -> str:
		...

	def Run(self) -> None:
		...
