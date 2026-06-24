interface Props {
  value: number; // 0..1
}

/** A small labeled confidence meter, colored by level. */
export default function ConfidenceBar({ value }: Props) {
  const pct = Math.round(value * 100);
  const color =
    value >= 0.66
      ? "bg-emerald-500"
      : value >= 0.35
        ? "bg-amber-500"
        : "bg-red-500";
  return (
    <div className="w-full">
      <div className="mb-1 flex justify-between text-xs text-slate-500">
        <span>Confidence</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate-200">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
