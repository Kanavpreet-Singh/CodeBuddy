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

type Phase = "pending" | "active" | "done";

function phaseState(reached: boolean, active: boolean): Phase {
  if (reached) return "done";
  return active ? "active" : "pending";
}

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
      if (line.startsWith(":")) continue; // SSE comment / heartbeat
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
      if (data.node === "planner" && data.plan) {
        setPlan(data.plan as Plan);
      } else if (data.node === "architect") {
        setStepCount(data.stepCount as number);
      } else if (data.node === "coder") {
        setCoder({ step: data.step as number, total: data.total as number });
      }
    } else if (eventName === "usage") {
      setUsage(data as unknown as Usage);
    } else if (eventName === "done") {
      if (data.status === "ERROR") {
        setError((data.message as string) ?? "Unknown error");
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
      if (!res.ok || !res.body) {
        throw new Error(`Request failed: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? ""; // keep the incomplete trailing block
        for (const block of blocks) handleBlock(block);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStatus("error");
    }
  }

  const plannerPhase = phaseState(plan !== null, running);
  const architectPhase = phaseState(stepCount !== null, running && plan !== null);
  const coderDone = status === "done";
  const coderPhase = phaseState(coderDone, running && stepCount !== null);

  return (
    <div className="mt-8 flex flex-col gap-8">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the app you want, e.g. 'A CLI todo app in Python'"
          rows={3}
          disabled={running}
          className="w-full resize-y rounded-lg border border-black/15 bg-transparent px-4 py-3 text-sm outline-none focus:border-black/40 disabled:opacity-60 dark:border-white/15 dark:focus:border-white/40"
        />
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={running || !prompt.trim()}
            className="rounded-lg bg-foreground px-5 py-2.5 text-sm font-medium text-background transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {running ? "Building…" : "Build it"}
          </button>
          <label className="flex items-center gap-2 text-xs opacity-70">
            Model
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={running || models.length === 0}
              className="rounded-md border border-black/15 bg-transparent px-2 py-1.5 text-xs outline-none disabled:opacity-60 dark:border-white/15"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </form>

      {status !== "idle" && (
        <div className="flex flex-col gap-4">
          <ol className="flex flex-col gap-3">
            <PhaseRow phase={plannerPhase} label="Planning" />
            <PhaseRow
              phase={architectPhase}
              label="Architecting"
              detail={stepCount !== null ? `${stepCount} tasks` : undefined}
            />
            <PhaseRow
              phase={coderPhase}
              label="Coding"
              detail={coder ? `${Math.min(coder.step, coder.total)} / ${coder.total} files` : undefined}
            />
          </ol>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-600 dark:text-red-400">
              <p className="break-words">{error}</p>
              <p className="mt-2 text-xs opacity-80">
                Tip: try a different model from the dropdown above and build again.
              </p>
            </div>
          )}

          {usage && (
            <p className="text-xs opacity-60">
              {usage.model} · {usage.inputTokens.toLocaleString()} in /{" "}
              {usage.outputTokens.toLocaleString()} out
              {usage.estimatedCostInr > 0 && <> · ~₹{usage.estimatedCostInr.toFixed(3)}</>}
            </p>
          )}

          {coderDone && appId && (
            <p className="text-sm text-green-700 dark:text-green-400">
              Done.{" "}
              <Link href={`/apps/${appId}`} className="underline">
                Open your app →
              </Link>
            </p>
          )}
        </div>
      )}

      {plan && (
        <div className="rounded-xl border border-black/10 p-5 dark:border-white/10">
          <h2 className="text-base font-semibold">{plan.name}</h2>
          <p className="mt-1 text-sm opacity-70">{plan.description}</p>
          <p className="mt-2 text-xs uppercase tracking-wide opacity-50">{plan.techstack}</p>

          <h3 className="mt-4 text-xs font-semibold uppercase tracking-wide opacity-50">Features</h3>
          <ul className="mt-1 list-disc pl-5 text-sm">
            {plan.features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>

          <h3 className="mt-4 text-xs font-semibold uppercase tracking-wide opacity-50">Files</h3>
          <ul className="mt-1 flex flex-col gap-1 text-sm">
            {plan.files.map((f) => (
              <li key={f.path}>
                <code className="font-mono text-xs">{f.path}</code>
                <span className="opacity-60"> — {f.purpose}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PhaseRow({ phase, label, detail }: { phase: Phase; label: string; detail?: string }) {
  const dot =
    phase === "done"
      ? "bg-green-500"
      : phase === "active"
        ? "animate-pulse bg-amber-500"
        : "bg-black/20 dark:bg-white/20";
  return (
    <li className="flex items-center gap-3 text-sm">
      <span className={`h-2.5 w-2.5 rounded-full ${dot}`} />
      <span className={phase === "pending" ? "opacity-50" : ""}>{label}</span>
      {detail && <span className="opacity-50">· {detail}</span>}
    </li>
  );
}
