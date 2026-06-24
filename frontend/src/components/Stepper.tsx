interface Props {
  hasV1: boolean;
  hasEvent: boolean;
  hasV2: boolean;
}

type Status = "done" | "active" | "todo";

function dot(status: Status): string {
  if (status === "done") return "bg-emerald-500 text-white";
  if (status === "active") return "bg-slate-800 text-white";
  return "bg-slate-200 text-slate-500";
}

/** 4-step progress indicator for the learning loop. */
export default function Stepper({ hasV1, hasEvent, hasV2 }: Props) {
  const steps: { label: string; status: Status }[] = [
    { label: "Ask", status: hasV1 ? "done" : "active" },
    {
      label: "Expert answer",
      status: hasEvent ? "done" : hasV1 ? "active" : "todo",
    },
    { label: "Learn", status: hasEvent ? "done" : "todo" },
    {
      label: "Re-run",
      status: hasV2 ? "done" : hasEvent ? "active" : "todo",
    },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      {steps.map((s, i) => (
        <div key={s.label} className="flex items-center gap-2">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${dot(
              s.status,
            )}`}
          >
            {s.status === "done" ? "✓" : i + 1}
          </span>
          <span
            className={
              s.status === "todo" ? "text-slate-400" : "text-slate-700"
            }
          >
            {s.label}
          </span>
          {i < steps.length - 1 && <span className="text-slate-300">→</span>}
        </div>
      ))}
    </div>
  );
}
