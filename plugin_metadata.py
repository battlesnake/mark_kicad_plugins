from dataclasses import dataclass
import os.path


@dataclass()
class PluginMetadata():
	name: str
	description: str
	category: str = "Mark's plugins"
	icon: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon/psygen.png")
	show_toolbar_button: bool = True
