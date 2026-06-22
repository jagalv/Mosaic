import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Chip } from "@/components/primitives/chip";
import { Delta } from "@/components/primitives/metric";
import { EmptyState } from "@/components/primitives/states";
import { STARTER_TICKERS } from "@/components/shell/nav-config";
import { fetchCompany, type CompanyData } from "@/lib/api";
import { fmtCompactUSD, pctChange } from "@/lib/format";

function latestRevenue(c: CompanyData): { value?: number; delta: number | null } {
  const rev = c.statements.income.find((r) => r.line_item === "Revenue");
  const years = [...c.years].sort((a, b) => b - a);
  const curr = rev?.values[String(years[0])];
  const prev = rev?.values[String(years[1])];
  return { value: curr, delta: pctChange(curr, prev) };
}

async function getCompanies(): Promise<CompanyData[]> {
  const results = await Promise.allSettled(
    STARTER_TICKERS.map((t) => fetchCompany(t)),
  );
  return results
    .filter(
      (r): r is PromiseFulfilledResult<CompanyData> =>
        r.status === "fulfilled" && r.value != null,
    )
    .map((r) => r.value);
}

export async function CompanyGrid() {
  const companies = await getCompanies();

  if (companies.length === 0) {
    return (
      <EmptyState
        title="No companies loaded"
        description="The API returned no companies. Make sure the backend is running and the SEC ingestion has been run."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {companies.map((c) => {
        const { value, delta } = latestRevenue(c);
        return (
          <Link
            key={c.ticker}
            href={`/company/${c.ticker.toLowerCase()}`}
            className="group flex flex-col gap-3 rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary/40 hover:bg-accent/40"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate font-heading text-sm font-semibold text-foreground">
                  {c.name}
                </p>
                <p className="mt-1 truncate text-xs text-muted-foreground">
                  {c.sector ?? "—"}
                </p>
              </div>
              <Chip variant="accent">{c.ticker}</Chip>
            </div>
            <div className="flex items-end justify-between gap-2">
              <div>
                <p className="text-[11px] text-muted-foreground">Revenue</p>
                <p className="tnum text-lg font-semibold tracking-tight text-foreground">
                  {fmtCompactUSD(value)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {delta != null ? <Delta value={delta} /> : null}
                <ArrowUpRight className="size-4 text-muted-foreground transition-colors group-hover:text-primary" />
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
