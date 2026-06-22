// Browser-side auth calls. Every request sends credentials so the httpOnly
// `mosaic_session` cookie rides cross-port (3000 -> 8000). Used by client
// components only (login/signup forms, AuthProvider/topbar logout).

import type { AuthUser, Note, Watchlist } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class AuthError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "AuthError";
  }
}

async function readError(res: Response): Promise<AuthError> {
  let detail = "Something went wrong. Please try again.";
  try {
    const body = await res.json();
    // FastAPI HTTPException -> string detail; pydantic validation -> array.
    if (typeof body.detail === "string") detail = body.detail;
    else if (Array.isArray(body.detail)) detail = "Please check your input.";
  } catch {
    /* non-JSON / empty body */
  }
  return new AuthError(res.status, detail);
}

async function postJson(path: string, body: unknown): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "include",
  });
}

export async function signup(
  email: string,
  password: string,
): Promise<AuthUser> {
  const res = await postJson("/auth/signup", { email, password });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function login(
  email: string,
  password: string,
): Promise<AuthUser> {
  const res = await postJson("/auth/login", { email, password });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function me(): Promise<AuthUser | null> {
  const res = await fetch(`${API_URL}/auth/me`, {
    credentials: "include",
    cache: "no-store",
  });
  if (res.status === 401) return null;
  if (!res.ok) throw await readError(res);
  return res.json();
}

// --- Watchlists (user-scoped; RLS enforced server-side) ---

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    cache: "no-store",
  });
  if (!res.ok) throw await readError(res);
  return res.json();
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw await readError(res);
}

export async function getWatchlists(): Promise<Watchlist[]> {
  return getJson("/watchlists");
}

export async function createWatchlist(name: string): Promise<Watchlist> {
  const res = await postJson("/watchlists", { name });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function deleteWatchlist(id: number): Promise<void> {
  return del(`/watchlists/${id}`);
}

export async function addWatchlistItem(
  id: number,
  ticker: string,
): Promise<Watchlist> {
  const res = await postJson(`/watchlists/${id}/items`, { ticker });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function removeWatchlistItem(
  id: number,
  itemId: number,
): Promise<void> {
  return del(`/watchlists/${id}/items/${itemId}`);
}

// --- Notes (user-scoped; RLS enforced server-side) ---

export type NoteFilter = { company?: string; accession?: string };

export async function getNotes(filter?: NoteFilter): Promise<Note[]> {
  const params = new URLSearchParams();
  if (filter?.company) params.set("company", filter.company);
  if (filter?.accession) params.set("accession", filter.accession);
  const qs = params.toString();
  return getJson(`/notes${qs ? `?${qs}` : ""}`);
}

export async function createNote(input: {
  body: string;
  company?: string;
  accession?: string;
}): Promise<Note> {
  const res = await postJson("/notes", input);
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function updateNote(id: number, body: string): Promise<Note> {
  const res = await fetch(`${API_URL}/notes/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ body }),
    credentials: "include",
  });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function deleteNote(id: number): Promise<void> {
  return del(`/notes/${id}`);
}
