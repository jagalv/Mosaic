"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { AuthProvider } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import type { AuthUser } from "@/lib/api";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

// The persistent app frame: fixed sidebar + sticky top bar, with the sidebar
// collapsing to an off-canvas drawer under `md` (custom, no dependency). Wraps
// children in AuthProvider seeded with the server-fetched user.
export function AppShell({
  user,
  children,
}: {
  user: AuthUser | null;
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <AuthProvider user={user}>
      <div className="flex min-h-screen w-full">
      <Sidebar className="hidden md:flex" />

      {/* Mobile drawer */}
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute inset-y-0 left-0 flex">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-[-3rem] top-2 text-white hover:bg-white/10"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation"
            >
              <X />
            </Button>
          </div>
        </div>
      ) : null}

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar onMenu={() => setMobileOpen(true)} />
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </AuthProvider>
  );
}
