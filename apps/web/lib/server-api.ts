// Server-side user-scoped fetches. Server components don't carry the browser's
// cookie automatically, so we read the incoming request cookie via next/headers
// and forward it. Importing next/headers makes this module server-only at
// runtime (it throws in a client bundle); we also only import it from server
// components. (No `import "server-only"` — that package isn't a dependency and
// we're holding the line on no new deps.)

import { cookies } from "next/headers";

import type { AuthUser, Note, Watchlist } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getForwarded<T>(path: string): Promise<T | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) return null;
  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers: { Cookie: cookieHeader },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/** Resolve the current user from the forwarded session cookie, or null (401 /
 *  unreachable API both read as "not authenticated"). */
export async function getMe(): Promise<AuthUser | null> {
  return getForwarded<AuthUser>("/auth/me");
}

/** The current user's watchlists (cookie-forwarded), or null if unauthenticated. */
export async function getWatchlists(): Promise<Watchlist[] | null> {
  return getForwarded<Watchlist[]>("/watchlists");
}

/** All of the current user's notes (cookie-forwarded), or null if unauthenticated. */
export async function getNotes(): Promise<Note[] | null> {
  return getForwarded<Note[]>("/notes");
}
