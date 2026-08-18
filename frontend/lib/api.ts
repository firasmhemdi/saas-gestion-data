import type { TokenResponse } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "saas_access_token";
const REFRESH_TOKEN_KEY = "saas_refresh_token";
const AUTH_COOKIE = "saas_auth";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface ApiOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
}

function safeGetItem(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

export function getAccessToken(): string | null {
  return safeGetItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return safeGetItem(REFRESH_TOKEN_KEY);
}

function setAuthCookie(active: boolean): void {
  if (typeof document === "undefined") return;
  const maxAge = active ? 60 * 60 * 24 * 7 : 0;
  document.cookie = `${AUTH_COOKIE}=${active ? "1" : ""}; path=/; max-age=${maxAge}; samesite=lax`;
}

export function setAuth(accessToken: string, refreshToken: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  setAuthCookie(true);
}

export function clearAuth(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  setAuthCookie(false);
  window.dispatchEvent(new Event("auth:logout"));
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return false;

  const data = (await res.json()) as TokenResponse;
  setAuth(data.access_token, data.refresh_token);
  return true;
}

async function request<T>(path: string, options: ApiOptions = {}, allowRetry = true): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (res.status === 204) return undefined as T;

  if (res.status === 401 && allowRetry && getRefreshToken()) {
    const refreshed = await tryRefresh();
    if (refreshed) return request<T>(path, options, false);
    clearAuth();
    throw new ApiError(401, "Session expirée, veuillez vous reconnecter.");
  }

  if (!res.ok) {
    let message = `Erreur ${res.status}`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (typeof data.detail === "object" && data.detail !== null) {
        const errors = data.detail as Array<{ msg?: string }>;
        message = errors.find((e) => e.msg)?.msg ?? message;
      }
    } catch {
      // réponse non JSON
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, options?: ApiOptions) => request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: ApiOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: ApiOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: ApiOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
