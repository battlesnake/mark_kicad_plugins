import logging
from pathlib import Path

from .entities import Project
from .schematic_loader import SchematicLoader
from .layout_loader import LayoutLoader


def run():
    import yaml
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    project_file = Path("/home/mark/projects/big-audio-interface/kicad/main.kicad_pro")
    logger.info("Loading %s", project_file.stem)
    schematic_file = project_file.with_suffix(".kicad_sch")
    layout_file = project_file.with_suffix(".kicad_pcb")
    project = Project()
    SchematicLoader.load(project, str(schematic_file))
    LayoutLoader.load(project, str(layout_file))
    print(yaml.dump(project))
