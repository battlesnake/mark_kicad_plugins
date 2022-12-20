from typing import Dict

from uuid import UUID
from logging import Logger

from .kicad_entities import UuidPath
from .hierarchy import Hierarchy


class HierarchyLogger():

	uuidmap: Dict[UUID, str] = {}

	def __init__(self, logger: Logger):
		self.logger = logger.getChild(type(self).__name__)

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
			logger.debug("Sheet template %s:", self.map_uuid(template.uuid))
			logger.debug("  Filename: %s", template.filename)
			logger.debug("")

	def log_instances(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for instance in hierarchy.instances.values():
			logger.debug("Sheet instance %s:", self.map_uuid(instance.uuid))
			logger.debug("  Name: %s", instance.name)
			logger.debug("  Template: %s (%s)", instance.template.filename, self.map_uuid(instance.template.uuid))
			if instance.parent:
				logger.debug("  Parent: %s (%s)", instance.parent.name, self.map_uuid(instance.parent.uuid))
			else:
				logger.debug("  Parent: %s", "(none)")
			logger.debug("  Name path: %s", instance.name_path)
			logger.debug("  Uuid path: %s", self.map_uuidpath(instance.uuid_path))
			logger.debug("")

	def log_symbols(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for symbol in hierarchy.symbols.values():
			logger.debug("Symbol %s:", self.map_uuid(symbol.uuid))
			logger.debug("  Reference: %s:%s", symbol.reference, symbol.unit)
			logger.debug("  Value: %s", symbol.value)
			logger.debug("  Path: %s", self.map_uuidpath(symbol.path))
			logger.debug("  Sheet: %s (%s)", symbol.sheet_template.filename, self.map_uuid(symbol.sheet_template.uuid))
			logger.debug("  Footprints: %s", ", ".join(footprint.reference for footprint in hierarchy.symbol_instances[symbol]))
			logger.debug("")

	def log_footprints(self, hierarchy: Hierarchy) -> None:
		logger = self.logger
		for footprint in hierarchy.footprints.values():
			logger.debug("Footprint %s:", footprint.reference)
			logger.debug("  Reference: %s", footprint.reference)
			logger.debug("  Value: %s", footprint.value)
			logger.debug("  Path: %s", self.map_uuidpath(footprint.path))
			logger.debug("  Symbol: %s", self.map_uuid(footprint.symbol.uuid))
			logger.debug("  Sheet instance: %s (%s)", footprint.sheet_instance.name_path, self.map_uuid(footprint.sheet_instance.uuid))
			logger.debug("")

	def log_all(self, hierarchy: Hierarchy) -> None:
		self.log_templates(hierarchy)
		self.log_instances(hierarchy)
		self.log_symbols(hierarchy)
		self.log_footprints(hierarchy)
