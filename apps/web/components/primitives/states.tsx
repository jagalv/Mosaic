import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/40 px-6 py-16 text-center",
        className,
      )}
    >
      {Icon ? (
        <span className="mb-4 flex size-11 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Icon className="size-5" />
        </span>
      ) : null}
      <h3 className="font-heading text-base font-semibold text-foreground">
        {title}
      </h3>
      {description ? (
        <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-16 text-center",
        className,
      )}
    >
      {Icon ? (
        <span className="mb-4 flex size-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <Icon className="size-5" />
        </span>
      ) : null}
      <h3 className="font-heading text-base font-semibold text-foreground">
        {title}
      </h3>
      {description ? (
        <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
