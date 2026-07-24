const STATUS: Record<string, { label: string; dot: string; text: string }> = {
  DONE: { label: "Ready", dot: "bg-live", text: "text-live" },
  ERROR: { label: "Failed", dot: "bg-danger", text: "text-danger" },
  PENDING: { label: "Queued", dot: "bg-warn", text: "text-warn" },
  PLANNING: { label: "Planning", dot: "bg-warn", text: "text-warn" },
  ARCHITECTING: { label: "Architecting", dot: "bg-warn", text: "text-warn" },
  CODING: { label: "Coding", dot: "bg-warn", text: "text-warn" },
};

export default function StatusPill({ status }: { status: string }) {
  const s = STATUS[status] ?? { label: status, dot: "bg-muted", text: "text-muted" };
  const live = status !== "DONE" && status !== "ERROR";
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-raised px-2.5 py-1">
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot} ${live ? "pulse-live" : ""}`} />
      <span className={`font-mono text-[0.68rem] uppercase tracking-wider ${s.text}`}>{s.label}</span>
    </span>
  );
}
