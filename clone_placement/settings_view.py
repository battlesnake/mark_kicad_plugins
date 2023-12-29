from typing import Optional, List, final, cast
from logging import Logger

import wx
import wx.dataview

from ..utils.kicad_units import UserUnits, SizeUnits

from ..parse_v8 import SheetInstance, Footprint

from ..ui.list_box_adapter import StaticListBoxAdapter
from ..ui.choice_adapter import StaticChoiceAdapter
from ..ui.tree_control_branch_selection_adapter import TreeControlBranchSelectionAdapter

from .placement_settings import ClonePlacementStrategyType, ClonePlacementGridFlow, ClonePlacementGridSort
from .settings import CloneSettings
from .settings_view_design import CloneSettingsViewDesign
from .settings_controller import CloneSettingsController


@final
class CloneSettingsView(CloneSettingsViewDesign):

	previous_instance: Optional["CloneSettingsView"] = None

	def __init__(
		self,
		logger: Logger,
		instances: List[SheetInstance],
		footprints: List[Footprint],
		controller: CloneSettingsController,
		settings: CloneSettings,
	):
		super().__init__(parent=wx.FindWindowByName("PcbFrame"))
		self.logger = logger.getChild(cast(str, type(self).__name__))
		self.controller = controller
		if not footprints:
			raise ValueError("No footprints provided")
		self.settings = settings
		this = self

		self.position_strategy.SetSelection(list(ClonePlacementStrategyType).index(self.settings.placement.strategy))
		self.grid_wrap.SetValue(self.settings.placement.grid.wrap)
		self.grid_wrap_at.SetValue(self.settings.placement.grid.wrap_at)

		self.update_length_views()

		@final
		class InstancesAdapter(TreeControlBranchSelectionAdapter[SheetInstance]):

			def selection_changed(self):
				this.instances_adapter_selection_changed()

			def get_view_text(self, item: SheetInstance):
				return str(item)

			def get_item_type_key(self, item: SheetInstance):
				return item.name

			def get_item_sort_key(self, item: SheetInstance):
				return item.name

		self.instances_adapter = InstancesAdapter(
			items=instances,
			get_parent=lambda item: item.parent,
			control=self.instances,
			selection=self.settings.instances,
		)

		@final
		class RelativeAnchorAdapter(StaticListBoxAdapter[Footprint]):

			def selection_changed(self):
				this.relative_anchor_adapter_selection_changed()

		self.relative_anchor_adapter = RelativeAnchorAdapter(
			control=self.relative_anchor,
			items=footprints,
			selection=[item for item in [self.settings.placement.relative.anchor] if item is not None],
		)

		@final
		class GridFlowDirectionAdapter(StaticChoiceAdapter[ClonePlacementGridFlow]):

			def get_caption(self, item: ClonePlacementGridFlow) -> str:
				return item.value

			def selection_changed(self):
				this.grid_flow_direction_adapter_selection_changed()

		self.grid_flow_direction_adapter = GridFlowDirectionAdapter(
			control=self.grid_flow_direction,
			items=list(ClonePlacementGridFlow),
			selection=this.settings.placement.grid.flow,
		)

		@final
		class GridSortAdapter(StaticChoiceAdapter[ClonePlacementGridSort]):

			def get_caption(self, item: ClonePlacementGridSort) -> str:
				return item.value

			def selection_changed(self):
				this.grid_sort_adapter_selection_changed()

		self.grid_sort_adapter = GridSortAdapter(
			control=self.grid_sort,
			items=list(ClonePlacementGridSort),
			selection=this.settings.placement.grid.sort,
		)

		@final
		class GridLengthUnitAdapter(StaticChoiceAdapter[UserUnits]):

			def get_caption(self, item: UserUnits) -> str:
				return item.get_abbreviation()

			def selection_changed(self):
				this.grid_length_unit_adapter_selection_changed()

		self.grid_length_unit_adapter = GridLengthUnitAdapter(
			control=self.grid_unit,
			items=list(UserUnits),
			selection=this.settings.placement.grid.length_unit,
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
		self.settings.placement.grid.main_interval, self.settings.placement.grid.cross_interval = self.settings.placement.grid.cross_interval, self.settings.placement.grid.main_interval
		self.update_length_views()
		self.model_changed()

	def grid_length_unit_adapter_selection_changed(self) -> None:
		self.settings.placement.grid.length_unit = self.grid_length_unit_adapter.selection
		self.update_length_views()
		self.model_changed()

	def update_length_views(self) -> None:
		user_unit = SizeUnits.get(self.settings.placement.grid.length_unit)
		self.grid_main_interval.SetValue(self.settings.placement.grid.main_interval / user_unit)
		self.grid_cross_interval.SetValue(self.settings.placement.grid.cross_interval / user_unit)

	# Overrides

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

	def grid_unit_changed(self, event: wx.Event):
		pass  # Handled by adapter

	def grid_wrap_changed(self, event: wx.Event):
		self.settings.placement.grid.wrap = self.grid_wrap.GetValue()
		self.model_changed()

	def grid_wrap_at_changed(self, event: wx.Event):
		self.settings.placement.grid.wrap_at = self.grid_wrap_at.GetValue()
		self.model_changed()

	def grid_main_interval_changed(self, event: wx.Event):
		user_unit = SizeUnits.get(self.settings.placement.grid.length_unit)
		self.settings.placement.grid.main_interval = int(self.grid_main_interval.GetValue() * user_unit)
		self.model_changed()

	def grid_cross_interval_changed(self, event: wx.Event):
		user_unit = SizeUnits.get(self.settings.placement.grid.length_unit)
		self.settings.placement.grid.cross_interval = int(self.grid_cross_interval.GetValue() * user_unit)
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
