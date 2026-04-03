import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe, RecipeIngredient
from app.models.week_config import WeekConfig

router = APIRouter()

DEFAULT_SERVING_OVERRIDE = 4  # Boy Week default


def _get_week_start(d: date) -> date:
    """Return Monday of the week containing the given date."""
    return d - timedelta(days=d.weekday())


# -- Pydantic schemas for Gemini grocery output --------------------

class SmartGroceryItem(BaseModel):
    name: str
    quantity: str
    category: str
    estimated_price: float


class SmartGroceryOutput(BaseModel):
    items: list[SmartGroceryItem]


_GROCERY_SYSTEM_INSTRUCTION = """\
You are an expert grocery list generator for a family that shops at Walmart (US).

You will be given a JSON list of recipes. Each recipe includes:
- A title
- Total servings needed (already scaled)
- A complete list of ingredients with pre-scaled quantities and units

## CRITICAL RULES — READ CAREFULLY

1. **EVERY ingredient from EVERY recipe MUST appear in your output.** Do NOT skip,
   drop, or forget any ingredient. After generating your list, mentally walk through
   each recipe and verify its ingredients are covered.

2. **COMBINE duplicates intelligently.** If the same ingredient appears in multiple
   recipes (e.g. butter in recipe A and recipe B), add the quantities together and
   list it ONCE with the combined total.

3. **Round UP to practical Walmart purchase sizes.** You cannot buy 0.33 cups of
   flour — round to the nearest real package ("1 bag (5 lb)"). Always round UP,
   never down.

4. **Group by store aisle.** Use these categories: Produce, Dairy, Meat & Seafood,
   Pantry, Frozen, Bakery, Condiments & Sauces, Spices & Seasonings, Canned Goods,
   Beverages, Other.

5. **Estimate realistic Walmart prices** (2025-2026 US pricing). Prefer Great Value
   / store brand when the item is a commodity. Use name-brand pricing for specialty
   items.

6. **Only omit true staples** that nearly every kitchen has: table salt, black pepper,
   water, cooking spray, ice. If a recipe calls for a meaningful quantity of any other
   ingredient (even oil, butter, sugar, flour), INCLUDE it.

## OUTPUT FORMAT

Return ONLY valid JSON matching this schema — no markdown fences, no commentary:

{
  "items": [
    {
      "name": "item name as you'd write on a shopping list",
      "quantity": "practical purchase quantity, e.g. '2 lbs', '1 bunch', '1 can (15 oz)'",
      "category": "store aisle category from the list above",
      "estimated_price": 3.47
    }
  ]
}
"""


class GroceryGenerateRequest(BaseModel):
    start_date: date
    end_date: date


