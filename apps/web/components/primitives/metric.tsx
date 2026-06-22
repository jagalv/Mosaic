import { TrendingDown, TrendingUp } from "lucide-react";

import { cn } from "@/lib/utils";

// A signed delta with a direction arrow. Green up / red down — deliberately not
// teal, so positive/negative reads instantly and never clashes with the accent.
export function Delta({
  value,
  suffix = "%",
  className,
}: {
  value: number | null | undefined;
  suffix?: string;
  className?: string;
}) {
  if (value == null || !Number.isFinite(value)) return null;
  const positive = value > 0;
  const zero = value === 0;
  const Icon = positive ? TrendingUp : TrendingDown;
  return (
    <span
      className={cn(
        "tnum inline-flex items-center gap-1 text-xs font-medium",
        zero
          ? "text-muted-foreground"
          : positive
            ? "text-success"
            : "text-destructive",
        className,
      )}
    >
      {!zero ? <Icon className="size-3.5" /> : null}
      {positive ? "+" : ""}
      {value.toFixed(1)}
      {suffix}
    </span>
  );
}

export function MetricCard({
  label,
  value,
  delta,
  hint,
  className,
}: {
  label: string;
  value: React.ReactNode;
  delta?: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-xl border border-border bg-card p-4",
        className,
      )}
    >
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="tnum mt-2 text-2xl font-semibold tracking-tight text-foreground">
        {value}
      </p>
      {delta || hint ? (
        <div className="mt-1.5 flex items-center gap-2">
          {delta}
          {hint ? (
            <span className="text-xs text-muted-foreground">{hint}</span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
