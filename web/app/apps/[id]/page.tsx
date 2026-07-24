import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { auth } from "@/auth";
import FileViewer from "@/components/FileViewer";
import FixPanel from "@/components/FixPanel";
import RunPanel from "@/components/RunPanel";
import StatusPill from "@/components/StatusPill";
import { apiFetch } from "@/lib/api";

type FileMeta = { path: string; purpose: string | null; sizeBytes: number | null };

type AppDetail = {
  id: string;
  name: string | null;
  description: string | null;
  techstack: string | null;
  features: string[];
  status: string;
  errorMessage: string | null;
  files: FileMeta[];
};

export default async function AppDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const session = await auth();
  if (!session?.user) redirect("/login");

  const { id } = await params;
  const res = await apiFetch(`apps/${id}`);
  if (res.status === 404) notFound();
  if (!res.ok) throw new Error(`Failed to load app (${res.status})`);
  const app: AppDetail = await res.json();

  return (
    <main className="mx-auto max-w-4xl px-5 py-12 sm:px-8">
      <Link href="/apps" className="font-mono text-xs text-muted transition-colors hover:text-ink">
        ← My apps
      </Link>

      <header className="mt-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">
            {app.name ?? "Untitled app"}
          </h1>
          {app.description && <p className="mt-2 max-w-xl text-muted">{app.description}</p>}
          {app.techstack && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {app.techstack.split(/[,·]/).map((t) => (
                <span key={t} className="chip">
                  {t.trim()}
                </span>
              ))}
            </div>
          )}
        </div>
        <StatusPill status={app.status} />
      </header>

      {app.status === "ERROR" && app.errorMessage && (
        <div className="mt-6 rounded-xl border border-danger/30 bg-danger/5 p-4">
          <p className="text-sm font-medium text-danger">This build failed</p>
          <p className="mt-2 break-words font-mono text-xs leading-relaxed text-danger/85">
            {app.errorMessage}
          </p>
        </div>
      )}

      {app.status === "DONE" && (
        <section className="mt-10">
          <p className="kicker mb-3">Run</p>
          <RunPanel appId={app.id} />
        </section>
      )}

      {(app.files?.length ?? 0) > 0 && (
        <section className="mt-10">
          <FixPanel appId={app.id} />
        </section>
      )}

      {app.features?.length > 0 && (
        <section className="mt-10">
          <p className="kicker mb-3">Features</p>
          <ul className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink">
            {app.features.map((f) => (
              <li key={f} className="flex items-center gap-2">
                <span className="h-1 w-1 rounded-full bg-accent" />
                {f}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-10">
        <p className="kicker mb-3">Files</p>
        <FileViewer appId={app.id} files={app.files ?? []} />
      </section>
    </main>
  );
}
