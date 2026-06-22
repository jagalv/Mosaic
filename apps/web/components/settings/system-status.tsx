"use client";

// The Milestone 0 health check, re-homed in Settings: browser -> FastAPI ->
// Postgres -> browser, proving the request path end to end.

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HealthState = "loading" | "ok" | "error";

function StatusBadge({ state }: { state: HealthState }) {
  if (state === "ok")
    return (
      <Badge className="border-success/30 bg-success/10 text-success">ok</Badge>
    );
  if (state === "loading") return <Badge variant="secondary">…</Badge>;
  return <Badge variant="destructive">error</Badge>;
}

export function SystemStatus() {
  const [health, setHealth] = useState<{
    service: HealthState;
    db: HealthState;
    detail?: string;
  }>({ service: "loading", db: "loading" });
  const [checkedAt, setCheckedAt] = useState<string | null>(null);

  const check = useCallback(async () => {
    setHealth({ service: "loading", db: "loading" });
    try {
      const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
      const data = await res.json();
      setHealth({
        service: data.service === "ok" ? "ok" : "error",
        db: data.db === "ok" ? "ok" : "error",
        detail: data.detail,
      });
    } catch {
      setHealth({
        service: "error",
        db: "error",
        detail: `Could not reach API at ${API_URL}`,
      });
    }
    setCheckedAt(new Date().toLocaleTimeString());
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">API</span>
        <StatusBadge state={health.service} />
      </div>
      <div className="h-px bg-border" />
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Database</span>
        <StatusBadge state={health.db} />
      </div>
      {health.detail ? (
        <p className="text-xs break-words text-muted-foreground">
          {health.detail}
        </p>
      ) : null}
      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-muted-foreground">
          {checkedAt ? `Checked ${checkedAt}` : "Checking…"}
        </span>
        <Button size="sm" variant="outline" onClick={check}>
          Refresh
        </Button>
      </div>
    </div>
  );
}
