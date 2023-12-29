from typing import Callable, Sequence, Any


class App():

	def __init__(self, a: bool):
		...

	def MainLoop(self):
		...


class EventType():
	...


class Event():

	def Veto(self):
		...


ID_OK: ...
ID_CANCEL: ...

ICON_INFORMATION: ...
ICON_EXCLAMATION: ...

OK: ...


EVT_LISTBOX: EventType
EVT_CHOICE: EventType

WXK_SHIFT: ...
WXK_CONTROL: ...
WXK_ALT: ...


def GetKeyState(key: int) -> bool:
	...


def Yield():
	...


class EventHandler():

	def Bind(self, event: EventType, handler: Callable[[Event], None]) -> None:
		...


class Window(EventHandler):
	def Destroy(self):
		...


def FindWindowByName(name: str) -> Window | None:
		...


class Dialog(Window):

	def ShowModal(self) -> int:
		...

	def EndModal(self, result: int) -> None:
		...

	def SetReturnCode(self, result: int) -> None:
		...

	def GetReturnCode(self) -> int:
		...


class MessageDialog(Dialog):

	def __init__(self, parent: Window | None, message: str, caption: str, style: int):
		...


class ItemContainer():

	def GetItems(self) -> Sequence[str]:
		...

	def Set(self, items: Sequence[str]) -> None:
		...

	def GetString(self) -> str:
		...

	def SetString(self, items: str) -> None:
		...

	def GetCount(self) -> int:
		...

	def GetClientData(self, index: int) -> Any:
		...

	def SetClientData(self, index: int, data: Any) -> None:
		...

	def GetSelection(self) -> int:
		...

	def SetSelection(self, index: int) -> bool:
		...

	def Clear(self) -> None:
		...


class ListBox(Window, ItemContainer):

	def GetSelections(self) -> Sequence[int]:
		...

	def IsSelected(self, index: int) -> bool:
		...

	def Deselect(self, index: int) -> bool:
		...


class Choice(Window, ItemContainer):
	...


class Notebook(Window):

	def GetSelection(self) -> int:
		...

	def SetSelection(self, value: int) -> None:
		...


class SpinCtrl(Window):

	def SetValue(self, value: int) -> None:
		...

	def GetValue(self) -> int:
		...


class SpinCtrlDouble(Window):

	def SetValue(self, value: float) -> None:
		...

	def GetValue(self) -> float:
		...

