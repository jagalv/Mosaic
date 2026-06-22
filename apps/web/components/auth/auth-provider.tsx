"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext } from "react";

import type { AuthUser } from "@/lib/api";
import { logout as apiLogout } from "@/lib/client-api";

interface AuthContextValue {
  user: AuthUser | null;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Seeded with the user the (app) layout fetched server-side — no client
// re-fetch. `user` is null for anonymous visitors (browse is public); only the
// personal pages/actions gate on it.
export function AuthProvider({
  user,
  children,
}: {
  user: AuthUser | null;
  children: React.ReactNode;
}) {
  const router = useRouter();

  async function logout() {
    try {
      await apiLogout();
    } finally {
      router.push("/login");
      router.refresh();
    }
  }

  return (
    <AuthContext.Provider value={{ user, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
