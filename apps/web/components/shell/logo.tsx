import { cn } from "@/lib/utils";

// Mosaic wordmark: a small tile grid (one teal accent tile) + the name.
export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        aria-hidden="true"
        className="shrink-0"
      >
        <rect x="2" y="2" width="9" height="9" rx="2.5" className="fill-primary" />
        <rect x="13" y="2" width="9" height="9" rx="2.5" className="fill-foreground/25" />
        <rect x="2" y="13" width="9" height="9" rx="2.5" className="fill-foreground/25" />
        <rect x="13" y="13" width="9" height="9" rx="2.5" className="fill-primary/60" />
      </svg>
      <span className="font-heading text-[15px] font-semibold tracking-tight text-foreground">
        Mosaic
      </span>
    </span>
  );
}
