class MessageBox():

	def __init__(self, title: str, message: str):
		self.title = title
		self.message = message

	def execute(self) -> None:
		import wx
		dialog = wx.MessageDialog(None, message=self.message, caption=self.title)
		dialog.ShowModal()
		dialog.Destroy()
