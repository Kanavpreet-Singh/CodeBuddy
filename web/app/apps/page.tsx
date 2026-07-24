import Link from "next/link";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import StatusPill from "@/components/StatusPill";
import { apiFetch } from "@/lib/api";

type AppRow = {
  id: string;
  name: string | null;
  description: string | null;
  techstack: string | null;
  status: string;
  createdAt: string;
};

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const s = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (s < 45) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d} d ago`;
  return new Date(iso).toLocaleDateString();
}

export default async function AppsPage() {
  const session = await auth();
  if (!session?.user) redirect("/login");

  const res = await apiFetch("apps");
  const apps: AppRow[] = res.ok ? await res.json() : [];

  return (
    <main className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="kicker">Your workspace</p>
          <h1 className="font-display mt-3 text-3xl font-semibold tracking-tight">My apps</h1>
        </div>
        <Link href="/" className="btn-primary">
          + New build
        </Link>
      </div>

      {apps.length === 0 ? (
        <div className="panel mt-10 flex flex-col items-center justify-center px-6 py-20 text-center">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden>
            <rect
              x="20"
              y="3"
              width="24"
              height="24"
              rx="4"
              transform="rotate(45 20 3)"
              stroke="var(--color-line)"
              strokeWidth="1.6"
            />
            <circle cx="20" cy="20" r="3.5" fill="var(--color-accent)" opacity="0.7" />
          </svg>
          <h2 className="font-display mt-5 text-lg font-semibold">No builds yet</h2>
          <p className="mt-1.5 max-w-xs text-sm text-muted">
            Describe an app and the agent will plan, architect, and code it for you.
          </p>
          <Link href="/" className="btn-primary mt-6">
            Start your first build →
          </Link>
        </div>
      ) : (
        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {apps.map((app) => (
            <li key={app.id}>
              <Link
                href={`/apps/${app.id}`}
                className="panel group flex h-full flex-col p-5 transition-all hover:-translate-y-0.5 hover:border-accent/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-display text-base font-semibold leading-snug tracking-tight">
                    {app.name ?? "Untitled app"}
                  </h3>
                  <StatusPill status={app.status} />
                </div>
                {app.description && (
                  <p className="mt-2 line-clamp-2 text-sm text-muted">{app.description}</p>
                )}
                <div className="mt-auto flex items-center justify-between gap-2 pt-5">
                  <span className="truncate font-mono text-[0.7rem] text-faint">
                    {app.techstack ?? "—"}
                  </span>
                  <span className="shrink-0 font-mono text-[0.7rem] text-faint">
                    {relativeTime(app.createdAt)}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
