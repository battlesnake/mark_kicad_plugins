import logging

from .schematic import SchematicLoader


def run():
    import yaml
    logging.basicConfig(level=logging.DEBUG)
    schematic = SchematicLoader.load("/home/mark/projects/big-audio-interface/kicad/main.kicad_sch")
    print(yaml.dump(schematic))
