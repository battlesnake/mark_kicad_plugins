from typing import Optional, List, final, cast
from dataclasses import dataclass
from logging import Logger

import wx
import wx.dataview

import pcbnew  # pyright: ignore

from .kicad_entities import SheetInstance, Footprint, SIZE_SCALE
from .list_box_adapter import StaticListBoxAdapter
from .choice_adapter import StaticChoiceAdapter
from .tree_control_branch_selection_adapter import TreeControlBranchSelectionAdapter
from .clone_placement_settings import ClonePlacementSettings, ClonePlacementStrategyType, ClonePlacementRelativeStrategySettings, ClonePlacementGridStrategySettings, ClonePlacementGridFlow, ClonePlacementGridSort
from .clone_settings import CloneSettings
from .clone_settings_view_design import CloneSettingsViewDesign
from .clone_settings_controller import CloneSettingsController


@final
@dataclass
class CloneSettingsViewDomain():
	instances: List[SheetInstance]
	footprints: List[Footprint]


@final
class CloneSettingsView(CloneSettingsViewDesign):

	previous_instance: Optional["CloneSettingsView"] = None

	def __init__(
		self,
		logger: Logger,
		domain: CloneSettingsViewDomain,
		controller: CloneSettingsController,
		settings: Optional[CloneSettings] = None
	):
		super().__init__(parent=wx.FindWindowByName("PcbFrame"))
		self.logger = logger.getChild(cast(str, type(self).__name__))
		self.controller = controller
		if not domain.footprints:
			raise ValueError("No footprints provided")
		self.domain = domain
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
		class InstancesAdapter(TreeControlBranchSelectionAdapter[SheetInstance]):
			def selection_changed(self): this.instances_adapter_selection_changed()
		self.instances_adapter = InstancesAdapter(
			items=self.domain.instances,
			get_parent=lambda item: item.parent,
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
		if CloneSettingsView.previous_instance is not None:
			previous_instance = CloneSettingsView.previous_instance
			CloneSettingsView.previous_instance = None
			previous_instance.DestroyLater()
		CloneSettingsView.previous_instance = self
		self.model_changed()
		self.Show()

	def model_changed(self) -> None:
		valid = self.settings.is_valid()
		self.ok_button.Enable(valid)
		self.preview_button.Enable(valid)
		if not valid and self.controller.has_preview():
			self.controller.clear_preview()
		self.undo_button.Enable(self.controller.can_undo())

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

	def instances_edit_veto(self, event: wx.Event):
		event.Veto()

	def instances_selection_toggle(self, event: wx.Event):
		pass  # Handled by adapter

	def position_strategy_changed(self, event: wx.Event):
		self.settings.placement.strategy = tuple(ClonePlacementStrategyType)[self.position_strategy.GetSelection()]
		self.model_changed()

	def relative_anchor_changed(self, event: wx.Event):
		pass  # Handled by adapter

	def grid_sort_changed(self, event: wx.Event):
		pass  # Handled by adapter

	def grid_flow_direction_changed(self, event: wx.Event):
		pass  # Handled by adapter

	def grid_wrap_changed(self, event: wx.Event):
		self.settings.placement.grid.wrap = self.grid_wrap.GetValue()
		self.model_changed()

	def grid_wrap_at_changed(self, event: wx.Event):
		self.settings.placement.grid.wrap_at = self.grid_wrap_at.GetValue()
		self.model_changed()

	def grid_main_interval_changed(self, event: wx.Event):
		self.settings.placement.grid.main_interval = int(self.grid_main_interval.GetValue() * SIZE_SCALE)
		self.model_changed()

	def grid_cross_interval_changed(self, event: wx.Event):
		self.settings.placement.grid.cross_interval = int(self.grid_cross_interval.GetValue() * SIZE_SCALE)
		self.model_changed()

	def preview_button_clicked(self, event: wx.Event):
		self.logger.info("Preview button pressed")
		self.controller.apply_preview(self.settings)
		self.model_changed()

	def undo_button_clicked(self, event: wx.Event):
		self.logger.info("Undo button pressed")
		self.controller.undo()
		self.model_changed()

	def ok_button_clicked(self, event: wx.Event):
		self.logger.info("Ok button pressed")
		self.controller.apply(self.settings)
		self.model_changed()
		self.Hide()

	def cancel_button_clicked(self, event: wx.Event):
		self.logger.info("Cancel button pressed")
		self.controller.clear_preview()
		self.model_changed()
		self.Hide()

	def dialog_closed(self, event: wx.Event):
		self.logger.info("Dialog closed")
		self.controller.clear_preview()
		self.model_changed()
		self.Hide()
