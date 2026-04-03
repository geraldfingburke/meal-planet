"""
Gemini-powered recipe parser.

Fetches raw HTML from a recipe URL, sends it to Gemini 2.5 Flash
with a system instruction to extract structured recipe data, and
validates the output with Pydantic.
"""

from dataclasses import dataclass

import httpx
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings


# -- Pydantic schema for Gemini output validation ------------------

class GeminiIngredient(BaseModel):
    name: str
    quantity: float
    unit: str
    walmart_search_term: str


class GeminiRecipeOutput(BaseModel):
    title: str
    instructions: str
    base_servings: int
    image_url: str | None = None
    category: str = "any"
    tags: list[str] = []
    ingredients: list[GeminiIngredient]


# -- Public dataclasses (consumed by the task) ---------------------

@dataclass
class ParsedIngredient:
    name: str
    quantity: float
    unit: str
    walmart_search_term: str


@dataclass
class ParsedRecipe:
    title: str
    instructions: str
    source_url: str
    base_servings: int
    image_url: str | None
    category: str
    tags: list[str]
    ingredients: list[ParsedIngredient]


# -- System instruction for Gemini ---------------------------------

_SYSTEM_INSTRUCTION = """\
You are a recipe-extraction engine. You will be given the raw HTML of a recipe web page.

Return ONLY a JSON object that matches this exact schema (no markdown, no commentary):

{
  "title": "string",
  "instructions": "string - numbered steps, one per line",
  "base_servings": integer,
  "image_url": "string or null - the main recipe/hero image URL from og:image meta tag, or the largest recipe photo src. Must be an absolute URL.",
  "category": "string - one of: breakfast, lunch, dinner, dessert, any",
  "tags": ["string - at least 3 descriptive tags for this recipe, e.g. 'quick', 'chicken', 'healthy', 'comfort food', 'vegetarian', 'spicy'"],
  "ingredients": [
    {
      "name": "string - the ingredient name, lowercase, singular where sensible",
      "quantity": number,
      "unit": "string - standard abbreviation (cup, tbsp, tsp, oz, lb, g, ml, clove, can, unit)",
      "walmart_search_term": "string - a Walmart-optimized search query for this item, e.g. 'Great Value All Purpose Flour 5lb'"
    }
  ]
}

Rules:
- Normalize written fractions to decimals: "half a cup" -> 0.5, "1/3 cup" -> 0.333
- If no serving count is found, default to 4.
- Keep ingredient names clean (no quantities or units in the name).
- walmart_search_term should prefer 'Great Value' brand when a store-brand equivalent exists.
- category: Determine the most appropriate meal category. Use "breakfast" for morning meals, "lunch" for midday, "dinner" for evening/main courses, "dessert" for sweets, "any" if it could fit multiple categories.
- tags: Provide at least 3 tags. Include cuisine type, protein, cooking method, dietary info, or other descriptors.
"""


async def parse_recipe_from_url(url: str) -> ParsedRecipe:
    """Fetch a URL, send its HTML to Gemini, and return structured recipe data."""

    # 1. Fetch raw HTML
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": "MealPlanet/1.0 RecipeParser"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    html_body = response.text

    # 2. Call Gemini
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract the recipe from this HTML:\n\n{html_body[:60000]}",
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiRecipeOutput,
            temperature=0.1,
        ),
    )

    # 3. Validate with Pydantic
    parsed = GeminiRecipeOutput.model_validate_json(gemini_response.text)

    return ParsedRecipe(
        title=parsed.title,
        instructions=parsed.instructions,
        source_url=url,
        base_servings=parsed.base_servings,
        image_url=parsed.image_url,
        category=parsed.category if parsed.category in ("breakfast", "lunch", "dinner", "dessert", "any") else "any",
        tags=parsed.tags if len(parsed.tags) >= 3 else parsed.tags + ["homemade", "recipe", "meal"][:3 - len(parsed.tags)],
        ingredients=[
            ParsedIngredient(
                name=ing.name,
                quantity=ing.quantity,
                unit=ing.unit,
                walmart_search_term=ing.walmart_search_term,
            )
            for ing in parsed.ingredients
        ],
    )
