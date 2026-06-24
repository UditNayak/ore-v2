interface Props {
  title: string;
  values: number[]; // y-values in order (oldest → newest)
  color?: string;
}

/** Minimal dependency-free SVG line chart for eval trends. */
export default function TrendChart({
  title,
  values,
  color = "#10b981",
}: Props) {
  const w = 280;
  const h = 80;
  const pad = 8;
  const max = Math.max(1, ...values);
  const min = Math.min(0, ...values);
  const span = max - min || 1;

  const points = values.map((v, i) => {
    const x = pad + (i * (w - 2 * pad)) / Math.max(1, values.length - 1);
    const y = h - pad - ((v - min) / span) * (h - 2 * pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-slate-600">{title}</h3>
        <span className="text-sm text-slate-800">
          {values.length ? values[values.length - 1].toFixed(2) : "—"}
        </span>
      </div>
      {values.length > 1 ? (
        <svg width={w} height={h} className="w-full">
          <polyline
            fill="none"
            stroke={color}
            strokeWidth="2"
            points={points.join(" ")}
          />
          {values.map((_, i) => {
            const [x, y] = points[i].split(",");
            return <circle key={i} cx={x} cy={y} r="2.5" fill={color} />;
          })}
        </svg>
      ) : (
        <p className="py-4 text-center text-xs text-slate-400">
          Need ≥2 runs to chart a trend.
        </p>
      )}
    </div>
  );
}
