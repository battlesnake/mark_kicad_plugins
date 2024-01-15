from abc import ABC, abstractmethod


class ParserObserver(ABC):

	@abstractmethod
	def progress(self, done: int, total: int):
		...


class NullParserObserver(ParserObserver):

	def progress(self, done: int, total: int):
		pass
