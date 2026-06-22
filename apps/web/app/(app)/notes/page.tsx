import { redirect } from "next/navigation";

import { NotesManager } from "@/components/notes/notes-manager";
import { PageHeader } from "@/components/primitives/page-header";
import { getMe, getNotes } from "@/lib/server-api";

// Personal page — self-guards (browse elsewhere is public).
export default async function NotesPage() {
  const user = await getMe();
  if (!user) redirect("/login?next=/notes");

  const initial = await getNotes();

  return (
    <div className="mx-auto w-full max-w-4xl p-6">
      <PageHeader
        eyebrow="Personal"
        title="Notes"
        description="Your saved notes, grouped by company and filing."
      />
      <div className="mt-6">
        <NotesManager initial={initial} />
      </div>
    </div>
  );
}
