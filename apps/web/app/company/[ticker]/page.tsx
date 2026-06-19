// Company page (server component). Renders header + 3 financial statement
// tables, years as columns, from the API's pivoted data. No AI, no auth.

import Link from "next/link";
import { notFound } from "next/navigation";

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
import {
  fetchCompany,
  type FilingSummary,
  type LineItemRow,
} from "@/lib/api";

// Machine line-item names -> human labels.
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

// Values are actual USD; show in millions. Negatives in parentheses, gaps as —.
function fmtMillions(value: number | undefined): string {
  if (value === undefined) return "—";
  const millions = Math.round(value / 1_000_000);
  if (millions < 0) return `(${Math.abs(millions).toLocaleString("en-US")})`;
  return millions.toLocaleString("en-US");
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
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-48">USD millions</TableHead>
              {years.map((y) => (
                <TableHead key={y} className="text-right tabular-nums">
                  FY{y}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.line_item}>
                <TableCell className="font-medium">
                  {LABELS[row.line_item] ?? row.line_item}
                </TableCell>
                {years.map((y) => (
                  <TableCell key={y} className="text-right tabular-nums">
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
      <CardHeader>
        <CardTitle className="text-base">Filings</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-24">Form</TableHead>
              <TableHead className="w-32">Filed</TableHead>
              <TableHead>Document</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filings.map((f) => (
              <TableRow key={f.accession_no}>
                <TableCell className="font-medium">{f.form_type}</TableCell>
                <TableCell className="tabular-nums">{f.filing_date ?? "—"}</TableCell>
                <TableCell>
                  {f.has_document ? (
                    <Link
                      href={`/filing/${f.accession_no}`}
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      Read
                      {f.section_count > 0
                        ? ` · ${f.section_count} sections`
                        : ""}
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

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">
          {company.name}{" "}
          <span className="text-muted-foreground">({company.ticker})</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          {[company.sector, company.industry].filter(Boolean).join(" · ") ||
            "—"}
        </p>
      </header>

      <div className="flex flex-col gap-6">
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
    </main>
  );
}
