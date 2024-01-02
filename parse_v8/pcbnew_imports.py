from typing import Iterable

from .entity_path import EntityPath


try:

	from pcbnew import FOOTPRINT  # pyright: ignore
	from pcbnew import BOARD      # pyright: ignore

except ModuleNotFoundError as exc:

	_pcbnew_not_found = exc

	class FOOTPRINT():  # pyright: ignore

		def GetReference(self) -> str:
			raise _pcbnew_not_found

		def GetPath(self) -> EntityPath:
			raise _pcbnew_not_found

	class BOARD():  # pyright: ignore

		def Footprints(self) -> Iterable[FOOTPRINT]:
			raise _pcbnew_not_found
