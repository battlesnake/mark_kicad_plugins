import logging
from parser import Parser
from schematic import SchematicLoader


logging.basicConfig(level=logging.DEBUG)


loader = Parser().parse_file


schematic = SchematicLoader("/home/mark/projects/big-audio-interface/kicad/main.kicad_sch", loader)


print(repr(schematic))
