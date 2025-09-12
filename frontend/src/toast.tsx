import { createContext, useContext, useState, type ReactNode } from "react";

type Kind = "success" | "error";
type Toast = { id: string; text: string; kind?: Kind };
const Ctx = createContext<{ push: (t: Omit<Toast, "id">) => void } | null>(
  null
);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = (t: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).slice(2);
    setItems((s) => [...s, { id, ...t }]);
    setTimeout(() => setItems((s) => s.filter((x) => x.id !== id)), 3000);
  };
  return (
    <Ctx.Provider value={{ push }}>
      <div className="toast-wrap">
        {items.map((x) => (
          <div key={x.id} className={`toast ${x.kind ?? ""}`}>
            {x.text}
          </div>
        ))}
      </div>
      {children}
    </Ctx.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => {
  const v = useContext(Ctx);
  if (!v) throw new Error("useToast must be inside <ToastProvider>");
  return v;
};
