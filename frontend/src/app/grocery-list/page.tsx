"use client";

import { useState } from "react";
import { api, type GroceryItem, type GroceryList } from "@/lib/api";
import { formatDate, getWeekStart, addDays } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function GroceryListPage() {
  const today = new Date();
  const mondayThisWeek = getWeekStart(today);

  const [startDate, setStartDate] = useState(() => formatDate(mondayThisWeek));
  const [endDate, setEndDate] = useState(() =>
    formatDate(addDays(mondayThisWeek, 13)),
  );
  const [groceryList, setGroceryList] = useState<GroceryList | null>(null);
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setChecked(new Set());
    try {
      const data = await api.generateGroceryList(startDate, endDate);
      setGroceryList(data);
    } catch (e) {
      setError(
        "Failed to generate grocery list. Make sure you have meals planned in this range.",
      );
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleCheck = (idx: number) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const handlePrint = () => window.print();

  const handleSaveAsText = () => {
    if (!groceryList) return;
    const groups = groupByCategory(groceryList.items);
    let text = `Grocery List -- ${groceryList.start_date} to ${groceryList.end_date}\n`;
    for (const w of groceryList.weeks) {
      text += `  ${w.week_start}: ${w.week_type} (${w.servings} servings)\n`;
    }
    text += "\n";

    for (const [category, items] of Object.entries(groups)) {
      text += `=== ${category} ===\n`;
      for (const item of items) {
        text += `  [ ] ${item.quantity} ${item.name} ($${item.estimated_price.toFixed(2)})\n`;
      }
      text += "\n";
    }

    text += `\nEstimated Total: $${groceryList.estimated_total.toFixed(2)}\n`;

    if (groceryList.recipe_cost_total > 0) {
      text += `Recipe Cost Total (from per-serving): $${groceryList.recipe_cost_total.toFixed(2)}\n`;
    }

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `grocery-list-${startDate}-to-${endDate}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const groupByCategory = (items: GroceryItem[]) => {
    const groups: Record<string, GroceryItem[]> = {};
    for (const item of items) {
      const cat = item.category || "Other";
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(item);
    }
    return groups;
  };

  const setTwoWeeks = () => {
    const monday = getWeekStart(new Date());
    setStartDate(formatDate(monday));
    setEndDate(formatDate(addDays(monday, 13)));
  };

  const setOneWeek = () => {
    const monday = getWeekStart(new Date());
    setStartDate(formatDate(monday));
    setEndDate(formatDate(addDays(monday, 6)));
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Grocery List</h2>
        <p className="text-muted-foreground">
          Generate a smart shopping list from your meal plan
        </p>
      </div>

      {/* Date Range + Generate */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Shopping Range</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={setOneWeek}>
              1 Week
            </Button>
            <Button variant="outline" size="sm" onClick={setTwoWeeks}>
              2 Weeks
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium">Start</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">End</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Servings are set per week via the Boy Week / Girls Week toggle on
            the Planner page.
          </p>
          <Button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full"
          >
            {loading ? "Generating with AI..." : "Generate Shopping List"}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-destructive text-sm">{error}</p>}

      {/* Results */}
      {groceryList && (
        <>
          {/* Week breakdown */}
          {groceryList.weeks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Weeks ({groceryList.weeks.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {groceryList.weeks.map((w) => (
                    <div
                      key={w.week_start}
                      className="flex justify-between text-sm"
                    >
                      <span>Week of {w.week_start}</span>
                      <span className="text-muted-foreground">
                        {w.week_type} &middot; {w.servings} servings
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recipes included */}
          {groceryList.recipes_included.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Recipes ({groceryList.recipes_included.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {groceryList.recipes_included.map((r) => (
                    <li key={r.id} className="text-sm flex justify-between">
                      <span>{r.title}</span>
                      {r.cost_per_serving != null && (
                        <span className="text-muted-foreground">
                          ${r.cost_per_serving.toFixed(2)}/serving
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-2 no-print">
            <Button variant="outline" size="sm" onClick={handlePrint}>
              Print
            </Button>
            <Button variant="outline" size="sm" onClick={handleSaveAsText}>
              Save as Text
            </Button>
          </div>

          {/* Grocery Items */}
          {groceryList.items.length === 0 ? (
            <p className="text-muted-foreground">
              No meals planned in this range. Add recipes to your meal plan
              first!
            </p>
          ) : (
            <>
              {Object.entries(groupByCategory(groceryList.items)).map(
                ([category, items]) => (
                  <Card key={category}>
                    <CardHeader>
                      <CardTitle className="text-base">{category}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {items.map((item) => {
                          const globalIdx = groceryList.items.indexOf(item);
                          return (
                            <li
                              key={globalIdx}
                              className="flex items-center gap-3"
                            >
                              <input
                                type="checkbox"
                                checked={checked.has(globalIdx)}
                                onChange={() => toggleCheck(globalIdx)}
                                className="h-4 w-4 rounded border-input no-print"
                              />
                              <span
                                className={
                                  checked.has(globalIdx)
                                    ? "line-through text-muted-foreground"
                                    : ""
                                }
                              >
                                <span className="font-medium">
                                  {item.quantity}
                                </span>{" "}
                                {item.name}
                              </span>
                              <span className="ml-auto text-sm text-muted-foreground">
                                ${item.estimated_price.toFixed(2)}
                              </span>
                            </li>
                          );
                        })}
                      </ul>
                    </CardContent>
                  </Card>
                ),
              )}

              {/* Totals */}
              <Card>
                <CardContent className="pt-6 space-y-2">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Estimated Shopping Total</span>
                    <span>${groceryList.estimated_total.toFixed(2)}</span>
                  </div>
                  {groceryList.recipe_cost_total > 0 && (
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>Based on recipe cost/serving</span>
                      <span>${groceryList.recipe_cost_total.toFixed(2)}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}
