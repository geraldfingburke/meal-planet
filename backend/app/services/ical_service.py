from datetime import date
from io import BytesIO

from icalendar import Calendar, Event

from app.models.meal_plan import MealPlan


def generate_ical(meal_plans: list[MealPlan], start: date, end: date) -> bytes:
    """Generate an .ics file from meal plan entries."""
    cal = Calendar()
    cal.add("prodid", "-//Meal Planet//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "Meal Planet")

    for plan in meal_plans:
        event = Event()
        meal_label = plan.meal_type.capitalize() if plan.meal_type else "Meal"
        event.add("summary", f"{meal_label}: {plan.recipe.title}")
        event.add("dtstart", plan.planned_date)
        event.add("dtend", plan.planned_date)

        if plan.recipe.source_url:
            event.add("url", plan.recipe.source_url)

        description = f"Recipe: {plan.recipe.title}"
        if plan.recipe.instructions:
            description += f"\n\n{plan.recipe.instructions[:500]}"
        event.add("description", description)

        event.add("uid", f"{plan.id}@mealplanet")
        cal.add_component(event)

    return cal.to_ical()
