import Link from "next/link";

import { Logo } from "@/components/shell/logo";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
      <Logo />
      <div>
        <p className="tnum font-heading text-5xl font-semibold tracking-tight text-foreground">
          404
        </p>
        <p className="mt-2 text-muted-foreground">
          This page doesn’t exist.
        </p>
      </div>
      <Button nativeButton={false} render={<Link href="/" />}>
        Back to home
      </Button>
    </div>
  );
}
