"use client";

import { useEffect, useState } from "react";
import { api, type MealPlanEntry, type Recipe } from "@/lib/api";
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
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [defaultServings, setDefaultServings] = useState(4);

  // Add meal dialog state
  const [addingFor, setAddingFor] = useState<{
    date: string;
    mealType: string;
  } | null>(null);
  const [recipeSearch, setRecipeSearch] = useState("");

  // Fill week dialog
  const [showFillWeek, setShowFillWeek] = useState(false);
  const [fillMealTypes, setFillMealTypes] = useState<string[]>([
    "breakfast",
    "lunch",
    "dinner",
  ]);
  const [filling, setFilling] = useState(false);

  // Editing servings
  const [editingServings, setEditingServings] = useState<string | null>(null);
  const [servingsInput, setServingsInput] = useState("");

  const loadWeek = async () => {
    setLoading(true);
    try {
      const ws = formatDate(weekStart);
      const [planData, recipeData] = await Promise.all([
        api.getMealPlan(ws),
        api.listRecipes(),
      ]);
      setPlans(planData);
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

  const addMeal = async (recipeId: string) => {
    if (!addingFor) return;
    await api.createMealPlan({
      recipe_id: recipeId,
      planned_date: addingFor.date,
      meal_type: addingFor.mealType,
      servings: defaultServings,
    });
    setAddingFor(null);
    setRecipeSearch("");
    await loadWeek();
  };

  const removeMeal = async (planId: string) => {
    await api.deleteMealPlan(planId);
    await loadWeek();
  };

  const updateServings = async (planId: string) => {
    const val = parseInt(servingsInput);
    if (!val || val < 1) return;
    await api.updateMealPlan(planId, { servings: val });
    setEditingServings(null);
    setServingsInput("");
    await loadWeek();
  };

  const handleFillWeek = async () => {
    if (fillMealTypes.length === 0) return;
    setFilling(true);
    try {
      await api.fillWeek({
        week_start: formatDate(weekStart),
        meal_types: fillMealTypes,
        default_servings: defaultServings,
      });
      setShowFillWeek(false);
      await loadWeek();
    } catch (e) {
      console.error("Fill week failed:", e);
    } finally {
      setFilling(false);
    }
  };

  const toggleFillMealType = (mt: string) => {
    setFillMealTypes((prev) =>
      prev.includes(mt) ? prev.filter((t) => t !== mt) : [...prev, mt],
    );
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

      {/* Controls */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Default Servings:</label>
          <Input
            type="number"
            min={1}
            max={20}
            value={defaultServings}
            onChange={(e) => setDefaultServings(parseInt(e.target.value) || 4)}
            className="w-20"
          />
        </div>
        <Button onClick={() => setShowFillWeek(true)}>Fill Week</Button>
        <Button variant="outline" size="sm" onClick={exportCalendar}>
          Export .ics
        </Button>
      </div>

      {/* Calendar Grid */}
      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : (
        <div className="grid grid-cols-7 gap-3">
          {days.map((day) => {
            const dateStr = formatDate(day);
            const isToday = dateStr === formatDate(new Date());
            return (
              <div
                key={dateStr}
                className={`rounded-lg border p-3 min-h-[280px] ${
                  isToday ? "border-primary bg-primary/5" : ""
                }`}
              >
                <div className="text-center mb-3">
                  <div className="text-sm font-medium text-muted-foreground">
                    {getDayName(day)}
                  </div>
                  <div className="text-base font-bold">{getMonthDay(day)}</div>
                </div>

                {MEAL_TYPES.map((mealType) => {
                  const meals = getMealsForSlot(dateStr, mealType);
                  return (
                    <div key={mealType} className="mb-3">
                      <div className="text-xs font-semibold uppercase text-muted-foreground tracking-wider mb-1">
                        {mealType}
                      </div>
                      {meals.map((meal) => (
                        <div
                          key={meal.id}
                          className="text-sm bg-primary/10 rounded-md px-2 py-1.5 mt-1 group"
                        >
                          <div className="flex items-center justify-between">
                            <span className="truncate font-medium">
                              {meal.recipe_title}
                            </span>
                            <button
                              onClick={() => removeMeal(meal.id)}
                              className="text-destructive opacity-0 group-hover:opacity-100 ml-1 text-xs"
                            >
                              ✕
                            </button>
                          </div>
                          <div className="flex items-center gap-1 mt-0.5">
                            {editingServings === meal.id ? (
                              <form
                                onSubmit={(e) => {
                                  e.preventDefault();
                                  updateServings(meal.id);
                                }}
                                className="flex items-center gap-1"
                              >
                                <input
                                  type="number"
                                  min={1}
                                  value={servingsInput}
                                  onChange={(e) =>
                                    setServingsInput(e.target.value)
                                  }
                                  className="w-12 text-xs bg-background border rounded px-1 py-0.5"
                                  autoFocus
                                  onBlur={() => setEditingServings(null)}
                                />
                              </form>
                            ) : (
                              <button
                                onClick={() => {
                                  setEditingServings(meal.id);
                                  setServingsInput(String(meal.servings));
                                }}
                                className="text-xs text-muted-foreground hover:text-primary cursor-pointer"
                              >
                                {meal.servings} servings
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                      <button
                        onClick={() =>
                          setAddingFor({ date: dateStr, mealType })
                        }
                        className="text-xs text-muted-foreground hover:text-primary mt-1"
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
                    <span>{recipe.title}</span>
                    {recipe.category !== "any" && (
                      <span className="ml-2 text-xs text-muted-foreground capitalize">
                        ({recipe.category})
                      </span>
                    )}
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

      {/* Fill Week Dialog */}
      {showFillWeek && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-96">
            <CardHeader>
              <CardTitle className="text-base">Fill Week</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Automatically fill empty meal slots with category-matched
                recipes.
              </p>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Meal types to fill:
                </label>
                {MEAL_TYPES.map((mt) => (
                  <label
                    key={mt}
                    className="flex items-center gap-2 text-sm capitalize"
                  >
                    <input
                      type="checkbox"
                      checked={fillMealTypes.includes(mt)}
                      onChange={() => toggleFillMealType(mt)}
                      className="h-4 w-4 rounded border-input"
                    />
                    {mt}
                  </label>
                ))}
              </div>
              <div>
                <label className="text-sm font-medium">
                  Servings per meal:
                </label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={defaultServings}
                  onChange={(e) =>
                    setDefaultServings(parseInt(e.target.value) || 4)
                  }
                  className="mt-1"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleFillWeek}
                  disabled={filling || fillMealTypes.length === 0}
                  className="flex-1"
                >
                  {filling ? "Filling..." : "Fill Week"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowFillWeek(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
