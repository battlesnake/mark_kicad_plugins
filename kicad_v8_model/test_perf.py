import logging
from pathlib import Path
import time
from typing import Callable
import cProfile
import pstats

from .entities import Project
from .schematic_loader import SchematicLoader
from .layout_loader import LayoutLoader
from . import parser


def now():
    return time.clock_gettime(time.CLOCK_MONOTONIC)


def timeit(name: str, op: Callable[[], None]) -> None:
    t0 = now()
    op()
    t1 = now()
    dt = t1 - t0
    print(f"bench: {name}, time: {dt:.2f}s")


def profileit(name: str, lines: int, op: Callable[[], None]) -> None:
    profiler = cProfile.Profile()
    profiler.enable()
    op()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats = stats.sort_stats('tottime')
    stats.print_stats(lines)


def run():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    project_file = Path("/home/mark/projects/big-audio-interface/kicad/main.kicad_pro")
    logger.info("Loading %s", project_file.stem)
    schematic_file = project_file.with_suffix(".kicad_sch")
    layout_file = project_file.with_suffix(".kicad_pcb")

    spin_end = now() + 2
    while now() < spin_end:
        pass

    # Profile fast parser
    project = Project()
    profileit(
        "fast parser",
        10,
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )

    # Profile layout loader with fast parser
    profileit(
        "layout",
        10,
        lambda: LayoutLoader.load(project, str(layout_file)),
    )

    # Time simple parser
    if False:
        project = Project()
        SchematicLoader.parser_class = parser.SimpleParser
        timeit(
            "simple parser",
            lambda: SchematicLoader.load(project, str(schematic_file)),
        )

    # Time fast parser
    project = Project()
    SchematicLoader.parser_class = parser.FastParser
    timeit(
        "fast parser",
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )

    # Time layoud loading (with fast parser)
    timeit(
        "layout",
        lambda: LayoutLoader.load(project, str(layout_file)),
    )

    # import yaml
    # print(yaml.dump(project))
