class UserException(ValueError):

	def __init__(self, message: str, *args: ...):
		super().__init__(self, message, *args)
		self.message = message
		self.args = args
