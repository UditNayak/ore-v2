import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }): string =>
  `rounded-lg px-3 py-1.5 text-sm font-medium ${
    isActive ? "bg-slate-800 text-white" : "text-slate-600 hover:bg-slate-100"
  }`;

/** Top navigation bar. */
export default function Nav() {
  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <span className="font-bold text-slate-800">ORE</span>
        <div className="flex gap-2">
          <NavLink to="/" className={linkClass} end>
            Ask
          </NavLink>
          <NavLink to="/dashboard" className={linkClass}>
            Dashboard
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
