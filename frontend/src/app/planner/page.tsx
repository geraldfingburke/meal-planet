"use client";

import { useEffect, useState } from "react";
import {
  api,
  type MealPlanEntry,
  type Recipe,
  type WeekConfig,
} from "@/lib/api";
import {
  formatDate,
  getWeekStart,
  addDays,
  getDayName,
  getMonthDay,
} from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const MEAL_TYPES = ["breakfast", "lunch", "dinner"];

export default function PlannerPage() {
  const [weekStart, setWeekStart] = useState(() => getWeekStart(new Date()));
  const [plans, setPlans] = useState<MealPlanEntry[]>([]);
  const [weekConfig, setWeekConfig] = useState<WeekConfig | null>(null);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);

  // Add meal dialog state
  const [addingFor, setAddingFor] = useState<{
    date: string;
    mealType: string;
  } | null>(null);
  const [recipeSearch, setRecipeSearch] = useState("");

  const loadWeek = async () => {
    setLoading(true);
    try {
      const ws = formatDate(weekStart);
      const [planData, configData, recipeData] = await Promise.all([
        api.getMealPlan(ws),
        api.getWeekConfig(ws),
        api.listRecipes(),
      ]);
      setPlans(planData);
      setWeekConfig(configData);
      setRecipes(recipeData);
    } catch (e) {
      console.error("Failed to load planner:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWeek();
  }, [weekStart]);

  const navigateWeek = (delta: number) => {
    setWeekStart((prev) => addDays(prev, delta * 7));
  };

  const toggleWeekType = async () => {
    const ws = formatDate(weekStart);
    const newType =
      weekConfig?.week_type === "Girls Week" ? "Boy Week" : "Girls Week";
    const updated = await api.setWeekConfig({
      week_start_date: ws,
      week_type: newType,
    });
    setWeekConfig(updated);
  };

  const addMeal = async (recipeId: string) => {
    if (!addingFor) return;
    await api.createMealPlan({
      recipe_id: recipeId,
      planned_date: addingFor.date,
      meal_type: addingFor.mealType,
    });
    setAddingFor(null);
    setRecipeSearch("");
    await loadWeek();
  };

  const removeMeal = async (planId: string) => {
    await api.deleteMealPlan(planId);
    await loadWeek();
  };

  const exportCalendar = () => {
    const start = formatDate(weekStart);
    const end = formatDate(addDays(weekStart, 6));
    window.open(`/api/calendar/export.ics?start=${start}&end=${end}`, "_blank");
  };

  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const getMealsForSlot = (date: string, mealType: string) =>
    plans.filter((p) => p.planned_date === date && p.meal_type === mealType);

  const filteredRecipes = recipes.filter((r) =>
    r.title.toLowerCase().includes(recipeSearch.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Meal Planner</h2>
          <p className="text-muted-foreground">
            Week of {getMonthDay(weekStart)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => navigateWeek(-1)}>
            ← Prev
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setWeekStart(getWeekStart(new Date()))}
          >
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigateWeek(1)}>
            Next →
          </Button>
        </div>
      </div>

      {/* Week Type Toggle + Export */}
      <div className="flex items-center gap-4">
        <Button
          variant={
            weekConfig?.week_type === "Girls Week" ? "default" : "outline"
          }
          onClick={toggleWeekType}
        >
          {weekConfig?.week_type || "Boy Week"} (
          {weekConfig?.serving_override || 4} servings)
        </Button>
        <Button variant="outline" size="sm" onClick={exportCalendar}>
          Export .ics
        </Button>
      </div>

      {/* Calendar Grid */}
      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : (
        <div className="grid grid-cols-7 gap-2">
          {days.map((day) => {
            const dateStr = formatDate(day);
            const isToday = dateStr === formatDate(new Date());
            return (
              <div
                key={dateStr}
                className={`rounded-lg border p-2 min-h-[200px] ${
                  isToday ? "border-primary bg-primary/5" : ""
                }`}
              >
                <div className="text-center mb-2">
                  <div className="text-xs font-medium text-muted-foreground">
                    {getDayName(day)}
                  </div>
                  <div className="text-sm font-bold">{getMonthDay(day)}</div>
                </div>

                {MEAL_TYPES.map((mealType) => {
                  const meals = getMealsForSlot(dateStr, mealType);
                  return (
                    <div key={mealType} className="mb-2">
                      <div className="text-[10px] font-semibold uppercase text-muted-foreground tracking-wider">
                        {mealType}
                      </div>
                      {meals.map((meal) => (
                        <div
                          key={meal.id}
                          className="text-xs bg-primary/10 rounded px-1 py-0.5 mt-0.5 flex items-center justify-between group"
                        >
                          <span className="truncate">{meal.recipe_title}</span>
                          <button
                            onClick={() => removeMeal(meal.id)}
                            className="text-destructive opacity-0 group-hover:opacity-100 ml-1 text-[10px]"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                      <button
                        onClick={() =>
                          setAddingFor({ date: dateStr, mealType })
                        }
                        className="text-[10px] text-muted-foreground hover:text-primary mt-0.5"
                      >
                        + add
                      </button>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Meal Dialog */}
      {addingFor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-96 max-h-[80vh] overflow-auto">
            <CardHeader>
              <CardTitle className="text-base">
                Add {addingFor.mealType} for {addingFor.date}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                placeholder="Search recipes..."
                value={recipeSearch}
                onChange={(e) => setRecipeSearch(e.target.value)}
                autoFocus
              />
              <div className="space-y-1 max-h-60 overflow-auto">
                {filteredRecipes.map((recipe) => (
                  <button
                    key={recipe.id}
                    onClick={() => addMeal(recipe.id)}
                    className="w-full text-left px-3 py-2 rounded-md hover:bg-accent text-sm transition-colors"
                  >
                    {recipe.title}
                  </button>
                ))}
                {filteredRecipes.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No recipes found
                  </p>
                )}
              </div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setAddingFor(null);
                  setRecipeSearch("");
                }}
              >
                Cancel
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
