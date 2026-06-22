"use client";

import { CircleAlert } from "lucide-react";

import { ErrorState } from "@/components/primitives/states";
import { Button } from "@/components/ui/button";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-3xl p-6">
      <ErrorState
        icon={CircleAlert}
        title="Something went wrong"
        description="The API may be unreachable. Make sure the backend is running, then retry."
        action={<Button onClick={reset}>Retry</Button>}
      />
    </div>
  );
}
