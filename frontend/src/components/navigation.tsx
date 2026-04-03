"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Dashboard", icon: "🏠" },
  { href: "/recipes", label: "Recipes", icon: "📖" },
  { href: "/planner", label: "Planner", icon: "📅" },
  { href: "/grocery-list", label: "Grocery List", icon: "🛒" },
  { href: "/spinner", label: "Spinner", icon: "🎰" },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="no-print w-64 border-r bg-card p-4 hidden md:block">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-primary">🪐 Meal Planet</h1>
        <p className="text-sm text-muted-foreground">Family Meal Planner</p>
      </div>
      <ul className="space-y-1">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                pathname === link.href
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              <span>{link.icon}</span>
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
