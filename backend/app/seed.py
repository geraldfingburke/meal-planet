"""Seed script: creates default family and common ingredient categories."""
import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models.family import Family
from app.models.ingredient import Ingredient


COMMON_INGREDIENTS = {
    "Produce": [
        "Onion", "Garlic", "Tomato", "Potato", "Carrot", "Celery",
        "Bell pepper", "Broccoli", "Spinach", "Lettuce", "Lemon", "Lime",
        "Avocado", "Mushrooms", "Ginger", "Green onion", "Cilantro", "Parsley",
    ],
    "Dairy": [
        "Butter", "Milk", "Heavy cream", "Sour cream", "Cream cheese",
        "Cheddar cheese", "Mozzarella cheese", "Parmesan cheese", "Eggs",
    ],
    "Meat": [
        "Chicken breast", "Chicken thighs", "Ground beef", "Ground turkey",
        "Bacon", "Pork chops", "Sausage", "Steak",
    ],
    "Pantry": [
        "Olive oil", "Vegetable oil", "Salt", "Black pepper", "Sugar",
        "Brown sugar", "All-purpose flour", "Rice", "Pasta", "Bread",
        "Chicken broth", "Beef broth", "Soy sauce", "Vinegar",
        "Tomato sauce", "Tomato paste", "Canned diced tomatoes",
    ],
    "Spices": [
        "Cumin", "Paprika", "Chili powder", "Garlic powder", "Onion powder",
        "Oregano", "Basil", "Thyme", "Cinnamon", "Red pepper flakes",
    ],
    "Frozen": [
        "Frozen corn", "Frozen peas", "Frozen mixed vegetables",
    ],
    "Canned": [
        "Black beans", "Kidney beans", "Chickpeas", "Canned corn",
    ],
}


async def seed():
    async with async_session() as db:
        # Create default family
        result = await db.execute(select(Family).limit(1))
        if not result.scalar_one_or_none():
            db.add(Family(name="My Family"))

        # Create common ingredients
        for category, names in COMMON_INGREDIENTS.items():
            for name in names:
                result = await db.execute(
                    select(Ingredient).where(Ingredient.name == name)
                )
                if not result.scalar_one_or_none():
                    db.add(Ingredient(name=name, category=category))

        await db.commit()
        print("Seed data created successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
