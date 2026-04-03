"""
Unit conversion utilities for ingredient aggregation.
Converts various units to a base unit for aggregation, then back to
human-readable units for display.
"""

# Base unit mappings: convert everything to a canonical unit for aggregation
# Volume: everything → tsp
# Weight: everything → g
# Count: stays as-is

_VOLUME_TO_TSP = {
    "tsp": 1,
    "teaspoon": 1,
    "teaspoons": 1,
    "tbsp": 3,
    "tablespoon": 3,
    "tablespoons": 3,
    "cup": 48,
    "cups": 48,
    "fl oz": 6,
    "pint": 96,
    "pints": 96,
    "quart": 192,
    "quarts": 192,
    "gallon": 768,
    "gallons": 768,
    "ml": 0.2029,  # 1 ml ≈ 0.2029 tsp
    "milliliter": 0.2029,
    "milliliters": 0.2029,
    "l": 202.9,
    "liter": 202.9,
    "liters": 202.9,
}

_WEIGHT_TO_G = {
    "g": 1,
    "gram": 1,
    "grams": 1,
    "kg": 1000,
    "kilogram": 1000,
    "kilograms": 1000,
    "oz": 28.35,
    "ounce": 28.35,
    "ounces": 28.35,
    "lb": 453.6,
    "lbs": 453.6,
    "pound": 453.6,
    "pounds": 453.6,
}


def normalize_unit(unit: str) -> str:
    """Normalize unit aliases to a canonical form."""
    unit = unit.strip().lower()

    # Volume aliases
    if unit in ("tsp", "teaspoon", "teaspoons"):
        return "tsp"
    if unit in ("tbsp", "tablespoon", "tablespoons"):
        return "tbsp"
    if unit in ("cup", "cups"):
        return "cup"
    if unit in ("ml", "milliliter", "milliliters"):
        return "ml"
    if unit in ("l", "liter", "liters"):
        return "l"

    # Weight aliases
    if unit in ("g", "gram", "grams"):
        return "g"
    if unit in ("kg", "kilogram", "kilograms"):
        return "kg"
    if unit in ("oz", "ounce", "ounces"):
        return "oz"
    if unit in ("lb", "lbs", "pound", "pounds"):
        return "lb"

    return unit


def convert_to_base(quantity: float, unit: str) -> tuple[float, str]:
    """
    Convert a quantity + unit to a base unit for aggregation.
    Returns (base_quantity, base_unit).
    Volume → tsp, Weight → g, everything else stays as-is.
    """
    unit_lower = unit.strip().lower()

    if unit_lower in _VOLUME_TO_TSP:
        return quantity * _VOLUME_TO_TSP[unit_lower], "tsp"

    if unit_lower in _WEIGHT_TO_G:
        return quantity * _WEIGHT_TO_G[unit_lower], "g"

    # Non-convertible units (clove, can, bunch, etc.) — pass through
    return quantity, normalize_unit(unit_lower)
