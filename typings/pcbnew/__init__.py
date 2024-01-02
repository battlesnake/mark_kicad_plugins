from typing import Any, Literal, Optional, Union

from .eda_angle import EDA_ANGLE, EDA_ANGLE_T, TENTHS_OF_A_DEGREE_T, DEGREE_T
from .vector2i import VECTOR2I
from .box2i import BOX2I

from .kicad_t import *
from .kicad_t import KICAD_T
from .kiid import KIID, KIID_PATH

from .eda_item import EDA_ITEM
from .board_item import BOARD_ITEM
from .pcb_group import PCB_GROUP
from .board_connected_item import BOARD_CONNECTED_ITEM
from .pcb_track import PCB_TRACK
from .pcb_via import PCB_VIA
from .zone import ZONE
from .board_item_container import BOARD_ITEM_CONTAINER
from .board import BOARD
from .footprint import FOOTPRINT

from .eda_text import EDA_TEXT
from .fp_text import FP_TEXT
from .pcb_text import PCB_TEXT

from .kicad_plugin import KicadPlugin
from .action_plugin import ActionPlugin

from .user_units import GetUserUnits, USER_UNITS_INCH, USER_UNITS_MILLIMETRE, USER_UNITS_MIL


def Refresh():
	...


def GetBoard() -> Optional[BOARD]:
	...


def GetBuildVersion() -> Any:
	...
