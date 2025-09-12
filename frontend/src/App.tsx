/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useMemo, useState } from "react";
import { createPayout, getMe, listPayouts, logout } from "./api";
import { useToast } from "./toast";

type Row = { id: number; amount: string; currency: string; status: string };

function badgeClass(s: string) {
  if (s === "paid") return "badge paid";
  if (s === "failed") return "badge failed";
  return "badge processing";
}

function uuid(): string {
  const c: unknown = (globalThis as { crypto?: unknown }).crypto;
  const hasRandomUUID =
    typeof c === "object" &&
    c !== null &&
    "randomUUID" in (c as Record<string, unknown>) &&
    typeof (c as { randomUUID?: unknown }).randomUUID === "function";
  if (hasRandomUUID) return (c as { randomUUID: () => string }).randomUUID();
  return Math.random().toString(36).slice(2);
}

export default function App() {
  const { push } = useToast();

  // ----- pagination state -----
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [total, setTotal] = useState(0);
  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / limit)),
    [total, limit]
  );
  const canPrev = page > 1;
  const canNext = page < totalPages;

  // ----- app state -----
  const [me, setMe] = useState<{
    id: number;
    email: string;
    name?: string;
  } | null>(null);
  const [amount, setAmount] = useState("25.00");
  const [currency, setCurrency] = useState("USD");
  const [rows, setRows] = useState<Row[]>([]);
  const [busy, setBusy] = useState(false);

  async function tryGetMe() {
    try {
      setMe(await getMe());
    } catch {
      /* not logged in */
    }
  }

  function errMsg(e: unknown) {
    if (e instanceof Error) return e.message;
    if (typeof e === "string") return e;
    try {
      return JSON.stringify(e);
    } catch {
      return "Unknown error";
    }
  }

  async function refresh(p: number = page) {
    try {
      const res = await listPayouts(p, limit);
      setRows(res.items);
      setTotal(res.total);
      setPage(res.page);
    } catch (e: unknown) {
      push({ text: errMsg(e) || "Fetch failed", kind: "error" });
    }
  }

  async function doLogout() {
    try {
      await logout();
      setMe(null);
      setRows([]);
      setTotal(0);
      setPage(1);
      push({ text: "Logged out", kind: "success" });
    } catch (e: unknown) {
      push({ text: errMsg(e) || "Logout failed", kind: "error" });
    }
  }

  async function submit() {
    setBusy(true);
    try {
      const key = uuid();
      await createPayout(amount, currency.toUpperCase(), key);
      push({ text: "Payout created", kind: "success" });
      await refresh();
    } catch (e: unknown) {
      push({ text: errMsg(e) || "Create failed", kind: "error" });
    } finally {
      setBusy(false);
    }
  }

  const goto = async (p: number) => {
    const clamped = Math.min(Math.max(1, p), totalPages);
    setPage(clamped);
    await refresh(clamped);
  };

  useEffect(() => {
    tryGetMe();
  }, []);
  useEffect(() => {
    if (!me) return;
    void refresh(page);
    const t = setInterval(() => void refresh(page), 2500);
    return () => clearInterval(t);
  }, [me, page]);

  const loggedIn = useMemo(() => !!me, [me]);

  return (
    <div className="container">
      {/* header + login/logout */}
      <div style={{ marginBottom: 18 }}>
        <h1 className="h1">Fintech Payouts</h1>
        {!loggedIn ? (
          <div
            className="card"
            style={{ display: "flex", gap: 10, alignItems: "center" }}
          >
            <a
              className="btn"
              href={`${import.meta.env.VITE_API_BASE}/auth/login`}
            >
              Login with GitHub
            </a>
          </div>
        ) : (
          <div
            className="subtle"
            style={{ display: "flex", gap: 12, alignItems: "center" }}
          >
            <span>
              Logged in: <strong>{me?.email}</strong>
            </span>
            <button className="btn" onClick={() => void doLogout()}>
              Logout
            </button>
          </div>
        )}
      </div>

      {loggedIn && (
        <>
          {/* create payout */}
          <div
            className="card"
            style={{
              display: "grid",
              gridTemplateColumns: "220px 120px auto",
              gap: 10,
              alignItems: "center",
              marginBottom: 18,
            }}
          >
            <input
              className="input"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Amount e.g. 25.00"
            />
            <input
              className="input"
              value={currency}
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
              placeholder="USD"
            />
            <div>
              <button
                className="btn"
                onClick={() => void submit()}
                disabled={busy}
              >
                {busy ? "Creating..." : "Create"}
              </button>
            </div>
          </div>

          {/* table + pagination */}
          <div className="card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
              }}
            >
              <h3 style={{ margin: 0 }}>Your Payouts</h3>
              <button className="btn" onClick={() => void refresh()}>
                Refresh
              </button>
            </div>

            <table className="table" style={{ marginTop: 10 }}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Amount</th>
                  <th>Currency</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.amount}</td>
                    <td>{r.currency}</td>
                    <td>
                      <span className={badgeClass(r.status)}>{r.status}</span>
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={4} className="subtle">
                      No payouts yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <div
              style={{
                display: "flex",
                gap: 8,
                alignItems: "center",
                justifyContent: "flex-end",
                marginTop: 12,
              }}
            >
              <button
                className="btn"
                disabled={!canPrev}
                onClick={() => void goto(page - 1)}
              >
                Prev
              </button>
              <span className="subtle">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn"
                disabled={!canNext}
                onClick={() => void goto(page + 1)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
