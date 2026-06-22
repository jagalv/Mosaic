"use client";

import { LogOut, Menu } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ThemeToggle } from "./theme-toggle";
import { TickerSearch } from "./ticker-search";

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onMenu}
        aria-label="Open navigation"
      >
        <Menu />
      </Button>

      <div className="w-full max-w-sm">
        <TickerSearch variant="bar" />
      </div>

      <div className="ml-auto flex items-center gap-1">
        <ThemeToggle />
        {user ? (
          <>
            <div className="ml-1 flex items-center gap-2 rounded-full border border-border py-1 pl-1 pr-3">
              <span className="flex size-6 items-center justify-center rounded-full bg-primary text-[11px] font-semibold text-primary-foreground">
                {user.email.slice(0, 2).toUpperCase()}
              </span>
              <span className="hidden max-w-[14ch] truncate text-sm font-medium sm:inline">
                {user.email}
              </span>
            </div>
            <Tooltip>
              <TooltipTrigger
                render={
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={logout}
                    aria-label="Log out"
                  />
                }
              >
                <LogOut />
              </TooltipTrigger>
              <TooltipContent>Log out</TooltipContent>
            </Tooltip>
          </>
        ) : (
          <Button
            variant="outline"
            nativeButton={false}
            render={
              <Link href={`/login?next=${encodeURIComponent(pathname)}`} />
            }
          >
            Log in
          </Button>
        )}
      </div>
    </header>
  );
}
