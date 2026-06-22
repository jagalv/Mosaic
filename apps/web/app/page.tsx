import Link from "next/link";
import { BookOpenText, Quote, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Chip } from "@/components/primitives/chip";
import { Logo } from "@/components/shell/logo";
import { STARTER_TICKERS } from "@/components/shell/nav-config";
import { ThemeToggle } from "@/components/shell/theme-toggle";
import { TickerSearch } from "@/components/shell/ticker-search";

const FEATURES = [
  {
    icon: BookOpenText,
    title: "Grounded retrieval",
    body: "Hybrid semantic + keyword search over section-chunked 10-Ks. Answers come only from the filing in front of you.",
  },
  {
    icon: Quote,
    title: "Inline citations",
    body: "Every claim carries a footnote that deep-links to the exact paragraph in the source text — click to verify.",
  },
  {
    icon: ShieldCheck,
    title: "Numbers guard",
    body: "A runtime check flags any figure that doesn't appear in the cited text, so a fabricated number never slips through.",
  },
];

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex h-16 items-center justify-between px-6">
        <Logo />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="ghost"
            nativeButton={false}
            render={<Link href="/login" />}
          >
            Log in
          </Button>
          <Button nativeButton={false} render={<Link href="/dashboard" />}>
            Open app
          </Button>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center px-6">
        <section className="flex w-full max-w-3xl flex-col items-center pt-20 pb-16 text-center sm:pt-28">
          <Chip variant="accent" className="mb-5">
            <span className="size-1.5 rounded-full bg-primary" />
            AI investment research
          </Chip>
          <h1 className="font-heading text-4xl font-semibold tracking-tight text-foreground sm:text-6xl">
            Ask any SEC filing.
            <br />
            <span className="text-primary">Get answers you can trust.</span>
          </h1>
          <p className="mt-6 max-w-xl text-base text-muted-foreground sm:text-lg">
            Mosaic reads 10-Ks for you and answers in plain language — every
            claim grounded in, and linked to, the primary source.
          </p>

          <div className="mt-8 w-full max-w-md">
            <TickerSearch variant="hero" placeholder="Try a ticker — AAPL, MSFT, NVDA…" />
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            {STARTER_TICKERS.slice(0, 6).map((t) => (
              <Link key={t} href={`/company/${t.toLowerCase()}`}>
                <Chip className="transition-colors hover:border-primary/40 hover:text-primary">
                  {t}
                </Chip>
              </Link>
            ))}
          </div>

          <p className="mt-8 flex items-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="size-4 text-success" />
            Grounded · cited · numbers-guarded
          </p>
        </section>

        <section className="grid w-full max-w-5xl grid-cols-1 gap-3 pb-24 md:grid-cols-3">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.title}
                className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5"
              >
                <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </span>
                <h3 className="font-heading text-sm font-semibold text-foreground">
                  {f.title}
                </h3>
                <p className="text-sm text-muted-foreground">{f.body}</p>
              </div>
            );
          })}
        </section>
      </main>

      <footer className="border-t border-border px-6 py-5 text-center text-xs text-muted-foreground">
        Mosaic — research tool, not investment advice. Data from SEC EDGAR.
      </footer>
    </div>
  );
}
