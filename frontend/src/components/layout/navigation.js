import { Building2, FileText, House, ListChecks, User, Users } from "lucide-react";

export const FACULTY_NAV = [
  { to: "/faculty", label: "Dashboard", icon: House, end: true },
  { to: "/faculty/generate", label: "Generate Paper", icon: FileText },
  { to: "/faculty/papers", label: "My Papers", icon: ListChecks },
  { to: "/faculty/profile", label: "Profile", icon: User },
];

export const ADMIN_NAV = [
  { to: "/admin", label: "Dashboard", icon: House, end: true },
  { to: "/admin/papers", label: "All Papers", icon: FileText },
  { to: "/admin/faculty", label: "Faculty", icon: Users },
  { to: "/admin/departments", label: "Departments", icon: Building2 },
];
