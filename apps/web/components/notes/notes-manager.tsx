"use client";

import { FileText } from "lucide-react";
import { useEffect, useState } from "react";

import { SectionHeader } from "@/components/primitives/page-header";
import { EmptyState } from "@/components/primitives/states";
import { Skeleton } from "@/components/ui/skeleton";
import type { Note } from "@/lib/api";
import { getNotes } from "@/lib/client-api";
import { NoteItem } from "./note-item";

function Group({
  title,
  notes,
  onChanged,
}: {
  title: string;
  notes: Note[];
  onChanged: () => void;
}) {
  if (notes.length === 0) return null;
  return (
    <div>
      <SectionHeader title={title} />
      <div className="mt-3 flex flex-col gap-2">
        {notes.map((n) => (
          <NoteItem key={n.id} note={n} showTarget onChanged={onChanged} />
        ))}
      </div>
    </div>
  );
}

export function NotesManager({ initial }: { initial: Note[] | null }) {
  const [notes, setNotes] = useState<Note[] | null>(initial);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      setNotes(await getNotes());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load notes.");
    }
  }

  useEffect(() => {
    if (notes === null) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
        {error}
      </p>
    );
  }

  if (notes === null) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-20 rounded-lg" />
        <Skeleton className="h-20 rounded-lg" />
      </div>
    );
  }

  if (notes.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No notes yet"
        description="Open a company or a filing and use the Notes panel to capture your thinking."
      />
    );
  }

  const companyNotes = notes.filter((n) => n.target.type === "company");
  const filingNotes = notes.filter((n) => n.target.type === "filing");

  return (
    <div className="flex flex-col gap-6">
      <Group title="Company notes" notes={companyNotes} onChanged={load} />
      <Group title="Filing notes" notes={filingNotes} onChanged={load} />
    </div>
  );
}