@router.post("/generate")
async def generate_grocery_list(
    data: GroceryGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Load week configs for every week in the range
    all_week_starts: set[date] = set()
    d = data.start_date
    while d <= data.end_date:
        all_week_starts.add(_get_week_start(d))
        d += timedelta(days=7)
    # Also catch the last partial week
    all_week_starts.add(_get_week_start(data.end_date))

    wc_stmt = select(WeekConfig).where(
        WeekConfig.week_start_date.in_(list(all_week_starts))
    )
    wc_result = await db.execute(wc_stmt)
    week_configs = {wc.week_start_date: wc for wc in wc_result.scalars().all()}

    # Build a lookup: date -> serving_override
    def servings_for_date(d: date) -> tuple[int, str]:
        ws = _get_week_start(d)
        wc = week_configs.get(ws)
        if wc:
            return wc.serving_override, wc.week_type
        return DEFAULT_SERVING_OVERRIDE, "Boy Week"

    # Build week summary for response
    weeks_summary = []
    for ws in sorted(all_week_starts):
        wc = week_configs.get(ws)
        weeks_summary.append({
            "week_start": ws.isoformat(),
            "week_type": wc.week_type if wc else "Boy Week",
            "servings": wc.serving_override if wc else DEFAULT_SERVING_OVERRIDE,
        })

    # 2. Get all meal plan entries in the date range with full recipe data
    stmt = (
        select(MealPlan)
        .options(
            selectinload(MealPlan.recipe)
            .selectinload(Recipe.ingredients)
            .joinedload(RecipeIngredient.ingredient)
        )
        .where(MealPlan.planned_date.between(data.start_date, data.end_date))
    )
    result = await db.execute(stmt)
    meal_plans = result.scalars().unique().all()

    if not meal_plans:
        return {
            "start_date": data.start_date.isoformat(),
            "end_date": data.end_date.isoformat(),
            "weeks": weeks_summary,
            "recipes_included": [],
            "items": [],
            "estimated_total": 0.0,
            "recipe_cost_total": 0.0,
        }

    # 3. Build recipe ingredient data for Gemini, scaled per meal plan entry's week
    #    A recipe can appear multiple times (different days, different weeks, different servings)
    recipes_data = []  # one entry per unique (recipe_id, servings) combo
    recipe_cost_total = 0.0
    recipes_included = []
    seen_recipe_ids = set()

    # Track per-recipe accumulated servings keyed by recipe_id
    recipe_servings_map: dict[str, dict] = {}

    for plan in meal_plans:
        recipe = plan.recipe
        plan_servings, _ = servings_for_date(plan.planned_date)
        rid = str(recipe.id)

        if rid in recipe_servings_map:
            recipe_servings_map[rid]["total_servings"] += plan_servings
        else:
            recipe_servings_map[rid] = {
                "recipe": recipe,
                "total_servings": plan_servings,
            }

        if recipe.id not in seen_recipe_ids:
            seen_recipe_ids.add(recipe.id)
            recipes_included.append({
                "id": rid,
                "title": recipe.title,
                "cost_per_serving": float(recipe.cost_per_serving) if recipe.cost_per_serving else None,
            })

    for rid, info in recipe_servings_map.items():
        recipe = info["recipe"]
        total_servings = info["total_servings"]
        scaling_factor = total_servings / recipe.base_servings

        ingredients = []
        for ri in recipe.ingredients:
            ingredients.append({
                "name": ri.ingredient.name,
                "quantity": round(float(ri.quantity) * scaling_factor, 2),
                "unit": ri.unit,
            })

        recipes_data.append({
            "recipe_id": rid,
            "title": recipe.title,
            "total_servings": total_servings,
            "ingredients": ingredients,
        })

        if recipe.cost_per_serving:
            recipe_cost_total += float(recipe.cost_per_serving) * total_servings

    # 4. Send to Gemini for smart consolidation
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    # Count total unique ingredients across all recipes for the prompt
    all_ingredient_names = set()
    for rd in recipes_data:
        for ing in rd["ingredients"]:
            all_ingredient_names.add(ing["name"].lower())

    prompt = (
        f"Create a consolidated grocery shopping list for these {len(recipes_data)} recipes "
        f"({len(all_ingredient_names)} unique ingredients total).\n\n"
        f"IMPORTANT: Every recipe's ingredients are pre-scaled to the correct servings. "
        f"Do NOT re-scale — just combine across recipes and round to store quantities.\n\n"
        f"Recipes and their ingredients:\n\n{json.dumps(recipes_data, indent=2)}\n\n"
        f"Remember: your output must cover ALL {len(all_ingredient_names)} unique ingredients. "
        f"Do not skip any."
    )

    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_GROCERY_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=SmartGroceryOutput,
            temperature=0.2,
        ),
    )

    grocery = SmartGroceryOutput.model_validate_json(gemini_response.text)

    estimated_total = round(sum(item.estimated_price for item in grocery.items), 2)

    return {
        "start_date": data.start_date.isoformat(),
        "end_date": data.end_date.isoformat(),
        "weeks": weeks_summary,
        "recipes_included": recipes_included,
        "items": [item.model_dump() for item in grocery.items],
        "estimated_total": estimated_total,
        "recipe_cost_total": round(recipe_cost_total, 2),
    }
