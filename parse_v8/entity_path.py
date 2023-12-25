from dataclasses import dataclass
from typing import Any, List, Sequence, Union, overload
from uuid import UUID


@dataclass(frozen=True, eq=True)
class EntityPathComponent():
    value: UUID

    @staticmethod
    def parse(value: str):
        return EntityPathComponent(UUID(hex=value))

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class EntityPath(Sequence[EntityPathComponent]):
    parts: Sequence[EntityPathComponent]

    @staticmethod
    def parse(path: str):
        if path.startswith("/"):
            path = path[1:]
        return EntityPath(parts=[
            EntityPathComponent.parse(part)
            for index, part in enumerate(path.split("/"))
            if not (part == "" and index == 0)
        ])

    def __iter__(self):
        return iter(self.parts)

    def __len__(self):
        return len(self.parts)

    def __contains__(self, value: Any):
        return value in self.parts

    def __bool__(self):
        return bool(self.parts)

    def __hash__(self):
        return hash(tuple(part for part in self.parts))

    def __eq__(self, other: Any):
        return (
            isinstance(other, EntityPath) and
            tuple(self.parts) == tuple(other.parts)
        )

    @overload
    def __getitem__(self, index_or_slice: int) -> EntityPathComponent:
        ...

    @overload
    def __getitem__(self, index_or_slice: slice) -> "EntityPath":
        ...

    def __getitem__(self, index_or_slice: Union[int, slice]):
        if isinstance(index_or_slice, int):
            return self.parts[index_or_slice]
        else:
            return EntityPath(self.parts[index_or_slice])

    def __str__(self):
        return "/" + "/".join(map(str, self.parts))

    def __repr__(self):
        return str(self)

    def startswith(self, prefix: Sequence[EntityPathComponent]):
        return (
            len(self) >= len(prefix) and
            all(
                a == b
                for a, b in zip(self, prefix)
            )
        )

    @overload
    def __add__(self, suffix: EntityPathComponent) -> "EntityPath":
        ...

    @overload
    def __add__(self, suffix: Sequence[EntityPathComponent]) -> "EntityPath":
        ...

    def __add__(self, suffix: EntityPathComponent | Sequence[EntityPathComponent]) -> "EntityPath":
        """ Concatenate """
        if isinstance(suffix, EntityPathComponent):
            return self + [suffix]
        else:
            return EntityPath(parts=list(self) + list(suffix))

    def __bitand__(self, other: "EntityPath") -> "EntityPath":
        """ Common prefix """
        prefix: List[EntityPathComponent] = []
        for a, b in zip(self, other):
            if a == b:
                prefix += [a]
            else:
                break
        return EntityPath(prefix)
