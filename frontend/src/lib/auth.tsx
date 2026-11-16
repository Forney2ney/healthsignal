import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { api, getToken, setToken } from "./api";

export type User = { id: number; email: string; full_name: string; role: string; clinician_verified: boolean };

type Ctx = { user: User | null; login: (email: string, password: string) => Promise<void>; logout: () => void };

const AuthCtx = createContext<Ctx>({ user: null, login: async () => {}, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);

  // Restore the session on a fresh page load: the JWT lives in localStorage,
  // so a reload should not silently sign the user out.
  useEffect(() => {
    if (!getToken()) {
      setChecking(false);
      return;
    }
    api.get<User>("/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setChecking(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const out = await api.post<{ access_token: string }>("/auth/login", { email, password });
    setToken(out.access_token);
    const me = await api.get<User>("/auth/me");
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthCtx.Provider value={{ user, login, logout }}>
      {checking ? (
        <div className="min-h-screen grid place-items-center text-sm text-muted">Restoring session…</div>
      ) : children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
export const hasToken = () => Boolean(getToken());
