const API =
  (import.meta.env.VITE_API_BASE as string) ?? "http://localhost:8000";

async function req(path: string, init?: RequestInit) {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) throw new Error(await res.text());
  return res;
}

export async function getMe() {
  const r = await fetch(`${API}/auth/me`, { credentials: "include" });
  if (!r.ok) throw new Error("not authenticated");
  return r.json();
}

export async function createPayout(
  amount: string,
  currency: string,
  idempKey: string
) {
  const body = { amount, currency };
  const res = await req(`/payouts`, {
    method: "POST",
    headers: {
      "Idempotency-Key": idempKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function logout() {
  const r = await fetch(`${API}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  if (!r.ok) throw new Error("Logout failed");
  return r.json();
}

export async function listPayouts(page = 1, limit = 20) {
  const r = await fetch(`${API}/payouts?page=${page}&limit=${limit}`, {
    credentials: "include",
  });
  if (!r.ok) throw new Error("Fetch payouts failed");
  return r.json();
}
