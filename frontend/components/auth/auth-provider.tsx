"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, clearAuth, getAccessToken, getRefreshToken, setAuth } from "@/lib/api";
import type { LoginResult, RegisterPayload, RegisterResult, TokenResponse, User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  verifyOtp: (otpToken: string, code: string) => Promise<void>;
  resendOtp: (otpToken: string) => Promise<LoginResult>;
  register: (payload: RegisterPayload) => Promise<RegisterResult>;
  verifyEmail: (verificationToken: string, code: string) => Promise<void>;
  resendEmailVerification: (verificationToken: string) => Promise<RegisterResult>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      try {
        if (!getAccessToken()) {
          setUser(null);
          return;
        }
        const me = await api.get<User>("/auth/me");
        if (!cancelled) setUser(me);
      } catch {
        clearAuth();
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const applyTokens = useCallback((tokens: TokenResponse) => {
    setAuth(tokens.access_token, tokens.refresh_token);
    setUser(tokens.user);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await api.post<LoginResult>("/auth/login", { email, password });
      if (!("requires_otp" in result)) applyTokens(result as TokenResponse);
      return result;
    },
    [applyTokens],
  );

  const verifyOtp = useCallback(
    async (otpToken: string, code: string) => {
      const tokens = await api.post<TokenResponse>("/auth/otp/verify", {
        otp_token: otpToken,
        code,
      });
      applyTokens(tokens);
    },
    [applyTokens],
  );

  const resendOtp = useCallback(async (otpToken: string) => {
    return api.post<LoginResult>("/auth/otp/resend", { challenge_token: otpToken });
  }, []);

  const register = useCallback(
    async (payload: RegisterPayload) => {
      const result = await api.post<RegisterResult>("/auth/register", payload);
      if (!("requires_email_verification" in result)) applyTokens(result as TokenResponse);
      return result;
    },
    [applyTokens],
  );

  const verifyEmail = useCallback(
    async (verificationToken: string, code: string) => {
      const tokens = await api.post<TokenResponse>("/auth/email/verify", {
        verification_token: verificationToken,
        code,
      });
      applyTokens(tokens);
    },
    [applyTokens],
  );

  const resendEmailVerification = useCallback(async (verificationToken: string) => {
    return api.post<RegisterResult>("/auth/email/resend", { challenge_token: verificationToken });
  }, []);

  const logout = useCallback(async () => {
    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) await api.post<void>("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // la révocation locale reste nécessaire même si l'API est injoignable
    } finally {
      clearAuth();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      verifyOtp,
      resendOtp,
      register,
      verifyEmail,
      resendEmailVerification,
      logout,
    }),
    [user, loading, login, verifyOtp, resendOtp, register, verifyEmail, resendEmailVerification, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans un AuthProvider.");
  return ctx;
}
