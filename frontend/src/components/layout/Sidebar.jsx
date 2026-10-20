import { LogOut } from "lucide-react";
import { NavLink } from "react-router-dom";
import BrandLogo from "./BrandLogo";

const itemBase = "flex h-[54px] items-center gap-4 rounded-xl px-4 text-[17px] font-medium transition-colors";

/** The dark navigation column. `onNavigate` lets the drawer close itself on small screens. */
export default function Sidebar({ items, onLogout, onNavigate }) {
  return (
    <nav aria-label="Main navigation" className="flex h-full flex-col bg-sidebar px-4 pb-6 pt-6">
      <div className="mb-8 px-1">
        <BrandLogo />
      </div>

      <ul className="flex flex-1 flex-col gap-2">
        {items.map(({ to, label, icon: Icon, end }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={end}
              onClick={onNavigate}
              className={({ isActive }) =>
                `${itemBase} ${isActive ? "bg-brand text-white shadow-lg shadow-blue-900/30" : "text-slate-200 hover:bg-sidebar-hover"}`
              }
            >
              <Icon className="size-6 shrink-0" strokeWidth={1.9} aria-hidden="true" />
              {label}
            </NavLink>
          </li>
        ))}
      </ul>

      <button type="button" onClick={onLogout} className={`${itemBase} w-full text-slate-200 hover:bg-sidebar-hover`}>
        <LogOut className="size-6 shrink-0" strokeWidth={1.9} aria-hidden="true" />
        Logout
      </button>
    </nav>
  );
}
