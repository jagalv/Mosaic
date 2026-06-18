// Typed client for the Mosaic API. Server components call these.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface LineItemRow {
  line_item: string;
  values: Record<string, number>; // year (string) -> value in actual USD
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
}

/** Fetch a company's pivoted financials. Returns null on 404. */
export async function fetchCompany(ticker: string): Promise<CompanyData | null> {
  const res = await fetch(`${API_URL}/company/${ticker}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} for ${ticker}`);
  return res.json();
}
