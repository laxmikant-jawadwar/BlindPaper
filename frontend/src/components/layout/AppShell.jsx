import { Menu } from "lucide-react";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/authContext";
import AdminProfileModal from "./AdminProfileModal";
import NotificationBell from "./NotificationBell";
import ProfileMenu from "./ProfileMenu";
import Sidebar from "./Sidebar";
import { ADMIN_NAV, FACULTY_NAV } from "./navigation";

const DESKTOP = "(min-width: 1024px)";

/**
 * The page frame for signed-in users: dark sidebar on the left, a white header on top and the page
 * below. On a phone the sidebar is a drawer that the menu button opens.
 */
export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(() => window.matchMedia(DESKTOP).matches);
  const [profileOpen, setProfileOpen] = useState(false);

  const isAdmin = user.role === "admin";
  const closeOnPhone = () => !window.matchMedia(DESKTOP).matches && setSidebarOpen(false);
  const signOut = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-canvas">
      {/* the sidebar: fixed on the left; slides away when toggled */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[264px] transform transition-transform duration-200 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <Sidebar items={isAdmin ? ADMIN_NAV : FACULTY_NAV} onLogout={signOut} onNavigate={closeOnPhone} />
      </aside>
      {sidebarOpen && <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={() => setSidebarOpen(false)} aria-hidden="true" />}

      <div className={`transition-[padding] duration-200 ${sidebarOpen ? "lg:pl-[264px]" : ""}`}>
        <header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-slate-100 bg-white px-4 shadow-[0_1px_3px_rgba(15,27,51,0.04)] sm:px-6">
          <button
            type="button"
            onClick={() => setSidebarOpen((wasOpen) => !wasOpen)}
            aria-label={sidebarOpen ? "Hide the sidebar" : "Show the sidebar"}
            className="grid size-11 place-items-center rounded-lg text-slate-700 hover:bg-slate-100"
          >
            <Menu className="size-7" aria-hidden="true" />
          </button>

          <div className="flex items-center gap-2 sm:gap-4">
            {!isAdmin && pathname === "/faculty" && <NotificationBell />}
            <ProfileMenu
              user={user}
              onProfile={() => (isAdmin ? setProfileOpen(true) : navigate("/faculty/profile"))}
              onLogout={signOut}
            />
          </div>
        </header>

        <main className="px-4 py-7 sm:px-6 lg:px-9">
          <Outlet />
        </main>
      </div>

      {isAdmin && <AdminProfileModal open={profileOpen} onClose={() => setProfileOpen(false)} user={user} />}
    </div>
  );
}
