import logging
from schematic import SchematicLoader


logging.basicConfig(level=logging.DEBUG)


schematic = SchematicLoader.load("/home/mark/projects/big-audio-interface/kicad/main.kicad_sch")


print(repr(schematic))
