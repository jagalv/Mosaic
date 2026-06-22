import { AppShell } from "@/components/shell/app-shell";
import { getMe } from "@/lib/server-api";

// Browse is public — dashboard/company/filing render for everyone. The shell is
// auth-aware (user|null); only the personal pages (e.g. /watchlist) self-guard.
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getMe();
  return <AppShell user={user}>{children}</AppShell>;
}
