"use client";

// Milestone 0 demo page. Polls the FastAPI /health endpoint and shows the
// service + DB status. This is the visible proof that the request path
// browser -> FastAPI -> Postgres -> browser works end to end.

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HealthState = "loading" | "ok" | "error";

interface Health {
  service: HealthState;
  db: HealthState;
  detail?: string;
}

function StatusBadge({ state }: { state: HealthState }) {
  if (state === "ok") return <Badge>ok</Badge>;
  if (state === "loading") return <Badge variant="secondary">…</Badge>;
  return <Badge variant="destructive">error</Badge>;
}

export default function Home() {
  const [health, setHealth] = useState<Health>({
    service: "loading",
    db: "loading",
  });
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
      // The API itself is unreachable (not running / wrong URL / CORS).
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
    <main className="flex flex-1 items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Mosaic</CardTitle>
          <CardDescription>Milestone 0 — skeleton health check</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">API</span>
            <StatusBadge state={health.service} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Database</span>
            <StatusBadge state={health.db} />
          </div>

          {health.detail ? (
            <p className="text-xs break-words text-muted-foreground">
              {health.detail}
            </p>
          ) : null}

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-muted-foreground">
              {checkedAt ? `Checked ${checkedAt}` : "Checking…"}
            </span>
            <Button size="sm" variant="outline" onClick={check}>
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
