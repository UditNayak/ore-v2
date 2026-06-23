import { useQuery } from "@tanstack/react-query";
import { getModels } from "../api/questions";

/** Compact "models in use" legend: each agent/component → its model. */
export default function ModelsLegend() {
  const { data } = useQuery({ queryKey: ["models"], queryFn: getModels });
  if (!data) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs">
      <span className="font-semibold text-slate-500">Models in use:</span>
      {data.agents.map((a) => (
        <span key={a.agent} className="flex items-center gap-1">
          <span className="text-slate-600">{a.agent}</span>
          <span className="rounded bg-violet-100 px-1.5 py-0.5 font-medium text-violet-700">
            {a.model}
          </span>
        </span>
      ))}
    </div>
  );
}
