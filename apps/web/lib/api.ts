// Typed client for the Mosaic API. Server components call these.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
