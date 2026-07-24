"use client";

import { useCallback, useEffect, useState } from "react";

type FileMeta = { path: string; purpose: string | null; sizeBytes: number | null };

export default function FileViewer({ appId, files }: { appId: string; files: FileMeta[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const open = useCallback(
    async (path: string) => {
      setSelected(path);
      setLoading(true);
      setContent("");
      setCopied(false);
      try {
        const res = await fetch(`/api/backend/apps/${appId}/files?path=${encodeURIComponent(path)}`);
        if (res.ok) {
          const data = await res.json();
          setContent(data.content ?? "");
        } else {
          setContent(`Could not load this file (${res.status}).`);
        }
      } catch (err) {
        setContent(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    },
    [appId],
  );

  useEffect(() => {
    if (files.length > 0) open(files[0].path);
  }, [files, open]);

  async function copy() {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  if (files.length === 0) {
    return (
      <div className="panel px-5 py-10 text-center text-sm text-muted">
        No files were generated for this app.
      </div>
    );
  }

  return (
    <div className="panel grid overflow-hidden sm:grid-cols-[minmax(180px,240px)_1fr]">
      {/* File rail */}
      <ul className="scroll-thin max-h-[220px] overflow-auto border-b border-line p-2 sm:max-h-[520px] sm:border-b-0 sm:border-r">
        {files.map((f) => {
          const active = selected === f.path;
          return (
            <li key={f.path}>
              <button
                onClick={() => open(f.path)}
                title={f.purpose ?? f.path}
                className={`flex w-full items-center gap-2 rounded-md border-l-2 px-2.5 py-1.5 text-left font-mono text-xs transition-colors ${
                  active
                    ? "border-accent bg-raised text-ink"
                    : "border-transparent text-muted hover:bg-raised/60 hover:text-ink"
                }`}
              >
                <span className="truncate">{f.path}</span>
              </button>
            </li>
          );
        })}
      </ul>

      {/* Code pane */}
      <div className="flex min-w-0 flex-col">
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-2.5">
          <code className="truncate font-mono text-xs text-muted">{selected}</code>
          <button
            onClick={copy}
            disabled={!content || loading}
            className="shrink-0 font-mono text-[0.7rem] text-faint transition-colors hover:text-ink disabled:opacity-40"
          >
            {copied ? "copied ✓" : "copy"}
          </button>
        </div>
        <div className="scroll-thin max-h-[520px] min-h-[220px] overflow-auto bg-[#0c0e14] p-4">
          {loading ? (
            <p className="font-mono text-xs text-faint">Loading…</p>
          ) : (
            <pre className="font-mono text-xs leading-relaxed text-ink/90">
              <code>{content}</code>
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
