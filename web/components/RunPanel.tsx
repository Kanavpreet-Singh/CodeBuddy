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
        let detail = `Run failed (${res.status})`;
        try {
          const body = await res.json();
          if (body?.detail) detail = body.detail;
        } catch {
          /* keep default */
        }
        throw new Error(detail);
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
    <div className="flex flex-col gap-4">
      {(state === "idle" || state === "starting" || state === "error") && (
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={run} disabled={busy} className="btn-primary">
            {busy ? (
              <>
                <Spinner /> Starting sandbox…
              </>
            ) : (
              <>▷ Run code</>
            )}
          </button>
          <span className="text-xs text-muted">Boots your app in an isolated cloud sandbox.</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-danger/30 bg-danger/5 p-4">
          <p className="text-sm font-medium text-danger">Couldn&apos;t run this app</p>
          <p className="mt-2 break-words font-mono text-xs leading-relaxed text-danger/85">{error}</p>
        </div>
      )}

      {state === "web" && previewUrl && (
        <div className="panel overflow-hidden">
          <div className="flex items-center gap-3 border-b border-line bg-raised px-3 py-2">
            <div className="flex gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-warn/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-live/70" />
            </div>
            <code className="min-w-0 flex-1 truncate rounded-md bg-ground px-2.5 py-1 font-mono text-[0.7rem] text-muted">
              {previewUrl}
            </code>
            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 font-mono text-[0.7rem] text-muted transition-colors hover:text-ink"
            >
              open ↗
            </a>
            <button
              onClick={stop}
              className="shrink-0 rounded-md border border-line px-2.5 py-1 font-mono text-[0.7rem] text-muted transition-colors hover:border-danger/50 hover:text-danger"
            >
              stop
            </button>
          </div>
          <iframe src={previewUrl} className="h-[480px] w-full bg-white" title="App preview" />
        </div>
      )}

      {state === "script" && (
        <div className="panel overflow-hidden">
          <div className="flex items-center gap-2 border-b border-line bg-raised px-4 py-2">
            <span className="h-2 w-2 rounded-full bg-live" />
            <span className="kicker">output</span>
            <button
              onClick={() => setState("idle")}
              className="ml-auto font-mono text-[0.7rem] text-faint transition-colors hover:text-ink"
            >
              clear
            </button>
          </div>
          <pre className="scroll-thin max-h-[400px] overflow-auto bg-[#0c0e14] p-4 font-mono text-xs leading-relaxed text-live/90">
            <code>{output || "(no output)"}</code>
          </pre>
        </div>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" className="animate-spin" aria-hidden>
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="2" opacity="0.25" fill="none" />
      <path d="M7 1.5a5.5 5.5 0 0 1 5.5 5.5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}
