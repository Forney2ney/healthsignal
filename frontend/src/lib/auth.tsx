import { createContext, useCallback, useContext, useState, ReactNode } from "react";
import { api, getToken, setToken } from "./api";

export type User = { id: number; email: string; full_name: string; role: string; clinician_verified: boolean };

type Ctx = { user: User | null; login: (email: string, password: string) => Promise<void>; logout: () => void };

const AuthCtx = createContext<Ctx>({ user: null, login: async () => {}, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

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

  return <AuthCtx.Provider value={{ user, login, logout }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
export const hasToken = () => Boolean(getToken());