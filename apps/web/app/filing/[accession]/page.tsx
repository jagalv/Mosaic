// Filing reader (server component). Renders a filing's cleaned text with a
// section nav. Sections come from the API as char offsets into content_text.

import Link from "next/link";
import { notFound } from "next/navigation";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchFiling } from "@/lib/api";

export default async function FilingPage({
  params,
}: {
  params: Promise<{ accession: string }>;
}) {
  const { accession } = await params;
  const filing = await fetchFiling(accession);
  if (!filing) notFound();

  const { content_text: text, sections } = filing;
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

      {sections.length === 0 ? (
        // 10-Q (and any unsegmented form): show the full document text.
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Full document</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-xs text-muted-foreground">
              Section segmentation is currently 10-K only; showing full text.
            </p>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {text}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-[220px_1fr]">
          <aside className="self-start md:sticky md:top-6">
            <nav className="flex flex-col gap-1 text-sm">
              {sections.map((s) => (
                <a
                  key={s.section_code}
                  href={`#${s.section_code}`}
                  className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                >
                  {s.title}
                </a>
              ))}
            </nav>
          </aside>

          <article className="flex flex-col gap-8">
            {sections.map((s) => {
              // The slice begins with the raw heading line; drop it so the
              // styled title isn't duplicated.
              const body = text
                .slice(s.char_start, s.char_end)
                .split("\n")
                .slice(1)
                .join("\n")
                .trim();
              return (
                <section key={s.section_code} id={s.section_code}>
                  <h2 className="mb-2 scroll-mt-6 text-lg font-semibold">
                    {s.title}
                  </h2>
                  <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
                    {body}
                  </div>
                </section>
              );
            })}
          </article>
        </div>
      )}
    </main>
  );
}
