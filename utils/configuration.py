from typing import TypeVar
from dataclasses import dataclass
from logging import Logger


ConfigurationType = TypeVar("ConfigurationType")


@dataclass
class ConfigurationInitParams():
	logger: Logger
