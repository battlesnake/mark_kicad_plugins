import logging
from pathlib import Path
import time
from typing import Callable
import cProfile
import pstats
import pprofile

from .entities import Project
from .schematic_loader import SchematicLoader
from .layout_loader import LayoutLoader
from . import parser


def now():
    return time.clock_gettime(time.CLOCK_MONOTONIC)


def time_execution(name: str, op: Callable[[], None]) -> None:
    t0 = now()
    op()
    t1 = now()
    dt = t1 - t0
    print("")
    print(f"bench: {name}, time: {dt:.2f}s")
    print("")


def profile_calls(name: str, op: Callable[[], None], lines: int = 6) -> None:
    profiler = cProfile.Profile()
    profiler.enable()
    op()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats = stats.sort_stats('tottime')
    print("")
    print(f"profile: {name}")
    stats.print_stats(lines)
    print("")


def profile_lines(name: str, op: Callable[[], None]) -> None:
    profiler = pprofile.Profile()
    with profiler():
        op()
    print("")
    print(f"profile: {name}")
    profiler.print_stats()
    print("")


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
    profile_calls(
        "fast parser: schematic",
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )
    profile_calls(
        "fast parser: layout",
        lambda: LayoutLoader.load(project, str(layout_file)),
    )

    # Time simple parser
    project = Project()
    SchematicLoader.parser_class = parser.SimpleParser
    time_execution(
        "simple parser: schematic",
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )
    time_execution(
        "simple parser: layout",
        lambda: LayoutLoader.load(project, str(layout_file)),
    )

    # Time fast parser
    project = Project()
    SchematicLoader.parser_class = parser.FastParser
    time_execution(
        "fast parser: schematic",
        lambda: SchematicLoader.load(project, str(schematic_file)),
    )
    time_execution(
        "fast parser: layout",
        lambda: LayoutLoader.load(project, str(layout_file)),
    )

    # import yaml
    # print(yaml.dump(project))
