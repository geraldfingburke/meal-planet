import type { Metadata } from "next";
import "./globals.css";
import { Navigation } from "@/components/navigation";

export const metadata: Metadata = {
  title: "Meal Planet",
  description: "Family meal planning, grocery lists, and dinner inspiration",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <div className="flex min-h-screen">
          <Navigation />
          <main className="flex-1 p-6 md:p-8 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
