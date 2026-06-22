"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { Logo } from "./logo";
import { NAV, type NavItem } from "./nav-config";

function isActive(pathname: string, item: NavItem): boolean {
  if (item.href === "/dashboard") return pathname === "/dashboard";
  if (item.href === "/companies") {
    return pathname.startsWith("/companies") || pathname.startsWith("/company") || pathname.startsWith("/filing");
  }
  return pathname === item.href || pathname.startsWith(item.href + "/");
}

export function Sidebar({
  className,
  onNavigate,
}: {
  className?: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex w-60 shrink-0 flex-col gap-1 border-r border-sidebar-border bg-sidebar text-sidebar-foreground",
        className,
      )}
    >
      <div className="flex h-14 items-center px-4">
        <Link href="/" className="flex items-center" onClick={onNavigate}>
          <Logo />
        </Link>
      </div>

      <nav className="flex flex-col gap-0.5 px-3 py-2">
        {NAV.map((item) => {
          const active = isActive(pathname, item);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-primary/12 text-sidebar-primary"
                  : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground",
              )}
            >
              <Icon
                className={cn(
                  "size-4 shrink-0",
                  active ? "text-sidebar-primary" : "text-muted-foreground group-hover:text-sidebar-foreground",
                )}
              />
              <span className="flex-1">{item.label}</span>
              {item.soon ? (
                <span className="rounded-full border border-border px-1.5 py-px text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                  Soon
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-4 py-4 text-xs text-muted-foreground">
        <p className="font-medium text-foreground/80">Phase 1 · the wedge</p>
        <p className="mt-0.5">Grounded, cited filing Q&amp;A.</p>
      </div>
    </aside>
  );
}
