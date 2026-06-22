"use client";

import { Plus, Star, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/primitives/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Watchlist } from "@/lib/api";
import {
  createWatchlist,
  deleteWatchlist,
  getWatchlists,
  removeWatchlistItem,
} from "@/lib/client-api";

export function WatchlistManager({
  initial,
}: {
  initial: Watchlist[] | null;
}) {
  const [lists, setLists] = useState<Watchlist[] | null>(initial);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setError(null);
      setLists(await getWatchlists());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load watchlists.");
    }
  }

  // Fallback if the server prefetch came back empty/unauthenticated (e.g. cookie
  // refresh race) — the page is already guarded, so we just (re)load client-side.
  useEffect(() => {
    if (lists === null) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function run(fn: () => Promise<unknown>) {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    await run(async () => {
      await createWatchlist(name);
      setNewName("");
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={onCreate} className="flex gap-2">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New watchlist name…"
          maxLength={120}
          className="h-10 flex-1 rounded-lg border border-border bg-background px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40"
        />
        <Button type="submit" size="lg" disabled={busy || !newName.trim()}>
          <Plus /> Create
        </Button>
      </form>

      {error ? (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {lists === null ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-24 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
        </div>
      ) : lists.length === 0 ? (
        <EmptyState
          icon={Star}
          title="No watchlists yet"
          description="Create one above, then add companies with the Watch button on any company page."
        />
      ) : (
        lists.map((wl) => (
          <Card key={wl.id}>
            <CardContent className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-baseline gap-2">
                  <span className="font-heading text-sm font-semibold text-foreground">
                    {wl.name}
                  </span>
                  <span className="tnum text-xs text-muted-foreground">
                    {wl.items.length}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => run(() => deleteWatchlist(wl.id))}
                  disabled={busy}
                  aria-label={`Delete ${wl.name}`}
                >
                  <Trash2 />
                </Button>
              </div>

              {wl.items.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No companies yet.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {wl.items.map((it) => (
                    <span
                      key={it.id}
                      className="inline-flex items-center overflow-hidden rounded-full border border-border bg-secondary text-xs font-medium"
                    >
                      <Link
                        href={`/company/${it.ticker.toLowerCase()}`}
                        className="py-1 pl-2.5 pr-1.5 text-secondary-foreground hover:text-primary"
                        title={it.name}
                      >
                        {it.ticker}
                      </Link>
                      <button
                        onClick={() =>
                          run(() => removeWatchlistItem(wl.id, it.id))
                        }
                        disabled={busy}
                        aria-label={`Remove ${it.ticker} from ${wl.name}`}
                        className="flex h-full items-center border-l border-border/70 px-1.5 text-muted-foreground hover:text-destructive"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
