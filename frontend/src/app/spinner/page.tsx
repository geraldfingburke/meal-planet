"use client";

import { useState } from "react";
import Link from "next/link";
import { api, type Recipe } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function SpinnerPage() {
  const [result, setResult] = useState<Recipe | null>(null);
  const [spinning, setSpinning] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [tagsLoaded, setTagsLoaded] = useState(false);
  const [noMatch, setNoMatch] = useState(false);

  const loadTags = async () => {
    if (tagsLoaded) return;
    try {
      const tags = await api.getTags();
      setAllTags(tags);
      setTagsLoaded(true);
    } catch (e) {
      console.error("Failed to load tags:", e);
    }
  };

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  };

  const handleSpin = async () => {
    await loadTags();
    setSpinning(true);
    setNoMatch(false);
    setResult(null);

    // Brief animation delay
    await new Promise((r) => setTimeout(r, 800));

    try {
      const tagsParam = selectedTags.length
        ? selectedTags.join(",")
        : undefined;
      const data = await api.spin(tagsParam);
      if (data.recipe) {
        setResult(data.recipe);
      } else {
        setNoMatch(true);
      }
    } catch (e) {
      console.error("Spin failed:", e);
    } finally {
      setSpinning(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto space-y-8 text-center">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">🎰 Dinner Spinner</h2>
        <p className="text-muted-foreground">
          Can&apos;t decide what to eat? Let fate choose!
        </p>
      </div>

      {/* Tag Filters */}
      {allTags.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Filter by tags:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {allTags.map((tag) => (
              <Badge
                key={tag}
                variant={selectedTags.includes(tag) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Spin Button */}
      <Button
        size="lg"
        className="text-xl px-12 py-6"
        onClick={handleSpin}
        disabled={spinning}
      >
        {spinning ? "🌀 Spinning..." : "🎲 Spin!"}
      </Button>

      {/* Result */}
      {noMatch && (
        <p className="text-muted-foreground">
          No recipes match your filters. Try removing some tags.
        </p>
      )}

      {result && (
        <Card className="text-left">
          <CardHeader>
            <CardTitle>{result.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {result.base_servings} servings · {result.ingredients.length}{" "}
              ingredients
            </p>

            {result.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {result.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            <div className="space-y-1">
              <h4 className="text-sm font-semibold">Ingredients:</h4>
              <ul className="text-sm space-y-0.5">
                {result.ingredients.map((ing) => (
                  <li key={ing.ingredient_id}>
                    {ing.quantity} {ing.unit} {ing.ingredient_name}
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex gap-2">
              <Button asChild size="sm">
                <Link href={`/recipes/${result.id}`}>View Full Recipe</Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="/planner">Add to Plan</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
