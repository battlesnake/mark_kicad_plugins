from typing import Optional, Generic, TypeVar
from dataclasses import dataclass

import wx


@dataclass
class WxDialogResources():
	app: wx.App
	frame: wx.Frame


ResultType = TypeVar("ResultType")


class WxDialog(Generic[ResultType]):

	def __init__(self, title: str, default_result: ResultType):
		self.title = title
		self.resources: Optional[WxDialogResources] = None
		self.result = default_result

	def set_result(self, result: ResultType):
		self.result = result

	def get_result(self) -> ResultType:
		return self.result

	def __enter__(self) -> wx.Frame:
		app = wx.App()
		frame = wx.Frame(None, -1, title=self.title)
		self.resources = WxDialogResources(app=app, frame=frame)
		return frame

	def __exit__(self, exception_type, exception_value, traceback):
		resources = self.resources
		if resources is None:
			return
		app = resources.app
		frame = resources.frame
		if not exception_value:
			frame.Layout()
			frame.Centre()
			frame.Show()
			app.MainLoop()
		app.Destroy()

class WxUtils():

	@staticmethod
	def dialog(title: str, default_result: ResultType) -> WxDialog[ResultType]:
		return WxDialog(title, default_result)

	@staticmethod
	def wrap_control_with_caption(control: wx.Control, caption: str, flag: int, spacing: int = 0, padding: int = 0) -> wx.BoxSizer:
		text = wx.StaticText(control.TopLevelParent, -1, caption)
		vbox = wx.BoxSizer(wx.VERTICAL)
		if padding:
			vbox.AddSpacer(padding)
		vbox.Add(text)
		if spacing:
			vbox.AddSpacer(spacing)
		vbox.Add(control)
		if padding:
			vbox.AddSpacer(padding)
		return vbox
