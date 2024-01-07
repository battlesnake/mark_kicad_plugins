
#import pcbnew  # pyright: ignore
#board = pcbnew.LoadBoard("/home/mark/projects/maru-logic/maru-logic.kicad_pcb")
#from .clone_plugin_wrapper import ClonePluginWrapper
#ClonePluginWrapper(board).Run()


from .kicad_v8_loader.test_schematic import run

run()
