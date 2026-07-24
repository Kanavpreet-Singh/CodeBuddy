"use client";

import { signIn } from "next-auth/react";

export default function LoginPage() {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col items-center justify-center gap-6 px-6 py-16">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">CodeBuddy</h1>
        <p className="mt-2 text-sm opacity-70">Sign in to build and save your apps.</p>
      </div>
      <button
        onClick={() => signIn("google", { callbackUrl: "/" })}
        className="w-full rounded-lg border border-black/15 px-5 py-2.5 text-sm font-medium transition-colors hover:bg-black/[.04] dark:border-white/15 dark:hover:bg-white/[.06]"
      >
        Continue with Google
      </button>
    </main>
  );
}
