import type {
  ApiError,
  Candidate,
  CandidateProfileUpdate,
  DashboardResponse,
  FeedResponse,
  JobListing,
  JobListingCreate,
  Match,
  MatchBreakdown,
  Application,
  TokenResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(access_token: string, refresh_token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_role");
}

let refreshPromise: Promise<string> | null = null;

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let token = getToken();
  let headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  let res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && path !== "/auth/login" && path !== "/auth/refresh") {
    // Try to refresh the token
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      if (!refreshPromise) {
        refreshPromise = fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
          .then(async (refreshRes) => {
            if (!refreshRes.ok) throw new Error("Refresh failed");
            const data = await refreshRes.json();
            setTokens(data.access_token, data.refresh_token);
            return data.access_token;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      try {
        token = await refreshPromise;
        // Retry the original request
        headers = {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          ...options.headers,
        };
        res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
      } catch (e) {
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    } else {
      clearTokens();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  }

  if (!res.ok) {
    const err: ApiError = await res.json().catch(() => ({
      error: { code: "UNKNOWN", message: `Request failed with status ${res.status}`, field: null },
    }));
    throw new Error(err.error?.message || `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  // Auth
  login: (email: string, password: string): Promise<TokenResponse> =>
    request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  registerCandidate: (data: { email: string; password: string; name: string }): Promise<TokenResponse> =>
    request("/api/v1/auth/candidate/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  registerCompany: (data: {
    company_name: string;
    industry?: string;
    description?: string;
    recruiter_email: string;
    recruiter_password: string;
  }): Promise<TokenResponse> =>
    request("/api/v1/auth/company/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  refreshToken: (refresh_token: string): Promise<TokenResponse> =>
    request("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  // Candidate
  getCandidateProfile: (): Promise<Candidate> => request("/api/v1/candidate/profile"),

  updateCandidateProfile: (data: CandidateProfileUpdate): Promise<Candidate> =>
    request("/api/v1/candidate/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getFeed: (cursor?: string): Promise<FeedResponse> =>
    request(`/api/v1/candidate/feed${cursor ? `?cursor=${cursor}` : ""}`),

  swipe: (job_listing_id: string, direction: "left" | "right"): Promise<{
    id: string;
    direction: string;
    created_at: string;
    matched: boolean;
    match_id: string | null;
    application_id: string | null;
    score: number | null;
    score_breakdown: Record<string, number> | null;
  }> =>
    request("/api/v1/candidate/swipe", {
      method: "POST",
      body: JSON.stringify({ job_listing_id, direction }),
    }),

  getMatches: (): Promise<Match[]> => request("/api/v1/candidate/matches"),

  getMatchBreakdown: (matchId: string): Promise<MatchBreakdown> =>
    request(`/api/v1/candidate/matches/${matchId}/breakdown`),

  resetSwipes: (): Promise<{ status: string }> =>
    request("/api/v1/candidate/swipes", { method: "DELETE" }),

  // Company
  getDashboard: (): Promise<DashboardResponse> => request("/api/v1/company/dashboard"),

  getJobs: (): Promise<JobListing[]> => request("/api/v1/company/jobs"),

  createJob: (data: JobListingCreate): Promise<JobListing> =>
    request("/api/v1/company/jobs", { method: "POST", body: JSON.stringify(data) }),

  patchJob: (jobId: string, data: Partial<JobListingCreate & { is_active: boolean }>): Promise<JobListing> =>
    request(`/api/v1/company/jobs/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getJobApplications: (jobId: string): Promise<Application[]> =>
    request(`/api/v1/company/jobs/${jobId}/applications`),

  updateApplicationStatus: (
    applicationId: string,
    status: "rejected" | "interview"
  ): Promise<Application> =>
    request(`/api/v1/company/applications/${applicationId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};
