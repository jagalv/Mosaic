"use client";

// Interactive filing reader: section nav + body, plus the "Ask this filing"
// panel. Lives client-side because it owns two pieces of interactive state —
// the question/answer exchange and which cited span is highlighted.
//
// TRUST-SPINE CONTRACT (do not regress): a footnote [n] (or grouped [n, m])
// carries the cited chunk's absolute char range; clicking it highlights that
// exact span in the source text and scrolls to it. The amber numbers-guard
// banner and the abstention line must keep rendering. Restyle around these.

import {
  ExternalLink,
  Info,
  Sparkles,
} from "lucide-react";
import { Fragment, useEffect, useRef, useState } from "react";

import { NotesPanel } from "@/components/notes/notes-panel";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { askFiling, type AskCitation, type AskResponse, type FilingData } from "@/lib/api";
import { cn } from "@/lib/utils";

const HIGHLIGHT_ID = "active-citation";

// "item1a" -> "Item 1A" for citation chips.
function sectionLabel(code: string): string {
  const m = code.match(/^item(\d+)([a-z])?$/i);
  if (m) return `Item ${m[1]}${m[2] ? m[2].toUpperCase() : ""}`;
  return code;
}

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
      {/* Active-citation highlight — violet token, distinct from teal + amber. */}
      <mark
        id={HIGHLIGHT_ID}
        className="scroll-mt-24 rounded bg-highlight px-0.5 text-highlight-foreground ring-1 ring-highlight"
      >
        {body.slice(a, b)}
      </mark>
      {body.slice(b)}
    </>
  );
}

// Split an answer into text + clickable [n] footnote markers (teal = interactive).
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
    <p className="text-[15px] leading-relaxed whitespace-pre-wrap text-foreground">
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
                className="mx-0.5 align-super text-[0.7rem] font-semibold text-primary underline-offset-2 hover:underline"
                title={`Jump to source · ${sectionLabel(cite.section_code)}`}
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
  const sourceUrl = filing.primary_doc_url;

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
        <CardHeader className="border-b [.border-b]:pb-3">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            Ask this filing
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <form onSubmit={onAsk} className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What are the main risks to the supply chain?"
              className="h-10 flex-1 rounded-lg border border-border bg-background px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40"
            />
            <Button type="submit" size="lg" disabled={loading || !question.trim()}>
              {loading ? "Thinking…" : "Ask"}
            </Button>
          </form>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Info className="size-3.5" />
            Answers come only from this filing, with citations to the source.
          </p>

          {error ? (
            <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          {result ? (
            <div className="mt-1 flex flex-col gap-3 border-t border-border pt-4">
              {result.abstained ? (
                <p className="flex items-start gap-2 text-[15px] leading-relaxed text-muted-foreground italic">
                  <Info className="mt-0.5 size-4 shrink-0" />
                  {result.answer}
                </p>
              ) : (
                <AnswerText
                  answer={result.answer}
                  citations={result.citations}
                  onCite={setActive}
                />
              )}

              {/* Citation chips: Item/section + external-link to the SEC source. */}
              {result.citations.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {result.citations.map((c) => (
                    <span
                      key={c.marker}
                      className={cn(
                        "inline-flex items-center overflow-hidden rounded-full border text-xs font-medium",
                        active?.chunk_id === c.chunk_id
                          ? "border-primary/50 bg-primary/15 text-primary"
                          : "border-border bg-secondary text-secondary-foreground",
                      )}
                    >
                      <button
                        onClick={() => setActive(c)}
                        className="py-1 pl-2.5 pr-1.5 hover:text-primary"
                        title="Highlight the source in the filing"
                      >
                        <span className="text-primary">[{c.marker}]</span>{" "}
                        {sectionLabel(c.section_code)}
                      </button>
                      {sourceUrl ? (
                        <a
                          href={sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex h-full items-center border-l border-border/70 px-1.5 text-muted-foreground hover:text-primary"
                          title="Open the original filing on SEC.gov"
                        >
                          <ExternalLink className="size-3" />
                        </a>
                      ) : null}
                    </span>
                  ))}
                </div>
              ) : null}

              {/* Numbers-guard warning — amber, distinct from teal + violet. */}
              {result.unsupported_numbers.length > 0 ? (
                <p className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-foreground">
                  <span className="mt-px text-warning">⚠</span>
                  <span>
                    Figure{result.unsupported_numbers.length === 1 ? "" : "s"}{" "}
                    <span className="tnum font-semibold text-warning">
                      {result.unsupported_numbers.join(", ")}
                    </span>{" "}
                    not found verbatim in the cited text — verify against the
                    source before relying on{" "}
                    {result.unsupported_numbers.length === 1 ? "it" : "them"}.
                  </span>
                </p>
              ) : null}

              <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                <span>
                  {result.abstained
                    ? "No supported answer found in this filing."
                    : `${result.citations.length} citation${
                        result.citations.length === 1 ? "" : "s"
                      }`}
                </span>
                <span className="text-border">·</span>
                <span className="tnum">{result.model}</span>
                <span className="text-border">·</span>
                <span className="tnum">
                  {result.cached ? "cached" : `${result.latency_ms} ms`}
                </span>
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <NotesPanel target={{ accession: accession_no }} className="mb-6" />

      {sections.length === 0 ? (
        <Card>
          <CardHeader className="border-b [.border-b]:pb-3">
            <CardTitle>Full document</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-xs text-muted-foreground">
              Section segmentation is currently 10-K only; showing full text.
            </p>
            <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
              {text}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-8 md:grid-cols-[200px_1fr]">
          <aside className="self-start md:sticky md:top-20">
            <p className="mb-2 px-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Sections
            </p>
            <nav className="flex flex-col gap-0.5 text-sm">
              {sections.map((s) => (
                <a
                  key={s.section_code}
                  href={`#${s.section_code}`}
                  className="rounded-md px-3 py-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                >
                  {s.title}
                </a>
              ))}
            </nav>
          </aside>

          <article className="flex min-w-0 flex-col gap-8">
            {sections.map((s) => {
              const absStart = bodyStart(text, s.char_start);
              const body = text.slice(absStart, s.char_end);
              return (
                <section key={s.section_code} id={s.section_code}>
                  <h2 className="mb-3 scroll-mt-20 border-b border-border pb-2 font-heading text-lg font-semibold tracking-tight text-foreground">
                    {s.title}
                  </h2>
                  <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
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
