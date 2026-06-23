import { useQuery } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";
import { listQuestions } from "../api/questions";

/** Recent-questions list for the sidebar; each row links to /q/:id. */
export default function Feed({ onNavigate }: { onNavigate?: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ["questions"],
    queryFn: listQuestions,
  });

  if (isLoading)
    return <p className="px-3 py-2 text-xs text-slate-400">Loading…</p>;
  if (!data || data.length === 0)
    return (
      <p className="px-3 py-2 text-xs text-slate-400">No questions yet.</p>
    );

  return (
    <ul className="space-y-0.5">
      {data.map((q) => (
        <li key={q.id}>
          <NavLink
            to={`/q/${q.id}`}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm ${
                isActive
                  ? "bg-slate-200 text-slate-900"
                  : "text-slate-600 hover:bg-slate-100"
              }`
            }
          >
            <span className="truncate">{q.text}</span>
            {q.versions >= 2 && (
              <span className="shrink-0 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700">
                V2
              </span>
            )}
          </NavLink>
        </li>
      ))}
    </ul>
  );
}
