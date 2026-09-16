"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { apiClient, clearTokens, getToken, setTokens } from "@/lib/api-client";
import type { Candidate, TokenResponse } from "@/lib/types";

interface UserSession {
  id: string;
  role: "candidate" | "recruiter";
  tenant_id?: string | null;
}

interface AuthContextType {
  user: UserSession | null;
  candidateProfile: Candidate | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<"candidate" | "recruiter">;
  registerCandidate: (data: { name: string; email: string; password: string }) => Promise<void>;
  registerCompany: (data: {
    company_name: string;
    industry?: string;
    description?: string;
    recruiter_email: string;
    recruiter_password: string;
  }) => Promise<void>;
  logout: () => void;
  refreshCandidateProfile: () => Promise<Candidate | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function decodeJwtPayload(token: string): any {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [candidateProfile, setCandidateProfile] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadProfileForCandidate() {
    try {
      const profile = await apiClient.getCandidateProfile();
      setCandidateProfile(profile);
      return profile;
    } catch (err) {
      console.warn("Candidate profile not found or uninitialized:", err);
      return null;
    }
  }

  useEffect(() => {
    const token = getToken();
    if (token) {
      const payload = decodeJwtPayload(token);
      if (payload && payload.sub) {
        const role = payload.role === "candidate" ? "candidate" : "recruiter";
        setUser({ id: payload.sub, role, tenant_id: payload.tenant_id });
        if (role === "candidate") {
          loadProfileForCandidate().finally(() => setLoading(false));
          return;
        }
      } else {
        clearTokens();
      }
    }
    setLoading(false);
  }, []);

  async function login(email: string, password: string): Promise<"candidate" | "recruiter"> {
    const res: TokenResponse = await apiClient.login(email, password);
    setTokens(res.access_token, res.refresh_token);
    const payload = decodeJwtPayload(res.access_token);
    const role: "candidate" | "recruiter" =
      payload?.role === "candidate" ? "candidate" : "recruiter";

    setUser({
      id: payload.sub,
      role,
      tenant_id: payload?.tenant_id,
    });

    if (role === "candidate") {
      await loadProfileForCandidate();
    }
    return role;
  }

  async function registerCandidate(data: { name: string; email: string; password: string }) {
    const res = await apiClient.registerCandidate(data);
    setTokens(res.access_token, res.refresh_token);
    const payload = decodeJwtPayload(res.access_token);
    setUser({ id: payload.sub, role: "candidate" });
    await loadProfileForCandidate();
  }

  async function registerCompany(data: {
    company_name: string;
    industry?: string;
    description?: string;
    recruiter_email: string;
    recruiter_password: string;
  }) {
    const res = await apiClient.registerCompany(data);
    setTokens(res.access_token, res.refresh_token);
    const payload = decodeJwtPayload(res.access_token);
    setUser({ id: payload.sub, role: "recruiter", tenant_id: payload?.tenant_id });
  }

  function logout() {
    clearTokens();
    setUser(null);
    setCandidateProfile(null);
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  }

  async function refreshCandidateProfile() {
    return await loadProfileForCandidate();
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        candidateProfile,
        loading,
        login,
        registerCandidate,
        registerCompany,
        logout,
        refreshCandidateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
