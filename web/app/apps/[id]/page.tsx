import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { auth } from "@/auth";
import FileViewer from "@/components/FileViewer";
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
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <Link href="/apps" className="text-sm underline opacity-70 hover:opacity-100">
        ← My apps
      </Link>

      <div className="mt-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">{app.name ?? "Untitled app"}</h1>
        <span className="text-xs uppercase tracking-wide opacity-50">{app.status}</span>
      </div>
      {app.description && <p className="mt-1 text-sm opacity-70">{app.description}</p>}
      {app.techstack && (
        <p className="mt-2 text-xs uppercase tracking-wide opacity-50">{app.techstack}</p>
      )}

      {app.status === "ERROR" && app.errorMessage && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-600 dark:text-red-400">
          {app.errorMessage}
        </p>
      )}

      {app.features?.length > 0 && (
        <div className="mt-6">
          <h2 className="text-xs font-semibold uppercase tracking-wide opacity-50">Features</h2>
          <ul className="mt-1 list-disc pl-5 text-sm">
            {app.features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <h2 className="text-xs font-semibold uppercase tracking-wide opacity-50">Files</h2>
        <FileViewer appId={app.id} files={app.files ?? []} />
      </div>
    </main>
  );
}
