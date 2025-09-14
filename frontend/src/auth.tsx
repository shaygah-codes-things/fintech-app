/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-refresh/only-export-components */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { type Me, getMe, authLogin, logout } from "./api";
import { useToast } from "./ui/Toast";

type AuthCtx = {
  me?: Me | null;
  loading: boolean;
  login: () => void;
  doLogout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const Ctx = createContext<AuthCtx>({
  me: null,
  loading: true,
  login: () => {},
  doLogout: async () => {},
  refresh: async () => {},
});

export function useAuth() {
  return useContext(Ctx);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { notify } = useToast();
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const m = await getMe();
      setMe(m);
    } catch (e: any) {
      if (e?.status && e.status !== 401) {
        notify(`Auth error: ${e.message ?? e.status}`);
      }
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = () => authLogin();
  const doLogout = async () => {
    try {
      await logout();
      setMe(null);
    } catch (e: any) {
      notify(`Logout failed: ${e.message ?? e.status}`);
    }
  };

  return (
    <Ctx.Provider value={{ me, loading, login, doLogout, refresh }}>
      {children}
    </Ctx.Provider>
  );
}
