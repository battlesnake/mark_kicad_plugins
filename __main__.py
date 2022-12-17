import pcbnew  # pyright: ignore

board = pcbnew.LoadBoard("/home/mark/projects/maru-logic/maru-logic.kicad_pcb")

from .clone_plugin import ClonePluginWrapper

ClonePluginWrapper(board).Run()
