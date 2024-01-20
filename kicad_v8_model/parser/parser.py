from typing import Optional, Protocol, Sequence

from ..selection import Selection

from .parser_observer import ParserObserver, NullParserObserver


class Parser(Protocol):

    def __init__(self, observer: ParserObserver = NullParserObserver()):
        ...

    def parse(self, text: str, root_values: Optional[Sequence[str]] = None) -> Selection:
        ...

    def parse_file(self, path: str) -> Selection:
        ...
