"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface IngredientInput {
  ingredient_name: string;
  quantity: number;
  unit: string;
}

export default function NewRecipePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [baseServings, setBaseServings] = useState(4);
  const [tags, setTags] = useState("");
  const [category, setCategory] = useState("any");
  const [ingredients, setIngredients] = useState<IngredientInput[]>([
    { ingredient_name: "", quantity: 1, unit: "" },
  ]);
  const [saving, setSaving] = useState(false);

  const addIngredient = () => {
    setIngredients([
      ...ingredients,
      { ingredient_name: "", quantity: 1, unit: "" },
    ]);
  };

  const removeIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const updateIngredient = (
    index: number,
    field: keyof IngredientInput,
    value: string | number,
  ) => {
    const updated = [...ingredients];
    (updated[index] as any)[field] = value;
    setIngredients(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setSaving(true);
    try {
      const recipe = await api.createRecipe({
        title,
        instructions: instructions || undefined,
        source_url: sourceUrl || undefined,
        image_url: imageUrl || undefined,
        base_servings: baseServings,
        category,
        ingredients: ingredients.filter((i) => i.ingredient_name.trim()),
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      router.push(`/recipes/${recipe.id}`);
    } catch (e) {
      alert("Failed to create recipe: " + e);
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">New Recipe</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Title *</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Recipe title"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Base Servings</label>
              <Input
                type="number"
                min={1}
                value={baseServings}
                onChange={(e) => setBaseServings(parseInt(e.target.value) || 4)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Source URL</label>
              <Input
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://..."
              />
            </div>
            <div>
              <label className="text-sm font-medium">Image URL</label>
              <Input
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://example.com/photo.jpg"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="any">Any</option>
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
                <option value="dessert">Dessert</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">
                Tags (comma separated)
              </label>
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="quick, chicken, weeknight"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ingredients</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {ingredients.map((ing, i) => (
              <div key={i} className="flex gap-2 items-end">
                <div className="w-20">
                  <label className="text-xs text-muted-foreground">Qty</label>
                  <Input
                    type="number"
                    step="0.25"
                    min="0"
                    value={ing.quantity}
                    onChange={(e) =>
                      updateIngredient(
                        i,
                        "quantity",
                        parseFloat(e.target.value) || 0,
                      )
                    }
                  />
                </div>
                <div className="w-24">
                  <label className="text-xs text-muted-foreground">Unit</label>
                  <Input
                    value={ing.unit}
                    onChange={(e) =>
                      updateIngredient(i, "unit", e.target.value)
                    }
                    placeholder="cup"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs text-muted-foreground">
                    Ingredient
                  </label>
                  <Input
                    value={ing.ingredient_name}
                    onChange={(e) =>
                      updateIngredient(i, "ingredient_name", e.target.value)
                    }
                    placeholder="Flour"
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeIngredient(i)}
                  disabled={ingredients.length === 1}
                >
                  ✕
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addIngredient}
            >
              + Add Ingredient
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Instructions</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Step-by-step instructions..."
            />
          </CardContent>
        </Card>

        <div className="flex gap-2">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Create Recipe"}
          </Button>
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
