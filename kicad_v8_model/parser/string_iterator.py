"""
Parse Kicad-style s-expression files

This is the bottleneck of the cloner plugin, on one project it takes 5 seconds
to read in all of the schematics, then <0.1 seconds to do all the actual
processing of the schematic node tree.

Perhaps replace with a parser that uses regexes to do the skip+search, instead
of skipping 1 char at a time in python-land.

Remember, function calls in python are also insanely expensive in both time and
space.
"""
import logging


logger = logging.getLogger(__name__)


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
