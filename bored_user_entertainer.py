import wx

from .bored_user_entertainer_design import BoredUserEntertainerDesign


class BoredUserEntertainer():

	_inst: BoredUserEntertainerDesign | None = None

	@staticmethod
	def start() -> None:
		if BoredUserEntertainer._inst is None:
			BoredUserEntertainer._inst = BoredUserEntertainerDesign(parent=wx.FindWindowByName("PcbFrame"))
		BoredUserEntertainer.message("Working, please wait...")
		BoredUserEntertainer._inst.Show()
		BoredUserEntertainer._inst.Refresh()

	@staticmethod
	def stop() -> None:
		if BoredUserEntertainer._inst is None:
			return
		BoredUserEntertainer._inst.Hide()

	@staticmethod
	def message(caption: str) -> None:
		inst = BoredUserEntertainer._inst
		if inst is None:
			return
		inst.caption_label.label = caption
		inst.caption_label.Refresh()
		inst.progress_gauge.Pulse()

	@staticmethod
	def progress(step: int, steps: int) -> None:
		inst = BoredUserEntertainer._inst
		if inst is None:
			return
		inst.progress_gauge.SetRange(steps)
		inst.progress_gauge.SetValue(step)
		inst.progress_gauge.Refresh()
