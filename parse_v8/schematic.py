from dataclasses import dataclass, field
import functools
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List

from entity_path import EntityPath, EntityPathComponent
from node import Node
from selection import Selection
from parser import Parser


logger = logging.getLogger(__name__)


@dataclass
class SheetDefinition():
    id: EntityPathComponent = field(compare=True, hash=True)
    version: str
    filename: str


@dataclass
class SheetInstance():
    definition: SheetDefinition
    path: EntityPath = field(compare=True, hash=True)
    name: str
    page: str
    children: List["SheetInstance"]


@dataclass
class SymbolDefinition():
    sheet: SheetDefinition
    id: EntityPathComponent = field(compare=True, hash=True)
    library_id: str
    in_bom: bool
    on_board: bool
    dnp: bool
    reference: str
    unit: int
    value: str
    multi_unit: bool


@dataclass
class SymbolInstance():
    sheet: SheetInstance
    definition: SymbolDefinition
    path: EntityPath = field(compare=True, hash=True)
    reference: str
    unit: int


@dataclass
class SheetInstanceMetadata():
    """ Intermediate data to help with loading stuff """
    node: Node
    id: EntityPathComponent
    path: EntityPath
    page: str
    name: str
    filename: str


@dataclass
class SymbolInstanceMetadata():
    """ Intermediate data to help with loading stuff """
    node: Node
    path: EntityPath
    reference: str
    unit: int


@dataclass
class SheetMetadata():
    node: Node
    filename: str
    instances: List[SheetInstanceMetadata]


@dataclass
class SymbolMetadata():
    node: Node
    instances: List[SymbolInstanceMetadata]


@dataclass
class Schematic():
    sheet_definitions: List[SheetDefinition]
    sheet_instances: List[SheetInstance]
    symbol_definitions: List[SymbolDefinition]
    symbol_instances: List[SymbolInstance]


