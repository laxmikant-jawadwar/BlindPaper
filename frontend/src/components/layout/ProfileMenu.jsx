import { ChevronDown, LogOut, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { initial } from "../../lib/format";

/** The avatar, name and department at the right of the header, with My Profile and Logout. */
export default function ProfileMenu({ user, onProfile, onLogout }) {
  const [open, setOpen] = useState(false);
  const box = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (event) => !box.current?.contains(event.target) && setOpen(false);
    const onKey = (event) => event.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const subtitle = user.role === "admin" ? user.designation || "Administrator" : `${user.department} Department`;

  const choose = (action) => {
    setOpen(false);
    action();
  };

  return (
    <div className="relative" ref={box}>
      <button
        type="button"
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-3 rounded-xl px-2 py-1.5 hover:bg-slate-50"
      >
        <span className="grid size-11 place-items-center rounded-full bg-brand text-lg font-semibold text-white">{initial(user.name)}</span>
        <span className="hidden text-left leading-tight sm:block">
          <span className="block text-base font-semibold text-ink">{user.name}</span>
          <span className="block text-[13px] text-slate-500">{subtitle}</span>
        </span>
        <ChevronDown className="size-5 text-slate-600" aria-hidden="true" />
      </button>

      {open && (
        <div role="menu" className="absolute right-0 z-30 mt-2 w-52 rounded-xl border border-slate-200 bg-white py-1.5 shadow-xl">
          <button
            type="button"
            role="menuitem"
            onClick={() => choose(onProfile)}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            <User className="size-4" aria-hidden="true" /> My Profile
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => choose(onLogout)}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
          >
            <LogOut className="size-4" aria-hidden="true" /> Logout
          </button>
        </div>
      )}
    </div>
  );
}
