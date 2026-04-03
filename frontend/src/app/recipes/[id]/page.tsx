"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type Recipe } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [servings, setServings] = useState<number>(4);

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

  const toggleServings = () => {
    setServings((prev) => (prev === 4 ? 6 : 4));
  };

  const scale = recipe ? servings / recipe.base_servings : 1;

  if (loading) return <div className="text-muted-foreground">Loading...</div>;
  if (!recipe) return <div className="text-destructive">Recipe not found</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{recipe.title}</h2>
          <div className="text-muted-foreground text-sm">
            <button
              onClick={toggleServings}
              className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 text-primary font-semibold hover:bg-primary/20 transition-colors cursor-pointer"
              title="Click to toggle between 4 and 6 servings"
            >
              {servings} servings
            </button>
            {recipe.cost_per_serving != null && (
              <>
                {" · "}
                <span className="text-primary font-medium">
                  ${(recipe.cost_per_serving * scale).toFixed(2)}/serving ($
                  {(recipe.cost_per_serving * servings).toFixed(2)} total)
                </span>
              </>
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
        <Button variant="outline" onClick={() => router.back()}>
          Back
        </Button>
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

      {recipe.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {recipe.tags.map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
            </Badge>
          ))}
        </div>
      )}

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

      {recipe.instructions && (
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
      )}
    </div>
  );
}
