from typing import List, Sequence

from .command import (
	Command,
	CommandTarget,
	DeleteCommand,
	DisplaceCommand,
	FlipCommand,
	MoveToLayerCommand,
	RotateCommand,
	SetOrientationCommand,
	SetPositionCommand,
	UniqueBoardItem,
	CloneCommand,
	GroupCommand,
	UngroupCommand,
)

from .action import (
	Action,
	ActionTarget,
	DeleteAction,
	DisplaceAction,
	FlipAction,
	InsertAction,
	MoveToLayerAction,
	RotateAction,
	SetOrientationAction,
	SetPositionAction,
	CloneAction,
	GroupAction,
	UngroupAction,
)

from kicad_v8_model import (
	EntityPathComponent,
	Angle,
	AngleUnit,
	Vector2
)

from pcbnew import (
	BOARD,
	BOARD_ITEM,
	FOOTPRINT,
	KIID,
	VECTOR2I,
	EDA_ANGLE,
	TENTHS_OF_A_DEGREE_T,
	EDA_ITEM,
)

class ScriptCompiler():
	commit_script: List[Action]
	rollback_script: List[Action]

	def __init__(self):
		self.commit_script = []
		self.rollback_script = []

	def compile(self, script: Sequence[Command]):
		...
