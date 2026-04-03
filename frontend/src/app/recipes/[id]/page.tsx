"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Recipe } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

const CATEGORIES = ["any", "breakfast", "lunch", "dinner", "dessert"];

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [servings, setServings] = useState<number>(4);

  // Editing state
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editCategory, setEditCategory] = useState("any");
  const [editTags, setEditTags] = useState("");
  const [editInstructions, setEditInstructions] = useState("");
  const [saving, setSaving] = useState(false);

  // New tag input
  const [newTag, setNewTag] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getRecipe(params.id as string);
        setRecipe(data);
        setServings(data.base_servings);
      } catch (e) {
        console.error("Failed to load recipe:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const startEditing = () => {
    if (!recipe) return;
    setEditTitle(recipe.title);
    setEditCategory(recipe.category || "any");
    setEditTags(recipe.tags.join(", "));
    setEditInstructions(recipe.instructions || "");
    setEditing(true);
  };

  const saveEdits = async () => {
    if (!recipe) return;
    setSaving(true);
    try {
      const updated = await api.updateRecipe(recipe.id, {
        title: editTitle,
        category: editCategory,
        tags: editTags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        instructions: editInstructions || undefined,
      });
      setRecipe(updated);
      setEditing(false);
    } catch (e) {
      alert("Failed to save: " + e);
    } finally {
      setSaving(false);
    }
  };

  const addTag = async () => {
    if (!recipe || !newTag.trim()) return;
    const updatedTags = [...recipe.tags, newTag.trim()];
    try {
      const updated = await api.updateRecipe(recipe.id, {
        tags: updatedTags,
      });
      setRecipe(updated);
      setNewTag("");
    } catch (e) {
      console.error("Failed to add tag:", e);
    }
  };

  const removeTag = async (tag: string) => {
    if (!recipe) return;
    const updatedTags = recipe.tags.filter((t) => t !== tag);
    try {
      const updated = await api.updateRecipe(recipe.id, {
        tags: updatedTags,
      });
      setRecipe(updated);
    } catch (e) {
      console.error("Failed to remove tag:", e);
    }
  };

  const scale = recipe ? servings / recipe.base_servings : 1;

  if (loading) return <div className="text-muted-foreground">Loading...</div>;
  if (!recipe) return <div className="text-destructive">Recipe not found</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          {editing ? (
            <Input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="text-2xl font-bold mb-2"
            />
          ) : (
            <h2 className="text-3xl font-bold tracking-tight">
              {recipe.title}
            </h2>
          )}
          <div className="text-muted-foreground text-sm flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1">
              <label className="text-xs">Servings:</label>
              <input
                type="number"
                min={1}
                value={servings}
                onChange={(e) =>
                  setServings(parseInt(e.target.value) || recipe.base_servings)
                }
                className="w-14 text-sm bg-primary/10 text-primary font-semibold rounded-md px-2 py-0.5 border-0"
              />
            </div>
            {recipe.category !== "any" && (
              <span className="capitalize text-primary font-medium">
                · {recipe.category}
              </span>
            )}
            {recipe.cost_per_serving != null && (
              <span className="text-primary font-medium">
                · ${(recipe.cost_per_serving * scale).toFixed(2)}/serving ($
                {(recipe.cost_per_serving * servings).toFixed(2)} total)
              </span>
            )}
            {recipe.source_url && (
              <>
                {" · "}
                <a
                  href={recipe.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Source
                </a>
              </>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {editing ? (
            <>
              <Button onClick={saveEdits} disabled={saving} size="sm">
                {saving ? "Saving..." : "Save"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditing(false)}
              >
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" size="sm" onClick={startEditing}>
                Edit
              </Button>
              <Button variant="outline" size="sm" onClick={() => router.back()}>
                Back
              </Button>
            </>
          )}
        </div>
      </div>

      {recipe.image_url && (
        <div className="relative w-full overflow-hidden rounded-lg">
          <img
            src={recipe.image_url}
            alt={recipe.title}
            className="w-full max-h-80 object-cover rounded-lg"
          />
        </div>
      )}

      {/* Category edit */}
      {editing && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Category</CardTitle>
          </CardHeader>
          <CardContent>
            <select
              value={editCategory}
              onChange={(e) => setEditCategory(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      <div className="space-y-2">
        <div className="flex flex-wrap gap-1">
          {recipe.tags.map((tag) => (
            <Badge
              key={tag}
              variant="secondary"
              className="cursor-pointer group"
            >
              {tag}
              {!editing && (
                <button
                  onClick={() => removeTag(tag)}
                  className="ml-1 opacity-0 group-hover:opacity-100 text-destructive"
                >
                  ✕
                </button>
              )}
            </Badge>
          ))}
        </div>
        {!editing && (
          <div className="flex gap-2">
            <Input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add a tag..."
              className="w-40"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addTag();
                }
              }}
            />
            <Button variant="outline" size="sm" onClick={addTag}>
              Add Tag
            </Button>
          </div>
        )}
        {editing && (
          <div>
            <label className="text-sm font-medium">
              Tags (comma separated)
            </label>
            <Input
              value={editTags}
              onChange={(e) => setEditTags(e.target.value)}
              placeholder="quick, chicken, weeknight"
            />
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Ingredients</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-1">
            {recipe.ingredients.map((ing) => {
              const qty = ing.quantity * scale;
              const display =
                qty % 1 === 0
                  ? qty.toString()
                  : qty.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
              return (
                <li key={ing.ingredient_id} className="text-sm">
                  <span className="font-medium">
                    {display} {ing.unit}
                  </span>{" "}
                  {ing.ingredient_name}
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>

      {editing ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Instructions</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={editInstructions}
              onChange={(e) => setEditInstructions(e.target.value)}
            />
          </CardContent>
        </Card>
      ) : (
        recipe.instructions && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Instructions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                {recipe.instructions}
              </div>
            </CardContent>
          </Card>
        )
      )}
    </div>
  );
}
