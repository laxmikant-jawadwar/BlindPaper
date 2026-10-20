import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { homeFor, useAuth } from "./auth/authContext";
import AuthProvider from "./auth/AuthProvider";
import { PublicOnly, RequireRole } from "./auth/guards";
import AppShell from "./components/layout/AppShell";
import AdminAllPapers from "./pages/admin/AllPapers";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminDepartments from "./pages/admin/Departments";
import AdminFaculty from "./pages/admin/Faculty";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ConfigurePaper from "./pages/faculty/ConfigurePaper";
import FacultyDashboard from "./pages/faculty/Dashboard";
import GeneratePaper from "./pages/faculty/GeneratePaper";
import MyPapers from "./pages/faculty/MyPapers";
import PaperPreview from "./pages/faculty/PaperPreview";
import Profile from "./pages/faculty/Profile";

/** "/" sends people to their own area, or to the sign-in page. */
function Home() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return <Navigate to={user ? homeFor(user) : "/login"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />

          <Route element={<PublicOnly />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Route>

          <Route element={<RequireRole role="faculty" />}>
            <Route element={<AppShell />}>
              <Route path="/faculty" element={<FacultyDashboard />} />
              <Route path="/faculty/generate" element={<GeneratePaper />} />
              <Route path="/faculty/generate/:syllabusId" element={<ConfigurePaper />} />
              <Route path="/faculty/papers" element={<MyPapers />} />
              <Route path="/faculty/papers/:paperId" element={<PaperPreview />} />
              <Route path="/faculty/profile" element={<Profile />} />
            </Route>
          </Route>

          <Route element={<RequireRole role="admin" />}>
            <Route element={<AppShell />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/papers" element={<AdminAllPapers />} />
              <Route path="/admin/faculty" element={<AdminFaculty />} />
              <Route path="/admin/departments" element={<AdminDepartments />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
