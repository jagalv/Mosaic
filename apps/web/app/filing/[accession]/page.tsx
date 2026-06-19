// Filing reader (server component). Fetches the filing and renders its header;
// the interactive body (section nav, text, and the "Ask this filing" panel)
// lives in the FilingReader client component.

import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchFiling } from "@/lib/api";
import { FilingReader } from "./reader";

export default async function FilingPage({
  params,
}: {
  params: Promise<{ accession: string }>;
}) {
  const { accession } = await params;
  const filing = await fetchFiling(accession);
  if (!filing) notFound();

  const ticker = filing.company.ticker;

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 p-6">
      <header className="mb-6">
        {ticker ? (
          <Link
            href={`/company/${ticker.toLowerCase()}`}
            className="text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            ← {filing.company.name}
          </Link>
        ) : null}
        <h1 className="mt-1 text-2xl font-semibold">
          {filing.form_type}{" "}
          <span className="text-muted-foreground">
            {filing.filing_date ? `· filed ${filing.filing_date}` : ""}
          </span>
        </h1>
        <p className="text-xs text-muted-foreground">
          {filing.accession_no}
          {filing.primary_doc_url ? (
            <>
              {" · "}
              <a
                href={filing.primary_doc_url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline-offset-4 hover:underline"
              >
                original on SEC.gov ↗
              </a>
            </>
          ) : null}
        </p>
      </header>

      <FilingReader filing={filing} />
    </main>
  );
}
