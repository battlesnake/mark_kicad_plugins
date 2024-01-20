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
QUOTED_VALUE = r'''"([^"\r\n\\]|\\[\\"rnt]|\\x[0-9a-fA-F][0-9a-fA-F]|\\[0-7][0-7][0-7])*"'''
SPACE = r"\s+"
SPACE_OPT = r"\s*"

NODE_START = re.compile(
	f"{SPACE_OPT}" +
	f"{OPEN}" +
	f"(?P<token>{TOKEN})" +
	f"({SPACE}" + (
		f"((?P<unquoted1>{UNQUOTED_VALUE})|(?P<quoted1>{QUOTED_VALUE}))" +
		f"({SPACE}" + (
			f"((?P<unquoted2>{UNQUOTED_VALUE})|(?P<quoted2>{QUOTED_VALUE}))" +
			f"({SPACE}" + (
				f"((?P<unquoted3>{UNQUOTED_VALUE})|(?P<quoted3>{QUOTED_VALUE}))"
				f"({SPACE}" + (
					f"((?P<unquoted4>{UNQUOTED_VALUE})|(?P<quoted4>{QUOTED_VALUE}))"
				) + ")?"
			) + ")?"
		) + ")?"
	) + ")?" +
	f"({SPACE_OPT}(?P<close>{CLOSE}))?"
)
NODE_ATTR = re.compile(
	f"{SPACE}" +
	f"((?P<unquoted>{UNQUOTED_VALUE})|(?P<quoted>{QUOTED_VALUE}))"
)
NODE_CLOSE = re.compile(
	f"{SPACE_OPT}" +
	f"{CLOSE}"
)
NODE_SPACE = re.compile(SPACE)

STR_ESCAPES = re.compile(r"""\\((?P<basic>[\\"rnt\\])|x(?P<hex>[0-9a-fA-F][0-9a-fA-F])|(?P<oct>[0-7][0-7][0-7]))""")


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
			if (esc := match.group("basic")) is not None:
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
			elif (esc := match.group("hex")) is not None:
				result.append(chr(int(esc, 16)))
			elif (esc := match.group("oct")) is not None:
				result.append(chr(int(esc, 8)))
			else:
				raise Exception()
			position = match.end()
		result.append(value[position:end])
		return "".join(result)

	def parse_node(self, state: FastParserState) -> Node:
		if (match := state.read(NODE_START)) is None:
			raise state.syntax_error()
		key: str = match.group("token")
		values: List[str] = []
		children: List[Node] = []
		# Optimisation to speed up parsing of node with 0-3/4+ unquoted
		# attributes, by parsing the first 0-2 attributes and the closing
		# bracket (if <=3 attributes) in the same match that we validate the
		# opening and read the token
		if (unquoted := match.group("unquoted1")):
			values.append(unquoted)
		elif (quoted := match.group("quoted1")):
			values.append(self.dequote(quoted))
		if (unquoted := match.group("unquoted2")):
			values.append(unquoted)
		elif (quoted := match.group("quoted2")):
			values.append(self.dequote(quoted))
		if (unquoted := match.group("unquoted3")):
			values.append(unquoted)
		elif (quoted := match.group("quoted3")):
			values.append(self.dequote(quoted))
		if (unquoted := match.group("unquoted4")):
			values.append(unquoted)
		elif (quoted := match.group("quoted4")):
			values.append(self.dequote(quoted))
		closed = match.group("close") is not None
		# End optimisation
		while not closed:
			if (match := state.read(NODE_ATTR)) is not None:
				if (unquoted := match.group("unquoted")) is not None:
					values.append(unquoted)
				elif (quoted := match.group("quoted")) is not None:
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
