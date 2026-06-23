import { NavLink, useLocation } from "react-router-dom";

const base = "rounded-lg px-3 py-1.5 text-sm font-medium";
const active = "bg-slate-800 text-white";
const idle = "text-slate-600 hover:bg-slate-100";

/** Top navigation bar: brand + Ask / Dashboard. */
export default function TopNav() {
  const { pathname } = useLocation();
  const onDashboard = pathname.startsWith("/dashboard");

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <NavLink to="/" className="font-bold text-slate-800">
          ORE
        </NavLink>
        <div className="flex gap-2">
          {/* "Ask" is active on / and /q/:id; only Dashboard owns /dashboard. */}
          <NavLink to="/" className={`${base} ${onDashboard ? idle : active}`}>
            Ask
          </NavLink>
          <NavLink
            to="/dashboard"
            className={`${base} ${onDashboard ? active : idle}`}
          >
            Dashboard
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
