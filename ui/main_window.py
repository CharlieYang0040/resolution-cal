import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSlider, QCheckBox, QComboBox, QDoubleSpinBox, QSpacerItem, QSizePolicy,
    QButtonGroup, QRadioButton, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, Signal as pyqtSignal, Slot as pyqtSlot, QRectF
from PySide6.QtGui import QDoubleValidator, QPainter, QColor, QBrush, QPen, QPaintEvent
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from core.calculator import ResolutionCalculator
from core.presets import get_preset_names, find_preset_by_name

# Constants for slider precision
SLIDER_PRECISION_MULTIPLIER = 100
DEFAULT_MAX_RESOLUTION_VALUE = 4096 # Default range up to 4K
EXTENDED_MAX_RESOLUTION_VALUE = 16384 # Extended range

# --- Ratio Preview Widget --- #
class RatioPreviewWidget(QWidget):
    """A widget to visually display the current aspect ratio compared to 16:9."""
    def __init__(self, calculator: ResolutionCalculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.setMinimumHeight(180) # Increased minimum height for better vertical display
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        widget_rect = self.rect() # Use the whole widget rect for centering
        padding = 10
        # draw_area is still useful for defining bounds, but scale depends mostly on width
        draw_area = widget_rect.adjusted(padding, padding, -padding, -padding)

        if draw_area.width() <= 0 or draw_area.height() <= 0:
            return

        painter.fillRect(widget_rect, self.palette().color(self.backgroundRole()))

        # --- Determine Scale Factor primarily based on Width fitting FHD --- #
        fhd_w = Decimal(1920)
        fhd_h = Decimal(1080)
        area_w = Decimal(draw_area.width())
        area_h = Decimal(draw_area.height())

        # 1. Calculate the maximum scale that fits FHD within the draw_area
        max_scale_w = area_w / fhd_w if fhd_w > 0 else Decimal(1)
        max_scale_h = area_h / fhd_h if fhd_h > 0 else Decimal(1)
        max_scale = min(max_scale_w, max_scale_h) # Max scale that fits

        # 2. Set the final drawing scale to be smaller (e.g., 40% of max fit)
        scale_reduction_factor = Decimal("0.4") # Less than half
        scale = max_scale * scale_reduction_factor

        if scale <= 0:
             return

        # Center point for drawing all rectangles
        center_x = widget_rect.center().x()
        center_y = widget_rect.center().y()

        # --- Draw 16:9 Aspect Ratio Background (Gray Fill) --- #
        # Draw this background based on the calculated scale fitting FHD
        bg_w = float(fhd_w * scale)
        bg_h = float(fhd_h * scale)
        bg_x = float(center_x - bg_w / 2)
        bg_y = float(center_y - bg_h / 2)
        bg_rect = QRectF(bg_x, bg_y, bg_w, bg_h)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(128, 128, 128, 100))
        # Clip the drawing to the padded draw_area to avoid spilling over padding
        painter.save()
        painter.setClipRect(draw_area)
        painter.drawRect(bg_rect)
        painter.restore()

        # --- Draw 1920x1080 (FHD) Reference Outline (Green Dashed Line) --- #
        # Uses the same rect as the background
        fhd_rect = bg_rect
        fhd_pen = QPen(QColor(0, 180, 0, 200))
        fhd_pen.setStyle(Qt.PenStyle.DashLine)
        fhd_pen.setWidth(1)
        painter.setPen(fhd_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.save()
        painter.setClipRect(draw_area)
        painter.drawRect(fhd_rect)
        painter.restore()

        # --- Draw Current Resolution Scaled Rectangle (Blue Fill) --- #
        try:
            current_width = self.calculator.width
            current_height = self.calculator.height

            if current_width > 0 and current_height > 0:
                # Calculate size based on the *same fixed scale*
                current_rect_w = float(current_width * scale)
                current_rect_h = float(current_height * scale)
                # Position centered in the widget
                current_rect_x = float(center_x - current_rect_w / 2)
                current_rect_y = float(center_y - current_rect_h / 2)
                current_rect = QRectF(current_rect_x, current_rect_y, current_rect_w, current_rect_h)

                painter.setPen(QPen(QColor(0, 0, 200, 150), 1))
                painter.setBrush(QColor(100, 100, 255, 150))
                painter.save()
                painter.setClipRect(draw_area) # Clip drawing within the bounds
                painter.drawRect(current_rect)
                painter.restore()

        except Exception as e:
            print(f"Error drawing current ratio: {e}")

    def _calculate_rect_in_area(self, area: QRectF, ratio: Decimal) -> QRectF:
        """Calculates the largest possible rectangle with the given ratio centered within the area."""
        if ratio <= 0:
            return QRectF()

        area_w = Decimal(area.width())
        area_h = Decimal(area.height())
        area_ratio = area_w / area_h

        target_w = area_w
        target_h = area_h

        if ratio > area_ratio: # Target is wider than area, constrained by width
            target_h = area_w / ratio
        else: # Target is taller or same as area, constrained by height
            target_w = area_h * ratio

        # Center the rectangle
        offset_x = (area_w - target_w) / 2
        offset_y = (area_h - target_h) / 2

        # Ensure coordinates are float for QRectF
        final_x = float(area.left() + offset_x)
        final_y = float(area.top() + offset_y)
        final_w = float(target_w)
        final_h = float(target_h)

        return QRectF(final_x, final_y, final_w, final_h)


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
        self.ratio_preview_widget = None # Initialize preview widget variable
        self.init_ui()
        self.connect_signals()
        self.update_ui_from_calculator() # Initialize UI with default values

    def init_ui(self):
        self.setWindowTitle("Resolution Calculator")
        self.setGeometry(100, 100, 550, 680) # Increased window height

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

        # --- Total Pixels & Range Control (Combined Layout) --- #
        pixels_and_range_layout = QHBoxLayout()
        pixels_label = QLabel("Total Pixels (W x H):")
        self.total_pixels_label = QLabel("0")
        self.total_pixels_label.setStyleSheet("font-weight: bold;")
        self.range_button = QPushButton(f"Extend Range (>{DEFAULT_MAX_RESOLUTION_VALUE})") # Moved button creation here

        pixels_and_range_layout.addWidget(pixels_label)
        pixels_and_range_layout.addWidget(self.total_pixels_label)
        pixels_and_range_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        pixels_and_range_layout.addWidget(self.range_button)
        main_layout.addLayout(pixels_and_range_layout)

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

        # --- Scaling (Enter to Apply, using QLineEdit) --- #
        scale_layout = QHBoxLayout()
        scale_label = QLabel("Scale by Factor:")
        self.scale_input_edit = QLineEdit() # Changed from QDoubleSpinBox
        self.scale_input_edit.setPlaceholderText("Enter scale and press Enter") # Added placeholder
        # self.scale_spinbox.setRange(0.01, 100.0) # Removed SpinBox settings
        # self.scale_spinbox.setSingleStep(0.1)
        # self.scale_spinbox.setValue(1.0)
        # self.scale_spinbox.setDecimals(2)
        # self.scale_spinbox.setToolTip("...") # Placeholder is enough

        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(self.scale_input_edit, 1) # Use the new QLineEdit
        main_layout.addLayout(scale_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)) # Adjusted spacer

        # --- Add Ratio Preview Widget --- #
        self.ratio_preview_widget = RatioPreviewWidget(self.calculator)
        main_layout.addWidget(self.ratio_preview_widget)

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
        self.width_slider.valueChanged.connect(self._handle_slider_value_changed)
        self.height_slider.valueChanged.connect(self._handle_slider_value_changed)

        self.lock_ratio_checkbox.stateChanged.connect(
            self._handle_lock_checkbox_change
        )
        self.preset_combo.currentIndexChanged.connect(self._handle_preset_selection)

        # --- New Connections ---
        self.range_button.clicked.connect(self._handle_range_button)
        self.ratio_input_edit.returnPressed.connect(self._handle_ratio_input) # Trigger on Enter key

        # Connect scale line edit return pressed signal
        # self.scale_spinbox.editingFinished.connect(self._handle_scale_input) # Remove old connection
        self.scale_input_edit.returnPressed.connect(self._handle_scale_input)

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

    @pyqtSlot(int)
    def _handle_slider_value_changed(self, slider_value: int):
        """Handles the valueChanged signal from sliders for real-time updates."""
        sender = self.sender()
        precise_value = Decimal(slider_value) / Decimal(SLIDER_PRECISION_MULTIPLIER)
        print(f"[UI Debug] Slider value changed. Precise value: {precise_value:.2f}")

        # Sync the corresponding spinbox/decimal display visually *without* emitting signals from them
        self._sync_slider_to_spinbox(slider_value)

        # Emit the precise value change signal
        if sender == self.width_slider:
            self.width_changed.emit(str(precise_value))
        elif sender == self.height_slider:
            self.height_changed.emit(str(precise_value))

    @pyqtSlot(int)
    def _handle_preset_selection(self, index: int):
        if index > 0: # Ignore the default "-- Select Preset --" item
            preset_name = self.preset_combo.itemText(index)
            print(f"[UI Debug] Preset selected: {preset_name}")
            self.preset_selected.emit(preset_name)

            # Reset the combo box to the default item after applying
            self.preset_combo.blockSignals(True) # Prevent re-triggering this slot
            self.preset_combo.setCurrentIndex(0)
            self.preset_combo.blockSignals(False)
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

        # Update total pixels display
        try:
            total_pixels_val = self.calculator.total_pixels
            self.total_pixels_label.setText(f"{total_pixels_val:,.0f}") # Use :.0f to avoid decimals for pixels
        except Exception as e:
            print(f"Error updating total pixels display: {e}")
            self.total_pixels_label.setText("Error")

        # --- Trigger Ratio Preview Update --- #
        if self.ratio_preview_widget:
            self.ratio_preview_widget.update() # Tell the preview widget to repaint

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

    # --- Slot for Scaling Input --- #
    @pyqtSlot()
    def _handle_scale_input(self):
        """Handles the returnPressed signal from the scale line edit."""
        scale_text = self.scale_input_edit.text().strip()
        if not scale_text:
            return # Ignore empty input

        try:
            # Attempt to convert text to Decimal for validation
            scale_factor = Decimal(scale_text)
            if scale_factor <= 0:
                 print("[UI Debug Warning] Scale factor must be positive.")
                 # Maybe add user feedback here (e.g., status bar message or brief popup)
                 return

            print(f"[UI Debug] Scale input Enter pressed. Factor: {scale_factor}")
            self.calculator.multiply_by_scale(scale_text) # Pass the original string
            self.update_ui_from_calculator() # Update UI after scaling
            # Clear the input field after successful application?
            # self.scale_input_edit.clear() # Consider uncommenting this line

        except InvalidOperation:
            print(f"[UI Debug Error] Invalid scale factor input: {scale_text}")
            # Add user feedback here as well
        except ValueError as e:
             print(f"[UI Debug Error] Error applying scale: {e}")
        except Exception as e:
            print(f"Error in scaling operation from UI: {e}")

    @pyqtSlot(int)
    def _sync_slider_to_spinbox(self, slider_value: int):
        """Visually synchronizes the SpinBox and Decimal Label with the Slider's value."""
        sender = self.sender()
        target_spinbox = None
        target_decimal_label = None

        # Determine which slider triggered the change
        if sender == self.width_slider:
            target_spinbox = self.width_spinbox
            target_decimal_label = self.width_decimal_label
        elif sender == self.height_slider:
            target_spinbox = self.height_spinbox
            target_decimal_label = self.height_decimal_label
        else:
            # If called unexpectedly (e.g., during setup), find the target based on slider value
            # This might happen if update_ui calls this indirectly before sender is set? Unlikely but safe.
            if hasattr(self, 'width_slider') and self.width_slider.value() == slider_value:
                 target_spinbox = self.width_spinbox
                 target_decimal_label = self.width_decimal_label
            elif hasattr(self, 'height_slider') and self.height_slider.value() == slider_value:
                 target_spinbox = self.height_spinbox
                 target_decimal_label = self.height_decimal_label
            else:
                print("[UI Debug Warning] _sync_slider_to_spinbox called without identifiable sender or matching value.")
                return

        precise_value = Decimal(slider_value) / Decimal(SLIDER_PRECISION_MULTIPLIER)
        int_value = int(precise_value.to_integral_value(rounding=ROUND_HALF_UP))
        decimal_part = abs(precise_value - Decimal(int_value))
        decimal_str = f"{decimal_part:.2f}"[1:] if not decimal_part.is_zero() else ""

        # Block signals to prevent infinite loops
        target_spinbox.blockSignals(True)
        target_spinbox.setValue(int_value)
        target_spinbox.blockSignals(False)
        target_decimal_label.setText(decimal_str)

# Example of how to run this window directly (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Need to instantiate the calculator if running standalone
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec()) 