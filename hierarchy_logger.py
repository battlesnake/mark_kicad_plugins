from typing import Dict

from uuid import UUID
from logging import Logger

from .kicad_entities import UuidPath
from .hierarchy_parser import Hierarchy


class HierarchyLogger():

	uuidmap: Dict[UUID, str] = {}

	def __init__(self, logger: Logger):
		self.logger = logger.getChild(self.__class__.__name__)

	def map_uuid(self, uuid: UUID) -> str:
		if uuid in self.uuidmap:
			value = self.uuidmap[uuid]
		else:
			value = f"${len(self.uuidmap)}"
			self.uuidmap[uuid] = value
		return value

	def map_uuidpath(self, path: UuidPath) -> str:
		return " / ".join(self.map_uuid(uuid) for uuid in path)

	def log_templates(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for template in hierarchy.templates.values():
			logger.info("Sheet template %s:", self.map_uuid(template.uuid))
			logger.info("  Filename: %s", template.filename)
			logger.info("")

	def log_instances(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for instance in hierarchy.instances.values():
			logger.info("Sheet instance %s:", self.map_uuid(instance.uuid))
			logger.info("  Name: %s", instance.name)
			logger.info("  Template: %s (%s)", instance.template.filename, self.map_uuid(instance.template.uuid))
			if instance.parent:
				logger.info("  Parent: %s (%s)", instance.parent.name, self.map_uuid(instance.parent.uuid))
			else:
				logger.info("  Parent: %s", "(none)")
			logger.info("  Name path: %s", instance.name_path)
			logger.info("  Uuid path: %s", self.map_uuidpath(instance.uuid_path))
			logger.info("")

	def log_symbols(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for symbol in hierarchy.symbols.values():
			logger.info("Symbol %s:", self.map_uuid(symbol.uuid))
			logger.info("  Reference: %s:%s", symbol.reference, symbol.unit)
			logger.info("  Value: %s", symbol.value)
			logger.info("  Path: %s", self.map_uuidpath(symbol.path))
			logger.info("  Sheet instance: %s", self.map_uuid(symbol.sheet_instance.uuid))
			logger.info("  Footprints: %s", ", ".join(footprint.reference for footprint in hierarchy.symbol_instances[symbol]))
			logger.info("")

	def log_footprints(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for footprint in hierarchy.footprints.values():
			logger.info("Footprint %s:", footprint.reference)
			logger.info("  Reference: %s", footprint.reference)
			logger.info("  Value: %s", footprint.value)
			logger.info("  Path: %s", self.map_uuidpath(footprint.path))
			logger.info("  Symbol: %s", self.map_uuid(footprint.symbol.uuid))
			logger.info("")

	def log_all(self, hierarchy: Hierarchy) -> None:
		self.log_templates(hierarchy)
		self.log_instances(hierarchy)
		self.log_symbols(hierarchy)
		self.log_footprints(hierarchy)
