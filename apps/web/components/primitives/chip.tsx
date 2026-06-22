import { cn } from "@/lib/utils";

// Small pill for metadata (sector, section code, form type). `accent` = teal
// (interactive/brand); `neutral` = quiet surface.
export function Chip({
  children,
  variant = "neutral",
  className,
}: {
  children: React.ReactNode;
  variant?: "neutral" | "accent";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        variant === "accent"
          ? "border-primary/30 bg-primary/10 text-primary"
          : "border-border bg-secondary text-secondary-foreground",
        className,
      )}
    >
      {children}
    </span>
  );
}
