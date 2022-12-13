from dataclasses import dataclass


@dataclass()
class PluginMetadata():
	name: str
	description: str
	category: str = "Mark's plugins"
	icon: str = "icon/psygen-hole.svg"
	show_toolbar_button: bool = True
