import wx

class MessageBox():

	def __init__(self, title: str, message: str, style: int):
		self.title = title
		self.message = message
		self.style = style

	def execute(self) -> None:
		dialog = wx.MessageDialog(
			parent=wx.FindWindowByName("PcbFrame"),
			message=self.message,
			caption=self.title,
			style=self.style,
		)
		try:
			dialog.ShowModal()
		finally:
			dialog.Destroy()

	@staticmethod
	def alert(message: str) -> None:
		MessageBox(title="Mart's plugins: Alert", message=message, style=wx.OK | wx.ICON_EXCLAMATION).execute()

	@staticmethod
	def info(message: str) -> None:
		MessageBox(title="Mart's plugins: Information", message=message, style=wx.OK | wx.ICON_INFORMATION).execute()
