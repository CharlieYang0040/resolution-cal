from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, DivisionByZero

class ResolutionCalculator:
    """Handles resolution and aspect ratio calculations."""
    def __init__(self):
        self._width: Decimal = Decimal("1920")
        self._height: Decimal = Decimal("1080")
        self._aspect_ratio: Decimal | None = None
        self._ratio_locked: bool = False
        self._calculate_ratio()

    @property
    def width(self) -> Decimal:
        return self._width

    @width.setter
    def width(self, value: str | float | Decimal):
        print(f"[Calc Debug] Setting width. Current locked: {self._ratio_locked}, ratio: {self._aspect_ratio}") # Debug print
        try:
            new_width = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if new_width <= 0:
                raise ValueError("Width must be positive")

            if self._ratio_locked and self._aspect_ratio is not None and self._aspect_ratio != 0:
                print("[Calc Debug] Width setter: Lock active, calculating height.") # Debug print
                new_height = (new_width / self._aspect_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if new_height <= 0:
                     print("[Calc Debug Warning] Calculated height would be non-positive. Width not changed.")
                     return
                self._height = new_height

            self._width = new_width
            if not self._ratio_locked:
                print("[Calc Debug] Width setter: Lock inactive, recalculating ratio.") # Debug print
                self._calculate_ratio()
            print(f"[Calc Debug] Width set. New W: {self._width}, H: {self._height}, Locked: {self._ratio_locked}") # Debug print

        except (InvalidOperation, ValueError) as e:
            print(f"Error setting width: {e}")

    @property
    def height(self) -> Decimal:
        return self._height

    @height.setter
    def height(self, value: str | float | Decimal):
        print(f"[Calc Debug] Setting height. Current locked: {self._ratio_locked}, ratio: {self._aspect_ratio}") # Debug print
        try:
            new_height = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if new_height <= 0:
                raise ValueError("Height must be positive")

            if self._ratio_locked and self._aspect_ratio is not None and self._aspect_ratio != 0:
                print("[Calc Debug] Height setter: Lock active, calculating width.") # Debug print
                new_width = (new_height * self._aspect_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if new_width <= 0:
                    print("[Calc Debug Warning] Calculated width would be non-positive. Height not changed.")
                    return
                self._width = new_width

            self._height = new_height
            if not self._ratio_locked:
                print("[Calc Debug] Height setter: Lock inactive, recalculating ratio.") # Debug print
                self._calculate_ratio()
            print(f"[Calc Debug] Height set. New W: {self._width}, H: {self._height}, Locked: {self._ratio_locked}") # Debug print

        except (InvalidOperation, ValueError) as e:
            print(f"Error setting height: {e}")

    @property
    def aspect_ratio(self) -> Decimal | None:
        return self._aspect_ratio

    @property
    def aspect_ratio_str(self) -> str:
        if self._aspect_ratio is None or self._aspect_ratio == 0:
            return "N/A"
        # Basic float representation for now
        # TODO: Implement common fraction representation (e.g., 16:9)
        return f"{self._aspect_ratio:.3f}:1" # Display more precision

    @property
    def is_ratio_locked(self) -> bool:
        return self._ratio_locked

    def lock_ratio(self, lock: bool):
        lock = bool(lock) # Ensure boolean
        print(f"[Calc Debug] lock_ratio called with: {lock}. Current state: {self._ratio_locked}") # Debug print
        if self._ratio_locked == lock:
            print("[Calc Debug] lock_ratio: No change needed.") # Debug print
            return

        self._ratio_locked = lock
        if lock:
            print("[Calc Debug] lock_ratio: Locking ratio, calculating current.") # Debug print
            self._calculate_ratio()
        print(f"[Calc Debug] lock_ratio finished. New state: {self._ratio_locked}, Ratio: {self._aspect_ratio}") # Debug print

    def _calculate_ratio(self):
        print("[Calc Debug] Calculating ratio...") # Debug print
        if self._height > 0:
            try:
                self._aspect_ratio = (self._width / self._height).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP) # Increased precision slightly
            except Exception as e:
                print(f"Error calculating ratio: {e}")
                self._aspect_ratio = None
        else:
            self._aspect_ratio = None
        print(f"[Calc Debug] Ratio calculated: {self._aspect_ratio}") # Debug print 

    def set_ratio_and_calculate(self, ratio_str: str, base_on_width: bool):
        """Parses a ratio string (e.g., '16:9') and updates width or height based on the selected base."""
        print(f"[Calc Debug] set_ratio_and_calculate called. Ratio: '{ratio_str}', BaseWidth: {base_on_width}")
        try:
            # Parse the ratio string
            if ':' not in ratio_str:
                # Try parsing as a single decimal number (e.g., 1.777)
                target_ratio = Decimal(ratio_str).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            else:
                parts = ratio_str.split(':')
                if len(parts) != 2:
                    raise ValueError("Invalid ratio format. Use W:H (e.g., 16:9)")
                w_part = Decimal(parts[0].strip())
                h_part = Decimal(parts[1].strip())
                if w_part <= 0 or h_part <= 0:
                    raise ValueError("Ratio parts must be positive")
                target_ratio = (w_part / h_part).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

            if target_ratio <= 0:
                 raise ValueError("Calculated ratio must be positive")

            print(f"[Calc Debug] Parsed target ratio: {target_ratio}")

            # Lock the newly calculated ratio immediately
            self._aspect_ratio = target_ratio
            self._ratio_locked = True # Automatically lock after setting ratio this way

            # Calculate the dependent value based on the selected base
            if base_on_width:
                # Calculate height based on current width and new ratio
                if self._width > 0 and self._aspect_ratio > 0:
                    new_height = (self._width / self._aspect_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if new_height > 0:
                        self._height = new_height
                        print(f"[Calc Debug] Calculated Height based on Width: {self._height}")
                    else:
                        print("[Calc Debug Warning] Calculated height non-positive, skipping update.")
                else:
                    print("[Calc Debug Warning] Cannot calculate height based on width (zero width or ratio). Ratio set, but height not updated.")
            else: # Base on height
                # Calculate width based on current height and new ratio
                if self._height > 0 and self._aspect_ratio > 0:
                    new_width = (self._height * self._aspect_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if new_width > 0:
                        self._width = new_width
                        print(f"[Calc Debug] Calculated Width based on Height: {self._width}")
                    else:
                         print("[Calc Debug Warning] Calculated width non-positive, skipping update.")
                else:
                     print("[Calc Debug Warning] Cannot calculate width based on height (zero height or ratio). Ratio set, but width not updated.")

            print(f"[Calc Debug] set_ratio finished. New W: {self._width}, H: {self._height}, Ratio: {self._aspect_ratio}, Locked: {self._ratio_locked}")

        except (InvalidOperation, ValueError, DivisionByZero) as e:
            print(f"Error setting ratio: {e}")
            # Optionally, revert lock state or ratio if parsing fails?
            # For now, just print error and potentially leave state as is. 

    # --- New properties for integer and decimal parts --- #
    @property
    def width_int(self) -> int:
        """Returns the width rounded to the nearest integer."""
        return int(self._width.to_integral_value(rounding=ROUND_HALF_UP))

    @property
    def height_int(self) -> int:
        """Returns the height rounded to the nearest integer."""
        return int(self._height.to_integral_value(rounding=ROUND_HALF_UP))

    @property
    def width_decimal_part_str(self) -> str:
        """Returns the decimal part of the width as a string (e.g., '.75'), or empty string if integer."""
        decimal_part = abs(self._width - Decimal(self.width_int))
        if decimal_part.is_zero():
            return ""
        # Format to two decimal places, remove leading zero
        return f"{decimal_part:.2f}"[1:] # Example: 0.75 -> .75

    @property
    def height_decimal_part_str(self) -> str:
        """Returns the decimal part of the height as a string (e.g., '.50'), or empty string if integer."""
        decimal_part = abs(self._height - Decimal(self.height_int))
        if decimal_part.is_zero():
            return ""
        return f"{decimal_part:.2f}"[1:]

    # --- New Property for Total Pixels ---
    @property
    def total_pixels(self) -> Decimal:
        """Calculates the total number of pixels (width * height)."""
        try:
            # Use integer values for pixel count
            return Decimal(self.width_int) * Decimal(self.height_int)
        except Exception:
            return Decimal("0") # Return 0 if calculation fails

    # --- New Method for Scaling ---
    def multiply_by_scale(self, scale_factor_str: str):
        """Multiplies the current width and height by the given scale factor."""
        print(f"[Calc Debug] multiply_by_scale called with scale: {scale_factor_str}")
        try:
            scale_factor = Decimal(scale_factor_str)
            if scale_factor <= 0:
                raise ValueError("Scale factor must be positive")

            # Store current lock state and temporarily unlock if needed for independent scaling
            was_locked = self._ratio_locked
            if was_locked:
                self.lock_ratio(False) # Temporarily unlock to scale both independently

            new_width = (self._width * scale_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            new_height = (self._height * scale_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Validate before setting
            if new_width <= 0 or new_height <= 0:
                 print("[Calc Debug Warning] Scaled dimensions would be non-positive. No change made.")
                 if was_locked: # Restore lock state if we temporarily unlocked
                     self.lock_ratio(True)
                 return

            # Use setters to handle potential side effects (like ratio calculation if unlocked)
            # Note: Since we unlocked, ratio will be recalculated by setters if was_locked was false.
            # If was_locked was true, we'll re-lock and recalculate below.
            self.width = new_width
            self.height = new_height

            # Restore lock state and recalculate ratio if it was locked initially
            if was_locked:
                self.lock_ratio(True) # This will recalculate the ratio based on the new W/H

            print(f"[Calc Debug] Scaling applied. New W: {self._width}, H: {self._height}, Locked: {self._ratio_locked}, Ratio: {self._aspect_ratio}")

        except (InvalidOperation, ValueError) as e:
            print(f"Error applying scale: {e}")
            # Consider if we need to restore lock state here as well in case of error mid-process 