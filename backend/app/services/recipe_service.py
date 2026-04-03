import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient
from app.schemas.recipe import RecipeIngredientCreate, RecipeIngredientResponse, RecipeResponse


def build_recipe_response(recipe: Recipe) -> RecipeResponse:
    ingredients = []
    for ri in recipe.ingredients:
        ingredients.append(
            RecipeIngredientResponse(
                ingredient_id=ri.ingredient_id,
                ingredient_name=ri.ingredient.name,
                ingredient_category=ri.ingredient.category,
                quantity=float(ri.quantity),
                unit=ri.unit,
                walmart_search_term=ri.walmart_search_term,
            )
        )

    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        instructions=recipe.instructions,
        source_url=recipe.source_url,
        image_url=recipe.image_url,
        base_servings=recipe.base_servings,
        cost_per_serving=float(recipe.cost_per_serving) if recipe.cost_per_serving else None,
        last_cooked_at=recipe.last_cooked_at,
        created_at=recipe.created_at,
        ingredients=ingredients,
        tags=[tag.name for tag in recipe.tags],
    )


async def upsert_recipe_ingredients(
    db: AsyncSession,
    recipe_id: uuid.UUID,
    items: list[RecipeIngredientCreate],
):
    # Remove existing ingredients
    await db.execute(
        delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
    )

    for item in items:
        # Resolve ingredient by ID or name
        if item.ingredient_id:
            ingredient_id = item.ingredient_id
        elif item.ingredient_name:
            result = await db.execute(
                select(Ingredient).where(
                    Ingredient.name.ilike(item.ingredient_name.strip())
                )
            )
            ingredient = result.scalar_one_or_none()
            if not ingredient:
                ingredient = Ingredient(name=item.ingredient_name.strip())
                db.add(ingredient)
                await db.flush()
            ingredient_id = ingredient.id
        else:
            continue

        ri = RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=item.quantity,
            unit=item.unit,
            walmart_search_term=item.walmart_search_term,
        )
        db.add(ri)
