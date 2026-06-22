import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/primitives/page-header";
import { SystemStatus } from "@/components/settings/system-status";
import { ThemeToggle } from "@/components/shell/theme-toggle";

export default function SettingsPage() {
  return (
    <div className="mx-auto w-full max-w-3xl p-6">
      <PageHeader
        eyebrow="Preferences"
        title="Settings"
        description="Appearance, system status, and app info."
      />

      <div className="mt-6 flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>
              Mosaic is dark by default. Your choice is saved on this device.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Theme</span>
              <ThemeToggle />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System status</CardTitle>
            <CardDescription>
              Live health check — browser → FastAPI → Postgres → browser.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SystemStatus />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
            <CardDescription>
              Phase 1 — the &ldquo;Ask this filing&rdquo; wedge.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Grounded, cited, numbers-guarded Q&amp;A over real SEC filings.
              Local embeddings, hybrid retrieval, and a runtime numbers guard
              keep every figure traceable to its source. Research tool, not
              investment advice.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
