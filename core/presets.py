from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ResolutionPreset:
    name: str
    width: Decimal
    height: Decimal

# Common Presets
PRESETS = [
    ResolutionPreset("SD (4:3)", Decimal("640"), Decimal("480")),
    ResolutionPreset("HD (16:9)", Decimal("1280"), Decimal("720")),
    ResolutionPreset("FHD (16:9)", Decimal("1920"), Decimal("1080")),
    ResolutionPreset("QHD (16:9)", Decimal("2560"), Decimal("1440")),
    ResolutionPreset("2K DCI (1.90:1)", Decimal("2048"), Decimal("1080")),
    ResolutionPreset("4K UHD (16:9)", Decimal("3840"), Decimal("2160")),
    ResolutionPreset("4K DCI (1.90:1)", Decimal("4096"), Decimal("2160")),
    ResolutionPreset("Square (1:1)", Decimal("1080"), Decimal("1080")),
    ResolutionPreset("CinemaScope (2.39:1)", Decimal("2048"), Decimal("858")),
]

def get_preset_names() -> list[str]:
    """Returns a list of preset names."""
    return [preset.name for preset in PRESETS]

def find_preset_by_name(name: str) -> ResolutionPreset | None:
    """Finds a preset by its name."""
    for preset in PRESETS:
        if preset.name == name:
            return preset
    return None 