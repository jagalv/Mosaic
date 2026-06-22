"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/shell/logo";
import { Button } from "@/components/ui/button";
import { login, signup } from "@/lib/client-api";

const COPY = {
  login: {
    title: "Welcome back",
    subtitle: "Log in to your research workspace.",
    submit: "Log in",
    alt: "Need an account?",
    altHref: "/signup",
    altLabel: "Sign up",
  },
  signup: {
    title: "Create your account",
    subtitle: "Start saving watchlists and notes.",
    submit: "Sign up",
    alt: "Already have an account?",
    altHref: "/login",
    altLabel: "Log in",
  },
} as const;

export function AuthForm({
  mode,
  next,
}: {
  mode: "login" | "signup";
  next: string;
}) {
  const router = useRouter();
  const copy = COPY[mode];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      if (mode === "login") await login(email, password);
      else await signup(email, password);
      // Re-render the server tree so the (app) layout re-reads the new cookie.
      router.push(next || "/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false); // on success we navigate away, so only reset on error
    }
  }

  const altHref = next ? `${copy.altHref}?next=${encodeURIComponent(next)}` : copy.altHref;

  return (
    <div className="w-full max-w-sm">
      <div className="mb-8 flex justify-center">
        <Link href="/" aria-label="Mosaic home">
          <Logo />
        </Link>
      </div>
      <div className="rounded-xl border border-border bg-card p-6">
        <h1 className="font-heading text-xl font-semibold tracking-tight text-foreground">
          {copy.title}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">{copy.subtitle}</p>

        <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Email</span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Password</span>
            <input
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
              minLength={mode === "signup" ? 8 : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/40"
            />
            {mode === "signup" ? (
              <span className="text-xs text-muted-foreground">
                At least 8 characters.
              </span>
            ) : null}
          </label>

          {error ? (
            <p
              role="alert"
              className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
            >
              {error}
            </p>
          ) : null}

          <Button type="submit" size="lg" className="mt-1 w-full" disabled={loading}>
            {loading ? "Please wait…" : copy.submit}
          </Button>
        </form>
      </div>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        {copy.alt}{" "}
        <Link href={altHref} className="font-medium text-primary underline-offset-4 hover:underline">
          {copy.altLabel}
        </Link>
      </p>
    </div>
  );
}
