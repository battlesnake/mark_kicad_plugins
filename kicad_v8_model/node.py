from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, eq=True)
class Node():
	key: str
	values: Sequence[str]
	children: Sequence["Node"]
