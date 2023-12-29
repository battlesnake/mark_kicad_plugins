from dataclasses import dataclass
from typing import List
from pcbnew import BOARD, FOOTPRINT

from .schematic import Schematic, ComponentInstance


@dataclass
class Footprint():
    pcbnew_footprint: FOOTPRINT
    component_instance: ComponentInstance


@dataclass
class Layout():
    schematic: Schematic
    footprints: List[Footprint]


class LayoutLoader():

    board: BOARD
    schematic: Schematic

    footprints: List[Footprint]

    @staticmethod
    def load(board: BOARD, schematic: Schematic):
        return LayoutLoader(board, schematic).get_result()

    def __init__(self, board: BOARD, schematic: Schematic):
        self.board = board
        self.schematic = schematic
        self.read_footprints()

    def get_result(self):
        return Layout(
            schematic=self.schematic,
            footprints=self.footprints,
        )

    def read_footprints(self):
        component_instances = {
            component_instance.reference.designator: component_instance
            for component_instance in self.schematic.component_instances
        }
        for pcbnew_footprint in self.board.Footprints():
            reference = pcbnew_footprint.GetReference()
            component_instance = component_instances[reference]
            footprint = Footprint(
                pcbnew_footprint=pcbnew_footprint,
                component_instance=component_instance,
            )
            self.footprints += [footprint]
