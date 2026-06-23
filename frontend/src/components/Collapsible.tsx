import { useState } from "react";

interface Props {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

/** A small disclosure: clickable header toggles the body. Collapsed by default. */
export default function Collapsible({
  title,
  defaultOpen = false,
  children,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-600"
      >
        <span className={`transition-transform ${open ? "rotate-90" : ""}`}>
          ›
        </span>
        {title}
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  );
}
