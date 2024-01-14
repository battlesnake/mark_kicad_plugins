import re


class CaseConverter():
	pascal_to_snake_pattern = re.compile(r'(?<!^)(?=[A-Z])')

	@staticmethod
	def pascal_to_snake(value: str):
		return CaseConverter.pascal_to_snake_pattern.sub('_', value).lower()
