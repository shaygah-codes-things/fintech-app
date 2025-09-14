/* eslint-disable @typescript-eslint/no-explicit-any */
const API = import.meta.env.VITE_API_BASE as string;

type HttpError = {
  status: number;
  code?: string;
  message?: string;
  request_id?: string;
  __raw?: any;
};

type RequestInitEx = Omit<RequestInit, "body" | "headers"> & {
  body?: any;
  headers?: HeadersInit;
};

async function http<T>(path: string, init: RequestInitEx = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  let bodyToSend = init.body;

  const isPlainObject =
    bodyToSend &&
    typeof bodyToSend === "object" &&
    !(bodyToSend instanceof FormData) &&
    !(bodyToSend instanceof Blob) &&
    !(bodyToSend instanceof ArrayBuffer);

  if (isPlainObject) {
    bodyToSend = JSON.stringify(bodyToSend);
    headers.set("Content-Type", "application/json; charset=utf-8");
  } else if (typeof bodyToSend === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json; charset=utf-8");
  }

  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    ...init,
    headers,
    body: bodyToSend as BodyInit | null | undefined, // <-- cast for TS
  });

  if (!res.ok) {
    let payload: any = undefined;
    try {
      payload = await res.json();
    } catch {
      /* empty */
    }
    const err: HttpError = {
      status: res.status,
      code: payload?.error,
      message: payload?.message || payload?.detail || res.statusText,
      request_id: payload?.request_id,
      __raw: payload,
    };
    throw err;
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ---------- API surface ----------

export async function authLogin(): Promise<void> {
  window.location.href = `${API}/auth/login`;
}

export type Me = { user_id: number; email: string };
export async function getMe(): Promise<Me> {
  return http<Me>("/auth/me");
}
export async function logout(): Promise<{ ok: true }> {
  return http<{ ok: true }>("/auth/logout", { method: "POST" });
}

export type CreatePayoutBody = { amount: string; currency: string };
export type Payout = {
  id: number;
  amount: string;
  currency: string;
  status: "pending" | "processing" | "paid" | "failed";
};
export type Page<T> = {
  page: number;
  limit: number;
  total: number;
  items: T[];
};

export async function createPayout(
  body: CreatePayoutBody,
  idempotencyKey: string
): Promise<Payout> {
  // pass object; http() handles stringify + headers
  return http<Payout>("/payouts", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body,
  });
}

export async function listPayouts(page = 1, limit = 10): Promise<Page<Payout>> {
  return http<Page<Payout>>(`/payouts?page=${page}&limit=${limit}`);
}
