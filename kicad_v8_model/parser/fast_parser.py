"""
Parse Kicad-style s-expression files 2x faster than simple parser
"""
from dataclasses import dataclass
from typing import List, Sequence, Optional
import logging
import re
from functools import reduce

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

#
# Run via ./test.sh
#
# Assume up to 10% error on all measurements, since we
# don't do any repeats (10% is what I saw when manually
# repeating the same test over and over).
#
# | N   | n   | t_sch   | t_lay   | p_sch   | p_lay   |
# |-----|-----|---------|---------|---------|---------|
# Simple parser
# | n/a | n/a |   2.70  |   2.90  |   ----  |   ----  |
# Fast parser (no head-attr batching)
# |   0 |   1 |   1.83  |   3.24  |   1.40  |   3.33  |
# |   0 |   2 |   1.81  |   3.32  |   1.36  |   3.01  |
# |   0 |   5 |   1.83  |   3.19  |   1.40  |   2.75  |
# |   0 |  10 |   1.83  |   3.25  |   1.31  |   2.67  |
# |   0 |  20 |   1.90  |   3.40  |   1.32  |   2.81  |
# |   0 | 200 |   2.06  |   3.64  |   1.38  |   2.99  |
# Fast parser (no attr-attr batching)
# |   2 |   1 |   1.72  |   3.17  |   1.42  |   2.70  |
# |   5 |   1 |   1.76  |   3.24  |   1.20  |   2.50  |
# |  10 |   1 |   1.78  |   3.18  |   1.05  |   2.62  |
# |  20 |   1 |   1.88  |   3.23  |   1.23  |   2.68  |
# |  50 |   1 |   1.79  |   3.54  |   1.33  |   2.72  |
# Fast parser (attr batching on both head and attr)
# |  10 |  10 |   1.79  |   3.16  |   1.10  |   2.78  |

# Max attrs that we can parse with the node-start regex
# There's a balance between less pat.match invocations, and slower head matching
NODE_START_ATTR_BATCH = 10
# Max attrs that can be parsed in one match/batch
NODE_ATTR_BATCH = 10

# Build parser regexes (named groups are nice, but also a lot slower to extract)
NODE_START = re.compile(
	f"{SPACE_OPT}"
	f"{OPEN}"
	f"({TOKEN})" +
	reduce(
		lambda s, _: (
			f"(?:{SPACE}" + (
				f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))" + s
			) + ")?"
		),
		range(0, NODE_START_ATTR_BATCH),
		"",
	) +
	f"(?:{SPACE_OPT}({CLOSE}))?"
)
NODE_ATTR = re.compile(
	reduce(
		lambda s, nesting: (
			f"(?:{SPACE}" + (
				f"(?:({UNQUOTED_VALUE})|({QUOTED_VALUE}))" + s
			) + ")" + ("" if nesting == 1 else "?")
		),
		range(NODE_ATTR_BATCH, 0, -1),
		"",
	) +
	f"(?:{SPACE_OPT}({CLOSE}))?"
)
NODE_CLOSE = re.compile(
	f"{SPACE_OPT}"
	f"{CLOSE}"
)
NODE_SPACE = re.compile(SPACE)

# Quoted-strin parser regexes
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
		if match is not None:
			self.position = match.end()
		return match

	def syntax_error(self):
		caret_pre = max(0, self.position - 40)
		caret_post = min(len(self.text), self.position + 40)
		caret_line = "  " + self.text[caret_pre:caret_post].replace("\n", "").replace("\t", "")
		caret_str = "-" * (2 + self.position - caret_pre - 1) + "^"
		logger.info("")
		logger.info("ERROR at position %d:", self.position)
		logger.info("%s", caret_line)
		logger.info("%s", caret_str)
		logger.info("")
		if self.position == len(self.text):
			return ValueError(f"Unexpected end-of-input at {self.position}/{len(self.text)}:\n{caret_line}\n{caret_str}")
		else:
			return ValueError(f"Syntax error at {self.position}/{len(self.text)}:\n{caret_line}\n{caret_str}")


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
		# Optimisation by parsing the first few attributes and the closing
		# bracket in the same match that we use to validate the opening bracket
		# and read the token name
		#
		# groups (for N=NODE_START_ATTR_BATCH):
		#  - 0: all (implicit)
		#  - 1: key
		#  - 2: arg/0/unquoted
		#  - 3: arg/0/quoted
		#  - 2N: arg/N-1/unquoted
		#  - 2N+1: arg/N-1/quoted
		#  - 2N+2: close
		for idx in range(2, 2 + 2 * NODE_START_ATTR_BATCH, 2):
			if (unquoted := match.group(idx)):
				values.append(unquoted)
			elif (quoted := match.group(idx + 1)):
				values.append(self.dequote(quoted))
			else:
				break
		closed = match.group(2 + 2 * NODE_START_ATTR_BATCH) is not None
		# End optimisation
		while not closed:
			if (match := state.read(NODE_ATTR)) is not None:
				# Similar optimisation, parse attributes in batches
				# groups (for N=NODE_ATTR_BATCH):
				#  - 0: all (implicit)
				#  - 1: arg/0/unquoted
				#  - 2: arg/0/quoted
				#  - 2N-1: arg/N-1/unquoted
				#  - 2N  : arg/N-1/quoted
				#  - 2N+1: close
				for idx in range(1, 2 * NODE_ATTR_BATCH, 2):
					if (unquoted := match.group(idx)) is not None:
						values.append(unquoted)
					elif (quoted := match.group(idx + 1)) is not None:
						values.append(self.dequote(quoted))
					else:
						break
				closed = match.group(1 + 2 * NODE_ATTR_BATCH) is not None
				# End optimisation
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
