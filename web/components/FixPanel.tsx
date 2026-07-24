"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

type ProgressResponse = {
  stage?: string;
  status?: string;
  message?: string;
};

type FixState = "idle" | "running" | "done" | "error";

const POLL_INTERVAL_MS = 1500;

export default function FixPanel({ appId }: { appId: string }) {
  const router = useRouter();
  const [feedback, setFeedback] = useState("");
  const [state, setState] = useState<FixState>("idle");
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  function startPolling() {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/backend/apps/${appId}/progress`);
        if (!res.ok) return;
        const data: ProgressResponse = await res.json();
        if (data.status === "DONE") {
          setState("done");
          stopPolling();
          setFeedback("");
          router.refresh();
        } else if (data.status === "ERROR") {
          setError(data.message ?? "The fix attempt failed.");
          setState("error");
          stopPolling();
        }
      } catch {
        // network hiccup — keep polling
      }
    }, POLL_INTERVAL_MS);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!feedback.trim() || state === "running") return;

    setState("running");
    setError(null);
    try {
      const res = await fetch(`/api/backend/apps/${appId}/fix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
      if (!res.ok) {
        let detail = `Request failed (${res.status})`;
        try {
          const body = await res.json();
          if (body?.detail) detail = body.detail;
        } catch {
          /* keep default */
        }
        throw new Error(detail);
      }
      startPolling();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setState("error");
    }
  }

  const running = state === "running";

  return (
    <form onSubmit={submit} className="panel overflow-hidden">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
        <span className={`h-2 w-2 rounded-full ${running ? "pulse-live bg-live" : "bg-line"}`} />
        <span className="kicker">ask ai to fix</span>
      </div>
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="What's wrong? e.g. “Opening the app shows Not Found” or paste an error message…"
        rows={2}
        disabled={running}
        className="w-full resize-y bg-transparent px-4 py-3 text-sm leading-relaxed text-ink outline-none placeholder:text-faint disabled:opacity-60"
      />
      <div className="flex items-center justify-between gap-3 border-t border-line px-3 py-3">
        <span className="text-xs text-muted">
          {running
            ? "Reading your files and applying a fix…"
            : state === "done"
              ? "Fixed — files refreshed below."
              : "The agent rereads your project and patches it."}
        </span>
        <button type="submit" disabled={running || !feedback.trim()} className="btn-ghost">
          {running ? (
            <>
              <Spinner /> Fixing…
            </>
          ) : (
            "Fix it"
          )}
        </button>
      </div>
      {error && (
        <div className="border-t border-danger/30 bg-danger/5 px-4 py-3">
          <p className="wrap-break-word font-mono text-xs leading-relaxed text-danger/85">{error}</p>
        </div>
      )}
    </form>
  );
}

function Spinner() {
  return (
    <svg width="12" height="12" viewBox="0 0 14 14" className="animate-spin" aria-hidden>
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="2" opacity="0.25" fill="none" />
      <path d="M7 1.5a5.5 5.5 0 0 1 5.5 5.5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}
