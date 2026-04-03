"use client";

import { useEffect, useState } from "react";
import {
  api,
  type SpendingEntry,
  type TopRecipe,
  type CategorySpending,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ReportsPage() {
  const [spending, setSpending] = useState<SpendingEntry[]>([]);
  const [topRecipes, setTopRecipes] = useState<TopRecipe[]>([]);
  const [expensiveDay, setExpensiveDay] = useState<{
    date: string | null;
    total_cost: number;
  } | null>(null);
  const [categorySpending, setCategorySpending] = useState<CategorySpending[]>(
    [],
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAll() {
      try {
        const [s, t, e, c] = await Promise.all([
          api.getSpendingOverTime(),
          api.getTopRecipes(),
          api.getMostExpensiveDay(),
          api.getAvgSpendingByCategory(),
        ]);
        setSpending(s);
        setTopRecipes(t);
        setExpensiveDay(e);
        setCategorySpending(c);
      } catch (e) {
        console.error("Failed to load reports:", e);
      } finally {
        setLoading(false);
      }
    }
    loadAll();
  }, []);

  if (loading)
    return <p className="text-muted-foreground">Loading reports...</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reports</h2>
        <p className="text-muted-foreground">
          Insights from your meal planning and grocery spending
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Most Expensive Day */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Most Expensive Day</CardTitle>
          </CardHeader>
          <CardContent>
            {expensiveDay?.date ? (
              <div>
                <div className="text-2xl font-bold">
                  ${expensiveDay.total_cost.toFixed(2)}
                </div>
                <p className="text-sm text-muted-foreground">
                  {expensiveDay.date}
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data yet</p>
            )}
          </CardContent>
        </Card>

        {/* Top 5 Recipes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top 5 Recipes</CardTitle>
          </CardHeader>
          <CardContent>
            {topRecipes.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data yet</p>
            ) : (
              <ul className="space-y-2">
                {topRecipes.map((r, i) => (
                  <li
                    key={r.recipe_id}
                    className="flex justify-between text-sm"
                  >
                    <span>
                      {i + 1}. {r.title}
                    </span>
                    <span className="text-muted-foreground">
                      {r.usage_count}x
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Spending Over Time */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Spending Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          {spending.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No grocery lists generated yet. Generate a list to see spending
              data.
            </p>
          ) : (
            <div className="space-y-2">
              {spending.map((entry, i) => {
                const maxSpending = Math.max(
                  ...spending.map((s) => s.estimated_total),
                );
                const pct =
                  maxSpending > 0
                    ? (entry.estimated_total / maxSpending) * 100
                    : 0;
                return (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>
                        {entry.start_date} to {entry.end_date}
                      </span>
                      <span className="font-medium">
                        ${entry.estimated_total.toFixed(2)}
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Average Spending by Category */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Spending by Grocery Category
          </CardTitle>
        </CardHeader>
        <CardContent>
          {categorySpending.length === 0 ? (
            <p className="text-sm text-muted-foreground">No data yet</p>
          ) : (
            <div className="space-y-2">
              {categorySpending.map((cat) => (
                <div
                  key={cat.category}
                  className="flex justify-between text-sm"
                >
                  <span>{cat.category}</span>
                  <span className="text-muted-foreground">
                    avg ${cat.avg_spending.toFixed(2)} · total $
                    {cat.total_spending.toFixed(2)} ({cat.list_count} lists)
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
