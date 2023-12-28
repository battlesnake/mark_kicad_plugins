from dataclasses import dataclass
from typing import List
from pcbnew import BOARD, FOOTPRINT

from .schematic import Schematic, SymbolInstance
from .entity_path import EntityPath


@dataclass
class Footprint():
    pcbnew_footprint: FOOTPRINT
    symbol_instance: SymbolInstance


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
        symbol_instances = {
            symbol_instance.path: symbol_instance
            for symbol_instance in self.schematic.symbol_instances
        }
        for pcbnew_footprint in self.board.Footprints():
            path = EntityPath(pcbnew_footprint.GetPath())
            symbol_instance = symbol_instances[path]
            footprint = Footprint(
                pcbnew_footprint=pcbnew_footprint,
                symbol_instance=symbol_instance,
            )
            self.footprints += [footprint]