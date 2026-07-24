"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type PlanFile = { path: string; purpose: string };

type Plan = {
  name: string;
  description: string;
  techstack: string;
  features: string[];
  files: PlanFile[];
};

type ModelOption = { id: string; label: string };

type Usage = { model: string; inputTokens: number; outputTokens: number; estimatedCostInr: number };

type Status = "idle" | "running" | "done" | "error";

type StageState = "pending" | "active" | "done";

const EXAMPLES = ["a todo app", "markdown notes with search", "a url shortener", "a pomodoro timer"];

export default function GenerateForm() {
  const [prompt, setPrompt] = useState("");
  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [stepCount, setStepCount] = useState<number | null>(null);
  const [coder, setCoder] = useState<{ step: number; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [appId, setAppId] = useState<string | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);

  const running = status === "running";

  useEffect(() => {
    fetch("/api/backend/models")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!d) return;
        setModels(d.models ?? []);
        setSelectedModel(d.default ?? d.models?.[0]?.id ?? "");
      })
      .catch(() => {});
  }, []);

  function handleBlock(block: string) {
    let eventName = "message";
    const dataLines: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith(":")) continue;
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (dataLines.length === 0) return;

    let data: Record<string, unknown>;
    try {
      data = JSON.parse(dataLines.join("\n"));
    } catch {
      return;
    }

    if (eventName === "created") {
      setAppId((data.id as string) ?? null);
    } else if (eventName === "node") {
      if (data.node === "planner" && data.plan) setPlan(data.plan as Plan);
      else if (data.node === "architect") setStepCount(data.stepCount as number);
      else if (data.node === "coder") setCoder({ step: data.step as number, total: data.total as number });
    } else if (eventName === "usage") {
      setUsage(data as unknown as Usage);
    } else if (eventName === "done") {
      if (data.status === "ERROR") {
        setError((data.message as string) ?? "Something went wrong.");
        setStatus("error");
      } else {
        setStatus("done");
        setAppId((data.id as string) ?? appId);
      }
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || running) return;

    setStatus("running");
    setPlan(null);
    setStepCount(null);
    setCoder(null);
    setError(null);
    setAppId(null);
    setUsage(null);

    try {
      const res = await fetch(`/api/backend/apps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, model: selectedModel || undefined }),
      });
      if (!res.ok || !res.body) throw new Error(`Request failed (${res.status})`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";
        for (const block of blocks) handleBlock(block);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStatus("error");
    }
  }

  const done = status === "done";
  const plannerState: StageState = plan ? "done" : running ? "active" : "pending";
  const architectState: StageState =
    stepCount !== null ? "done" : running && plan ? "active" : "pending";
  const coderState: StageState = done ? "done" : running && stepCount !== null ? "active" : "pending";

  return (
    <div className="mt-10 flex flex-col gap-6">
      {/* Build console */}
      <form onSubmit={handleSubmit} className="panel overflow-hidden">
        <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-line" />
          <span className="kicker">new build</span>
        </div>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the app you want to build…"
          rows={3}
          disabled={running}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(e);
          }}
          className="w-full resize-y bg-transparent px-4 py-4 text-[0.98rem] leading-relaxed text-ink outline-none placeholder:text-faint disabled:opacity-60"
        />
        <div className="flex items-center justify-between gap-3 border-t border-line px-3 py-3">
          <label className="flex items-center gap-2 rounded-lg border border-line bg-raised px-2.5 py-1.5">
            <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
              <rect x="6" y="0.7" width="7.5" height="7.5" rx="1.2" transform="rotate(45 6 0.7)" fill="var(--color-accent)" />
            </svg>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={running || models.length === 0}
              aria-label="Model"
              className="cursor-pointer bg-transparent font-mono text-xs text-ink outline-none disabled:opacity-60"
            >
              {models.length === 0 && <option>loading…</option>}
              {models.map((m) => (
                <option key={m.id} value={m.id} className="bg-panel text-ink">
                  {m.label}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={running || !prompt.trim()} className="btn-primary">
            {running ? (
              <>
                <Spinner /> Building…
              </>
            ) : (
              <>
                Build
                <span aria-hidden>→</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Examples (idle only) */}
      {status === "idle" && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="kicker mr-1">try</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setPrompt(ex)}
              className="chip transition-colors hover:border-accent/50 hover:text-ink"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {/* Pipeline */}
      {status !== "idle" && (
        <div className="panel animate-rise p-5 sm:p-6">
          <p className="kicker mb-5">Build pipeline</p>
          <ol className="relative">
            <span aria-hidden className="absolute left-[7px] top-2 bottom-2 w-px bg-line" />
            <Stage n="01" label="Planning" state={plannerState} note={plan ? "plan ready" : "reading your idea"} />
            <Stage
              n="02"
              label="Architecting"
              state={architectState}
              note={stepCount !== null ? `${stepCount} tasks` : "breaking into tasks"}
            />
            <Stage
              n="03"
              label="Coding"
              state={coderState}
              note={
                coder
                  ? `${Math.min(coder.step, coder.total)} / ${coder.total} files`
                  : "writing files"
              }
            />
          </ol>

          {usage && (
            <p className="mt-5 border-t border-line pt-4 font-mono text-[0.72rem] text-faint">
              {usage.model} · {usage.inputTokens.toLocaleString()} in · {usage.outputTokens.toLocaleString()} out
              {usage.estimatedCostInr > 0 && <> · ~₹{usage.estimatedCostInr.toFixed(3)}</>}
            </p>
          )}

          {done && appId && (
            <Link href={`/apps/${appId}`} className="btn-primary mt-5">
              Open your app →
            </Link>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="animate-rise rounded-xl border border-danger/30 bg-danger/5 p-4">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-danger" />
            <p className="text-sm font-medium text-danger">Build failed</p>
          </div>
          <p className="mt-2 break-words font-mono text-xs leading-relaxed text-danger/85">{error}</p>
          <p className="mt-3 text-xs text-muted">
            Try a different model from the selector above, then build again.
          </p>
        </div>
      )}

      {/* Plan */}
      {plan && (
        <div className="panel animate-rise p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="font-display text-lg font-semibold tracking-tight">{plan.name}</h2>
              <p className="mt-1 max-w-lg text-sm text-muted">{plan.description}</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {plan.techstack.split(/[,·]/).map((t) => (
                <span key={t} className="chip">
                  {t.trim()}
                </span>
              ))}
            </div>
          </div>

          <p className="kicker mt-6 mb-2">Features</p>
          <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-ink">
            {plan.features.map((f) => (
              <li key={f} className="flex items-center gap-2">
                <span className="h-1 w-1 rounded-full bg-accent" />
                {f}
              </li>
            ))}
          </ul>

          <p className="kicker mt-6 mb-2">Files</p>
          <ul className="divide-y divide-line/70 overflow-hidden rounded-lg border border-line">
            {plan.files.map((f) => (
              <li key={f.path} className="flex items-baseline gap-3 px-3 py-2">
                <code className="font-mono text-xs text-accent">{f.path}</code>
                <span className="truncate text-xs text-muted">{f.purpose}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function Stage({
  n,
  label,
  state,
  note,
}: {
  n: string;
  label: string;
  state: StageState;
  note: string;
}) {
  const dot =
    state === "done"
      ? "border-accent bg-accent"
      : state === "active"
        ? "pulse-live border-live bg-live"
        : "border-line bg-panel";
  return (
    <li className="relative flex items-center gap-4 py-2.5 pl-7">
      <span className={`absolute left-0 top-1/2 h-3.5 w-3.5 -translate-y-1/2 rounded-full border-2 ${dot}`} />
      <span className="font-mono text-xs text-faint">{n}</span>
      <span className={`text-sm ${state === "pending" ? "text-muted" : "text-ink"}`}>{label}</span>
      <span className="ml-auto font-mono text-xs text-muted">
        {state === "done" ? "done" : state === "active" ? note : ""}
      </span>
    </li>
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
