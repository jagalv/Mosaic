"use client";

import { Pencil, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Chip } from "@/components/primitives/chip";
import { Button } from "@/components/ui/button";
import type { Note } from "@/lib/api";
import { deleteNote, updateNote } from "@/lib/client-api";

function targetLink(note: Note): { href: string; label: string } {
  return note.target.type === "company"
    ? { href: `/company/${note.target.ticker.toLowerCase()}`, label: note.target.ticker }
    : { href: `/filing/${note.target.accession_no}`, label: note.target.accession_no };
}

export function NoteItem({
  note,
  showTarget = false,
  onChanged,
}: {
  note: Note;
  showTarget?: boolean;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [body, setBody] = useState(note.body);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    const v = body.trim();
    if (!v || busy) return;
    setBusy(true);
    setError(null);
    try {
      await updateNote(note.id, v);
      setEditing(false);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save.");
      setBusy(false);
    }
  }

  async function remove() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await deleteNote(note.id);
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't delete.");
      setBusy(false);
    }
  }

  const link = targetLink(note);

  return (
    <div className="rounded-lg border border-border bg-card p-3">
      {showTarget ? (
        <div className="mb-2">
          <Link href={link.href} title={note.target.type === "company" ? note.target.name : undefined}>
            <Chip variant="accent">{link.label}</Chip>
          </Link>
        </div>
      ) : null}

      {editing ? (
        <div className="flex flex-col gap-2">
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={3}
            maxLength={10000}
            className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={save} disabled={busy || !body.trim()}>
              Save
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setEditing(false);
                setBody(note.body);
                setError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <p className="whitespace-pre-wrap text-sm text-foreground/90">
            {note.body}
          </p>
          <div className="mt-2 flex items-center justify-between">
            <span className="tnum text-xs text-muted-foreground">
              {note.updated_at?.slice(0, 10)}
            </span>
            <div className="flex gap-1">
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setEditing(true)}
                aria-label="Edit note"
              >
                <Pencil />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                onClick={remove}
                disabled={busy}
                aria-label="Delete note"
              >
                <Trash2 />
              </Button>
            </div>
          </div>
        </>
      )}

      {error ? <p className="mt-1 text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
