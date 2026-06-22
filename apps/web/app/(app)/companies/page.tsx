import { Suspense } from "react";

import { CompanyGrid } from "@/components/company/company-grid";
import { PageHeader } from "@/components/primitives/page-header";
import { Skeleton } from "@/components/ui/skeleton";

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 9 }).map((_, i) => (
        <Skeleton key={i} className="h-[116px] rounded-xl" />
      ))}
    </div>
  );
}

export default function CompaniesPage() {
  return (
    <div className="mx-auto w-full max-w-6xl p-6">
      <PageHeader
        eyebrow="Corpus"
        title="Companies"
        description="The companies currently ingested into Mosaic."
      />
      <div className="mt-6">
        <Suspense fallback={<GridSkeleton />}>
          <CompanyGrid />
        </Suspense>
      </div>
    </div>
  );
}
