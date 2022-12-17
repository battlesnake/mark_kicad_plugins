from typing import Optional, Iterable, List, final
from dataclasses import dataclass
from logging import Logger

import wx
import wx.dataview

import pcbnew  # pyright: ignore

from .kicad_entities import SheetInstance, Footprint, SIZE_SCALE
from .multi_map import MultiMap
from .list_box_adapter import StaticListBoxAdapter
from .choice_adapter import StaticChoiceAdapter
from .tree_control_branch_selection_adapter import TreeControlBranchSelectionAdapter
from .clone_placement_settings import ClonePlacementSettings, ClonePlacementStrategyType, ClonePlacementRelativeStrategySettings, ClonePlacementGridStrategySettings, ClonePlacementGridFlow, ClonePlacementGridSort
from .clone_settings import CloneSettings
from .clone_settings_dialog_design import CloneSettingsDialogDesign


@dataclass
class CloneSettingsDialogDomain():
	instances: List[SheetInstance]
	footprints: List[Footprint]
	relations: MultiMap[SheetInstance, SheetInstance]


@final
class CloneSettingsDialog(CloneSettingsDialogDesign):

	def __init__(
		self,
		logger: Logger,
		footprints: Iterable[Footprint],
		instances: Iterable[SheetInstance],
		relations: MultiMap[SheetInstance, SheetInstance],
		settings: Optional[CloneSettings] = None
	):
		super().__init__(parent=wx.FindWindowByName("PcbFrame"))
		self.logger = logger.getChild(self.__class__.__name__)
		if not footprints:
			raise ValueError("No footprints provided")
		self.domain = CloneSettingsDialogDomain(
			instances=sorted(instances, key=lambda instance: instance.name_path),
			footprints=sorted(footprints, key=lambda footprint: footprint.reference),
			relations=relations,
		)
		if settings is None:
			settings = CloneSettings(
				instances=set(self.domain.instances),
				placement=ClonePlacementSettings(
					strategy=ClonePlacementStrategyType.RELATIVE,
					relative=ClonePlacementRelativeStrategySettings(
						anchor=self.domain.footprints[0],
					),
					grid=ClonePlacementGridStrategySettings(),
				)
			)
		self.settings = settings
		this = self

		self.position_strategy.SetSelection(list(ClonePlacementStrategyType).index(self.settings.placement.strategy))
		self.grid_wrap.SetValue(self.settings.placement.grid.wrap)
		self.grid_wrap_at.SetValue(self.settings.placement.grid.wrap_at)
		self.grid_main_interval.SetValue(self.settings.placement.grid.main_interval / SIZE_SCALE)
		self.grid_cross_interval.SetValue(self.settings.placement.grid.cross_interval / SIZE_SCALE)

		@final
		class InstancesAdapter(TreeControlBranchSelectionAdapter):
			def selection_changed(self): this.instances_adapter_selection_changed()
		self.instances_adapter = InstancesAdapter(
			items=self.domain.instances,
			relations=self.domain.relations,
			control=self.instances,
			selection=self.settings.instances,
		)

		@final
		class RelativeAnchorAdapter(StaticListBoxAdapter[Footprint]):
			def selection_changed(self): this.relative_anchor_adapter_selection_changed()
		self.relative_anchor_adapter = RelativeAnchorAdapter(
			control=self.relative_anchor,
			items=self.domain.footprints,
			selection=[item for item in [self.settings.placement.relative.anchor] if item is not None],
		)

		@final
		class GridFlowDirectionAdapter(StaticChoiceAdapter[ClonePlacementGridFlow]):
			def get_caption(self, item: ClonePlacementGridFlow) -> str: return item.value
			def selection_changed(self): this.grid_flow_direction_adapter_selection_changed()
		self.grid_flow_direction_adapter = GridFlowDirectionAdapter(
			control=self.grid_flow_direction,
			items=list(ClonePlacementGridFlow),
			selection=this.settings.placement.grid.flow,
		)

		@final
		class GridSortAdapter(StaticChoiceAdapter[ClonePlacementGridSort]):
			def get_caption(self, item: ClonePlacementGridSort) -> str: return item.value
			def selection_changed(self): this.grid_sort_adapter_selection_changed()
		self.grid_sort_adapter = GridSortAdapter(
			control=self.grid_sort,
			items=list(ClonePlacementGridSort),
			selection=this.settings.placement.grid.sort,
		)

	def execute(self) -> Optional[CloneSettings]:
		try:
			self.SetReturnCode(wx.ID_CANCEL)
			result = self.ShowModal()
			self.logger.info("Result: %s", result)
			if result == wx.ID_OK:
				return self.settings
			else:
				return None
		finally:
			self.Destroy()

	def model_changed(self) -> None:
		self.ok_button.Enable(self.settings.is_valid())

	def instances_adapter_selection_changed(self) -> None:
		self.settings.instances = self.instances_adapter.selection
		self.model_changed()

	def relative_anchor_adapter_selection_changed(self) -> None:
		self.settings.placement.relative.anchor = self.relative_anchor_adapter.selection[0]
		self.model_changed()

	def grid_sort_adapter_selection_changed(self) -> None:
		self.settings.placement.grid.sort = self.grid_sort_adapter.selection
		self.model_changed()

	def grid_flow_direction_adapter_selection_changed(self) -> None:
		self.settings.placement.grid.flow = self.grid_flow_direction_adapter.selection
		self.model_changed()

	### Overrides

	def instances_edit_veto(self, event):
		event.Veto()

	def instances_selection_toggle(self, event):
		pass  # Handled by adapter

	def position_strategy_changed(self, event):
		self.settings.placement.strategy = tuple(ClonePlacementStrategyType)[self.position_strategy.GetSelection()]
		self.model_changed()

	def relative_anchor_changed(self, event):
		pass  # Handled by adapter

	def grid_sort_changed(self, event):
		pass  # Handled by adapter

	def grid_flow_direction_changed(self, event):
		pass  # Handled by adapter

	def grid_wrap_changed(self, event):
		self.settings.placement.grid.wrap = self.grid_wrap.GetValue()
		self.model_changed()

	def grid_wrap_at_changed(self, event):
		self.settings.placement.grid.wrap_at = self.grid_wrap_at.GetValue()
		self.model_changed()

	def grid_main_interval_changed(self, event):
		self.settings.placement.grid.main_interval = int(self.grid_main_interval.GetValue() * SIZE_SCALE)
		self.model_changed()

	def grid_cross_interval_changed(self, event):
		self.settings.placement.grid.cross_interval = int(self.grid_cross_interval.GetValue(), SIZE_SCALE)
		self.model_changed()

	def ok_button_clicked(self, event):
		self.EndModal(wx.ID_OK)

	def dialog_closed(self, event):
		self.EndModal(wx.ID_CANCEL)
