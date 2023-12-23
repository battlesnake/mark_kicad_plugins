from dataclasses import dataclass, field
import functools
import logging
from typing import List, Callable
from pathlib import Path
import os

from selection import Selection
from node import Node
from entity_path import EntityPath, EntityPathComponent


logger = logging.getLogger(__name__)


@dataclass
class NestedSheetMetadata():
    """ Intermediate data to help with loading stuff """
    id: EntityPathComponent
    path: EntityPath
    page: str
    name: str
    filename: str


@dataclass
class SymbolInstanceMetadata():
    """ Intermediate data to help with loading stuff """
    path: EntityPath
    reference: str
    unit: int


@dataclass
class SheetDefinition():
    node: Node = field(repr=False, hash=False, compare=False)
    id: EntityPathComponent
    version: str
    filename: str
    inner_sheet_instances: List[NestedSheetMetadata]

@dataclass
class SheetInstance():
    definition: SheetDefinition
    path: EntityPath
    name: str
    page: str
    children: List["SheetInstance"]


@dataclass
class SymbolDefinition():
    sheet: SheetDefinition
    node: Node
    id: EntityPathComponent
    library_id: str
    in_bom: bool
    on_board: bool
    dnp: bool
    reference: str
    unit: int
    value: str
    multi_unit: bool
    instance_metadata: List[SymbolInstanceMetadata]


@dataclass
class SymbolInstance():
    sheet: SheetInstance
    definition: SymbolDefinition
    path: EntityPath
    reference: str
    unit: int


class SchematicLoader():
    filename: str
    project: str
    schematic_loader: Callable[[str], Selection]
    sheet_definitions: List[SheetDefinition]
    sheet_instances: List[SheetInstance]
    symbol_definitions: List[SymbolDefinition]
    symbol_instances: List[SymbolInstance]

    def __init__(self, filename: str, schematic_loader: Callable[[str], Selection]):
        self.filename = os.path.join(os.path.curdir, filename)
        self.project = Path(filename).stem
        self.schematic_loader = schematic_loader
        self.sheet_definitions = []
        self.sheet_instances = []
        self.symbol_definitions = []
        self.symbol_instances = []
        self.read_sheet_definitions()
        self.read_sheet_instances()
        self.read_symbol_definitions()
        self.read_symbol_instances()

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
            id = EntityPathComponent.parse(node.uuid[0])
            version = node.version[0]
            inner_sheet_instances: List[NestedSheetMetadata] = []
            for sheet_node in node.sheet:
                inner_sheet_instance_nodes = sheet_node.instances.project.filter(0, self.project).path
                inner_sheet_instances += [
                    NestedSheetMetadata(
                        id=EntityPathComponent.parse(sheet_node.uuid[0]),
                        path=EntityPath.parse(instance_node[0]) + EntityPathComponent.parse(sheet_node.uuid[0]),
                        page=instance_node.page[0],
                        name=sheet_node.property.filter(0, "Sheetname")[1],
                        filename=os.path.join(
                            os.path.dirname(filename),
                            sheet_node.property.filter(0, "Sheetfile")[1],
                        ),
                    )
                    for instance_node in inner_sheet_instance_nodes
                ]
            definition = SheetDefinition(
                node=~node,
                id=id,
                version=version,
                filename=filename,
                inner_sheet_instances=inner_sheet_instances,
            )
            self.sheet_definitions.append(definition)
            for inner_sheet_instance in definition.inner_sheet_instances:
                read_sheet_definition(inner_sheet_instance.filename)
        read_sheet_definition(self.filename)

    def read_sheet_instances(self):
        logger.info("Reading sheet instances")
        root_defintion = self.sheet_definitions[0]
        root_path = EntityPath([root_defintion.id])
        logger.info("Reading sheet instance: %s / %s", self.project, root_path)
        root_instance = SheetInstance(
            definition=root_defintion,
            path=root_path,
            name=self.project,
            page=Selection([root_defintion.node]).sheet_instances.path.page[0],
            children=[],
        )
        self.sheet_instances.append(root_instance)
        def instantiante_inner_sheets(parent: SheetInstance):
            for metadata in parent.definition.inner_sheet_instances:
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
        instantiante_inner_sheets(root_instance)

    def read_symbol_definitions(self):
        logger.info("Reading symbol definitions")
        for sheet_definition in self.sheet_definitions:
            for symbol_node in Selection([sheet_definition.node]).symbol:
                id = EntityPathComponent.parse(symbol_node.uuid[0])
                library_id = symbol_node.lib_id[0]
                in_bom = symbol_node.in_bom[0] == "yes"
                on_board = symbol_node.on_board[0] == "yes"
                dnp = symbol_node.dnp[0] == "yes"
                reference = symbol_node.property.filter(0, "Reference")[1]
                unit = int(symbol_node.unit[0])
                value = symbol_node.property.filter(0, "Value")[0]
                logger.info("Reading symbol definition: %s / %s / %s", id, library_id, value)
                instance_metadata = [
                    SymbolInstanceMetadata(
                        path=EntityPath.parse(path_node[0]) + id,
                        reference=path_node.reference[0],
                        unit=int(path_node.unit[0]),
                    )
                    for path_node in symbol_node.instances.project.filter(0, self.project).path
                ]
                library_info = Selection([sheet_definition.node]).lib_symbols.symbol.filter(0, library_id)
                multi_unit = len([
                    ...
                    for symbol in library_info.symbol
                    for unit in symbol[0].split("_")[-2]
                    if unit != "0"
                ]) > 1
                definition = SymbolDefinition(
                    sheet=sheet_definition,
                    node=~symbol_node,
                    id=id,
                    library_id=library_id,
                    in_bom=in_bom,
                    on_board=on_board,
                    dnp=dnp,
                    reference=reference,
                    unit=unit,
                    value=value,
                    multi_unit=multi_unit,
                    instance_metadata=instance_metadata,
                )
                self.symbol_definitions.append(definition)


    def read_symbol_instances(self):
        logger.info("Reading symbol instances")
        sheet_map = {
            item.path: item
            for item in self.sheet_instances
        }
        for symbol_definition in self.symbol_definitions:
            for instance_metadata in symbol_definition.instance_metadata:
                logger.info(
                    "Reading symbol instance: %s%s",
                    instance_metadata.reference,
                    chr(ord("A") + instance_metadata.unit - 1) if symbol_definition.multi_unit else "",
                )
                symbol_instance = SymbolInstance(
                    definition=symbol_definition,
                    path=instance_metadata.path,
                    reference=instance_metadata.reference,
                    unit=instance_metadata.unit,
                    sheet=sheet_map[instance_metadata.path[:-1]],
                )
                self.symbol_instances.append(symbol_instance)
