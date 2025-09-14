/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useCallback, useContext, useState } from "react";

type Ctx = { version: number; bump: () => void };
const PayoutsCtx = createContext<Ctx>({ version: 0, bump: () => {} });

export function PayoutsRefreshProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [version, setVersion] = useState(0);
  const bump = useCallback(() => setVersion((v) => v + 1), []);
  return (
    <PayoutsCtx.Provider value={{ version, bump }}>
      {children}
    </PayoutsCtx.Provider>
  );
}

export const usePayoutsRefresh = () => useContext(PayoutsCtx);
