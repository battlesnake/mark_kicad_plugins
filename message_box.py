class MessageBox():

	def __init__(self, title: str, message: str):
		self.title = title
		self.message = message

	def execute(self) -> None:
		import wx
		app = wx.App()
		dialog = wx.MessageDialog(app, message=self.message, caption=self.title)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()
			app.Destroy()
