import { useCallback, useEffect, useMemo, useState } from "react";
import { api, onUnauthorized, tokenStore } from "../api/client";
import { AuthContext } from "./authContext";

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(tokenStore.get()));

  // Restore the session after a page reload
  useEffect(() => {
    if (!tokenStore.get()) return;
    let cancelled = false;
    api.auth
      .me()
      .then((me) => !cancelled && setUser(me))
      .catch(() => tokenStore.clear())
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  // The server ended our session (it expired, or we signed out elsewhere)
  useEffect(() => {
    onUnauthorized(() => setUser(null));
    return () => onUnauthorized(null);
  }, []);

  const startSession = useCallback(({ token, user: signedIn }) => {
    tokenStore.set(token);
    setUser(signedIn);
    return signedIn;
  }, []);

  const login = useCallback(async (email, password) => startSession(await api.auth.login(email, password)), [startSession]);
  const register = useCallback(async (details) => startSession(await api.auth.register(details)), [startSession]);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch {
      /* the session may already be gone; either way we are signed out here */
    }
    tokenStore.clear();
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (changes) => {
    const updated = await api.auth.updateMe(changes);
    setUser(updated);
    return updated;
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, updateProfile }),
    [user, loading, login, register, logout, updateProfile],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
