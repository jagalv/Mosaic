// Filing reader (server component). Fetches the filing and renders its header;
// the interactive body (section nav, text, and the "Ask this filing" panel)
// lives in the FilingReader client component.

import { ArrowLeft, ExternalLink } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Chip } from "@/components/primitives/chip";
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
    <div className="mx-auto w-full max-w-5xl p-6">
      <header className="mb-6 flex flex-col gap-2">
        {ticker ? (
          <Link
            href={`/company/${ticker.toLowerCase()}`}
            className="inline-flex w-fit items-center gap-1 text-sm text-muted-foreground underline-offset-4 hover:text-foreground"
          >
            <ArrowLeft className="size-4" />
            {filing.company.name}
          </Link>
        ) : null}
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
            {filing.form_type}
          </h1>
          {filing.filing_date ? <Chip>Filed {filing.filing_date}</Chip> : null}
        </div>
        <p className="tnum text-xs text-muted-foreground">
          {filing.accession_no}
          {filing.primary_doc_url ? (
            <>
              {" · "}
              <a
                href={filing.primary_doc_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-0.5 underline-offset-4 hover:text-foreground hover:underline"
              >
                original on SEC.gov
                <ExternalLink className="size-3" />
              </a>
            </>
          ) : null}
        </p>
      </header>

      <FilingReader filing={filing} />
    </div>
  );
}
