from typing import List, Optional, cast


class ChoiceBox():

	result: Optional[List[int]]

	def __init__(self, title: str, message: str, choices: List[str], multiple: bool = False):
		self.title = title
		self.message = message
		self.choices = choices
		self.multiple = multiple
		self.result = None

	def execute(self) -> Optional[List[int]]:
		import wx
		app = wx.App()
		frame = wx.Frame(None, -1, title=self.title)

		self.result = None

		def ok_button_click(event) -> None:
			self.result = list_box.GetSelections()
			frame.Close()

		message_text = wx.StaticText(frame, -1, self.message)
		message_text.Wrap(250)

		list_box = wx.ListBox(frame, -1, choices=self.choices, style=wx.LB_MULTIPLE if self.multiple else wx.LB_SINGLE, size=(300, 200))

		ok_button = wx.Button(frame, -1, "Ok")
		frame.Bind(wx.EVT_BUTTON, ok_button_click, ok_button)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(10)
		vbox.Add(message_text, flag=wx.ADJUST_MINSIZE)
		vbox.AddSpacer(10)
		vbox.Add(list_box, flag=wx.EXPAND)
		vbox.AddSpacer(10)
		vbox.Add(ok_button, flag=wx.ADJUST_MINSIZE)
		vbox.AddSpacer(10)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddSpacer(10)
		hbox.Add(vbox, flag=wx.EXPAND)
		hbox.AddSpacer(10)

		frame.SetSizer(hbox)
		hbox.Fit(frame)
		frame.Layout()
		frame.Centre()

		frame.Show()
		app.MainLoop()
		app.Destroy()

		return self.result


if __name__ == "__main__":
	print(ChoiceBox("TITLE", "MESSAGE", ["a", "b", "42"], False).execute())
	print(ChoiceBox("TITLE", "MESSAGE", ["a", "b", "42"], True).execute())
