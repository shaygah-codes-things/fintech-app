/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useCallback } from "react";

type Toast = { id: number; text: string; type?: "error" | "success" };
export type ToastCtx = {
  notify: (text: string, type?: "error" | "success") => void;
};

const Ctx = createContext<ToastCtx>({ notify: () => {} });
export const useToast = () => useContext(Ctx);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const notify = useCallback((text: string, type?: "error" | "success") => {
    const id = Date.now() + Math.random();
    setItems((xs) => [...xs, { id, text, type }]);
    setTimeout(() => setItems((xs) => xs.filter((t) => t.id !== id)), 4000);
  }, []);

  return (
    <Ctx.Provider value={{ notify }}>
      {children}
      <div className="toast-wrap">
        {items.map((t) => (
          <div key={t.id} className={`toast ${t.type ?? ""}`}>
            {t.text}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
