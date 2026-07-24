"use client";

import { useState } from "react";

type RunState = "idle" | "starting" | "web" | "script" | "error";

export default function RunPanel({ appId }: { appId: string }) {
  const [state, setState] = useState<RunState>("idle");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [sandboxId, setSandboxId] = useState<string | null>(null);
  const [output, setOutput] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setState("starting");
    setError(null);
    setOutput("");
    setPreviewUrl(null);
    try {
      const res = await fetch(`/api/backend/apps/${appId}/run`, { method: "POST" });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Run failed (${res.status})`);
      }
      const data = await res.json();
      setSandboxId(data.sandboxId ?? null);
      if (data.kind === "web") {
        setPreviewUrl(data.previewUrl ?? null);
        setState("web");
      } else {
        setOutput(data.output ?? "");
        setState("script");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setState("error");
    }
  }

  async function stop() {
    if (sandboxId) {
      await fetch(`/api/backend/apps/${appId}/run/${sandboxId}/stop`, { method: "POST" });
    }
    setState("idle");
    setPreviewUrl(null);
    setSandboxId(null);
  }

  const busy = state === "starting";

  return (
    <div className="mt-4 flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <button
          onClick={run}
          disabled={busy}
          className="rounded-lg bg-foreground px-4 py-2 text-sm font-medium text-background transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {busy ? "Starting sandbox…" : "Run code"}
        </button>
        {state === "web" && (
          <button
            onClick={stop}
            className="rounded-lg border border-black/15 px-4 py-2 text-sm transition-colors hover:bg-black/[.04] dark:border-white/15 dark:hover:bg-white/[.06]"
          >
            Stop
          </button>
        )}
      </div>

      {error && (
        <p className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      {state === "web" && previewUrl && (
        <div className="overflow-hidden rounded-lg border border-black/10 dark:border-white/10">
          <div className="flex items-center justify-between border-b border-black/10 px-3 py-1.5 text-xs dark:border-white/10">
            <span className="opacity-60">Live preview</span>
            <a href={previewUrl} target="_blank" rel="noopener noreferrer" className="underline opacity-70">
              Open in new tab ↗
            </a>
          </div>
          <iframe src={previewUrl} className="h-[480px] w-full bg-white" title="App preview" />
        </div>
      )}

      {state === "script" && (
        <pre className="max-h-[400px] overflow-auto rounded-lg border border-black/10 bg-black/[.02] p-4 text-xs leading-relaxed dark:border-white/10 dark:bg-white/[.02]">
          <code>{output}</code>
        </pre>
      )}
    </div>
  );
}
