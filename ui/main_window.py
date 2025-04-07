import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSlider, QCheckBox, QComboBox, QDoubleSpinBox, QSpacerItem, QSizePolicy,
    QButtonGroup, QRadioButton, QSpinBox
)
from PySide6.QtCore import Qt, Signal as pyqtSignal, Slot as pyqtSlot
from PySide6.QtGui import QDoubleValidator
from decimal import Decimal, ROUND_HALF_UP

from core.calculator import ResolutionCalculator
from core.presets import get_preset_names, find_preset_by_name

# Constants for slider precision
SLIDER_PRECISION_MULTIPLIER = 100
DEFAULT_MAX_RESOLUTION_VALUE = 4096 # Default range up to 4K
EXTENDED_MAX_RESOLUTION_VALUE = 16384 # Extended range

class MainWindow(QWidget):
    """Main application window."""
    # Signals to notify calculator of UI changes
    width_changed = pyqtSignal(str)
    height_changed = pyqtSignal(str)
    lock_ratio_changed = pyqtSignal(bool)
    preset_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.calculator = ResolutionCalculator()
        # Keep track of slider range state
        self.current_max_resolution = DEFAULT_MAX_RESOLUTION_VALUE
        self.init_ui()
        self.connect_signals()
        self.update_ui_from_calculator() # Initialize UI with default values

    def init_ui(self):
        self.setWindowTitle("Resolution Calculator")
        self.setGeometry(100, 100, 500, 400) # x, y, width, height

        main_layout = QVBoxLayout(self)

        # --- Presets --- #
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["-- Select Preset --"] + get_preset_names())
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        main_layout.addLayout(preset_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # --- Width --- #
        width_layout = self._create_value_slider_layout("Width:", "width")
        main_layout.addLayout(width_layout)

        # --- Height --- #
        height_layout = self._create_value_slider_layout("Height:", "height")
        main_layout.addLayout(height_layout)

        # --- Slider Range Control --- #
        range_layout = QHBoxLayout()
        self.range_button = QPushButton(f"Extend Range (>{DEFAULT_MAX_RESOLUTION_VALUE})")
        range_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        range_layout.addWidget(self.range_button)
        main_layout.addLayout(range_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # --- Aspect Ratio Display & Lock --- #
        ratio_display_lock_layout = QHBoxLayout()
        ratio_label = QLabel("Aspect Ratio:")
        self.ratio_display_label = QLabel("N/A") # Updated dynamically
        self.lock_ratio_checkbox = QCheckBox("Lock Ratio")
        ratio_display_lock_layout.addWidget(ratio_label)
        ratio_display_lock_layout.addWidget(self.ratio_display_label, 1)
        ratio_display_lock_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        ratio_display_lock_layout.addWidget(self.lock_ratio_checkbox)
        main_layout.addLayout(ratio_display_lock_layout)

        # --- Aspect Ratio Input & Base --- #
        ratio_input_layout = QHBoxLayout()
        ratio_input_label = QLabel("Set Ratio (e.g., 16:9):")
        self.ratio_input_edit = QLineEdit()
        self.ratio_input_edit.setPlaceholderText("Enter ratio and press Enter")

        # Ratio base selection
        self.ratio_base_group = QButtonGroup(self) # Group for radio buttons
        self.base_width_radio = QRadioButton("Width Based")
        self.base_height_radio = QRadioButton("Height Based")
        self.base_width_radio.setChecked(True) # Default to width based
        self.ratio_base_group.addButton(self.base_width_radio, 1) # ID 1 for width
        self.ratio_base_group.addButton(self.base_height_radio, 2) # ID 2 for height

        ratio_input_layout.addWidget(ratio_input_label)
        ratio_input_layout.addWidget(self.ratio_input_edit, 2) # Stretch input field
        ratio_input_layout.addWidget(self.base_width_radio)
        ratio_input_layout.addWidget(self.base_height_radio)

        main_layout.addLayout(ratio_input_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(main_layout)
        # Update slider/spinbox ranges initially
        self._update_widget_ranges()

    def _create_value_slider_layout(self, label_text: str, value_attr_name: str) -> QHBoxLayout:
        """Helper to create a layout with Label, SpinBox, Decimal Label, and Slider."""
        layout = QHBoxLayout()
        label = QLabel(label_text)
        spinbox = QSpinBox()
        decimal_label = QLabel("")
        decimal_label.setMinimumWidth(30)
        slider = QSlider(Qt.Orientation.Horizontal)

        spinbox.setRange(1, EXTENDED_MAX_RESOLUTION_VALUE)
        spinbox.setSingleStep(1)
        spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        slider.setRange(1 * SLIDER_PRECISION_MULTIPLIER, EXTENDED_MAX_RESOLUTION_VALUE * SLIDER_PRECISION_MULTIPLIER)
        slider.setSingleStep(1 * SLIDER_PRECISION_MULTIPLIER)
        slider.setPageStep(100 * SLIDER_PRECISION_MULTIPLIER)

        layout.addWidget(label)
        layout.addWidget(spinbox)
        layout.addWidget(decimal_label)
        layout.addWidget(slider, 1)

        setattr(self, f"{value_attr_name}_spinbox", spinbox)
        setattr(self, f"{value_attr_name}_decimal_label", decimal_label)
        setattr(self, f"{value_attr_name}_slider", slider)

        return layout

    def connect_signals(self):
        """Connect UI signals to slots and calculator methods."""
        # --- UI -> Internal Slots ---
        self.width_spinbox.valueChanged.connect(self._emit_width_changed_from_spinbox)
        self.height_spinbox.valueChanged.connect(self._emit_height_changed_from_spinbox)
        self.width_slider.valueChanged.connect(self._sync_slider_to_spinbox)
        self.height_slider.valueChanged.connect(self._sync_slider_to_spinbox)

        self.width_slider.sliderReleased.connect(self._emit_precise_value_from_slider)
        self.height_slider.sliderReleased.connect(self._emit_precise_value_from_slider)

        self.lock_ratio_checkbox.stateChanged.connect(
            self._handle_lock_checkbox_change
        )
        self.preset_combo.currentIndexChanged.connect(self._handle_preset_selection)

        # --- New Connections ---
        self.range_button.clicked.connect(self._handle_range_button)
        self.ratio_input_edit.returnPressed.connect(self._handle_ratio_input) # Trigger on Enter key

        # --- Internal Signals -> Calculator Logic (via slots) ---
        self.width_changed.connect(self._update_calculator_width)
        self.height_changed.connect(self._update_calculator_height)
        self.lock_ratio_changed.connect(self.calculator.lock_ratio)
        self.preset_selected.connect(self._apply_preset)

    # --- Slots for handling UI events --- #

    @pyqtSlot(int)
    def _emit_width_changed_from_spinbox(self, value: int):
        print(f"[UI Debug] Width SpinBox changed: {value}")
        self.width_changed.emit(str(value))

    @pyqtSlot(int)
    def _emit_height_changed_from_spinbox(self, value: int):
        print(f"[UI Debug] Height SpinBox changed: {value}")
        self.height_changed.emit(str(value))

    @pyqtSlot()
    def _emit_precise_value_from_slider(self):
        sender = self.sender()
        precise_value = Decimal(sender.value()) / Decimal(SLIDER_PRECISION_MULTIPLIER)
        print(f"[UI Debug] Slider released. Precise value: {precise_value:.2f}")
        if sender == self.width_slider:
             self.width_changed.emit(str(precise_value))
        elif sender == self.height_slider:
             self.height_changed.emit(str(precise_value))

    @pyqtSlot(int)
    def _sync_slider_to_spinbox(self, slider_value: int):
        sender = self.sender()
        target_spinbox = None
        target_decimal_label = None

        if sender == self.width_slider:
            target_spinbox = self.width_spinbox
            target_decimal_label = self.width_decimal_label
        elif sender == self.height_slider:
            target_spinbox = self.height_spinbox
            target_decimal_label = self.height_decimal_label
        else:
            return

        precise_value = Decimal(slider_value) / Decimal(SLIDER_PRECISION_MULTIPLIER)
        int_value = int(precise_value.to_integral_value(rounding=ROUND_HALF_UP))
        decimal_part = abs(precise_value - Decimal(int_value))
        decimal_str = f"{decimal_part:.2f}"[1:] if not decimal_part.is_zero() else ""

        target_spinbox.blockSignals(True)
        target_spinbox.setValue(int_value)
        target_spinbox.blockSignals(False)
        target_decimal_label.setText(decimal_str)

    @pyqtSlot(int)
    def _handle_preset_selection(self, index: int):
        if index > 0: # Ignore the default "-- Select Preset --" item
            preset_name = self.preset_combo.itemText(index)
            self.preset_selected.emit(preset_name)
        # If index is 0, we might want to do nothing or clear fields, TBD.

    @pyqtSlot(int)
    def _handle_lock_checkbox_change(self, state: int):
        is_checked = (state == Qt.CheckState.Checked.value)
        print(f"[UI Debug] Checkbox state changed. Raw state: {state}, Is Checked: {is_checked}")
        self.lock_ratio_changed.emit(is_checked)
        print(f"[UI Debug] lock_ratio_changed signal emitted with: {is_checked}")

    # --- Slots for updating the calculator --- #
    @pyqtSlot(str)
    def _update_calculator_width(self, value_str: str):
        """Slot to update the calculator's width property."""
        print(f"[UI Debug] _update_calculator_width called with: {value_str}")
        try:
            locked_before = self.calculator.is_ratio_locked
            print(f"[UI Debug] Before width update - Locked: {locked_before}")

            self.calculator.width = value_str

            locked_after = self.calculator.is_ratio_locked
            print(f"[UI Debug] After width update - Locked: {locked_after}")

            print("[UI Debug] Calling update_ui_from_calculator after width update")
            self.update_ui_from_calculator()
        except Exception as e:
            print(f"Error updating calculator width: {e}")

    @pyqtSlot(str)
    def _update_calculator_height(self, value_str: str):
        """Slot to update the calculator's height property."""
        print(f"[UI Debug] _update_calculator_height called with: {value_str}")
        try:
            locked_before = self.calculator.is_ratio_locked
            print(f"[UI Debug] Before height update - Locked: {locked_before}")

            self.calculator.height = value_str

            locked_after = self.calculator.is_ratio_locked
            print(f"[UI Debug] After height update - Locked: {locked_after}")

            print("[UI Debug] Calling update_ui_from_calculator after height update")
            self.update_ui_from_calculator()
        except Exception as e:
            print(f"Error updating calculator height: {e}")

    @pyqtSlot(str)
    def _apply_preset(self, preset_name: str):
        preset = find_preset_by_name(preset_name)
        if preset:
            is_locked = self.calculator.is_ratio_locked
            if is_locked:
                self.calculator.lock_ratio(False)

            self.calculator.width = preset.width
            self.calculator.height = preset.height

            if is_locked:
                self.calculator.lock_ratio(True)

            self.update_ui_from_calculator()
        else:
            print(f"Warning: Preset '{preset_name}' not found.")

    # --- Update UI --- #
    def update_ui_from_calculator(self):
        """Updates all relevant UI elements based on the calculator's state."""
        print("[UI Debug] update_ui_from_calculator called.")
        calculator_locked_state = self.calculator.is_ratio_locked
        checkbox_current_state = self.lock_ratio_checkbox.isChecked()
        print(f"[UI Debug] Updating UI. Calculator locked: {calculator_locked_state}, Checkbox currently: {checkbox_current_state}")

        self.width_spinbox.blockSignals(True)
        self.width_slider.blockSignals(True)
        self.width_decimal_label.blockSignals(True)
        self.height_spinbox.blockSignals(True)
        self.height_slider.blockSignals(True)
        self.height_decimal_label.blockSignals(True)
        self.lock_ratio_checkbox.blockSignals(True)
        self.preset_combo.blockSignals(True)

        width_precise = self.calculator.width
        height_precise = self.calculator.height
        width_int = self.calculator.width_int
        height_int = self.calculator.height_int
        width_decimal_str = self.calculator.width_decimal_part_str
        height_decimal_str = self.calculator.height_decimal_part_str

        self.width_spinbox.setValue(width_int)
        self.width_decimal_label.setText(width_decimal_str)
        self.height_spinbox.setValue(height_int)
        self.height_decimal_label.setText(height_decimal_str)

        self.width_slider.setValue(int(width_precise * SLIDER_PRECISION_MULTIPLIER))
        self.height_slider.setValue(int(height_precise * SLIDER_PRECISION_MULTIPLIER))

        self.ratio_display_label.setText(self.calculator.aspect_ratio_str)

        if checkbox_current_state != calculator_locked_state:
             print(f"[UI Debug] Checkbox state mismatch! Setting checkbox to: {calculator_locked_state}")
             self.lock_ratio_checkbox.setChecked(calculator_locked_state)
        else:
             print("[UI Debug] Checkbox state matches calculator. No change needed.")

        self.width_spinbox.blockSignals(False)
        self.width_slider.blockSignals(False)
        self.width_decimal_label.blockSignals(False)
        self.height_spinbox.blockSignals(False)
        self.height_slider.blockSignals(False)
        self.height_decimal_label.blockSignals(False)
        self.lock_ratio_checkbox.blockSignals(False)
        self.preset_combo.blockSignals(False)
        print("[UI Debug] update_ui_from_calculator finished.")

    def _update_widget_ranges(self):
        """Sets the min/max for sliders and spinboxes based on current_max_resolution."""
        max_val_precise = Decimal(self.current_max_resolution)
        max_val_int = int(max_val_precise.to_integral_value(rounding=ROUND_HALF_UP))
        slider_max = int(max_val_precise * SLIDER_PRECISION_MULTIPLIER)

        print(f"[UI Debug] Updating widget ranges. Max int val: {max_val_int}")

        self.width_spinbox.blockSignals(True)
        self.width_slider.blockSignals(True)
        self.width_decimal_label.blockSignals(True)
        self.height_spinbox.blockSignals(True)
        self.height_slider.blockSignals(True)
        self.height_decimal_label.blockSignals(True)

        for name in ["width", "height"]:
            spinbox = getattr(self, f"{name}_spinbox")
            slider = getattr(self, f"{name}_slider")

            current_spin_value = spinbox.value()
            current_precise_value = getattr(self.calculator, name)

            spinbox.setRange(1, max_val_int)
            slider.setRange(1 * SLIDER_PRECISION_MULTIPLIER, slider_max)

            if current_precise_value > max_val_precise:
                setattr(self.calculator, name, str(max_val_precise))
                spinbox.setValue(max_val_int)
                slider.setValue(slider_max)
                decimal_label = getattr(self, f"{name}_decimal_label")
                decimal_label.setText(getattr(self.calculator, f"{name}_decimal_part_str"))
            else:
                spinbox.setValue(current_spin_value)
                slider.setValue(int(current_precise_value * SLIDER_PRECISION_MULTIPLIER))
                decimal_label = getattr(self, f"{name}_decimal_label")
                decimal_label.setText(getattr(self.calculator, f"{name}_decimal_part_str"))

        if self.current_max_resolution == DEFAULT_MAX_RESOLUTION_VALUE:
            self.range_button.setText(f"Extend Range (>{DEFAULT_MAX_RESOLUTION_VALUE})")
        else:
            self.range_button.setText(f"Reset Range (≤{DEFAULT_MAX_RESOLUTION_VALUE})")

        self.width_spinbox.blockSignals(False)
        self.width_slider.blockSignals(False)
        self.width_decimal_label.blockSignals(False)
        self.height_spinbox.blockSignals(False)
        self.height_slider.blockSignals(False)
        self.height_decimal_label.blockSignals(False)

    @pyqtSlot()
    def _handle_range_button(self):
        """Toggles the slider/spinbox range between default and extended."""
        print("[UI Debug] Range button clicked.")
        if self.current_max_resolution == DEFAULT_MAX_RESOLUTION_VALUE:
            self.current_max_resolution = EXTENDED_MAX_RESOLUTION_VALUE
        else:
            self.current_max_resolution = DEFAULT_MAX_RESOLUTION_VALUE
        self._update_widget_ranges()
        self.update_ui_from_calculator()

    @pyqtSlot()
    def _handle_ratio_input(self):
        """Handles the Enter key press in the ratio input field."""
        ratio_text = self.ratio_input_edit.text().strip()
        if not ratio_text:
            return

        print(f"[UI Debug] Ratio input entered: '{ratio_text}'")

        base_on_width = self.base_width_radio.isChecked()
        print(f"[UI Debug] Ratio base selected: {'Width' if base_on_width else 'Height'}")

        self.calculator.set_ratio_and_calculate(ratio_text, base_on_width)

        self.update_ui_from_calculator()

# Example of how to run this window directly (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Need to instantiate the calculator if running standalone
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec()) 