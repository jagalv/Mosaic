// Company page (server component). Header + metric cards + 3 financial
// statement tables + filings, from the API's pivoted data. No AI, no auth.

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { notFound } from "next/navigation";

import { Chip } from "@/components/primitives/chip";
import { Delta, MetricCard } from "@/components/primitives/metric";
import { PageHeader } from "@/components/primitives/page-header";
import { WatchButton } from "@/components/company/watch-button";
import { NotesPanel } from "@/components/notes/notes-panel";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchCompany, type FilingSummary, type LineItemRow } from "@/lib/api";
import { fmtCompactUSD, fmtMillions, fmtPercent, pctChange } from "@/lib/format";

const LABELS: Record<string, string> = {
  Revenue: "Revenue",
  CostOfRevenue: "Cost of revenue",
  GrossProfit: "Gross profit",
  OperatingIncome: "Operating income",
  NetIncome: "Net income",
  TotalAssets: "Total assets",
  CurrentAssets: "Current assets",
  TotalLiabilities: "Total liabilities",
  CurrentLiabilities: "Current liabilities",
  StockholdersEquity: "Stockholders’ equity",
  CashAndEquivalents: "Cash & equivalents",
  OperatingCashFlow: "Operating cash flow",
  InvestingCashFlow: "Investing cash flow",
  FinancingCashFlow: "Financing cash flow",
  CapitalExpenditures: "Capital expenditures",
};

const STATEMENT_TITLES: Record<string, string> = {
  income: "Income Statement",
  balance: "Balance Sheet",
  cash_flow: "Cash Flow",
};

function pick(rows: LineItemRow[], name: string, year: number): number | undefined {
  return rows.find((r) => r.line_item === name)?.values[String(year)];
}

function StatementTable({
  title,
  rows,
  years,
}: {
  title: string;
  rows: LineItemRow[];
  years: number[];
}) {
  if (rows.length === 0) return null;
  return (
    <Card>
      <CardHeader className="border-b [.border-b]:pb-3">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="px-0">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="sticky top-0 bg-card pl-6 text-xs font-medium text-muted-foreground">
                USD in millions
              </TableHead>
              {years.map((y) => (
                <TableHead
                  key={y}
                  className="tnum sticky top-0 bg-card pr-6 text-right text-xs font-medium text-muted-foreground last:pr-6"
                >
                  FY{y}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.line_item} className="border-border/60">
                <TableCell className="pl-6 font-medium text-foreground">
                  {LABELS[row.line_item] ?? row.line_item}
                </TableCell>
                {years.map((y) => (
                  <TableCell
                    key={y}
                    className="tnum pr-6 text-right text-foreground/90"
                  >
                    {fmtMillions(row.values[String(y)])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function FilingsCard({ filings }: { filings: FilingSummary[] }) {
  if (filings.length === 0) return null;
  return (
    <Card>
      <CardHeader className="border-b [.border-b]:pb-3">
        <CardTitle>Filings</CardTitle>
      </CardHeader>
      <CardContent className="px-0">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-24 pl-6 text-xs font-medium text-muted-foreground">Form</TableHead>
              <TableHead className="w-32 text-xs font-medium text-muted-foreground">Filed</TableHead>
              <TableHead className="pr-6 text-xs font-medium text-muted-foreground">Document</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filings.map((f) => (
              <TableRow key={f.accession_no} className="border-border/60">
                <TableCell className="pl-6">
                  <Chip>{f.form_type}</Chip>
                </TableCell>
                <TableCell className="tnum text-muted-foreground">
                  {f.filing_date ?? "—"}
                </TableCell>
                <TableCell className="pr-6">
                  {f.has_document ? (
                    <Link
                      href={`/filing/${f.accession_no}`}
                      className="inline-flex items-center gap-1 font-medium text-primary underline-offset-4 hover:underline"
                    >
                      Read
                      {f.section_count > 0 ? ` · ${f.section_count} sections` : ""}
                      <ArrowUpRight className="size-3.5" />
                    </Link>
                  ) : (
                    <span className="text-muted-foreground">not ingested</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const company = await fetchCompany(ticker);
  if (!company) notFound();

  const years = [...company.years].sort((a, b) => b - a);
  const [y0, y1] = years;
  const inc = company.statements.income;

  const rev0 = pick(inc, "Revenue", y0);
  const rev1 = pick(inc, "Revenue", y1);
  const ni0 = pick(inc, "NetIncome", y0);
  const ni1 = pick(inc, "NetIncome", y1);
  const margin0 = rev0 && ni0 != null ? ni0 / rev0 : null;
  const margin1 = rev1 && ni1 != null ? ni1 / rev1 : null;
  const marginDeltaPp =
    margin0 != null && margin1 != null ? (margin0 - margin1) * 100 : null;

  return (
    <div className="mx-auto w-full max-w-5xl p-6">
      <PageHeader
        eyebrow={<Link href="/companies" className="hover:text-foreground">Companies</Link>}
        title={
          <span className="flex flex-wrap items-center gap-3">
            {company.name}
            <Chip variant="accent">{company.ticker}</Chip>
          </span>
        }
        description={
          [company.sector, company.industry].filter(Boolean).join(" · ") || "—"
        }
        actions={<WatchButton ticker={company.ticker} />}
      />

      {y0 ? (
        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <MetricCard
            label={`Revenue (FY${y0})`}
            value={fmtCompactUSD(rev0)}
            delta={<Delta value={pctChange(rev0, rev1)} />}
            hint="YoY"
          />
          <MetricCard
            label={`Net income (FY${y0})`}
            value={fmtCompactUSD(ni0)}
            delta={<Delta value={pctChange(ni0, ni1)} />}
            hint="YoY"
          />
          <MetricCard
            label={`Net margin (FY${y0})`}
            value={fmtPercent(margin0)}
            delta={
              marginDeltaPp != null ? (
                <Delta value={marginDeltaPp} suffix="pp" />
              ) : null
            }
            hint="vs prior"
          />
        </div>
      ) : null}

      <div className="mt-6 flex flex-col gap-4">
        <StatementTable
          title={STATEMENT_TITLES.income}
          rows={company.statements.income}
          years={company.years}
        />
        <StatementTable
          title={STATEMENT_TITLES.balance}
          rows={company.statements.balance}
          years={company.years}
        />
        <StatementTable
          title={STATEMENT_TITLES.cash_flow}
          rows={company.statements.cash_flow}
          years={company.years}
        />
        <FilingsCard filings={company.filings} />
      </div>

      <NotesPanel target={{ company: company.ticker }} className="mt-6" />
    </div>
  );
}
