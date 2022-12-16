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
		from .wx_utils import WxUtils

		dialog = WxUtils.dialog("Mark's text-placement plugin", cast(Optional[List[int]], None))
		with dialog as frame:

			def ok_button_click(event) -> None:
				dialog.set_result(list_box.GetSelections())
				frame.Close()

			list_box = wx.ListBox(frame, -1, choices=self.choices, style=wx.LB_MULTIPLE if self.multiple else wx.LB_SINGLE, size=(300, 200))

			ok_button = wx.Button(frame, -1, "Ok")
			frame.Bind(wx.EVT_BUTTON, ok_button_click, ok_button)

			vbox = WxUtils.wrap_control_with_caption(list_box, self.message, wx.EXPAND, 10, 10)
			vbox.Add(ok_button, flag=wx.ADJUST_MINSIZE)
			vbox.AddSpacer(10)

			hbox = wx.BoxSizer(wx.HORIZONTAL)
			hbox.AddSpacer(10)
			hbox.Add(vbox, flag=wx.EXPAND)
			hbox.AddSpacer(10)

			frame.SetSizer(hbox)
			hbox.Fit(frame)

		return dialog.get_result()
