import { Suspense } from "react";

import { CompanyGrid } from "@/components/company/company-grid";
import { PageHeader } from "@/components/primitives/page-header";
import { Skeleton } from "@/components/ui/skeleton";

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-[116px] rounded-xl" />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="mx-auto w-full max-w-6xl p-6">
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Your starter universe — real SEC financials for 10 companies. Open one to read its filings and ask grounded questions."
      />
      <div className="mt-6">
        <Suspense fallback={<GridSkeleton />}>
          <CompanyGrid />
        </Suspense>
      </div>
    </div>
  );
}
