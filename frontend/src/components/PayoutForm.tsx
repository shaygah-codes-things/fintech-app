/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { createPayout } from "../api";
import { useToast } from "../ui/Toast";
import { usePayoutsRefresh } from "../context/PayoutsRefresh";

const CURRENCIES = ["USD", "EUR", "GBP"];

export function PayoutForm() {
  const { notify } = useToast();
  const { bump } = usePayoutsRefresh();
  const [amount, setAmount] = useState("10.00");
  const [currency, setCurrency] = useState("USD");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);

    // normalize amount & currency
    let amt = amount.trim().replace(",", ".");
    const [int, frac = ""] = amt.split(".");
    amt = `${int}.${(frac + "00").slice(0, 2)}`;
    const cur = currency.trim().toUpperCase();
    const key = crypto.randomUUID();

    try {
      await createPayout({ amount: amt, currency: cur }, key);
      notify("Payout created", "success");
      bump(); // tell the list to reload
    } catch (e: any) {
      if (e?.status === 401) notify("Please login first.", "error");
      else if (e?.status === 429) notify("⚡ Too many requests.", "error");
      else notify(`Create failed: ${e?.message ?? e?.status}`, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="card"
      style={{ marginBottom: 20, display: "flex", gap: 12, flexWrap: "wrap" }}
    >
      <input
        className="input"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="10.00"
        required
      />
      <select
        className="input"
        value={currency}
        onChange={(e) => setCurrency(e.target.value)}
      >
        {CURRENCIES.map((c) => (
          <option key={c}>{c}</option>
        ))}
      </select>
      <button className="btn" type="submit" disabled={busy}>
        {busy ? "Creating…" : "Create payout"}
      </button>
    </form>
  );
}
