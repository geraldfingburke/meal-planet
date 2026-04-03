"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type MealPlanEntry, type Recipe } from "@/lib/api";
import { formatDate, getWeekStart } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Dashboard() {
  const [todayMeals, setTodayMeals] = useState<MealPlanEntry[]>([]);
  const [recipeCount, setRecipeCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const weekStart = formatDate(getWeekStart(new Date()));
        const [plans, recipes] = await Promise.all([
          api.getMealPlan(weekStart),
          api.listRecipes(),
        ]);
        const today = formatDate(new Date());
        setTodayMeals(plans.filter((p) => p.planned_date === today));
        setRecipeCount(recipes.length);
      } catch (e) {
        console.error("Failed to load dashboard:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to Meal Planet. Here&apos;s your day at a glance.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Today&apos;s Meals</CardTitle>
          </CardHeader>
          <CardContent>
            {todayMeals.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Nothing planned yet
              </p>
            ) : (
              <ul className="space-y-2">
                {todayMeals.map((m) => (
                  <li key={m.id} className="text-sm">
                    <span className="font-medium capitalize">
                      {m.meal_type || "Meal"}:
                    </span>{" "}
                    {m.recipe_title}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recipe Library</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{recipeCount}</p>
            <p className="text-sm text-muted-foreground">recipes saved</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button asChild className="w-full" size="sm">
              <Link href="/planner">Open Planner</Link>
            </Button>
            <Button asChild variant="outline" className="w-full" size="sm">
              <Link href="/spinner">Spin for Dinner</Link>
            </Button>
            <Button asChild variant="outline" className="w-full" size="sm">
              <Link href="/grocery-list">View Grocery List</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
