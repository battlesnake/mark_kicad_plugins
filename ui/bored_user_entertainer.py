import wx

from .bored_user_entertainer_design import BoredUserEntertainerDesign


class BoredUserEntertainer():

	_inst: BoredUserEntertainerDesign | None = None
	_refcount: int = 0

	@staticmethod
	def start() -> None:
		if BoredUserEntertainer._inst is None:
			BoredUserEntertainer._inst = BoredUserEntertainerDesign(parent=wx.FindWindowByName("PcbFrame"))
		BoredUserEntertainer.message("Working, please wait...")
		BoredUserEntertainer._inst.Show()
		BoredUserEntertainer._refcount += 1
		wx.Yield()

	@staticmethod
	def stop() -> None:
		if BoredUserEntertainer._inst is None:
			return
		BoredUserEntertainer._refcount -= 1
		if BoredUserEntertainer._refcount == 0:
			BoredUserEntertainer._inst.Hide()
		wx.Yield()

	@staticmethod
	def message(caption: str) -> None:
		inst = BoredUserEntertainer._inst
		if inst is None:
			return
		inst.caption_label.label = caption
		inst.progress_gauge.Pulse()
		wx.Yield()

	@staticmethod
	def progress(step: int, steps: int) -> None:
		inst = BoredUserEntertainer._inst
		if inst is None:
			return
		inst.progress_gauge.SetRange(steps)
		inst.progress_gauge.SetValue(step)
		wx.Yield()
