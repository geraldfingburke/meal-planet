"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Recipe } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export default function RecipesPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [search, setSearch] = useState("");
  const [importUrl, setImportUrl] = useState("");
  const [importing, setImporting] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadRecipes = async () => {
    try {
      const data = await api.listRecipes(search || undefined);
      setRecipes(data);
    } catch (e) {
      console.error("Failed to load recipes:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecipes();
  }, [search]);

  const handleImport = async () => {
    if (!importUrl.trim()) return;
    setImporting(true);
    try {
      const { job_id } = await api.importRecipe(importUrl);
      // Poll for completion
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const job = await api.getJob(job_id);
          if (job.status === "completed" || job.status === "failed") {
            clearInterval(poll);
            setImporting(false);
            setImportUrl("");
            if (job.status === "completed") {
              await loadRecipes();
            } else {
              alert("Import failed: " + JSON.stringify(job.result));
            }
          }
        } catch {
          if (attempts > 30) {
            clearInterval(poll);
            setImporting(false);
          }
        }
      }, 2000);
    } catch (e) {
      setImporting(false);
      alert("Failed to start import: " + e);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this recipe?")) return;
    await api.deleteRecipe(id);
    await loadRecipes();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Recipes</h2>
          <p className="text-muted-foreground">Manage your recipe collection</p>
        </div>
        <Button asChild>
          <Link href="/recipes/new">Add Recipe</Link>
        </Button>
      </div>

      {/* Import from URL */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Import from URL</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input
            placeholder="Paste a recipe URL..."
            value={importUrl}
            onChange={(e) => setImportUrl(e.target.value)}
            disabled={importing}
          />
          <Button
            onClick={handleImport}
            disabled={importing || !importUrl.trim()}
          >
            {importing ? "Importing..." : "Import"}
          </Button>
        </CardContent>
      </Card>

      {/* Search */}
      <Input
        placeholder="Search recipes..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* Recipe Grid */}
      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : recipes.length === 0 ? (
        <p className="text-muted-foreground">
          No recipes yet. Add one above or import from a URL!
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function RecipeCard({
  recipe,
  onDelete,
}: {
  recipe: Recipe;
  onDelete: (id: string) => void;
}) {
  return (
    <Card className="flex flex-col overflow-hidden">
      {recipe.image_url && (
        <div className="relative h-40 w-full">
          <img
            src={recipe.image_url}
            alt={recipe.title}
            className="h-full w-full object-cover"
          />
        </div>
      )}
      <CardHeader>
        <CardTitle className="text-lg">
          <Link
            href={`/recipes/${recipe.id}`}
            className="hover:text-primary transition-colors"
          >
            {recipe.title}
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        <div className="text-sm text-muted-foreground">
          {recipe.ingredients.length} ingredients · {recipe.base_servings}{" "}
          servings
          {recipe.category !== "any" && (
            <span className="capitalize"> · {recipe.category}</span>
          )}
          {recipe.cost_per_serving != null && (
            <> · ${recipe.cost_per_serving.toFixed(2)}/serving</>
          )}
        </div>
        {recipe.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {recipe.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        <div className="flex gap-2 pt-2">
          <Button asChild size="sm" variant="outline">
            <Link href={`/recipes/${recipe.id}`}>View</Link>
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => onDelete(recipe.id)}
          >
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
