from typing import List, Sequence, Optional
from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class KicadSexpNode():

	""" Parse Kicad-style s-expression files """

	key: str
	values: Sequence[str]
	children: Sequence["KicadSexpNode"]

	def __getattr__(self, key: str) -> "KicadSexpNode":
		items = self[key]
		if not items:
			raise KeyError(f"No values for key {key}")
		if len(items) > 1:
			raise KeyError(f"Multiple values for key {key}")
		return items[0]

	def __getitem__(self, key: str) -> Sequence["KicadSexpNode"]:
		return [
			child
			for child in self.children
			if child.key == key
		]

	def __str_lines__(self, indent: int) -> Sequence[str]:
		INDENT = "  "
		result = []
		result.append(INDENT * indent + f"{self.key}:")
		for value in self.values:
			result.append(INDENT * indent + INDENT + f"- {value}")
		for child in self.children:
			result += child.__str_lines__(indent + 1)
		return result

	def __str__(self) -> str:
		return "\n".join(self.__str_lines__(0))


class StringIterator():

	def __init__(self, string: str, begin: int, end: int):
		self.string = string
		self.begin = begin
		self.end = end
		self.it = self.begin
		if begin < 0 or end > len(string):
			raise ValueError("Invalid range")
		if self.it < self.begin or self.it > self.end:
			raise ValueError("Iterator out of range")

	def done(self) -> bool:
		return self.it == self.end

	def next(self):
		if self.it < self.begin or self.it >= self.end:
			raise StopIteration()
		self.it = self.it + 1

	def peek(self) -> str:
		if self.it < self.begin or self.it >= self.end:
			raise StopIteration()
		return self.string[self.it]

	def mark(self) -> int:
		return self.it

	def slice(self, from_mark: int) -> str:
		return self.string[from_mark:self.it]

	def seek(self, chars: str):
		while self.peek() not in chars:
			self.next()

	def skip(self, chars: str):
		while not self.done() and self.peek() in chars:
			self.next()

	def expect(self, chars: str):
		actual = self.peek()
		if actual not in chars:
			raise ValueError(f"Expected one of «{chars}» at index {self.it} but found «{actual}»")


class KicadSexpParser():

	WHITESPACE = " \t\n\r"
	EXPR_BEGIN = "("
	EXPR_END = ")"
	QUOTE_BEGIN = "\""
	QUOTE_END = "\""
	QUOTE_ESCAPE = "\\"
	UNQUOTED_VALUE = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-."

	def __init__(self):
		pass

	def parse_unquoted(self, it: StringIterator) -> str:
		begin = it.mark()
		it.skip(self.UNQUOTED_VALUE)
		return it.slice(begin)

	def parse_quoted(self, it: StringIterator) -> str:
		it.expect(self.QUOTE_BEGIN)
		it.next()
		begin = it.mark()
		escape = False
		while True:
			ch = it.peek()
			if ch == self.QUOTE_ESCAPE:
				escape = True
			elif ch == self.QUOTE_END and not escape:
				break
			else:
				escape = False
			it.next()
		result = it.slice(begin)
		it.next()
		return result

	def parse_value(self, it: StringIterator) -> str:
		if it.peek() == self.QUOTE_BEGIN:
			return self.parse_quoted(it)
		elif it.peek() not in self.WHITESPACE:
			return self.parse_unquoted(it)
		else:
			raise ValueError(f"Expected value at index {it.it} but found whitespace")

	def parse_node(self, it: StringIterator) -> KicadSexpNode:
		it.expect(self.EXPR_BEGIN)
		it.next()
		it.skip(self.WHITESPACE)
		key = self.parse_value(it)
		values: List[str] = []
		children: List[KicadSexpNode] = []
		it.skip(self.WHITESPACE)
		while (char := it.peek()) != self.EXPR_END:
			if char == self.EXPR_BEGIN:
				children.append(self.parse_node(it))
			else:
				values.append(self.parse_value(it))
			it.skip(self.WHITESPACE)
		it.next()
		return KicadSexpNode(key=key, values=tuple(values), children=tuple(children))


	def parse(self, text: str, root_values: Optional[Sequence[str]] = None) -> KicadSexpNode:
		try:
			it = StringIterator(text, 0, len(text))
			it.skip(self.WHITESPACE)
			result = self.parse_node(it)
			it.skip(self.WHITESPACE)
			return KicadSexpNode(
				key="(root)",
				values=tuple([] if root_values is None else root_values),
				children=tuple([result]),
			)
		except StopIteration as exc:
			raise ValueError("Unexpected end of expression") from exc


	def parse_file(self, path: str) -> KicadSexpNode:
		with open(path, "r", encoding="utf-8") as fp:
			text = fp.read()
		return self.parse(text, root_values=[path])
