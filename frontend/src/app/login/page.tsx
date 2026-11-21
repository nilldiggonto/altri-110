import { LoginPicker } from "@/components/shell/login-picker"

export default function LoginPage() {
  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center gap-6 px-4 py-12">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Sign in to altri</h1>
        <p className="text-sm text-muted-foreground">Pick a seeded user. Roles decide what you can change.</p>
      </div>
      <LoginPicker />
    </main>
  )
}
