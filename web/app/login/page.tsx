"use client";

import { signIn } from "next-auth/react";

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden>
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.47.9 11.43 0 9 0A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"
      />
    </svg>
  );
}

const STAGES = [
  { n: "01", label: "Planning", note: "4 files", state: "done" },
  { n: "02", label: "Architecting", note: "6 tasks", state: "done" },
  { n: "03", label: "Coding", note: "writing app.py", state: "live" },
];

export default function LoginPage() {
  return (
    <main className="mx-auto grid min-h-[calc(100vh-3.5rem)] max-w-6xl items-center gap-12 px-5 py-12 sm:px-8 lg:grid-cols-2">
      {/* Thesis / showcase */}
      <section className="order-2 lg:order-1">
        <p className="kicker">Build · watch it happen</p>
        <h1 className="font-display mt-4 text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl">
          Describe it.
          <br />
          Watch it get <span className="text-accent">built.</span>
        </h1>
        <p className="mt-5 max-w-md text-muted">
          One prompt becomes a running app, planned, architected, and coded by an agent you can
          watch, step by step.
        </p>

        <div className="panel mt-9 max-w-md p-5">
          <p className="kicker mb-4">The build pipeline</p>
          <ol className="relative">
            <span aria-hidden className="absolute left-[7px] top-1 bottom-1 w-px bg-line" />
            {STAGES.map((s) => (
              <li key={s.n} className="relative flex items-center gap-4 py-2.5 pl-7">
                <span
                  className={`absolute left-0 top-1/2 h-3.5 w-3.5 -translate-y-1/2 rounded-full border-2 ${
                    s.state === "live"
                      ? "pulse-live border-live bg-live"
                      : "border-accent bg-accent"
                  }`}
                />
                <span className="font-mono text-xs text-faint">{s.n}</span>
                <span className="text-sm text-ink">{s.label}</span>
                <span className="ml-auto font-mono text-xs text-muted">{s.note}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Sign in */}
      <section className="order-1 lg:order-2 lg:justify-self-end">
        <div className="panel w-full max-w-sm p-8">
          <h2 className="font-display text-xl font-semibold tracking-tight">Welcome</h2>
          <p className="mt-1.5 text-sm text-muted">Sign in to build and save your apps.</p>

          <button
            onClick={() => signIn("google", { callbackUrl: "/" })}
            className="btn-ghost mt-7 w-full"
          >
            <GoogleMark />
            Continue with Google
          </button>

          <p className="mt-5 text-center font-mono text-[0.7rem] leading-relaxed text-faint">
            Free to start · your generated apps stay private to your account
          </p>
        </div>
      </section>
    </main>
  );
}