class SchematicLoader():
    filename: str
    project: str
    schematic_loader: Callable[[str], Selection]

    # use filename, there is significant risk of copy/paste hierarchical sheets
    # causing UUID clashes
    sheet_metadata: Dict[str, SheetMetadata]
    symbol_metadata: Dict[EntityPathComponent, SymbolMetadata]

    sheet_definitions: List[SheetDefinition]
    sheet_instances: List[SheetInstance]
    symbol_definitions: List[SymbolDefinition]
    symbol_instances: List[SymbolInstance]

    root_sheet_definition: SheetDefinition
    root_sheet_instance: SheetInstance

    @staticmethod
    def load(filename: str):
        loader = Parser().parse_file
        return SchematicLoader(filename, loader).get_result()

    def __init__(self, filename: str, schematic_loader: Callable[[str], Selection]):
        self.filename = os.path.join(os.path.curdir, filename)
        self.project = Path(filename).stem
        self.schematic_loader = schematic_loader
        self.sheet_metadata = {}
        self.symbol_metadata = {}
        self.sheet_definitions = []
        self.sheet_instances = []
        self.symbol_definitions = []
        self.symbol_instances = []
        self.read_sheet_definitions()
        self.read_sheet_instances()
        self.read_symbol_definitions()
        self.read_symbol_instances()

    def get_result(self):
        return Schematic(
            sheet_definitions=self.sheet_definitions,
            sheet_instances=self.sheet_instances,
            symbol_definitions=self.symbol_definitions,
            symbol_instances=self.symbol_instances,
        )

    def read_sheet_definitions(self):
        logger.info("Reading sheet definition")

        @functools.cache
        def read_sheet_definition(filename: str):
            if already_loaded := next(
                (
                    item
                    for item in self.sheet_definitions
                    if item.filename == filename
                ), None
            ):
                return already_loaded
            logger.info("Reading schematic: %s", filename)
            node = self.schematic_loader(filename).kicad_sch
            sheet_id = EntityPathComponent.parse(node.uuid[0])
            version = node.version[0]
            sheet_definition = SheetDefinition(
                id=sheet_id,
                version=version,
                filename=filename,
            )
            sheet_instances = [
                SheetInstanceMetadata(
                    node=~node,
                    id=EntityPathComponent.parse(inner_sheet_node.uuid[0]),
                    path=EntityPath.parse(inner_path_node[0]) + EntityPathComponent.parse(inner_sheet_node.uuid[0]),
                    page=inner_path_node.page[0],
                    name=inner_sheet_node.property.filter(0, "Sheetname")[1],
                    filename=os.path.join(
                        os.path.dirname(filename),
                        inner_sheet_node.property.filter(0, "Sheetfile")[1],
                    ),
                )
                for inner_sheet_node in node.sheet
                for inner_path_node in inner_sheet_node.instances.project.filter(0, self.project).path
            ]
            self.sheet_definitions.append(sheet_definition)
            assert filename not in self.sheet_metadata
            self.sheet_metadata[filename] = SheetMetadata(
                node=~node,
                filename=filename,
                instances=sheet_instances,
            )
            for sheet_instance in sheet_instances:
                read_sheet_definition(sheet_instance.filename)
            return sheet_definition

        self.root_sheet_definition = read_sheet_definition(self.filename)

    def read_sheet_instances(self):
        logger.info("Reading sheet instances")
        root_path = EntityPath([self.root_sheet_definition.id])
        logger.info("Reading sheet instance: %s / %s", self.project, root_path)
        self.root_sheet_instance = SheetInstance(
            definition=self.root_sheet_definition,
            path=root_path,
            name=self.project,
            page=Selection([self.sheet_metadata[self.root_sheet_definition.filename].node]).sheet_instances.path.page[0],
            children=[],
        )
        self.sheet_instances.append(self.root_sheet_instance)

        def instantiante_inner_sheets(parent: SheetInstance):
            for metadata in self.sheet_metadata[parent.definition.filename].instances:
                logger.info("Reading sheet instance: %s / %s", metadata.name, metadata.path)
                definition = next(
                    item
                    for item in self.sheet_definitions
                    if item.filename == metadata.filename
                )
                sheet_instance = SheetInstance(
                    definition=definition,
                    path=metadata.path,
                    name=metadata.name,
                    page=metadata.page,
                    children=[],
                )
                self.sheet_instances.append(sheet_instance)
                parent.children.append(sheet_instance)
                instantiante_inner_sheets(sheet_instance)

        instantiante_inner_sheets(self.root_sheet_instance)

    def read_symbol_definitions(self):
        logger.info("Reading symbol definitions")
        for sheet_definition in self.sheet_definitions:
            sheet_node = Selection([self.sheet_metadata[sheet_definition.filename].node])
            for symbol_node in sheet_node.symbol:
                symbol_id = EntityPathComponent.parse(symbol_node.uuid[0])
                library_id = symbol_node.lib_id[0]
                in_bom = symbol_node.in_bom[0] == "yes"
                on_board = symbol_node.on_board[0] == "yes"
                dnp = symbol_node.dnp[0] == "yes"
                reference = symbol_node.property.filter(0, "Reference")[1]
                unit = int(symbol_node.unit[0])
                value = symbol_node.property.filter(0, "Value")[0]
                logger.info("Reading symbol definition: %s / %s / %s", id, library_id, value)
                library_info = sheet_node.lib_symbols.symbol.filter(0, library_id)
                multi_unit = len([
                    ...
                    for symbol in library_info.symbol
                    for unit in symbol[0].split("_")[-2]
                    if unit != "0"
                ]) > 1
                symbol_definition = SymbolDefinition(
                    sheet=sheet_definition,
                    id=symbol_id,
                    library_id=library_id,
                    in_bom=in_bom,
                    on_board=on_board,
                    dnp=dnp,
                    reference=reference,
                    unit=unit,
                    value=value,
                    multi_unit=multi_unit,
                )
                self.symbol_definitions.append(symbol_definition)
                assert symbol_id not in self.symbol_metadata
                self.symbol_metadata[symbol_definition.id] = SymbolMetadata(
                    node=~symbol_node,
                    instances=[
                        SymbolInstanceMetadata(
                            node=~symbol_node,
                            path=EntityPath.parse(path_node[0]) + symbol_id,
                            reference=path_node.reference[0],
                            unit=int(path_node.unit[0]),
                        )
                        for path_node in symbol_node.instances.project.filter(0, self.project).path
                    ],
                )

    def read_symbol_instances(self):
        logger.info("Reading symbol instances")
        sheet_map = {
            item.path: item
            for item in self.sheet_instances
        }
        for symbol_definition in self.symbol_definitions:
            metadata = self.symbol_metadata[symbol_definition.id]
            for symbol_instance_metadata in metadata.instances:
                logger.info(
                    "Reading symbol instance: %s%s",
                    symbol_instance_metadata.reference,
                    chr(ord("A") + symbol_instance_metadata.unit - 1) if symbol_definition.multi_unit else "",
                )
                symbol_instance = SymbolInstance(
                    definition=symbol_definition,
                    path=symbol_instance_metadata.path,
                    reference=symbol_instance_metadata.reference,
                    unit=symbol_instance_metadata.unit,
                    sheet=sheet_map[symbol_instance_metadata.path[:-1]],
                )
                self.symbol_instances.append(symbol_instance)
