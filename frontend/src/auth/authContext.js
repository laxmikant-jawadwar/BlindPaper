import { createContext, useContext } from "react";

export const AuthContext = createContext(null);

/** The signed-in user and the actions on the session: { user, loading, login, register, logout, updateProfile }. */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>.");
  return context;
}

/** Where each role lands after signing in. */
export function homeFor(user) {
  return user?.role === "admin" ? "/admin" : "/faculty";
}
