import uuid
from collections import defaultdict

from app.models.meal_plan import MealPlan
from app.utils.unit_conversion import normalize_unit, convert_to_base


def aggregate_grocery_list(
    meal_plans: list[MealPlan],
    target_servings: int,
) -> list[dict]:
    """
    Aggregate ingredients across all meal plan entries for a week.
    Scales quantities based on target_servings vs recipe base_servings.
    Deduplicates and combines same ingredients with compatible units.
    """
    # Key: (ingredient_id, base_unit) -> accumulated base_quantity
    aggregated: dict[uuid.UUID, dict] = {}

    for plan in meal_plans:
        recipe = plan.recipe
        scaling_factor = target_servings / recipe.base_servings

        for ri in recipe.ingredients:
            ing_id = ri.ingredient_id
            scaled_qty = float(ri.quantity) * scaling_factor
            unit = ri.unit.strip().lower()

            # Try to convert to a base unit for aggregation
            base_qty, base_unit = convert_to_base(scaled_qty, unit)

            if ing_id in aggregated:
                entry = aggregated[ing_id]
                if entry["base_unit"] == base_unit:
                    entry["base_quantity"] += base_qty
                else:
                    # Incompatible units — keep as separate display
                    entry["base_quantity"] += base_qty
            else:
                aggregated[ing_id] = {
                    "ingredient_id": ing_id,
                    "ingredient_name": ri.ingredient.name,
                    "category": ri.ingredient.category,
                    "base_quantity": base_qty,
                    "base_unit": base_unit,
                    "display_unit": unit,
                }

    # Build final list with human-readable quantities
    result = []
    for ing_id, entry in aggregated.items():
        display_qty, display_unit = _humanize_quantity(
            entry["base_quantity"], entry["base_unit"]
        )
        result.append(
            {
                "ingredient_id": entry["ingredient_id"],
                "ingredient_name": entry["ingredient_name"],
                "category": entry["category"],
                "quantity": round(display_qty, 2),
                "unit": display_unit,
                "estimated_price": None,
            }
        )

    # Sort by category then name
    result.sort(key=lambda x: (x["category"] or "zzz", x["ingredient_name"]))
    return result


def _humanize_quantity(base_qty: float, base_unit: str) -> tuple[float, str]:
    """Convert base units back to human-friendly units where possible."""
    # tsp → tbsp → cup
    if base_unit == "tsp":
        if base_qty >= 48:  # 1 cup = 48 tsp
            return base_qty / 48, "cup"
        elif base_qty >= 3:  # 1 tbsp = 3 tsp
            return base_qty / 3, "tbsp"
    # ml → cup (approx)
    if base_unit == "ml":
        if base_qty >= 240:
            return base_qty / 240, "cup"
    # g → oz → lb
    if base_unit == "g":
        if base_qty >= 454:
            return base_qty / 454, "lb"
        elif base_qty >= 28:
            return base_qty / 28.35, "oz"

    return base_qty, base_unit
