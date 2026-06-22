"use client";

import { Check, Plus, Star } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import type { Watchlist } from "@/lib/api";
import {
  addWatchlistItem,
  createWatchlist,
  getWatchlists,
} from "@/lib/client-api";

export function WatchButton({ ticker }: { ticker: string }) {
  const { user } = useAuth();
  const pathname = usePathname();

  if (!user) {
    return (
      <Button
        variant="outline"
        nativeButton={false}
        render={<Link href={`/login?next=${encodeURIComponent(pathname)}`} />}
      >
        <Star /> Watch
      </Button>
    );
  }
  return <WatchPopover ticker={ticker} />;
}

function WatchPopover({ ticker }: { ticker: string }) {
  const tk = ticker.toUpperCase();
  const [open, setOpen] = useState(false);
  const [lists, setLists] = useState<Watchlist[] | null>(null);
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const contains = (wl: Watchlist) =>
    wl.items.some((it) => it.ticker.toUpperCase() === tk);

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next && lists === null) {
      getWatchlists()
        .then(setLists)
        .catch((e) =>
          setError(e instanceof Error ? e.message : "Failed to load lists."),
        );
    }
  }

  async function addTo(wl: Watchlist) {
    if (busy || contains(wl)) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await addWatchlistItem(wl.id, ticker);
      setLists((prev) =>
        prev ? prev.map((w) => (w.id === wl.id ? updated : w)) : prev,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't add to list.");
    } finally {
      setBusy(false);
    }
  }

  async function createAndAdd(e: React.FormEvent) {
    e.preventDefault();
    const name = newName.trim();
    if (!name || busy) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createWatchlist(name);
      const updated = await addWatchlistItem(created.id, ticker);
      setLists((prev) => [...(prev ?? []), updated]);
      setNewName("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't create list.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      <Button variant="outline" onClick={toggle} aria-expanded={open}>
        <Star /> Watch
      </Button>

      {open ? (
        <>
          {/* click-away */}
          <button
            aria-hidden
            tabIndex={-1}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-40 cursor-default"
          />
          <div className="absolute right-0 z-50 mt-2 w-64 rounded-xl border border-border bg-popover p-2 shadow-md">
            <p className="px-2 py-1 text-xs font-medium text-muted-foreground">
              Add {tk} to…
            </p>

            {lists === null ? (
              <p className="px-2 py-2 text-sm text-muted-foreground">Loading…</p>
            ) : lists.length === 0 ? (
              <p className="px-2 py-2 text-sm text-muted-foreground">
                No lists yet — create one below.
              </p>
            ) : (
              <div className="flex flex-col">
                {lists.map((wl) => {
                  const has = contains(wl);
                  return (
                    <button
                      key={wl.id}
                      onClick={() => addTo(wl)}
                      disabled={busy || has}
                      className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-accent disabled:opacity-100"
                    >
                      <span className="truncate">{wl.name}</span>
                      {has ? (
                        <Check className="size-4 shrink-0 text-success" />
                      ) : (
                        <Plus className="size-4 shrink-0 text-muted-foreground" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            <form
              onSubmit={createAndAdd}
              className="mt-1 flex gap-1 border-t border-border pt-2"
            >
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="New list…"
                maxLength={120}
                className="h-8 flex-1 rounded-md border border-border bg-background px-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
              />
              <Button type="submit" size="sm" disabled={busy || !newName.trim()}>
                Add
              </Button>
            </form>

            {error ? (
              <p className="px-2 pt-1.5 text-xs text-destructive">{error}</p>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
