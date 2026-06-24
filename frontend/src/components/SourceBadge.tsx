// Single source of truth for source-type colors across the UI.
const SOURCE_COLORS: Record<string, string> = {
  doc: "bg-blue-100 text-blue-700",
  issue: "bg-purple-100 text-purple-700",
  slack: "bg-green-100 text-green-700",
  commit: "bg-orange-100 text-orange-700",
  learning: "bg-pink-100 text-pink-700",
};

export default function SourceBadge({ type }: { type: string }) {
  const cls = SOURCE_COLORS[type] ?? "bg-slate-100 text-slate-700";
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>
      {type}
    </span>
  );
}
