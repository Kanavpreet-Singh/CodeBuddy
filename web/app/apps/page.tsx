import Link from "next/link";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import { apiFetch } from "@/lib/api";

type AppRow = {
  id: string;
  name: string | null;
  description: string | null;
  techstack: string | null;
  status: string;
  createdAt: string;
};

export default async function AppsPage() {
  const session = await auth();
  if (!session?.user) redirect("/login");

  const res = await apiFetch("apps");
  const apps: AppRow[] = res.ok ? await res.json() : [];

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-16">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">My apps</h1>
        <Link href="/" className="text-sm underline opacity-70 hover:opacity-100">
          + New app
        </Link>
      </div>

      {apps.length === 0 ? (
        <p className="mt-8 text-sm opacity-60">No apps yet. Build your first one.</p>
      ) : (
        <ul className="mt-8 flex flex-col gap-3">
          {apps.map((app) => (
            <li key={app.id}>
              <Link
                href={`/apps/${app.id}`}
                className="block rounded-xl border border-black/10 p-4 transition-colors hover:bg-black/[.03] dark:border-white/10 dark:hover:bg-white/[.04]"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{app.name ?? "Untitled app"}</span>
                  <span className="text-xs uppercase tracking-wide opacity-50">{app.status}</span>
                </div>
                {app.description && <p className="mt-1 text-sm opacity-70">{app.description}</p>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
