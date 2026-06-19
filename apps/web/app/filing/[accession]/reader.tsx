"use client";

// Interactive filing reader: section nav + body, plus the "Ask this filing"
// panel. Lives client-side because it owns two pieces of interactive state —
// the question/answer exchange and which cited span is highlighted. The page
// (server component) still does the data fetch and hands us the filing.
//
// Deep-linking is the point: a footnote [n] in the answer carries the cited
// chunk's absolute char range, and clicking it highlights that exact span in
// the source text and scrolls to it. Because this component owns content_text,
// it can slice precisely by offset — the same offset contract the whole RAG
// pipeline is built on.

import { Fragment, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { askFiling, type AskCitation, type AskResponse, type FilingData } from "@/lib/api";

const HIGHLIGHT_ID = "active-citation";

// Absolute offset where a section's BODY begins (just after its heading line),
// so highlight math lines up with what we actually render.
function bodyStart(text: string, charStart: number): number {
  const nl = text.indexOf("\n", charStart);
  return nl === -1 ? charStart : nl + 1;
}

function renderBody(
  body: string,
  absStart: number,
  absEnd: number,
  hl: AskCitation | null,
) {
  if (!hl) return body;
  const cs = Math.max(hl.char_start, absStart);
  const ce = Math.min(hl.char_end, absEnd);
  if (cs >= ce) return body; // citation isn't in this section
  const a = cs - absStart;
  const b = ce - absStart;
  return (
    <>
      {body.slice(0, a)}
      <mark id={HIGHLIGHT_ID} className="scroll-mt-24 rounded bg-yellow-200/70 dark:bg-yellow-500/30">
        {body.slice(a, b)}
      </mark>
      {body.slice(b)}
    </>
  );
}

// Split an answer into text + clickable [n] footnote markers.
function AnswerText({
  answer,
  citations,
  onCite,
}: {
  answer: string;
  citations: AskCitation[];
  onCite: (c: AskCitation) => void;
}) {
  // Split on citation brackets, which may group numbers: [1], [1, 2], [1,2,3].
  const parts = answer.split(/(\[[\d,\s]+\])/g);
  return (
    <p className="text-sm leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) => {
        const m = part.match(/^\[([\d,\s]+)\]$/);
        if (!m) return <Fragment key={i}>{part}</Fragment>;
        const markers = m[1]
          .split(",")
          .map((n) => Number(n.trim()))
          .filter((n) => Number.isInteger(n));
        const cited = markers
          .map((marker) => citations.find((c) => c.marker === marker))
          .filter((c): c is AskCitation => Boolean(c));
        if (cited.length === 0) return <Fragment key={i}>{part}</Fragment>;
        return (
          <Fragment key={i}>
            {cited.map((cite) => (
              <button
                key={cite.marker}
                onClick={() => onCite(cite)}
                className="mx-0.5 align-super text-xs font-medium text-primary underline-offset-2 hover:underline"
                title={`Jump to source · ${cite.section_code}`}
              >
                [{cite.marker}]
              </button>
            ))}
          </Fragment>
        );
      })}
    </p>
  );
}

export function FilingReader({ filing }: { filing: FilingData }) {
  const { content_text: text, sections, accession_no } = filing;

  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [active, setActive] = useState<AskCitation | null>(null);
  const pending = useRef(false);

  // Scroll the highlighted span into view once it has rendered.
  useEffect(() => {
    if (active) {
      document.getElementById(HIGHLIGHT_ID)?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [active]);

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || pending.current) return;
    pending.current = true;
    setLoading(true);
    setError(null);
    setActive(null);
    try {
      setResult(await askFiling(accession_no, q));
    } catch {
      setError("Couldn't reach the AI service. Is the API running?");
      setResult(null);
    } finally {
      setLoading(false);
      pending.current = false;
    }
  }

  return (
    <>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Ask this filing</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onAsk} className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What are the main risks to the supply chain?"
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <Button type="submit" size="lg" disabled={loading || !question.trim()}>
              {loading ? "Thinking…" : "Ask"}
            </Button>
          </form>
          <p className="mt-2 text-xs text-muted-foreground">
            Answers come only from this filing, with citations linking to the
            source text. The model says “not stated in the filings” when the
            answer isn’t there.
          </p>

          {error ? (
            <p className="mt-4 text-sm text-destructive">{error}</p>
          ) : null}

          {result ? (
            <div className="mt-4 border-t border-border pt-4">
              <AnswerText
                answer={result.answer}
                citations={result.citations}
                onCite={setActive}
              />
              <p className="mt-3 text-xs text-muted-foreground">
                {result.abstained
                  ? "No supported answer found in this filing."
                  : `${result.citations.length} citation${
                      result.citations.length === 1 ? "" : "s"
                    } · `}
                {result.model}
                {result.cached ? " · cached" : ` · ${result.latency_ms} ms`}
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {sections.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Full document</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-xs text-muted-foreground">
              Section segmentation is currently 10-K only; showing full text.
            </p>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">{text}</div>
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
              const absStart = bodyStart(text, s.char_start);
              const body = text.slice(absStart, s.char_end);
              return (
                <section key={s.section_code} id={s.section_code}>
                  <h2 className="mb-2 scroll-mt-6 text-lg font-semibold">
                    {s.title}
                  </h2>
                  <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
                    {renderBody(body, absStart, s.char_end, active)}
                  </div>
                </section>
              );
            })}
          </article>
        </div>
      )}
    </>
  );
}
