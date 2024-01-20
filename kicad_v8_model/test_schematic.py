import logging
from pathlib import Path
import time
from typing import Callable, List, Tuple

from .entities import Project
from .schematic_loader import SchematicLoader
from .layout_loader import LayoutLoader
from . import parser


def now():
    return time.clock_gettime(time.CLOCK_MONOTONIC)


benchmarks: List[Tuple[str, float]] = []


def timeit(logger: logging.Logger, name: str, op: Callable[[], None]) -> float:
    t0 = now()
    op()
    t1 = now()
    dt = t1 - t0
    benchmarks.append((name, dt))
    return dt


def run():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    project_file = Path("/home/mark/projects/big-audio-interface/kicad/main.kicad_pro")
    logger.info("Loading %s", project_file.stem)
    schematic_file = project_file.with_suffix(".kicad_sch")
    layout_file = project_file.with_suffix(".kicad_pcb")
    project = Project()
    SchematicLoader.parser_class = parser.SimpleParser
    timeit(
        logger,
        "simple parser",
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )
    project = Project()
    SchematicLoader.parser_class = parser.FastParser
    timeit(
        logger,
        "fast parser",
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )
    timeit(
        logger,
        "layout",
        lambda: LayoutLoader.load(project, str(layout_file))
    )
    # import yaml
    # print(yaml.dump(project))
    for name, dt in benchmarks:
        logger.info("%s: %.1fs", name, dt)
