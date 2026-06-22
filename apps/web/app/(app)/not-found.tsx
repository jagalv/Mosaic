import { SearchX } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/primitives/states";
import { Button } from "@/components/ui/button";

export default function AppNotFound() {
  return (
    <div className="mx-auto w-full max-w-3xl p-6">
      <EmptyState
        icon={SearchX}
        title="Not found"
        description="We couldn’t find that company or filing. It may not be in the corpus yet."
        action={
          <Button nativeButton={false} render={<Link href="/dashboard" />}>
            Go to dashboard
          </Button>
        }
      />
    </div>
  );
}
