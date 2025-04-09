from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ResolutionPreset:
    name: str
    width: Decimal
    height: Decimal

# Common Presets
PRESETS = [
    # Standard Video/Display
    ResolutionPreset("SD (4:3)", Decimal("640"), Decimal("480")),
    ResolutionPreset("HD (16:9)", Decimal("1280"), Decimal("720")),
    ResolutionPreset("FHD (16:9)", Decimal("1920"), Decimal("1080")),
    ResolutionPreset("QHD (16:9)", Decimal("2560"), Decimal("1440")),
    ResolutionPreset("4K UHD (16:9)", Decimal("3840"), Decimal("2160")),

    # Cinema Standards
    ResolutionPreset("2K DCI (1.90:1)", Decimal("2048"), Decimal("1080")),
    ResolutionPreset("4K DCI (1.90:1)", Decimal("4096"), Decimal("2160")),
    ResolutionPreset("Academy Ratio (1.375:1)", Decimal("1998"), Decimal("1453")),
    ResolutionPreset("Widescreen Flat (1.85:1)", Decimal("1998"), Decimal("1080")),
    ResolutionPreset("CinemaScope (2.39:1)", Decimal("2048"), Decimal("858")),
    ResolutionPreset("Univisium (2:1)", Decimal("2160"), Decimal("1080")),
    ResolutionPreset("IMAX Digital (1.90:1)", Decimal("4096"), Decimal("2160")), # Same as 4K DCI, different name
    ResolutionPreset("IMAX 70mm Film (1.43:1 approx)", Decimal("4096"), Decimal("2864")), # Approximated based on 4K width

    # Mobile (Portrait Focus)
    ResolutionPreset("Mobile FHD+ (9:19.5)", Decimal("1080"), Decimal("2340")),
    ResolutionPreset("Mobile FHD+ (9:20)", Decimal("1080"), Decimal("2400")),
    ResolutionPreset("Mobile QHD+ (9:19 approx)", Decimal("1440"), Decimal("3040")),
    ResolutionPreset("Mobile QHD+ (9:21 approx)", Decimal("1440"), Decimal("3360")),

    # Tablet Aspect Ratios
    ResolutionPreset("iPad 10.9\" (1640x2360)", Decimal("1640"), Decimal("2360")), # ~7:10 ratio
    ResolutionPreset("iPad Pro 11\" (1668x2388)", Decimal("1668"), Decimal("2388")), # ~7:10 ratio
    ResolutionPreset("Android Tab (16:10)", Decimal("2560"), Decimal("1600")),
    ResolutionPreset("Surface Pro (3:2)", Decimal("2880"), Decimal("1920")),

    # Photography & Common Ratios
    ResolutionPreset("Square (1:1)", Decimal("1080"), Decimal("1080")),
    ResolutionPreset("Photo 35mm (3:2)", Decimal("3000"), Decimal("2000")), # Example Resolution
    ResolutionPreset("Photo Micro 4/3 (4:3)", Decimal("2000"), Decimal("1500")), # Example Resolution
    ResolutionPreset("Photo Medium Format (6:7 approx)", Decimal("2100"), Decimal("2450")), # Example Resolution
    ResolutionPreset("Print 5x7 (7:5)", Decimal("2100"), Decimal("1500")), # Example Resolution
    ResolutionPreset("Print 8x10 (5:4)", Decimal("2400"), Decimal("1920")), # Example Resolution

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