import logging

from .schematic import SchematicLoader


if __name__ == "__main__":
    import yaml
    logging.basicConfig(level=logging.DEBUG)
    schematic = SchematicLoader.load("/home/mark/projects/big-audio-interface/kicad/main.kicad_sch")
    print(yaml.dump(schematic))
