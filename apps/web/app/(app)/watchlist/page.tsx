import { redirect } from "next/navigation";

import { PageHeader } from "@/components/primitives/page-header";
import { WatchlistManager } from "@/components/watchlist/watchlist-manager";
import { getMe, getWatchlists } from "@/lib/server-api";

// Personal page — self-guards (browse elsewhere is public).
export default async function WatchlistPage() {
  const user = await getMe();
  if (!user) redirect("/login?next=/watchlist");

  const initial = await getWatchlists();

  return (
    <div className="mx-auto w-full max-w-4xl p-6">
      <PageHeader
        eyebrow="Personal"
        title="Watchlist"
        description="Companies you're tracking. Add from any company page."
      />
      <div className="mt-6">
        <WatchlistManager initial={initial} />
      </div>
    </div>
  );
}
