import { AuthForm } from "@/components/auth/auth-form";

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <AuthForm mode="signup" next={next ?? ""} />
    </main>
  );
}
