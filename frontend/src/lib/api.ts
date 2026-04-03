const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Recipes ─────────────────────────────────────────────
export interface RecipeIngredient {
  ingredient_id: string;
  ingredient_name: string;
  ingredient_category: string | null;
  quantity: number;
  unit: string;
}

export interface Recipe {
  id: string;
  title: string;
  instructions: string | null;
  source_url: string | null;
  image_url: string | null;
  base_servings: number;
  cost_per_serving: number | null;
  last_cooked_at: string | null;
  created_at: string;
  ingredients: RecipeIngredient[];
  tags: string[];
}

export interface RecipeCreateInput {
  title: string;
  instructions?: string;
  source_url?: string;
  image_url?: string;
  base_servings?: number;
  ingredients?: {
    ingredient_name: string;
    quantity: number;
    unit: string;
  }[];
  tags?: string[];
}

export const api = {
  // Recipes
  listRecipes: (q?: string, tag?: string) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (tag) params.set("tag", tag);
    const qs = params.toString();
    return request<Recipe[]>(`/api/recipes${qs ? `?${qs}` : ""}`);
  },
  getRecipe: (id: string) => request<Recipe>(`/api/recipes/${id}`),
  createRecipe: (data: RecipeCreateInput) =>
    request<Recipe>("/api/recipes", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateRecipe: (id: string, data: Partial<RecipeCreateInput>) =>
    request<Recipe>(`/api/recipes/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteRecipe: (id: string) =>
    request<void>(`/api/recipes/${id}`, { method: "DELETE" }),
  importRecipe: (url: string) =>
    request<{ job_id: string; status: string }>("/api/recipes/import", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  // Ingredients
  listIngredients: (q?: string) => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    return request<{ id: string; name: string; category: string | null }[]>(
      `/api/ingredients${qs}`,
    );
  },

  // Meal Plan
  getMealPlan: (weekStart: string) =>
    request<MealPlanEntry[]>(`/api/meal-plan?week_start=${weekStart}`),
  createMealPlan: (data: {
    recipe_id: string;
    planned_date: string;
    meal_type?: string;
  }) =>
    request<MealPlanEntry>("/api/meal-plan", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateMealPlan: (
    id: string,
    data: { recipe_id?: string; planned_date?: string; meal_type?: string },
  ) =>
    request<MealPlanEntry>(`/api/meal-plan/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteMealPlan: (id: string) =>
    request<void>(`/api/meal-plan/${id}`, { method: "DELETE" }),

  // Week Config
  getWeekConfig: (weekStart: string) =>
    request<WeekConfig | null>(`/api/week-config?week_start=${weekStart}`),
  setWeekConfig: (data: { week_start_date: string; week_type: string }) =>
    request<WeekConfig>("/api/week-config", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Grocery List
  generateGroceryList: (startDate: string, endDate: string) =>
    request<GroceryList>("/api/grocery-list/generate", {
      method: "POST",
      body: JSON.stringify({
        start_date: startDate,
        end_date: endDate,
      }),
    }),

  // Spinner
  spin: (tags?: string) => {
    const qs = tags ? `?tags=${encodeURIComponent(tags)}` : "";
    return request<{ recipe: Recipe | null; message?: string }>(
      `/api/spinner/spin${qs}`,
    );
  },
  getTags: () => request<string[]>("/api/spinner/tags"),

  // Jobs
  getJob: (id: string) =>
    request<{
      id: string;
      job_type: string;
      status: string;
      result: Record<string, unknown> | null;
    }>(`/api/jobs/${id}`),
};

// ── Types ───────────────────────────────────────────────
export interface MealPlanEntry {
  id: string;
  recipe_id: string;
  recipe_title: string;
  planned_date: string;
  meal_type: string | null;
}

export interface WeekConfig {
  id: string;
  week_start_date: string;
  week_type: string;
  serving_override: number;
}

export interface GroceryItem {
  name: string;
  quantity: string;
  category: string;
  estimated_price: number;
}

export interface GroceryRecipe {
  id: string;
  title: string;
  cost_per_serving: number | null;
}

export interface WeekSummary {
  week_start: string;
  week_type: string;
  servings: number;
}

export interface GroceryList {
  start_date: string;
  end_date: string;
  weeks: WeekSummary[];
  recipes_included: GroceryRecipe[];
  items: GroceryItem[];
  estimated_total: number;
  recipe_cost_total: number;
}
