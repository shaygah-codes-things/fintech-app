/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useCallback, useRef } from "react";
import { listPayouts, createPayout } from "../api";
import type { Payout, Page } from "../api";
import { useToast } from "../ui/Toast";
import { usePayoutsRefresh } from "../context/PayoutsRefresh";

const LIMIT = 10;
const MAX_POLLS = 6;
const BASE_DELAY_MS = 1200;

function Badge({ status }: { status: Payout["status"] }) {
  return <span className={`badge ${status}`}>{status}</span>;
}

export function PayoutList() {
  const { notify } = useToast();
  const { version, bump } = usePayoutsRefresh();

  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<Payout> | null>(null);
  const [loading, setLoading] = useState(false);

  // polling state
  const pollTimer = useRef<number | null>(null);
  const pollCount = useRef(0);

  const clearPoll = () => {
    if (pollTimer.current != null) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const schedulePoll = (p: number, immediate = false) => {
    if (pollCount.current >= MAX_POLLS) return;
    const delay = immediate
      ? 0
      : Math.min(BASE_DELAY_MS * 2 ** pollCount.current, 6000);
    clearPoll();
    pollTimer.current = window.setTimeout(async () => {
      pollCount.current += 1;
      await load(p);
    }, delay) as unknown as number;
  };

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const res = await listPayouts(p, LIMIT);
        setData(res);
        setPage(p);

        const hasProcessing = res.items.some((i) => i.status === "processing");
        if (hasProcessing) {
          schedulePoll(p, false);
        } else {
          clearPoll();
          pollCount.current = 0;
        }
      } catch (e: any) {
        clearPoll();
        if (e?.status === 401) notify("Please login.", "error");
        else if (e?.status === 429)
          notify("Too many requests. Try again shortly.", "error");
        else notify(`Fetch failed: ${e?.message ?? e?.status}`, "error");
      } finally {
        setLoading(false);
      }
    },
    [notify]
  );

  // initial load
  useEffect(() => {
    load(1);
    return clearPoll;
  }, [load]);

  useEffect(() => {
    if (version > 0) {
      pollCount.current = 0;
      clearPoll();
      load(1);
      schedulePoll(1, true);
    }
  }, [version, load]);

  async function retryAsReplacement(item: Payout) {
    try {
      const key = crypto.randomUUID();
      await createPayout({ amount: item.amount, currency: item.currency }, key);
      notify("Retry submitted", "success");
      bump(); // triggers version effect above
    } catch (e: any) {
      if (e?.status === 429) notify("⚡ Too many requests.", "error");
      else notify(`Retry failed: ${e?.message ?? e?.status}`, "error");
    }
  }

  const total = data?.total ?? 0;
  const from = Math.max(total - (page - 1) * LIMIT, 0);
  const to = data ? Math.max(from - data.items.length + 1, 0) : 0;

  const canPrev = page > 1;
  const canNext = data ? page * LIMIT < data.total : false;

  const onPrev = () => {
    if (canPrev && !loading) load(page - 1);
  };
  const onNext = () => {
    if (canNext && !loading) load(page + 1);
  };
  const onManualRefresh = () => {
    pollCount.current = 0;
    clearPoll();
    load(page);
  };

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <h3>Payouts</h3>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {data && (
            <span style={{ fontSize: 13, color: "var(--muted)" }}>
              {from}–{to} of {total}
            </span>
          )}
          <button className="btn" onClick={onManualRefresh} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Amount</th>
            <th>Currency</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.items.map((i) => (
            <tr key={i.id}>
              <td>{i.id}</td>
              <td>{i.amount}</td>
              <td>{i.currency}</td>
              <td>
                <Badge status={i.status} />
              </td>
              <td style={{ display: "flex", gap: 8 }}>
                {i.status === "failed" && (
                  <button className="btn" onClick={() => retryAsReplacement(i)}>
                    Create new attempt
                  </button>
                )}
              </td>
            </tr>
          ))}
          {(!data || data.items.length === 0) && (
            <tr>
              <td colSpan={5}>{loading ? "Loading…" : "No payouts yet"}</td>
            </tr>
          )}
        </tbody>
      </table>

      <div
        style={{
          marginTop: 12,
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <button className="btn" disabled={!canPrev || loading} onClick={onPrev}>
          Prev
        </button>
        <button className="btn" disabled={!canNext || loading} onClick={onNext}>
          Next
        </button>
      </div>
    </div>
  );
}
