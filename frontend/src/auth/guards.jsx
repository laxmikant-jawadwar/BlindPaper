import { Navigate, Outlet, useLocation } from "react-router-dom";
import Spinner from "../components/ui/Spinner";
import { homeFor, useAuth } from "./authContext";

function FullPageSpinner() {
  return (
    <div className="grid min-h-screen place-items-center bg-canvas">
      <Spinner label="Loading..." />
    </div>
  );
}

/** Only a signed-in user with this role gets through; everyone else is sent where they belong. */
export function RequireRole({ role }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  if (user.role !== role) return <Navigate to={homeFor(user)} replace />;
  return <Outlet />;
}

/** Login and register are for people who are not signed in. */
export function PublicOnly() {
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (user) return <Navigate to={homeFor(user)} replace />;
  return <Outlet />;
}
