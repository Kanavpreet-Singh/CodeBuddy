"use client";

import { useState } from "react";

type FileMeta = { path: string; purpose: string | null; sizeBytes: number | null };

export default function FileViewer({ appId, files }: { appId: string; files: FileMeta[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  async function open(path: string) {
    setSelected(path);
    setLoading(true);
    setContent("");
    try {
      const res = await fetch(`/api/backend/apps/${appId}/files?path=${encodeURIComponent(path)}`);
      if (res.ok) {
        const data = await res.json();
        setContent(data.content ?? "");
      } else {
        setContent(`Error loading file (${res.status})`);
      }
    } catch (err) {
      setContent(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  if (files.length === 0) {
    return <p className="mt-4 text-sm opacity-60">No files generated yet.</p>;
  }

  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-[220px_1fr]">
      <ul className="flex flex-col gap-1">
        {files.map((f) => (
          <li key={f.path}>
            <button
              onClick={() => open(f.path)}
              className={`w-full truncate rounded-md px-2 py-1.5 text-left font-mono text-xs transition-colors hover:bg-black/[.05] dark:hover:bg-white/[.06] ${
                selected === f.path ? "bg-black/[.06] dark:bg-white/[.08]" : ""
              }`}
              title={f.purpose ?? f.path}
            >
              {f.path}
            </button>
          </li>
        ))}
      </ul>
      <div className="min-h-[200px] overflow-auto rounded-lg border border-black/10 bg-black/[.02] p-4 dark:border-white/10 dark:bg-white/[.02]">
        {selected ? (
          loading ? (
            <p className="text-sm opacity-60">Loading…</p>
          ) : (
            <pre className="overflow-x-auto text-xs leading-relaxed">
              <code>{content}</code>
            </pre>
          )
        ) : (
          <p className="text-sm opacity-60">Select a file to view its contents.</p>
        )}
      </div>
    </div>
  );
}
