import { useQuery } from "@tanstack/react-query";
import { listQuestions } from "../api/questions";

interface Props {
  activeId: number | null;
  onSelect: (id: number) => void;
}

/** Recent-questions feed; click a row to load it into the workspace. */
export default function Feed({ activeId, onSelect }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["questions"],
    queryFn: listQuestions,
  });

  if (isLoading) return <p className="text-sm text-slate-400">Loading feed…</p>;
  if (!data || data.length === 0)
    return (
      <p className="text-sm text-slate-400">
        No questions yet — ask one above.
      </p>
    );

  return (
    <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
      {data.map((q) => (
        <li key={q.id}>
          <button
            onClick={() => onSelect(q.id)}
            className={`flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-slate-50 ${
              q.id === activeId ? "bg-slate-50" : ""
            }`}
          >
            <span className="truncate text-slate-700">{q.text}</span>
            <span className="flex shrink-0 gap-1">
              {q.versions >= 2 && (
                <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-xs text-emerald-700">
                  V2
                </span>
              )}
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">
                {q.status}
              </span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
