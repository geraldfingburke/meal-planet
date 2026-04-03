import random
from datetime import datetime, timedelta, timezone

from app.models.recipe import Recipe


def weighted_random_recipe(recipes: list[Recipe]) -> Recipe:
    """
    Select a weighted random recipe. Recipes not cooked recently get higher weight:
    - >14 days or never cooked: weight 3
    - 7-14 days: weight 2
    - <7 days: weight 1
    """
    now = datetime.now(timezone.utc)
    weights = []

    for recipe in recipes:
        if recipe.last_cooked_at is None:
            weights.append(3)
        else:
            days_since = (now - recipe.last_cooked_at).days
            if days_since > 14:
                weights.append(3)
            elif days_since > 7:
                weights.append(2)
            else:
                weights.append(1)

    return random.choices(recipes, weights=weights, k=1)[0]
