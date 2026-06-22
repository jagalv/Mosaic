"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { cn } from "@/lib/utils";

// Search affordance — routes a typed ticker to its company page. Not full
// search (that's a later feature); just the entry point into the corpus.
export function TickerSearch({
  variant = "bar",
  placeholder = "Search a ticker (e.g. AAPL)…",
  autoFocus = false,
}: {
  variant?: "bar" | "hero";
  placeholder?: string;
  autoFocus?: boolean;
}) {
  const router = useRouter();
  const [q, setQ] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const t = q.trim().toLowerCase();
    if (t) router.push(`/company/${encodeURIComponent(t)}`);
  }

  const hero = variant === "hero";
  return (
    <form onSubmit={submit} className="relative w-full" role="search">
      <Search
        className={cn(
          "pointer-events-none absolute top-1/2 -translate-y-1/2 text-muted-foreground",
          hero ? "left-4 size-5" : "left-3 size-4",
        )}
      />
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        aria-label="Search a ticker"
        spellCheck={false}
        className={cn(
          "w-full rounded-lg border border-border bg-background/80 text-foreground placeholder:text-muted-foreground outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40",
          hero
            ? "h-12 pl-12 pr-4 text-base shadow-sm"
            : "h-9 pl-9 pr-3 text-sm",
        )}
      />
    </form>
  );
}
