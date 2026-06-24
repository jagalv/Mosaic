// Typed client for the Mosaic API. Shared types live here; public server
// fetches (company/filing) below. Auth/user-scoped calls live in client-api.ts
// (browser, credentials: include) and server-api.ts (server, cookie-forwarded).

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** The authenticated user, as returned by /auth/me, /auth/login, /auth/signup. */
export interface AuthUser {
  id: number;
  email: string;
}

export interface WatchlistItem {
  id: number;
  company_cik: number;
  ticker: string;
  name: string;
}

export interface Watchlist {
  id: number;
  name: string;
  created_at: string | null;
  items: WatchlistItem[];
}

export type NoteTarget =
  | { type: "company"; cik: number; ticker: string; name: string }
  | { type: "filing"; filing_id: number; accession_no: string };

export interface Note {
  id: number;
  body: string;
  created_at: string | null;
  updated_at: string | null;
  target: NoteTarget;
}

export interface LineItemRow {
  line_item: string;
  values: Record<string, number>; // year (string) -> value in actual USD
}

export interface FilingSummary {
  accession_no: string;
  form_type: string;
  filing_date: string | null;
  period_of_report: string | null;
  has_document: boolean;
  section_count: number;
}

export interface CompanyData {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  years: number[];
  statements: {
    income: LineItemRow[];
    balance: LineItemRow[];
    cash_flow: LineItemRow[];
  };
  filings: FilingSummary[];
}

export interface FilingSection {
  section_code: string;
  title: string;
  char_start: number;
  char_end: number;
}

export interface FilingData {
  accession_no: string;
  form_type: string;
  filing_date: string | null;
  period_of_report: string | null;
  primary_doc_url: string | null;
  company: { ticker: string | null; name: string | null };
  content_text: string;
  sections: FilingSection[];
}

/** One company as listed on the browse grid: identity + a lightweight latest
 * Revenue metric (current + prior FY) so the grid needs only one API call. */
export interface CompanySummary {
  ticker: string;
  name: string;
  sector: string | null;
  revenue: number | null;
  revenue_prev: number | null;
}

/** Fetch every ingested company with its latest-revenue metric (one call). */
export async function fetchCompanies(): Promise<CompanySummary[]> {
  const res = await fetch(`${API_URL}/companies`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${res.status} for /companies`);
  return res.json();
}

/** Fetch a company's pivoted financials + filing list. Returns null on 404. */
export async function fetchCompany(ticker: string): Promise<CompanyData | null> {
  const res = await fetch(`${API_URL}/company/${ticker}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} for ${ticker}`);
  return res.json();
}

/** Fetch a single filing's text + sections. Returns null on 404. */
export async function fetchFiling(accession: string): Promise<FilingData | null> {
  const res = await fetch(`${API_URL}/filing/${accession}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} for filing ${accession}`);
  return res.json();
}

export interface AskCitation {
  marker: number; // the [n] used in the answer
  chunk_id: number;
  section_code: string;
  char_start: number;
  char_end: number;
}

export interface AskResponse {
  answer: string;
  abstained: boolean;
  citations: AskCitation[];
  unsupported_numbers: string[]; // figures not found verbatim in retrieved text
  cached: boolean;
  provider: string;
  model: string;
  latency_ms: number;
}

/** Ask a grounded question about a filing (called client-side from the reader). */
export async function askFiling(
  accession: string,
  question: string,
): Promise<AskResponse> {
  const res = await fetch(`${API_URL}/filing/${accession}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`API ${res.status} for ask ${accession}`);
  return res.json();
}
