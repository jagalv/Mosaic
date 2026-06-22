"use client";

import { FileText } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Note } from "@/lib/api";
import { createNote, getNotes, type NoteFilter } from "@/lib/client-api";
import { NoteItem } from "./note-item";

type Target = { company: string } | { accession: string };

function toFilter(t: Target): NoteFilter {
  return "company" in t ? { company: t.company } : { accession: t.accession };
}

function toCreate(t: Target, body: string) {
  return "company" in t ? { body, company: t.company } : { body, accession: t.accession };
}

export function NotesPanel({
  target,
  className,
}: {
  target: Target;
  className?: string;
}) {
  const { user } = useAuth();
  const pathname = usePathname();
  const authed = !!user;
  // Stable key so the fetch effect doesn't re-run on every render (target is a
  // fresh object literal each time).
  const filterKey = "company" in target ? `c:${target.company}` : `a:${target.accession}`;

  const [notes, setNotes] = useState<Note[] | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      setNotes(await getNotes(toFilter(target)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load notes.");
    }
  }

  useEffect(() => {
    if (authed) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authed, filterKey]);

  if (!authed) {
    return (
      <Card className={className}>
        <CardHeader className="border-b [.border-b]:pb-3">
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-4 text-primary" />
            Notes
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            Log in to add private notes here.
          </p>
          <Button
            variant="outline"
            size="sm"
            nativeButton={false}
            render={<Link href={`/login?next=${encodeURIComponent(pathname)}`} />}
          >
            Log in
          </Button>
        </CardContent>
      </Card>
    );
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    const v = draft.trim();
    if (!v || busy) return;
    setBusy(true);
    setError(null);
    try {
      await createNote(toCreate(target, v));
      setDraft("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't add note.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="border-b [.border-b]:pb-3">
        <CardTitle className="flex items-center gap-2">
          <FileText className="size-4 text-primary" />
          Notes
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <form onSubmit={onCreate} className="flex flex-col gap-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Add a note…"
            rows={2}
            maxLength={10000}
            className="w-full resize-y rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40"
          />
          <div className="flex justify-end">
            <Button type="submit" size="sm" disabled={busy || !draft.trim()}>
              Add note
            </Button>
          </div>
        </form>

        {error ? (
          <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {notes === null ? (
          <Skeleton className="h-16 rounded-lg" />
        ) : notes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No notes yet.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {notes.map((n) => (
              <NoteItem key={n.id} note={n} onChanged={load} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
