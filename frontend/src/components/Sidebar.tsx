import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Feed from "./Feed";

const STORAGE_KEY = "ore.sidebar.open";

/** Collapsible "Recent questions" sidebar (state persisted). Nav lives in the top bar. */
export default function Sidebar() {
  const navigate = useNavigate();
  const [open, setOpen] = useState<boolean>(
    () => (localStorage.getItem(STORAGE_KEY) ?? "true") === "true",
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(open));
  }, [open]);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="Show recent questions"
        className="fixed left-3 top-[68px] z-20 rounded-md border border-slate-300 bg-white px-2 py-1 text-slate-600 shadow-sm hover:bg-slate-100"
      >
        ☰
      </button>
    );
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center justify-between px-3 py-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Recent questions
        </span>
        <button
          onClick={() => setOpen(false)}
          title="Collapse"
          className="rounded-md px-2 py-1 text-slate-400 hover:bg-slate-100"
        >
          ‹
        </button>
      </div>

      <div className="px-3">
        <button
          onClick={() => navigate("/")}
          className="mb-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          ＋ New question
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        <Feed />
      </div>
    </aside>
  );
}
