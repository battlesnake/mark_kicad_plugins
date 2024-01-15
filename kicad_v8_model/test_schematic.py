import logging
from pathlib import Path
import time

from .entities import Project
from .schematic_loader import SchematicLoader
from .layout_loader import LayoutLoader


def now():
    return time.clock_gettime(time.CLOCK_MONOTONIC)


def run():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    project_file = Path("/home/mark/projects/big-audio-interface/kicad/main.kicad_pro")
    logger.info("Loading %s", project_file.stem)
    schematic_file = project_file.with_suffix(".kicad_sch")
    layout_file = project_file.with_suffix(".kicad_pcb")
    project = Project()
    t0 = now()
    SchematicLoader.load(project, str(schematic_file))
    t1 = now()
    LayoutLoader.load(project, str(layout_file))
    t2 = now()
    # import yaml
    # print(yaml.dump(project))
    t_schematic = t1 - t0
    t_layout = t2 - t1
    logger.info(f"Times: schematic={t_schematic:.1f}s layout={t_layout:.1f}s")
