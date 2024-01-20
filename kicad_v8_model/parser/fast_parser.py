"""
Parse Kicad-style s-expression files 2x faster than simple parser
"""
from dataclasses import dataclass
from typing import List, Sequence, Optional
import logging
import re

from ..node import Node
from ..selection import Selection

from .parser import Parser
from .parser_observer import ParserObserver, NullParserObserver


logger = logging.getLogger(__name__)


OPEN = r"\("
CLOSE = r"\)"
TOKEN = r"""[a-z0-9_]+"""
UNQUOTED_VALUE = r"""[^\s"\\()]+"""
QUOTED_VALUE = r'''"(?:[^"\r\n\\]|\\[\\"rnt]|\\x[0-9a-fA-F][0-9a-fA-F]|\\[0-7][0-7][0-7])*"'''
SPACE = r"\s+"
SPACE_OPT = r"\s*"

NODE_START = re.compile(
	f"{SPACE_OPT}" +
	f"{OPEN}" +
	f"({TOKEN})" +
	f"(?:{SPACE}" + (
		f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))" +
		f"(?:{SPACE}" + (
			f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))" +
			f"(?:{SPACE}" + (
				f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))"
				f"(?:{SPACE}" + (
					f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))"
				) + ")?"
			) + ")?"
		) + ")?"
	) + ")?" +
	f"(?:{SPACE_OPT}({CLOSE}))?"
)
NODE_ATTR = re.compile(
	f"{SPACE}" +
	f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))"
)
NODE_CLOSE = re.compile(
	f"{SPACE_OPT}" +
	f"{CLOSE}"
)
NODE_SPACE = re.compile(SPACE)

ESCAPE_BASIC = r"""([\\"rnt\\])"""
ESCAPE_HEX = r"""x([0-9a-fA-F][0-9a-fA-F])"""
ESCAPE_OCT = r"""([0-7][0-7][0-7])"""
STR_ESCAPES = re.compile(r"\\(?:{ESCAPE_BASIC}|{ESCAPE_HEX}|{ESCAPE_OCT})")


@dataclass
class FastParserState():
	text: str
	position: int

	__slots__ = ("text", "position")

	def read(self, pattern: re.Pattern[str]):
		match = pattern.match(self.text, self.position)
		if match:
			self.position = match.end()
		return match

	def syntax_error(self):
		caret_pre = max(0, self.position - 20)
		caret_post = min(len(self.text), self.position + 20)
		caret_line = "  " + self.text[caret_pre:caret_post].replace("\n", "").replace("\t", "")
		caret_str = "-" * (2 + self.position - caret_pre - 1) + "^"
		logger.info("")
		logger.info("ERROR at position %d:", self.position)
		logger.info("%s", caret_line)
		logger.info("%s", caret_str)
		logger.info("")
		return ValueError(f"Syntax error at {self.position}:\n{caret_line}\n{caret_str}")


class FastParser(Parser):

	observer: ParserObserver

	__slots__ = ("observer")

	def __init__(self, observer: ParserObserver = NullParserObserver()):
		self.observer = observer

	def dequote(self, value: str):
		assert value[0] == "\""
		assert value[-1] == "\""
		position = 1
		end = len(value) - 1
		result: List[str] = []
		while (match := STR_ESCAPES.search(value, position, end)) is not None:
			result.append(value[position:match.start()])
			if (esc := match.group(1)) is not None:  # escaped/special char
				if esc == r"\\":
					result.append("\\")
				elif esc == r'"':
					result.append("\"")
				elif esc == r'r':
					result.append("\r")
				elif esc == r'n':
					result.append("\n")
				elif esc == r't':
					result.append("\t")
				else:
					raise Exception()
			elif (esc := match.group(2)) is not None:  # hexadecimal charcode
				result.append(chr(int(esc, 16)))
			elif (esc := match.group(3)) is not None:  # octal charcode
				result.append(chr(int(esc, 8)))
			else:
				raise Exception()
			position = match.end()
		result.append(value[position:end])
		return "".join(result)

	def parse_node(self, state: FastParserState) -> Node:
		if (match := state.read(NODE_START)) is None:
			raise state.syntax_error()
		key: str = match.group(1)
		values: List[str] = []
		children: List[Node] = []
		# Optimisation by parsing the first 0-3 attributes and the closing
		# bracket (if <=3 attributes) in the same match that we validate the
		# opening bracket and read the token name
		if (unquoted := match.group(2)):
			values.append(unquoted)
		elif (quoted := match.group(3)):
			values.append(self.dequote(quoted))
		if (unquoted := match.group(4)):
			values.append(unquoted)
		elif (quoted := match.group(5)):
			values.append(self.dequote(quoted))
		if (unquoted := match.group(6)):
			values.append(unquoted)
		elif (quoted := match.group(7)):
			values.append(self.dequote(quoted))
		if (unquoted := match.group(8)):
			values.append(unquoted)
		elif (quoted := match.group(9)):
			values.append(self.dequote(quoted))
		closed = match.group(10) is not None
		# End optimisation, read extra attributes / children / closing
		while not closed:
			if (match := state.read(NODE_ATTR)) is not None:
				if (unquoted := match.group(1)) is not None:
					values.append(unquoted)
				elif (quoted := match.group(2)) is not None:
					values.append(self.dequote(quoted))
			elif state.read(NODE_CLOSE) is not None:
				closed = True
			else:
				children.append(self.parse_node(state))
		self.observer.progress(state.position, len(state.text))
		return Node(
			key=key,
			values=values,
			children=children,
		)

	def parse(self, text: str, root_values: Optional[Sequence[str]] = None) -> Selection:
		state = FastParserState(text, 0)
		self.observer.progress(0, len(text))
		root = Node(
			key="(root)",
			values=tuple([] if root_values is None else root_values),
			children=tuple([self.parse_node(state)]),
		)
		state.read(NODE_SPACE)
		if state.position != len(text):
			raise state.syntax_error()
		return Selection(nodes=[root])

	def parse_file(self, path: str) -> Selection:
		with open(path, "r", encoding="utf-8") as fp:
			text = fp.read()
		return self.parse(text, root_values=[path])
